#!/usr/bin/env python3
"""
Post-publish verification log (WORKFLOW Step 9). About 30 days after a page ships,
record whether it earned AI citations and how GSC moved, so the pipeline learns
which levers actually worked instead of optimizing blind.

Usage:
    # record a verification pass for a page
    python optimizer/verify.py add info/product-certification \
        --keyword "product certification" \
        --cited chatgpt,perplexity --not-cited gemini,claude \
        --ai-overview yes --ctr-delta +0.4 --pos-delta -3 \
        --note "cited in the AI Overview definition block"

    # list all entries, or one page's
    python optimizer/verify.py list
    python optimizer/verify.py list product-certification

Stored at data/verification_log.json.
"""
import argparse
import json
import os
import sys
from datetime import date

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(BASE, "data", "verification_log.json")

ENGINES = ["chatgpt", "perplexity", "gemini", "claude", "google-ai-overview"]


def _split(csv):
    return [x.strip().lower() for x in (csv or "").split(",") if x.strip()]


def build_cited(cited_csv, not_cited_csv):
    """Map engine -> bool from --cited / --not-cited lists. Unmentioned engines omitted."""
    out = {}
    for e in _split(cited_csv):
        out[e] = True
    for e in _split(not_cited_csv):
        out[e] = False
    return out


def load():
    if os.path.exists(LOG):
        with open(LOG, encoding="utf-8") as f:
            return json.load(f)
    return {"entries": []}


def save(data):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add(slug, keyword, cited, ctr_delta, pos_delta, ai_overview, note):
    data = load()
    entry = {
        "date": date.today().isoformat(),
        "page_slug": slug,
        "keyword": keyword or "",
        "cited": cited,
        "ai_overview": ai_overview,
        "ctr_delta": ctr_delta,
        "pos_delta": pos_delta,
        "note": note or "",
    }
    data["entries"].append(entry)
    save(data)
    cited_str = ", ".join(f"{k}={'yes' if v else 'no'}" for k, v in cited.items()) or "-"
    print(f"Verification recorded for {slug} ('{keyword}'): {cited_str}")
    return 0


def list_entries(slug=None):
    data = load()
    rows = [e for e in data["entries"] if not slug or slug.lower() in e["page_slug"].lower()]
    if not rows:
        print("Verification log is empty." if not slug else f"No entries for '{slug}'.")
        return 0
    for e in rows:
        cited = ", ".join(f"{k}={'y' if v else 'n'}" for k, v in e.get("cited", {}).items()) or "-"
        deltas = []
        if e.get("ctr_delta"):
            deltas.append(f"CTR {e['ctr_delta']}")
        if e.get("pos_delta"):
            deltas.append(f"pos {e['pos_delta']}")
        line = f'  [{e["date"]}] {e["page_slug"]} ("{e.get("keyword","")}"): {cited}'
        if e.get("ai_overview"):
            line += f" | AIO={e['ai_overview']}"
        if deltas:
            line += " | " + ", ".join(deltas)
        if e.get("note"):
            line += f" | {e['note']}"
        print(line)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add")
    a.add_argument("slug")
    a.add_argument("--keyword", default="")
    a.add_argument("--cited", default="", help="comma list of engines that cited the page")
    a.add_argument("--not-cited", dest="not_cited", default="", help="comma list that did not")
    a.add_argument("--ai-overview", dest="ai_overview", default="", help="yes/no/partial")
    a.add_argument("--ctr-delta", dest="ctr_delta", default="", help="e.g. +0.4 (points vs before)")
    a.add_argument("--pos-delta", dest="pos_delta", default="", help="e.g. -3 (avg position change)")
    a.add_argument("--note", default="")

    l = sub.add_parser("list")
    l.add_argument("slug", nargs="?", default=None)

    args = ap.parse_args()
    if args.cmd == "add":
        cited = build_cited(args.cited, args.not_cited)
        sys.exit(add(args.slug, args.keyword, cited, args.ctr_delta, args.pos_delta,
                     args.ai_overview, args.note))
    if args.cmd == "list":
        sys.exit(list_entries(args.slug))
