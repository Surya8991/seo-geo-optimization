#!/usr/bin/env python3
"""
Post-publish verification log (WORKFLOW Step 9). About 30 days after a page ships,
record whether it earned AI citations and how GSC moved, so the pipeline learns
which levers actually worked instead of optimizing blind.

Usage:
    # once the page is live, record the publish date (starts the 30-day clock)
    python optimizer/verify.py publish info/product-certification [--date 2026-10-22]

    # which published pages are due (or overdue) for verification
    python optimizer/verify.py due [--days 30]

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
from datetime import date, timedelta

try:
    from jsonstore import locked
except ImportError:
    from optimizer.jsonstore import locked

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(BASE, "data", "verification_log.json")

VERIFY_AFTER_DAYS = 30
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
            data = json.load(f)
    else:
        data = {}
    # "published" arrived after "entries"; older logs simply lack it.
    data.setdefault("entries", [])
    data.setdefault("published", [])
    return data


def save(data):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    tmp = f"{LOG}.tmp.{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, LOG)


def add(slug, keyword, cited, ctr_delta, pos_delta, ai_overview, note):
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
    with locked(LOG):
        data = load()
        data["entries"].append(entry)
        save(data)
    cited_str = ", ".join(f"{k}={'yes' if v else 'no'}" for k, v in cited.items()) or "-"
    print(f"Verification recorded for {slug} ('{keyword}'): {cited_str}")
    return 0


def _tail(slug):
    """Last path segment, lowercased, so info/foo and foo name the same page."""
    return str(slug or "").strip().rstrip("/").rsplit("/", 1)[-1].lower()


def publish(slug, on=None):
    """Record the go-live date for a page (re-publishing replaces the earlier date)."""
    on = on or date.today().isoformat()
    date.fromisoformat(on)  # fail loudly on a typo rather than store garbage
    with locked(LOG):
        data = load()
        data["published"] = [p for p in data["published"] if _tail(p["page_slug"]) != _tail(slug)]
        data["published"].append({"page_slug": slug, "date": on})
        save(data)
    print(f"Publish date recorded for {slug}: {on}. Verification due "
          f"{(date.fromisoformat(on) + timedelta(days=VERIFY_AFTER_DAYS)).isoformat()}.")
    return 0


def due_items(published, entries, today, days=VERIFY_AFTER_DAYS):
    """Published pages still lacking a verification entry dated on/after their publish date.

    Returns dicts {page_slug, published, due, days_left}, most overdue first.
    days_left <= 0 means due now (negative = overdue)."""
    out = []
    for p in published:
        pub = date.fromisoformat(p["date"])
        verified = any(
            _tail(e.get("page_slug")) == _tail(p["page_slug"])
            and date.fromisoformat(e["date"]) >= pub
            for e in entries
        )
        if verified:
            continue
        due = pub + timedelta(days=days)
        out.append({"page_slug": p["page_slug"], "published": pub.isoformat(),
                    "due": due.isoformat(), "days_left": (due - today).days})
    return sorted(out, key=lambda r: r["days_left"])


def print_due(items, indent="  "):
    for r in items:
        if r["days_left"] < 0:
            when = f"OVERDUE by {-r['days_left']}d"
        elif r["days_left"] == 0:
            when = "due today"
        else:
            when = f"due in {r['days_left']}d"
        print(f"{indent}{r['page_slug']}  (published {r['published']}, {when})")


def due(days=VERIFY_AFTER_DAYS):
    data = load()
    if not data["published"]:
        print("No publish dates recorded. After a page goes live: "
              "`verify.py publish <slug>` starts its verification clock.")
        return 0
    items = due_items(data["published"], data["entries"], date.today(), days)
    if not items:
        print("Every published page has a verification entry.")
        return 0
    print(f"\nVerification queue ({len(items)} page(s), {days}-day window):\n")
    print_due(items)
    print()
    return 0


def _num(s):
    """Parse a signed delta string like '+0.4' / '-3' to a float; None if not numeric."""
    try:
        return float(str(s).strip().lstrip("+"))
    except (ValueError, AttributeError):
        return None


def summarize(entries):
    """Aggregate the log: per-engine citation rate, AI-Overview rate, mean deltas."""
    engine_cited, engine_total = {}, {}
    aio_yes = aio_total = 0
    ctr_deltas, pos_deltas = [], []
    for e in entries:
        for eng, cited in e.get("cited", {}).items():
            engine_total[eng] = engine_total.get(eng, 0) + 1
            engine_cited[eng] = engine_cited.get(eng, 0) + (1 if cited else 0)
        aio = str(e.get("ai_overview", "")).lower()
        if aio in ("yes", "no", "partial"):
            aio_total += 1
            if aio in ("yes", "partial"):
                aio_yes += 1
        cd, pd = _num(e.get("ctr_delta")), _num(e.get("pos_delta"))
        if cd is not None:
            ctr_deltas.append(cd)
        if pd is not None:
            pos_deltas.append(pd)
    rates = {eng: (engine_cited[eng], engine_total[eng]) for eng in engine_total}
    return {
        "pages": len({e.get("page_slug") for e in entries}),
        "entries": len(entries),
        "engine_rates": rates,
        "ai_overview": (aio_yes, aio_total),
        "avg_ctr_delta": round(sum(ctr_deltas) / len(ctr_deltas), 2) if ctr_deltas else None,
        "avg_pos_delta": round(sum(pos_deltas) / len(pos_deltas), 2) if pos_deltas else None,
    }


def report():
    data = load()
    s = summarize(data["entries"])
    if not s["entries"]:
        print("Verification log is empty. Record passes with `verify.py add ...`.")
        return 0
    print(f"\nVerification rollup: {s['entries']} entries across {s['pages']} pages\n")
    print("Citation rate by engine:")
    for eng, (cited, total) in sorted(s["engine_rates"].items()):
        pct = round(100 * cited / total) if total else 0
        print(f"  {eng:<20} {cited}/{total} cited ({pct}%)")
    ay, at = s["ai_overview"]
    if at:
        print(f"\nAI Overview presence: {ay}/{at} ({round(100*ay/at)}%)")
    if s["avg_ctr_delta"] is not None:
        print(f"Avg CTR delta: {s['avg_ctr_delta']:+} points")
    if s["avg_pos_delta"] is not None:
        print(f"Avg position delta: {s['avg_pos_delta']:+} (negative = moved up)")
    print()
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

    sub.add_parser("report")

    pb = sub.add_parser("publish", help="record the go-live date (starts the verification clock)")
    pb.add_argument("slug")
    pb.add_argument("--date", default=None, help="YYYY-MM-DD, defaults to today")

    d = sub.add_parser("due", help="published pages awaiting their verification pass")
    d.add_argument("--days", type=int, default=VERIFY_AFTER_DAYS)

    args = ap.parse_args()
    if args.cmd == "add":
        cited = build_cited(args.cited, args.not_cited)
        sys.exit(add(args.slug, args.keyword, cited, args.ctr_delta, args.pos_delta,
                     args.ai_overview, args.note))
    if args.cmd == "list":
        sys.exit(list_entries(args.slug))
    if args.cmd == "report":
        sys.exit(report())
    if args.cmd == "publish":
        sys.exit(publish(args.slug, args.date))
    if args.cmd == "due":
        sys.exit(due(args.days))
