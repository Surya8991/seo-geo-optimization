# shellcheck shell=sh
# Shared pre-push guards, sourced by .githooks/pre-push.
#
# This file is IDENTICAL in every repo under Coding\. The master copy is
# _workspace/templates/githooks/lib/guards.sh; edit it there and copy it out,
# never fork it per project. Project-specific checks live in .githooks/pre-push.
#
# Guards (always run, cheap, no dependencies beyond git + POSIX sh):
#   1. Block pushes that update or delete main/master.
#   2. Block commits authored/committed as edstellarmarketing on repos it
#      doesn't own (same rule as the check-git-identity CI workflow).
#   3. Block commits that ADD secret-looking files (.env, keys.env, *.pem...).
#   4. Block commits that ADD lines matching high-confidence secret patterns.
#
# Environment switches:
#   PREPUSH_ALLOW_MAIN=1   let a human push to main/master on purpose
#   PREPUSH_FULL=1         also run the slow steps (production build, etc.)
#   git push --no-verify   skip the hook entirely (emergencies only)
#
# Suppressions:
#   - put `pre-push:allow-secret` on a line to skip it in the content scan
#   - list path globs in .githooks/secret-allowlist (one per line, # comments)

PP_FAILED=0
PP_HAS_UPDATES=0
PP_START=$(date +%s)

pp_say()  { printf '[pre-push] %s\n' "$*"; }
pp_warn() { printf '[pre-push] WARN: %s\n' "$*" >&2; }
pp_fail() { printf '[pre-push] BLOCKED: %s\n' "$*" >&2; PP_FAILED=1; }

pp_is_zero() { case $1 in *[!0]*) return 1 ;; *) return 0 ;; esac; }

pp_cleanup() { [ -n "${PP_TMP:-}" ] && rm -rf "$PP_TMP"; }

# pp_init <remote-name> <remote-url>   (reads git's ref list from stdin)
pp_init() {
  PP_REMOTE_NAME=${1:-}
  PP_REMOTE_URL=${2:-}
  PP_ROOT=$(git rev-parse --show-toplevel) || exit 1
  PP_TMP=$(mktemp -d 2>/dev/null || mktemp -d -t prepush)
  trap pp_cleanup EXIT
  trap 'pp_cleanup; exit 130' INT TERM
  cat > "$PP_TMP/refs"
  : > "$PP_TMP/commits"
  PP_PUSHED_TIPS=""
}

# Load .githooks/secret-allowlist (path globs) into PP_ALLOW.
pp_load_allowlist() {
  PP_ALLOW=""
  f="$PP_ROOT/.githooks/secret-allowlist"
  [ -f "$f" ] || return 0
  PP_ALLOW=$(sed -e 's/#.*//' -e 's/[[:space:]]*$//' -e '/^$/d' "$f" | tr -d '\r')
}

pp_path_allowed() {
  case $1 in .githooks/lib/guards.sh) return 0 ;; esac
  [ -n "$PP_ALLOW" ] || return 1
  old_ifs=$IFS; IFS='
'
  for g in $PP_ALLOW; do
    # shellcheck disable=SC2254
    case $1 in $g) IFS=$old_ifs; return 0 ;; esac
  done
  IFS=$old_ifs
  return 1
}

# 1. Branch guard + collect the commits that are new to the remote.
pp_guard_refs() {
  while read -r lref lsha rref rsha; do
    [ -n "${lref:-}" ] || continue
    case $rref in
      refs/heads/main|refs/heads/master)
        if [ "${PREPUSH_ALLOW_MAIN:-}" = "1" ]; then
          pp_warn "pushing to ${rref#refs/heads/} because PREPUSH_ALLOW_MAIN=1"
        else
          pp_fail "direct push to '${rref#refs/heads/}' is not allowed. Push a feature/fix branch and open a PR (workspace AGENTS.md section 3)."
        fi ;;
    esac
    if pp_is_zero "$lsha"; then
      continue  # branch/tag deletion: nothing to scan
    fi
    PP_HAS_UPDATES=1
    PP_PUSHED_TIPS="$PP_PUSHED_TIPS $lsha"
    if ! pp_is_zero "$rsha" && git cat-file -e "$rsha^{commit}" 2>/dev/null; then
      git rev-list "$rsha..$lsha" >> "$PP_TMP/commits" 2>/dev/null
    else
      git rev-list "$lsha" --not --remotes >> "$PP_TMP/commits" 2>/dev/null
    fi
  done < "$PP_TMP/refs"
  sort -u "$PP_TMP/commits" -o "$PP_TMP/commits"
  PP_COMMIT_COUNT=$(wc -l < "$PP_TMP/commits" | tr -d ' ')
}

