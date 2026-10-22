#!/usr/bin/env python3
"""
`seo-geo` console script: one entry point that dispatches a subcommand to the
existing standalone script, with the remaining arguments passed through untouched.

    seo-geo qa "final output/page-green.html" --words 3200 --json
    seo-geo lookup product-certification
    seo-geo check-bots https://www.example.com

Each subcommand runs exactly as `python optimizer/<script>.py ...` would (same
argv, same __main__ block), so the documented script commands keep working and
the two forms never drift. Install with `pip install -e .` from the repo root so
data/ and config.json resolve to your checkout.
"""
import os
import runpy
import sys

OPTIMIZER_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(OPTIMIZER_DIR)

# subcommand -> (script path relative to the project root, one-line help)
COMMANDS = {
    "qa": ("optimizer/qa_check.py", "QA gate for a built page (--new, --keyword, --json)"),
    "lookup": ("optimizer/lookup.py", "Step 1 brief: scorecard + audit for a slug"),
    "cannibal": ("optimizer/cannibal.py", "Rule 6 cannibalization check for a section title"),
    "ledger": ("optimizer/ledger.py", "content ledger: add / list / search new sections"),
    "next": ("optimizer/next.py", "rank pending pages by priority"),
    "striking": ("optimizer/striking.py", "striking-distance pages (position 8-20)"),
    "interlink": ("optimizer/interlink.py", "pages that should link TO a slug"),
    "check-bots": ("optimizer/check_bots.py", "robots.txt AI retrieval/training bot access"),
    "meta-audit": ("optimizer/meta_audit.py", "duplicate meta titles/descriptions"),
    "linkcheck": ("optimizer/linkcheck.py", "resolve internal + breadcrumb links in a built page"),
    "technical-seo": ("optimizer/technical_seo.py", "live noindex/canonical/hreflang check"),
    "sitecheck": ("optimizer/sitecheck.py", "sitemap coverage + site-wide broken-link crawl"),
    "citations": ("optimizer/citations.py", "citation-provenance ledger"),
    "verify": ("optimizer/verify.py", "post-publish verification log + report"),
    "llms-txt": ("optimizer/llms_txt.py", "generate /llms.txt from the inventory"),
    "pricing": ("optimizer/pricing.py", "generate a /pricing.md skeleton"),
    "build-scorecard": ("build_scorecard.py", "build data/*.json from GSC + inventory exports"),
}

# Accept the script's own name too (qa_check, check_bots, build_scorecard, ...).
ALIASES = {os.path.splitext(os.path.basename(p))[0]: name for name, (p, _) in COMMANDS.items()}


def usage():
    width = max(len(n) for n in COMMANDS)
    lines = ["usage: seo-geo <command> [args...]", "", "commands:"]
    lines += [f"  {n.ljust(width)}  {h}" for n, (_, h) in COMMANDS.items()]
    lines += ["", "Run `seo-geo <command> --help` for a command's own options."]
    return "\n".join(lines)


def resolve(name):
    """Script path for a subcommand name or alias, or None if unknown."""
    name = ALIASES.get(name, name)
    entry = COMMANDS.get(name)
    return os.path.join(PROJECT_ROOT, entry[0]) if entry else None


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(usage())
        return 0
    script = resolve(argv[0])
    if script is None:
        print(f"seo-geo: unknown command '{argv[0]}'\n\n{usage()}", file=sys.stderr)
        return 2
    if not os.path.exists(script):
        print(f"seo-geo: {script} not found (run from a repo checkout installed with "
              f"`pip install -e .`)", file=sys.stderr)
        return 2
    # Mirror `python <script> args...`: the script's dir first on sys.path (so its
    # flat sibling imports resolve), the project root next, argv[0] = the script.
    for p in (PROJECT_ROOT, os.path.dirname(script)):
        if p not in sys.path:
            sys.path.insert(0, p)
    old_argv = sys.argv
    sys.argv = [script, *argv[1:]]
    try:
        runpy.run_path(script, run_name="__main__")
    except SystemExit as e:
        code = e.code
        if code is None:
            return 0
        if isinstance(code, int):
            return code
        print(code, file=sys.stderr)
        return 1
    finally:
        sys.argv = old_argv
    return 0


if __name__ == "__main__":
    sys.exit(main())
