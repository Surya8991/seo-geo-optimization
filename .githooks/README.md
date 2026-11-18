# Git hooks (`.githooks/`)

This repo's pre-push gate. It needs no dependencies: just git and POSIX `sh`, which Git for Windows provides.

## Enable once per clone

```bash
git config core.hooksPath .githooks
```

ResumeBuildz is the exception: it uses husky (`npm install` runs `prepare: husky`), and `.husky/pre-push` delegates to `.githooks/pre-push`.

## What runs on `git push`

1. **Guards** (`lib/guards.sh`, identical in every repo under `Coding\`):
   - Blocks any push that updates or deletes `main` or `master`.
   - Blocks commits made as `edstellarmarketing` on repos that account doesn't own.
   - Blocks commits that add `.env`, `keys.env`, `*.pem`, `*.key`, `id_rsa`, or similar files.
   - Blocks added lines that match high-confidence secret patterns: AWS, GitHub, Slack, Stripe live, Google, OpenAI/Anthropic, private keys, Discord/Slack webhooks, and cloud Postgres URLs with passwords.
2. **Project checks** (`pre-push`): lint, typecheck, tests, and a build where it's cheap. They're fail-fast, so the first failure blocks the push.

## Switches

| Variable / flag | Effect |
|---|---|
| `PREPUSH_FULL=1 git push` | Also runs the slow steps, such as a production build. |
| `PREPUSH_ALLOW_MAIN=1 git push` | Allows a deliberate human push to `main`. |
| `git push --no-verify` | Skips the hook entirely. Use it only in an emergency. |

To suppress a false positive in the secret scan, put `pre-push:allow-secret` on that line, or list the path glob in `.githooks/secret-allowlist`.

## Test the hook without pushing

```bash
printf 'refs/heads/x %s refs/heads/x 0000000000000000000000000000000000000000\n' "$(git rev-parse HEAD)" | sh .githooks/pre-push origin "$(git remote get-url origin)"
```

The master copy of `lib/guards.sh` lives in `Coding\_workspace\templates\githooks\`. Edit it there and copy it into each repo; don't fork it per repo.

When you commit these files from Windows, mark them executable so macOS and Linux clones run them:

```bash
git add --chmod=+x .githooks/pre-push
```
