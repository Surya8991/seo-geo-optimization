---
description: Create a brand-new SEO + GEO optimized blog/page from scratch (not an edit of an existing one)
argument-hint: <topic or working title> [primary keyword] [gsc keywords: ...]
---

# Create a new page (SEO + AEO + GEO)

This is the NEW-content track. Use it to write a page that does not exist yet. To improve
an existing live page, use `/optimize-page` instead. The rules in `AGENTS.md`, the tactics
in `optimizer/MODERN-SEO-PLAYBOOK.md`, the 50-point bar in
`optimizer/OPTIMIZATION-CHECKLIST.md`, and the QA gate all still apply. Brand specifics come
from `config.json`.

**Input for this run:** `$ARGUMENTS` (topic/working title, optional primary keyword, optional GSC keywords).

## How the new track differs from optimizing
- No live page to scrape or audit, and no scorecard row yet.
- Output is CLEAN, publish-ready HTML: no green/red diff markers, no changes-summary table.
- Cannibalization is the make-or-break step: the whole page must not duplicate what an
  existing page or a past build already owns.
- QA runs in new mode: `qa_check.py ... --new`.

## Non-negotiables (same as always)
- Quality over speed. One page at a time; wait for confirmation before the next.
- ZERO em/en dashes and no double-hyphen breaks. American English. Stats 2024-2026 only.
- Brand named once, in the conclusion, only if natural.

---

## Step 1 - Define target and intent
Fix the primary keyword and the search intent. If GSC keywords were supplied, treat them as
real demand. Confirm this topic is worth a standalone page (business value, realistic to rank).

Once per site (not per page), confirm the AI retrieval bots can reach the content, since no
on-page work earns a citation if they are blocked:
```bash
python optimizer/check_bots.py
```
If a retrieval bot (OAI-SearchBot, ChatGPT-User, PerplexityBot, Claude-Web) is BLOCKED, flag it
to the user as a site-level fix; it is outside this page but gates all GEO results.

## Step 2 - Cannibalization clearance (do this before writing anything)
The topic and every planned H2 must not already be owned by an existing page, a blog, or a
past build:

```bash
python optimizer/cannibal.py "<topic / each proposed H2>"
```

If a page already owns the core topic in depth: STOP and recommend optimizing that page
(`/optimize-page`) or narrowing this one to a distinct angle. A `[LEDGER]` hit means a past
build already wrote that section: link to it, do not rewrite it.

## Step 3 - Competitor and SERP research
Top 5-10 results for the primary keyword across USA, India, Canada, UK, Australia. Check the
AI Overview: who is cited, in what format, and what angle would earn a citation. Capture the
content outline, secondary and longtail keywords, and the real PAA questions.

## Step 4 - Plan (get approval before writing)
Slug (short, keyword-rich), heading structure (strict H1 > H2 > H3), primary keyword
placement (max 5-6), secondary and longtail keyword placement, link budget from the
word-count band (internal links only to money/course and content pages with contextual
descriptive anchors, ZERO CTA anchors, ZERO country/city links), FAQ set, and which external
sources get a hyperlink vs a name-only mention.

The new page will have no inbound links until it is published. Plan them now so they go live
with it (Checklist #29): find existing pages that should link TO the new page by its topic:
```bash
python optimizer/interlink.py "<primary keyword>"
```
List the source pages to update with a contextual link once the page is live. **Present the
plan and wait for approval.**

## Step 5 - Write the page
Start from `optimizer/template.html` but REMOVE the review-only blocks (the green/red example
markers and the changes-summary), since this is clean output. Keep the publishing-fields box,
the AIO answer-first opening paragraph (40-60 words), strict heading hierarchy, contextual
internal links, `rel="nofollow" target="_blank"` external links only for a specific
stat/study/quote, 2024-2026 stats, and the FAQ accordion with matching JSON-LD. Bake in
`optimizer/MODERN-SEO-PLAYBOOK.md` (answer-first blocks, cited stats + one named-authority
quote + one original element, self-contained passages, entity clarity, the schema set). Read
for flow and readability as you write: short paragraphs, active voice, one idea per paragraph.
Then produce 3 meta-title/description options from the actual content.

## Step 6 - QA gate, ledger, save
```bash
python optimizer/qa_check.py "final output/<slug>.html" --words <reader_word_count> --new --keyword "<primary keyword>"
python optimizer/meta_audit.py   # confirm the new meta title/description are unique site-wide
```
All hard checks must pass (heading hierarchy, image alt text, keyword placement, valid JSON-LD);
aim for a Flesch reading ease of 60+. Then record every substantive new section so future pages do not repeat it:

```bash
python optimizer/ledger.py add <slug> --section "<H2 title>" --angle "<what makes it unique>" --asset "<any unique table/data>"
```

Save to `final output/<slug>.html`. Report: the plan delivered, the 50-point coverage, the QA
scorecard + readability, the AI Overview angle, the 3 meta options, and the ledger entries
added. **Wait for confirmation before the next page.**

## Step 7 - Post-publish verification (later, ~30 days after this page is live)
Not part of this run. About a month after publishing, close the loop (see `WORKFLOW.md`
Step 9): confirm the planned inbound links went live, re-check the live AI Overview, run a few
buyer prompts across ChatGPT, Perplexity, Gemini, and Claude, and log the result:
```bash
python optimizer/verify.py add <slug> --keyword "<primary keyword>" \
    --cited chatgpt,perplexity --not-cited gemini,claude \
    --ai-overview yes --note "<what earned/missed the citation>"
```