# 2. Identity guard (mirrors .github/workflows/check-git-identity.yml).
pp_guard_identity() {
  [ -s "$PP_TMP/commits" ] || return 0
  case $(printf '%s' "$PP_REMOTE_URL" | tr '[:upper:]' '[:lower:]') in
    *github.com[:/]edstellarmarketing/*) return 0 ;;
  esac
  bad=$(git log --no-walk --stdin --format='%h %an <%ae> / %cn <%ce>' < "$PP_TMP/commits" \
        | grep -i 'edstellarmarketing')
  if [ -n "$bad" ]; then
    pp_fail "commits use the edstellarmarketing identity on a repo it doesn't own:"
    printf '%s\n' "$bad" | sed 's/^/           /' >&2
    printf '           Fix: git config user.name/user.email, then rewrite those commits locally.\n' >&2
  fi
}

# 3. Secret-file guard: files ADDED in the pushed commits.
pp_guard_secret_files() {
  [ -s "$PP_TMP/commits" ] || return 0
  git log --no-walk --stdin --format= --name-only --diff-filter=A < "$PP_TMP/commits" \
    | sort -u > "$PP_TMP/added"
  found=""
  while IFS= read -r p; do
    [ -n "$p" ] || continue
    pp_path_allowed "$p" && continue
    base=${p##*/}
    case $base in
      *.example|*.sample|*.template|*.dist) ;;
      .env|.env.*|*.env|*.pem|*.p12|*.pfx|*.key|*.keystore|*.jks|id_rsa|id_dsa|id_ecdsa|id_ed25519)
        found="$found
           $p" ;;
    esac
  done < "$PP_TMP/added"
  if [ -n "$found" ]; then
    pp_fail "pushed commits add secret-looking files (never commit .env/keys):$found"
    printf '           Fix: git rm --cached <file>, add it to .gitignore, rewrite the commit. If it is safe, list it in .githooks/secret-allowlist.\n' >&2
  fi
}

# 4. Secret-content guard: high-confidence token patterns on ADDED lines.
PP_SECRET_RE='AKIA[0-9A-Z]{16}|(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{50,}|xox[abprs]-[A-Za-z0-9-]{10,}|(sk|rk)_live_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{35}|GOCSPX-[A-Za-z0-9_-]{24,}|sk-ant-[A-Za-z0-9_-]{20,}|sk-(proj|svcacct|admin)-[A-Za-z0-9_-]{20,}|-----BEGIN ([A-Z]+ )?PRIVATE KEY-----|hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[A-Za-z0-9]{16,}|discord(app)?\.com/api/webhooks/[0-9]+/[A-Za-z0-9_-]{40,}|postgres(ql)?://[^:@/ ]+:[^@/ ]{12,}@[^/ ]*(neon\.tech|supabase\.co|supabase\.com|rds\.amazonaws\.com)' # pre-push:allow-secret

