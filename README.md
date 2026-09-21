# SEO & GEO Optimization

A brand-agnostic, human-in-the-loop pipeline that optimizes **one web page at a time** for
classic SEO plus AI search (AI Overviews, answer engines, and generative engines like
ChatGPT, Gemini, Perplexity, and Claude). You give it a page slug (plus any GSC keywords);
it pulls the page's performance and strategy into one brief, audits the live page against a
50-point checklist, uses the scorecard category to pick the right intensity, and outputs a
self-contained HTML file with color-coded review markers (green = add, red = remove) ready
for review before publishing.

Nothing brand-specific is hard-coded. Set your brand, domain, and URL paths once in
**`config.json`** and the whole system points at your site.

## Start here
- **`config.json`** - set brand, domain, URL paths, money-page keyword map, and geo-slug list.
- **`AGENTS.md`** - full context: the 12 quality rules, the 8-lever framework, the 8-step pipeline. Source of truth (`CLAUDE.md` just imports it).
- **`WORKFLOW.md`** - the per-page runbook.
- **`.claude/commands/optimize-page.md`** - the runbook as a slash command (`/optimize-page <slug>`).
- **`optimizer/QUALITY-RULES.md`** - the QA pass criteria + link/FAQ bands.
- **`optimizer/MODERN-SEO-PLAYBOOK.md`** - the SEO + AEO + GEO + LLM tactics baked into every build.

## Quick start

Two tracks, one page at a time. As a single command in Claude Code:

```
/optimize-page product-certification     # improve an existing live page
/new-page "how to measure training roi"  # create a brand-new page from scratch
```

Or run the pipeline manually:

```bash
# 1. Pull the page's performance + strategy brief (and the lever to pull)
python optimizer/lookup.py <slug>

# 2. Before any new H2, check cannibalization (existing pages, blogs, AND past builds):
python optimizer/cannibal.py "<proposed section title>" --exclude <slug>
#    ...then build from optimizer/template.html...

# 3. QA gate before saving (pass the reader word count for the right link band)
python optimizer/qa_check.py "final output/<slug>-green.html" --words <n>          # optimize
python optimizer/qa_check.py "final output/<slug>.html" --words <n> --new          # new page

# 4. Record new sections so future pages never repeat them
python optimizer/ledger.py add <slug> --section "<H2 title>" --angle "<unique angle>"
```

Build the data from raw GSC + inventory exports (only when the source files change):

```bash
pip install openpyxl
python build_scorecard.py    # regenerates data/scorecard.json + data/audit.json
```

The input contract (which workbook, sheets, and columns `build_scorecard.py` expects) is
documented at the top of that file. Adjust the constants to match your own exports.

## Structure
```
SEO & GEO Optimization/
├── config.json                   Brand config (the ONE place brand lives)
├── AGENTS.md                     Project context + rules (authoritative)
├── CLAUDE.md                     One-line import of AGENTS.md
├── README.md                     This file
├── WORKFLOW.md                   Per-page operating procedure
├── build_scorecard.py            Builds the JSON data from GSC + inventory exports
├── .claude/commands/
│   ├── optimize-page.md          Optimize an existing page (/optimize-page)
│   └── new-page.md               Create a new page from scratch (/new-page)
├── optimizer/
│   ├── OPTIMIZATION-CHECKLIST.md     The 50-point checklist (10 categories)
│   ├── QUALITY-RULES.md             QA pass criteria + link/FAQ bands
│   ├── MODERN-SEO-PLAYBOOK.md        SEO + AEO + GEO + LLM best practices
│   ├── template.html                 Blank output skeleton (CSS + FAQ JS + JSON-LD + changes-summary)
│   ├── config_loader.py              Shared config reader
│   ├── lookup.py                     Step 1: merge scorecard + audit into one brief
│   ├── cannibal.py                   Rule 6: find pages/blogs/past builds covering a subtopic
│   ├── ledger.py                     Content ledger: record new sections, block future repeats
│   └── qa_check.py                   QA gate (optimize + --new modes, readability score)
├── data/                         Generated scorecard.json, audit.json, content_ledger.json (gitignored)
└── final output/                 Optimized pages ({slug}-green.html) and new pages ({slug}.html)
```

## The 5 categories -> intensity
| Category | Intensity |
|----------|-----------|
| Dead Since Birth | Near-complete rewrite: new angle, structure, fresh content |
| Quick Win | Targeted fixes: missing sections, keywords, FAQ |
| Lost Momentum | Content refresh: stats, new sections, depth |
| Top Performers Falling | Careful updates: do not break what works, add freshness |
| Performing Well | Light touch: date, stats, FAQ if missing |

## Rules that never bend
Zero em/en dashes. Keyword not stuffed (max 5-6 primary placements). Link budget by word
count, max 1 link per paragraph. No CTA anchor text. No country/city page links. Brand named
once, in the conclusion. Cannibalization checked before any new H2. American English. Stats
2024-2026 only. FAQ HTML must match its JSON-LD. See `optimizer/QUALITY-RULES.md` for the
full gate, enforced by `qa_check.py`.
