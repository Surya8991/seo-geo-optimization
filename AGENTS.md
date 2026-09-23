# SEO & GEO Optimization System

## What this is
A sequential, human-in-the-loop pipeline that optimizes one web page at a time for
classic SEO plus AI search (AIO, AEO, GEO/LLM). It scrapes the live page, scores it
against a 50-point checklist, uses Search Console performance data to pick the right
strategy, and outputs a self-contained HTML file with color-coded review markers
(green = add, red = remove) ready for review before publishing.

It is brand-agnostic. Every brand specific (name, domain, URL paths, money-page keyword
map, geo-slug list) lives in **`config.json`**, and every script and doc reads from there.
Point it at any site by editing that one file.

## Configure first
Open `config.json` and set:
- `brand_name` - the brand, used for the "brand mentioned once" rule and keyword stripping.
- `domain` / `base_url` - used to classify internal vs external links and build URLs.
- `info_path` / `blog_path` - the URL segments for the page types (e.g. `info`, `blog`).
- `money_page_pattern` - the shape of your money/course page URLs.
- `max_brand_mentions` - allowed brand mentions in reader body (default 1).
- `course_keyword_map` - maps slug keywords to money pages (used by `build_scorecard.py`).
- `country_slugs` - geo pages that must never be linked to (drives the automated check).

