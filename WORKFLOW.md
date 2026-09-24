# Per-Page Optimization Workflow

The runbook for **one** page. Follow it in order, quality over speed. `AGENTS.md` holds the
full rules; this is the operating procedure that runs them. Brand, domain, and URL paths come
from `config.json`.

## Two tracks: pick one
- **Existing page (optimize)** - this document, or `/optimize-page <slug>`. Scrapes the live
  page, audits it, and outputs a review copy with green (add) / red (remove) markers plus an
  end changes-summary table.
- **New page (create from scratch)** - `.claude/commands/new-page.md`, or `/new-page <topic>`.
  No scrape or audit; outputs clean, publish-ready HTML with no diff markers. QA runs with
  `--new`. See that file for the full new-content procedure.

The steps below are the OPTIMIZE-EXISTING track.

## Input the user provides
- **Page slug** (required) - e.g., `product-certification` or `info/product-certification`.
- **GSC keywords** (optional) - if given, they are real query demand; fold them in naturally.
  Never invent keywords from site-wide GSC data.

The system scrapes the live page from the configured domain automatically.

---

## STEP 1 - Gather intelligence
Pull the page's full situation in one command:

```bash
python optimizer/lookup.py <slug-or-url-fragment>
```

This prints the **scorecard** (category, priority, clicks, impressions, CTR, avg position,
trend) merged with the **audit** (primary keyword, meta title, meta description, H1, search
intent, money page) and the **lever** the numbers point to:
- **High impressions + low CTR** -> the problem is the title/meta/snippet, not the body.
- **Low avg position (page 2+)** -> needs depth, authority, internal links.
- **Page 1 below fold (4-10)** -> freshness + featured-snippet targeting.
- **Declining trend** -> content decay: refresh stats, re-match intent.

Then scrape the live page and read `optimizer/OPTIMIZATION-CHECKLIST.md`.

**Before trusting any site-wide result below** (cannibalization, meta-duplicate audit,
striking-distance report, next-page ranking, inbound-link discovery), confirm
`data/scorecard.json`/`data/audit.json` actually hold the full site export, not a
one-page test fixture. `cannibal.py`, `meta_audit.py`, `next.py`, `interlink.py`, and
`striking.py` all now print a `WARNING: only N page(s) loaded ...` line when the
inventory is too small to make their comparison meaningful - if you see it, a "no
overlap" / "no duplicates" / "no candidates" result is not a clean bill of health, it
just means there was nothing real to compare against. Re-run `build_scorecard.py`
against the real GSC + inventory exports first.

## STEP 2 - Slug & URL review
Check the current slug against the primary keyword: short, keyword-rich, no filler.
Output: KEEP (no change needed) or CHANGE (new slug + "301 redirect from old to new").

## STEP 3 - Scope & pivot assessment
Judge whether the keyword is realistic and whether the page is redundant.
Output: OPTIMIZE AS-IS / PIVOT KEYWORD (to X) / MERGE WITH [page] / REPOSITION.

## STEP 4 - Audit current content
Score the current content against all 50 points (PASS / NEEDS WORK / MISSING / N/A). Record
the current meta title (char count), meta description (char count), and H1. Flag missing or
thin sections, pre-2024 stats, weak heading structure, missing schema, no FAQ, keyword gaps,
and any content that should be removed (red block). Note where the article jumps or buries
the answer.

## STEP 5 - Competitor & keyword research
Search the top 5-10 SERP results for the primary keyword across USA, India, Canada, UK,
Australia. **Check the AI Overview for the keyword** and record who is cited, in what format,
and the angle that would earn a citation (about 44% of AI citations come from the first 30%
of the page, so plan an answer-first lead). Capture the content gap, the **secondary and
longtail keywords** to place (competitor headings + supplied GSC keywords), and the real PAA
questions for the FAQ (research them, do not guess). Note which SERP feature to target.

**Record the check, not just the result.** When you write the AI Overview / competitor finding
into the changes-summary table (Step 7), date it and say how it was checked (a live search
performed this session vs. carried over from a prior note). AI Overview results are checked
live in this session's Step 5, not asserted from memory - and either way, since the citable
set rotates, name the competitors currently cited so a future reviewer can tell whether the
note is fresh enough to trust or needs a re-check before publishing.

## STEP 6 - Plan (show the user before building)
Set intensity from the category (see `AGENTS.md` table). For **Dead Since Birth** or any page
at avg position 20+ (page 2-3+), depth is the lever, not just intensity of edits: plan for the
upper half of the applicable link-budget word band (see `optimizer/QUALITY-RULES.md`), not
just enough to clear the category's minimum. A near-complete rewrite that lands short of what
page-1 competitors cover will not move the position even if every mechanical rule passes.

