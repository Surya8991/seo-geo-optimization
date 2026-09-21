---
description: Run the full SEO & GEO page-optimization pipeline for one page (8 steps + post-publish verification)
argument-hint: <slug> [gsc keywords: kw1, kw2, ...]
---

# Optimize one page (SEO + AEO + GEO)

You are running the per-page optimization pipeline on a single page. The full rules live
in `AGENTS.md`, the runbook in `WORKFLOW.md`, the checklist in
`optimizer/OPTIMIZATION-CHECKLIST.md`, the QA gate in `optimizer/QUALITY-RULES.md`, and the
modern tactics in `optimizer/MODERN-SEO-PLAYBOOK.md`. All brand specifics come from
`config.json`. Those are the source of truth; this command runs them in order with the gates.

**Input for this run:** `$ARGUMENTS`
- First token is the page slug (for example `product-certification` or `info/product-certification`).
- Anything after it is optional GSC keywords the user supplied. Treat those as real query
  demand and fold them in naturally. Never invent keywords from site-wide GSC data.

## Non-negotiables (carry through every step)
- One page at a time. Do not start another page until the user confirms this one.
- Quality over speed. Do not skip a step or rush a gate.
- Never remove content that is working; add and improve, mark changes with green/red blocks.
- ZERO em dashes, ZERO en dashes, ZERO double-hyphen breaks. American English only.
- Show the plan and get approval before building (end of Step 6). Then build.

---

## Step 1 - Gather intelligence
```bash
python optimizer/lookup.py <slug>
```
Read the lever it prints (high impressions + low CTR = title/meta, low position = depth,
page 1 below fold = freshness + snippet, declining = content decay). Scrape the live page
on the configured domain, and open `optimizer/OPTIMIZATION-CHECKLIST.md`. Note any GSC
keywords from `$ARGUMENTS`.

Once per site (not per page), confirm the AI retrieval bots can even reach the content, since
no on-page work earns a citation if they are blocked:
```bash
python optimizer/check_bots.py
```
If a retrieval bot (OAI-SearchBot, ChatGPT-User, PerplexityBot, Claude-Web) is BLOCKED, flag it
to the user as a site-level fix; it is outside this page edit but gates all GEO results.

## Step 2 - Slug and URL review
Output: KEEP (no change needed) or CHANGE (new slug + "301 redirect from old to new").

## Step 3 - Scope and pivot assessment
Output: OPTIMIZE AS-IS / PIVOT KEYWORD (to X) / MERGE WITH [page] / REPOSITION.

## Step 4 - Audit current content
Score the live content against all 50 points. Record current meta title (char count), meta
description (char count), and H1. Flag thin or outdated sections, pre-2024 stats, weak
structure, missing schema/FAQ, and content to remove (red block).

## Step 5 - Competitor and keyword research
Top 5-10 SERP results across USA, India, Canada, UK, Australia. **Check the AI Overview for
the primary keyword**: record who is cited, in what format, and the angle that would earn a
citation (research shows ~44% of AI citations come from the first 30% of the page, so plan an
answer-first lead). Capture the content gap, the secondary and longtail keywords to place,
and the real PAA questions (research them).

## Step 6 - Plan (get approval before building)
Set intensity from the category. Before ANY new H2 or FAQ:
```bash
python optimizer/cannibal.py "<proposed section title>" --exclude <slug>
```
Strong overlap = add a mention + internal link, or skip. For inbound internal links
(Checklist #29, links FROM other pages TO this one), list candidate source pages:
```bash
python optimizer/interlink.py <slug>
```
Plan headings, keyword placement (max 5-6 primary), link budget from the word band (internal
links only to money/course and content pages, ZERO country/city links), the inbound links to
add from the `interlink.py` candidates, FAQ, and hyperlink vs name-only external sources.
No meta tags yet. **Present this plan and wait for approval.**

## Step 7 - Build the optimized HTML
Start from `optimizer/template.html`. Green blocks for additions, red for removals,
publishing-fields box, AIO opening paragraph (40-60 words), 2024-2026 stats, FAQ with matching
JSON-LD. Bake in `optimizer/MODERN-SEO-PLAYBOOK.md`. Specifically:
- **Contextual internal links + anchor text:** each link is one a reader would genuinely
  click here; descriptive anchor naming the destination topic; no CTA words; max 1 per
  paragraph; no country/city pages.
- **Secondary + longtail keywords:** place the terms from Step 5 naturally in H2/H3s and body.
- **Flow:** logical order, one idea per paragraph, no jumps or repeats; answer-first per section.
- **Readability:** short paragraphs, active voice, plain words (aim for Flesch 60+).
- **Changes summary:** fill the `.changes-summary` table so the reviewer sees exactly what was
  done (sections, keywords placed, links added, stats refreshed, AI Overview angle).

Then generate 3 meta options from the actual content.

## Step 8 - QA gate, ledger, save
```bash
python optimizer/qa_check.py "final output/<slug>-green.html" --words <reader_word_count>
```
Every hard check must pass (including the changes-summary table and valid JSON-LD parsing); aim
for Flesch 60+. Then the manual checks: re-score the 50-point checklist (PASS-before vs
PASS-after), spot-check 3-4 external sources, read for flow, confirm no cannibalization. Record
every NEW section so future pages do not repeat it:

```bash
python optimizer/ledger.py add <slug> --section "<H2 title>" --angle "<what makes it unique>" --asset "<unique table/data>"
```

Save to `final output/<slug>-green.html`. Report what changed, before/after metrics, the QA
scorecard + readability, the AI Overview angle, slug and scope verdicts, the 50-point delta,
the 3 meta options, and the ledger entries added. To surface the highest-priority page to do
next, run `python optimizer/next.py`.
**Then wait for confirmation before the next page.**

## Step 9 - Post-publish verification (later, ~30 days after this page is live)
Not part of this run. About a month after the page ships, close the loop (see `WORKFLOW.md`
Step 9): re-check the live AI Overview and run a few buyer prompts across ChatGPT, Perplexity,
Gemini, and Claude, pull fresh GSC numbers, and log the result:
```bash
python optimizer/verify.py add <slug> --keyword "<primary keyword>" \
    --cited chatgpt,perplexity --not-cited gemini,claude \
    --ai-overview yes --ctr-delta +0.4 --pos-delta -3 --note "<what earned/missed the citation>"
```
