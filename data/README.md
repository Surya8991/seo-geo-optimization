# data/

Generated files, not brand data you edit by hand.

Built by `build_scorecard.py` (regenerate after your GSC/inventory exports change):
- **scorecard.json** - `{"pages": [...], "stats": {...}}`. Performance + category + priority per page. Read by `lookup.py`, `cannibal.py`, `next.py`, `interlink.py`.
- **audit.json** - `{"audit_rows": [...], "money_pages": [...], "blog_pages": [...]}`. Strategy per page plus the blog slugs and money pages used for cannibalization, internal linking, and `meta_audit.py`.

Written by the helper scripts as you work:
- **content_ledger.json** - `{"entries": [...]}`. New sections produced so far (created on first `ledger.py add`; read by `cannibal.py` and `next.py`).
- **verification_log.json** - `{"entries": [...]}`. Post-publish verification results (created on first `verify.py add`; WORKFLOW Step 9).

Committed samples (tracked, not gitignored):
- **scorecard.example.json** / **audit.example.json** - copy to the real names to run the tooling before you have GSC exports.

```bash
python build_scorecard.py    # regenerate scorecard.json + audit.json from exports
```

The non-example `*.json` files are gitignored (they are outputs and may contain site data).