## Key files
- `config.json` - the only place brand specifics live.
- `data/scorecard.json` - performance per page (category, clicks, impressions, CTR, position, trend, priority).
- `data/audit.json` - strategy per page (primary keyword, intent, money page) + blog slugs + money pages.
- `optimizer/OPTIMIZATION-CHECKLIST.md` - the 50-point checklist (10 categories).
- `optimizer/QUALITY-RULES.md` - the 12 hard rules as pass criteria + link/FAQ bands.
- `optimizer/MODERN-SEO-PLAYBOOK.md` - SEO + AEO + GEO + LLM tactics, applied in the build step.
- `optimizer/template.html` - blank output skeleton (CSS + FAQ JS + JSON-LD).
- `optimizer/config_loader.py` - shared config reader.
- `optimizer/constants.py` - shared stop-word list + rule thresholds (link/meta bands).
- `optimizer/scoring.py` - pure, unit-tested scoring/parsing helpers used by `build_scorecard.py`.
- `optimizer/lookup.py` - Step 1: merge scorecard + audit into one brief with the lever to pull.
- `optimizer/cannibal.py` - Rule 6: check if another page, blog, or past build already owns a subtopic (reads the content ledger too).
- `optimizer/ledger.py` - the content ledger: record new sections so future pages do not repeat them (`add` / `list` / `search`).
- `optimizer/qa_check.py` - the automated QA gate. Optimize mode by default; `--new` for brand-new pages; `--keyword` checks primary-keyword placement (Rule 2). Also validates heading hierarchy (one H1, no skipped levels), image alt text/filenames, JSON-LD parsing + Article-schema completeness, a current-year freshness date, and pre-2024 stats (Rule 12). Reports a Flesch readability score. It computes its own reader word count for the link-budget band (notes fully stripped, even when they wrap tables), so `--words` is advisory only and a too-high value can no longer unlock a larger link budget.
- `optimizer/meta_audit.py` - find duplicate meta titles/descriptions across the site (reads audit.json).
- `optimizer/next.py` - rank pending pages by priority (skips ones already built) to pick the next page to optimize.
- `optimizer/striking.py` - list striking-distance pages (avg position 8-20 with impressions), the highest-ROI targets.
- `optimizer/llms_txt.py` - generate an `/llms.txt` from the inventory (agent/MCP convenience; not a citation lever).
- `optimizer/interlink.py` - inbound-link finder (Checklist #29): existing pages that should link TO the page being optimized.
- `optimizer/linkcheck.py` - resolve every internal link in the built page and flag any that 404 (broken) or 301/302 (redirecting to a non-canonical URL). Run it before saving so no stale-slug or dead internal link ships.
- `optimizer/check_bots.py` - fetch the live `robots.txt` and report whether the AI retrieval/search bots are allowed (a make-or-break GEO lever).
- `optimizer/verify.py` - the post-publish verification log (WORKFLOW Step 9): record per-engine citation presence + GSC deltas; `verify.py report` rolls them up.
- `build_scorecard.py` - builds `scorecard.json` + `audit.json` from GSC + inventory exports.
- `docs/guide.html` - a self-contained HTML operator guide (open in a browser) covering setup, both tracks, every helper, and the QA gate.
- `data/content_ledger.json` - the running record of new sections produced (created on first `ledger.py add`).
- `data/verification_log.json` - post-publish verification results (created on first `verify.py add`).
- `data/*.example.json` - committed sample scorecard/audit so the tooling runs before you have GSC exports.
- `.github/workflows/ci.yml` - CI: runs the pytest suite and byte-compiles all Python on every push/PR.
- `tests/` - `pytest` suite for `qa_check.py`, `scoring.py`, `ledger.py`, `cannibal.py`, `next.py`, `interlink.py`, `check_bots.py`, `verify.py`, `meta_audit.py`, `striking.py`, `llms_txt.py`, `linkcheck.py` (`pip install -r requirements.txt && pytest`). Tests pin a fixed config via `SEO_GEO_CONFIG` (see `tests/fixtures/config.test.json`), so they stay green no matter which brand `config.json` holds.
- `WORKFLOW.md` - the per-page operating procedure (optimize-existing track), including Step 9 post-publish verification.
- `.claude/commands/optimize-page.md` - optimize an existing page (`/optimize-page <slug>`).
- `.claude/commands/new-page.md` - create a new page from scratch (`/new-page <topic>`).
- `final output/` - optimized pages saved as `{slug}-green.html`; new pages as `{slug}.html`.

## Output HTML structure (every optimized page follows this)
1. Review note (yellow `.note`) - what changed, source articles, publish instructions, slug change (if any). Not reader-facing.
2. Publishing fields (blue `.note`) - meta title `(NN/60)`, meta description `(NN/155)`, H1. Not reader-facing.
3. H1 containing the primary keyword.
4. AIO opening paragraph (40-60 word answer-first definition, natural prose, no card), then 2-3 context sentences.
5. Body with strict H2/H3 hierarchy. New content in `.new-block` + `.new-tag`; inline additions in `.new-inline`; removals in `.remove-block` + `.remove-tag` with the reason.
6. Tables wrapped in `.table-scroll`.
7. Conclusion (brand named once max, only if natural).
8. Changes-summary table (`.changes-summary`, review only) listing what was done: sections, secondary/longtail keywords placed, internal/external links added, stats refreshed, FAQ, AI Overview angle. Optimize mode only.
9. FAQ accordion with FAQPage JSON-LD that matches the visible items exactly, plus the accordion JS.
Self-contained: inline CSS + inline JS. New pages (the `/new-page` track) ship clean: no diff markers and no changes-summary.

---

## Quality rules (apply to every page, no exceptions)

1. **Zero em dashes.** Also zero en dashes and zero `--` used as a sentence break. Regular hyphens only for compound words. Replace with commas, periods, colons, semicolons, or parentheses. Em-dash overuse is a known AI-content signal.
2. **No keyword stuffing.** Primary keyword only in title, H1, meta description, URL, first 100 words, and once in the conclusion (max 5-6 total). If a sentence reads fine without the keyword, remove it.
3. **Link budget + contextual interlinking.** Follow the band table in `QUALITY-RULES.md`. Max 1 link per paragraph. Every internal link must be contextually relevant (a reader would genuinely click it there) with descriptive anchor text that names the destination topic. **Never link to country/city pages** (see `config.json` `country_slugs`). Internal links go to money/course pages, category pages, or other content pages.
4. **No CTA anchor text on internal links.** No "Explore", "Discover", "Get Started", "Learn More", "View All", "Check Out", "Try". Use descriptive anchor text that names the destination topic.
5. **Minimal brand usage.** The brand appears only in the conclusion, only if natural (`max_brand_mentions`). Internal links use generic descriptive anchor text, not brand-prefixed text.
6. **Cannibalization check before new sections, and no future repeats.** Before adding any new H2, run `cannibal.py` (it searches existing pages, blogs, and the content ledger). If another page owns the subtopic in depth, add a 1-2 sentence mention with an internal link, or skip it. After a build, record every new section with `ledger.py add` so a later page cannot write the same section again near-verbatim. A `[LEDGER]` hit means a past build already produced it: link to it, do not duplicate.
7. **Red markers for removals.** Thin, off-topic, or harmful content goes in `.remove-block` + `.remove-tag` labeled with the reason.
8. **External link discipline.** Hyperlink only for a specific stat, study, or quote; well-known sources can be name-only. All external links `rel="nofollow" target="_blank"`.
9. **American English only.** organize, behavior, color, analyze. No British spellings.
10. **No AI content signals.** No em dashes; vary sentence structure; no filler ("In today's rapidly evolving...", "It's worth noting..."); no excessive hedging.
11. **FAQ quality and limits.** FAQs target real PAA and new angles, not body rehash. Count band by word count (5-6 under 3K, 6-8 for 3-6K, 8-10 for 6K+). HTML items must match JSON-LD entries exactly.
12. **Stat verification.** Every stat real, sourced, and 2024-2026. Replace or remove anything older or unverifiable.
13. **Secondary + longtail keyword coverage.** Beyond the primary keyword, place the secondary and longtail terms found in research naturally in H2/H3s and body. Never force them; never stuff.
14. **Flow and readability.** Logical section order, one idea per paragraph, no jumps or repeats, answer-first per section. Short paragraphs, active voice, plain words. Target Flesch reading ease 60+ (`qa_check.py` reports it).
15. **Changes summary (optimize mode).** End the review copy with the `.changes-summary` table documenting exactly what was done. `qa_check.py` requires it in optimize mode; new pages omit it.

## 8-lever SEO framework (address all 8 on every page)
1. **Title/Meta SERP validation** - competitor titles, year for freshness, meta hook, char counts (title <=60, meta 140-160, target ~150-155).
2. **Competitor content-gap analysis** - top 5-10 results across USA, India, Canada, UK, Australia + AI Overview; find sections/angles/data they have and you don't.
3. **Content freshness audit** - replace pre-2024 stats with 2024-2026 equivalents; update names; add current-year references.
4. **Money-page internal link** - link to the page's money page from `audit.json` with descriptive anchor text (Rule 4), no country/city links.
5. **Schema / FAQ expansion** - FAQ targeting PAA with JSON-LD, new angles only (Rule 11).
6. **Content-depth additions** - new H2/H3 sections filling competitor gaps; cannibalization check first (Rule 6).
7. **Keyword targeting** - primary keyword placement (Rule 2); secondary keywords from competitors; fold in any GSC keywords the user supplies.
8. **QA rules check** - run `qa_check.py`; every rule passes before saving.

## The 5 categories -> intensity
| Category | Intensity |
|----------|-----------|
| Dead Since Birth | Near-complete rewrite: new angle, structure, fresh content |
| Quick Win | Targeted fixes: missing sections, keywords, FAQ |
| Lost Momentum | Content refresh: stats, new sections, depth |
| Top Performers Falling | Careful updates: do not break what works, add freshness |
| Performing Well | Light touch: date, stats, FAQ if missing |

## How to run
Two tracks, one page at a time:
- **Optimize an existing page:** follow `WORKFLOW.md`, or run `/optimize-page <slug>`. Outputs a review copy with green/red markers + the changes-summary table.
- **Create a new page:** follow `.claude/commands/new-page.md`, or run `/new-page <topic>`. Outputs clean publish-ready HTML (no diff markers); QA runs with `--new`.

Quality over speed. Never remove content that works; add and improve. Run the cannibalization
check before any new H2 and record new sections in the ledger after. Wait for user
confirmation before starting the next page.

## What the 2026 research changed (applied in the playbook)
- **AI crawlers split into training vs retrieval bots.** To be cited you must allow the
  retrieval bots (`OAI-SearchBot`, `ChatGPT-User`, `PerplexityBot`, `Claude-Web`); blocking
  the training bots (`GPTBot`, `Google-Extended`, `CCBot`) does not affect citations.
- **Schema helps parsing, not citations directly.** Evidence is split, so add JSON-LD for
  correctness but do not rely on it as a ranking lever.
- **Brand mentions and entity authority beat markup.** Third-party mentions, Wikipedia/entity
  clarity, and original data are the strongest generative-visibility levers.
- **Engines barely overlap.** Ranking on one AI engine rarely transfers to another; check the
  AI Overview per keyword and target the specific angle that earns a citation.
See `optimizer/MODERN-SEO-PLAYBOOK.md` for the full detail.

## Notes for the human
- `build_scorecard.py` expects GSC and inventory exports in a specific sheet/column shape;
  the input contract is documented at the top of that file. Adjust the constants to match
  your own exports, then run it to regenerate the data files.
- Data files (`data/*.json`) and finished pages (`final output/*.html`) are outputs; they
  are gitignored by default.