Before ANY new H2 or FAQ, run the cannibalization check:

```bash
python optimizer/cannibal.py "<proposed section title>" --exclude <slug>
```

A strong overlap means add a 1-2 sentence mention plus an internal link, or skip the section.
Plan: heading structure, keyword placement (max 5-6 primary), link budget from the word-count
band (internal links only to money/course and content pages, ZERO country/city links), FAQ
questions, and which external sources get a hyperlink vs a name-only mention. Do NOT propose
meta tags yet; those come after the build.

For inbound internal links (Checklist #29, links FROM other pages TO this one), list the
candidate source pages:

```bash
python optimizer/interlink.py <slug>
```

Add a contextual link from each strong candidate to the target with descriptive anchor text.

**Present this plan and get approval before Step 7.**

## STEP 7 - Build the optimized HTML
Start from `optimizer/template.html`. Keep good content unmarked; wrap additions in
`.new-block` + `.new-tag` (inline in `.new-inline`) and removals in `.remove-block` +
`.remove-tag` with the reason. Include the publishing-fields box (meta title `NN/60`, meta
description `NN/155`, H1), the AIO answer-first opening paragraph (40-60 words) after the H1,
2024-2026 stats only, and a FAQ accordion whose JSON-LD matches the visible items. Bake in
`optimizer/MODERN-SEO-PLAYBOOK.md`. The brand is named once, in the conclusion, only if
natural. ZERO em/en dashes. American English only. Specifically:

- **Contextual internal links + anchor text.** Each internal link is one a reader would
  genuinely click in that paragraph; anchor text is descriptive and names the destination
  topic (no CTA words); max 1 link per paragraph; never link to country/city pages. External
  links use `rel="nofollow" target="_blank"` and only when citing a specific stat/study/quote.
- **Secondary + longtail keywords.** Place the terms captured in Step 5 naturally in H2/H3s
  and body; never force them.
- **Flow.** Logical section order, one idea per paragraph, no jumps or repeats, answer-first
  per section.
- **Readability.** Short paragraphs, active voice, plain words. Aim for Flesch reading ease 60+.
- **Section self-sufficiency (Rule 16).** AI answer engines usually quote a single H2/H3 chunk,
  not the whole page. Give every H2/H3 an `id` slug (for a ToC and precise citation), and once
  the draft is otherwise done, read each section in isolation as if it were the only thing an
  AI pulled - if it doesn't make sense standalone, rewrite the opening sentence to name the
  actual subject instead of leaning on the heading or a bare pronoun. `qa_check.py`'s "Section
  may depend on prior context" INFO note catches the mechanical case; this read-through catches
  the rest.
- **Original data, when it fits.** Third-party stats are useful but easy for a competitor to
  replicate; per `MODERN-SEO-PLAYBOOK.md`, original data and brand mentions are the strongest
  GEO levers. If the brand has its own numbers relevant to this topic (survey results, aggregate
  customer outcomes, an internal benchmark), prefer citing those over another third-party stat.
  Not every page will have one - don't force it - but check before defaulting to citations only.
- **Changes summary.** Fill the `.changes-summary` table near the end (review only) so the
  reviewer sees exactly what was done: sections, secondary/longtail keywords placed, internal
  and external links added, stats refreshed, FAQ, and the AI Overview angle.

Then generate 3 meta-title/description options based on what the article actually contains.

## STEP 8 - QA gate, ledger, save
Run the automated gate **after the content is final**, not against an earlier draft's word
count - `qa_check.py` computes its own reader word count and uses that for the link band
regardless of what `--words` says, but a stale `--words` value is a sign you edited content
after the last QA run and should re-verify nothing else drifted (FAQ count, link count,
keyword placement). Pass the reader-facing word count for the right link band, plus the
primary keyword so placement is checked:

```bash
python optimizer/qa_check.py "final output/<slug>-green.html" --words <reader_word_count> --keyword "<primary keyword>"
python optimizer/linkcheck.py "final output/<slug>-green.html"   # every internal link resolves to a live, canonical URL (no 404s, no redirects)
python optimizer/meta_audit.py   # confirm this page's meta title/description are unique site-wide
```

All hard checks must pass: the changes-summary table, heading hierarchy (one H1, no skipped
levels), image alt text, primary-keyword placement, and valid JSON-LD parsing; aim for Flesch
60+. Also check the soft `[INFO]` notes if any appear - repeated stat (Rule 14), a section
opening on a bare pronoun (Rule 16), an over-length paragraph or question-answer, a fragment-y
FAQ answer, or missing author credentials - vary/rewrite/fill in as appropriate; none of these
block the gate, but each is a real, actionable signal. Then the manual checks the tool cannot
do: re-score the 50-point checklist (PASS-before vs PASS-after), spot-check 3-4 external
sources, read for flow and readability, and confirm no new section or FAQ conflicts with
another page (each FAQ must add a genuinely new angle, not restate a stat already given in the
body).

Once the page is live, run the live-only technical check against the published URL (the
pre-publish draft never carries a canonical tag or a robots meta tag, so this can't run earlier):

```bash
python optimizer/technical_seo.py <published URL or slug>   # not accidentally noindexed; exactly one, correct canonical tag
```

Record every NEW section in the content ledger so future pages do not repeat it:

```bash
python optimizer/ledger.py add <slug> --section "<H2 title>" --angle "<what makes it unique>" --asset "<unique table/data>"
```

Also record every NEW external stat cited, so staleness and cross-page conflicts can be
caught proactively later:

```bash
python optimizer/citations.py add <slug> --stat "<the stat as written>" --source "<source>" --year <YYYY> --url "<source url>"
```

Save to `final output/{slug}-green.html`. Report: what changed, before/after metrics, the QA
scorecard + readability, the AI Overview angle, the slug and scope verdicts, the 50-point
delta, the 3 meta options, and the ledger entries added.
**Wait for confirmation before the next page.**

## STEP 9 - Post-publish verification (about 30 days after publishing)
Optimization is not done when the page ships; GEO is probabilistic and the citable set rotates
month to month (see the playbook). Close the loop so you learn which changes actually earned
visibility, rather than optimizing blind.

Roughly 30 days after the page goes live, for the primary keyword and 3-5 real buyer prompts:
- Re-check the **live Google AI Overview**: is the page (or brand) now cited? In what format?
- Run the same prompts across **ChatGPT, Perplexity, Gemini, and Claude** and record citation
  presence (present / absent), since engines barely overlap and output is probabilistic (run
  each prompt a few times, not once).
- Pull fresh **GSC** numbers for the URL: clicks, impressions, CTR, average position, and
  compare against the before snapshot from Step 1.

Log the result with `verify.py` so it is captured in one place:

```bash
python optimizer/verify.py add <slug> --keyword "<primary keyword>" \
    --cited chatgpt,perplexity --not-cited gemini,claude \
    --ai-overview yes --ctr-delta +0.4 --pos-delta -3 --note "<what earned/missed the citation>"
```

Feed it back: pages that moved confirm the lever; pages that did not get re-queued with a new
angle. When exports refresh, rerun `python build_scorecard.py` so the scorecard/decay signal
(`trend_label`, category) reflects the new reality, then `python optimizer/next.py` to pick the
next page by priority.

**Site-level measurement to set up once (from the AEO course), not per page:**
- **GA4 AI-traffic channel.** Create a custom channel group "AI Traffic" matching the AI
  referrers so assistant-driven visits are attributable:
  `chatgpt\.com|perplexity\.ai|gemini\.google\.com|copilot\.microsoft\.com|claude\.ai|deepseek\.com`.
- **Bot-hit analytics.** Monitor crawl frequency from `GPTBot` / `OAI-SearchBot` in server or
  CDN logs (complements `check_bots.py`, which only confirms access is allowed).
- **Zero-party attribution.** Add a "How did you hear about us?" field at signup/checkout to
  capture the 72% of brand mentions that are unlinked (no referrer to measure).
- **Inbound 404 audit.** AI assistants hallucinate URLs, so periodically pull 404s with AI
  referrers and 301-redirect them to the closest live page.
- **Site-wide technical + link health.** `python optimizer/sitecheck.py sitemap <sitemap-url>`
  and `python optimizer/sitecheck.py crawl` check the WHOLE inventory (not just the page you're
  currently optimizing) for sitemap orphans and broken/redirecting pages.
- **pricing.md for AI agents.** `python optimizer/pricing.py > pricing.md` generates a
  skeleton (name + URL per money page); fill in real price/limits/features by hand, publish at
  the site root, and keep it current - an AI agent evaluating the service skips a vendor whose
  pricing it can't parse. Revisit whenever a money page's pricing changes, not just quarterly.
- **Stat freshness + consistency.** `python optimizer/citations.py stale` surfaces cited stats
  approaching (or past) the `MIN_STAT_YEAR` cutoff before a reader notices; `python
  optimizer/citations.py conflicts` flags likely contradicting numbers across pages.
- **Cadence.** Monthly: re-check share of voice / citations for priority pages. Quarterly:
  competitive audit, a sleeper-page refresh pass (the scorecard's decay categories drive this),
  the sitemap/crawl check, and the citations staleness/conflicts check.