pp_guard_secret_content() {
  [ -s "$PP_TMP/commits" ] || return 0
  git log --no-walk --stdin -p -U0 --format='commit %h' --no-color --no-ext-diff --no-textconv \
      < "$PP_TMP/commits" 2>/dev/null \
    | awk '/^commit [0-9a-f]+$/ { c=$2; next }
           /^\+\+\+ / { f=substr($0,5); sub(/^b\//,"",f); next }
           /^\+/ { print c "\t" f "\t" substr($0,2) }' > "$PP_TMP/added_lines"
  grep -E "$PP_SECRET_RE" "$PP_TMP/added_lines" 2>/dev/null \
    | grep -v 'pre-push:allow-secret' > "$PP_TMP/hits"
  [ -s "$PP_TMP/hits" ] || return 0
  tab=$(printf '\t')
  report=""
  while IFS="$tab" read -r c f line; do
    pp_path_allowed "$f" && continue
    m=$(printf '%s\n' "$line" | grep -oE "$PP_SECRET_RE" | head -n 1)
    case $m in *xxxx*|*XXXX*|*your_*|*YOUR_*|*'<'*|*example*|*EXAMPLE*|*placeholder*|*'${'*) continue ;; esac
    # Never echo the secret itself: show only its first 8 characters.
    short=$(printf '%s' "$m" | cut -c1-8)
    report="$report
           $c  $f  (${short}...)"
  done < "$PP_TMP/hits"
  if [ -n "$report" ]; then
    pp_fail "pushed commits add lines that look like real secrets:$report"
    printf '           Fix: move the value to an env var, rotate it if it was ever real, rewrite the commit.\n' >&2
    printf '           False positive? Append the comment pre-push:allow-secret to that line, or list the path in .githooks/secret-allowlist.\n' >&2
  fi
}

# Run all guards. Returns non-zero when anything was blocked.
pp_run_guards() {
  pp_load_allowlist
  pp_guard_refs
  pp_guard_identity
  pp_guard_secret_files
  pp_guard_secret_content
  if [ "$PP_FAILED" -ne 0 ]; then
    printf '[pre-push] Push blocked by guards. (Bypass only in an emergency: git push --no-verify)\n' >&2
    return 1
  fi
  pp_say "guards ok: branch, identity, secrets (${PP_COMMIT_COUNT:-0} new commit(s) scanned)"
  return 0
}

# True when there is something to check (not just ref deletions).
pp_should_check() {
  [ "$PP_HAS_UPDATES" -eq 1 ] || { pp_say "only deletions pushed; skipping project checks"; return 1; }
  cd "$PP_ROOT" || return 1
  if [ -n "$(git status --porcelain --untracked-files=no 2>/dev/null)" ]; then
    pp_warn "working tree has uncommitted changes; checks run against the working tree, not exactly what is pushed"
  fi
  head=$(git rev-parse HEAD 2>/dev/null)
  for t in $PP_PUSHED_TIPS; do
    c=$(git rev-parse "$t^{commit}" 2>/dev/null)
    [ "$c" = "$head" ] || pp_warn "pushing ${t%"${t#???????}"} which is not HEAD; checks run against HEAD"
  done
  return 0
}

# pp_step "<label>" cmd args...   fail-fast: blocks the push on first failure.
pp_step() {
  label=$1; shift
  t0=$(date +%s)
  pp_say "-> $label"
  if "$@"; then
    pp_say "   ok: $label ($(( $(date +%s) - t0 ))s)"
  else
    printf '[pre-push] BLOCKED: "%s" failed (%s). Fix it, or bypass in an emergency with git push --no-verify.\n' "$label" "$*" >&2
    exit 1
  fi
}

# pp_full_step "<label>" cmd...   only runs when PREPUSH_FULL=1.
pp_full_step() {
  if [ "${PREPUSH_FULL:-}" = "1" ]; then
    pp_step "$@"
  else
    pp_say "-> skip: $1 (set PREPUSH_FULL=1 to run it)"
  fi
}

# Node helpers ---------------------------------------------------------------
pp_require_node_modules() {
  [ -d "$PP_ROOT/node_modules" ] && return 0
  printf '[pre-push] BLOCKED: node_modules missing. Run npm ci first.\n' >&2
  exit 1
}

# Python helpers -------------------------------------------------------------
# Sets PP_PY to the project venv's python if present, else a working python 3.
pp_find_python() {
  for c in "$PP_ROOT/.venv/Scripts/python.exe" "$PP_ROOT/.venv/bin/python" \
           "$PP_ROOT/venv/Scripts/python.exe" "$PP_ROOT/venv/bin/python" python3 python; do
    if "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1; then
      PP_PY=$c; return 0
    fi
  done
  printf '[pre-push] BLOCKED: no Python 3 found (create .venv or install python).\n' >&2
  exit 1
}

# True when "$PP_PY -m <module>" is importable.
pp_py_has() { "$PP_PY" -c "import $1" >/dev/null 2>&1; }

# pp_py_step_if <module> "<label>" cmd...   warn+skip when the tool isn't installed.
pp_py_step_if() {
  mod=$1; shift
  if pp_py_has "$mod"; then
    pp_step "$@"
  else
    pp_warn "skipped: $1 ($mod not installed in $PP_PY; pip install $mod)"
  fi
}

pp_done() {
  pp_say "all checks passed in $(( $(date +%s) - PP_START ))s. Pushing."
  exit 0
}
