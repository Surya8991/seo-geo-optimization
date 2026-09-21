# Quality Rules - QA Reference

The 12 hard rules from `AGENTS.md`, restated as **pass criteria** with how each is
verified. `AUTO` = enforced by `qa_check.py`. `MANUAL` = human judgment required.
`AGENTS.md` is the authoritative wording; this is the checklist you run against.
Wherever this says "the brand" or `example.com`, the real values come from `config.json`.

Run the gate before saving any output:

```bash
python optimizer/qa_check.py "final output/{slug}-green.html" --words <reader_word_count>
```

| # | Rule | Pass criteria | Check |
|---|------|---------------|-------|
| 1 | Zero em dashes | Count of em dashes = 0 (in tables use a real value or a blank cell) | AUTO |
| 1b | Zero en dashes / double-hyphen breaks | Count of en dashes = 0; no ` -- ` as a sentence break | AUTO |
| 2 | No keyword stuffing | Primary keyword in title, H1, meta desc, URL, first 100 words, conclusion - max 5-6 total | MANUAL |
| 3 | Link budget | Internal + external within the word-count band table; **max 1 link per paragraph**. **Never link to country/city pages** (e.g., example.com/australia/, example.com/india/). Only link to generic money/course pages (example.com/&lt;slug&gt;/), category pages, or other content pages. | AUTO |
| 3b | Link relevancy | Every link passes "would a reader actually click this here?" No filler sentences to justify a link | MANUAL |
| 4 | No CTA anchor text | No "Explore / Discover / Get Started / Learn More / View All / Check Out / Try / Click Here / Read More" as anchor text | AUTO |
| 5 | Minimal brand usage | The brand name appears 0-1 times in reader body (conclusion only); notes box excluded | AUTO |
| 6 | Cannibalization check | No new H2 duplicates a subtopic another page or blog owns (search scorecard/audit data) | MANUAL |
| 7 | Red removal markers | Thin/off-topic/outdated content wrapped in `.remove-block` + `.remove-tag` | MANUAL |
| 8 | External link discipline | Hyperlink only for a specific stat/study/quote; well-known sources may be name-only. All ext links `rel="nofollow" target="_blank"` | AUTO (attrs) + MANUAL (judgment) |
| 9 | American English | No British spellings (`-ise/-isation/-our/-re`, colour, behaviour, etc.) | AUTO |
| 10 | No AI signals | No em dashes; varied sentences; no filler ("In today's rapidly evolving...", "It's worth noting...") | AUTO (dashes) + MANUAL (voice) |
| 11 | FAQ quality + limits | FAQs target PAA / new angles, not body rehash; count band by words; HTML items == JSON-LD entries | AUTO (count) + MANUAL (angle) |
| 12 | Stat verification | Every stat real, sourced, and 2024-2026; unverifiable stats removed | MANUAL |

## Link budget bands (Rule 3)

| Reader word count | Internal (max) | External hyperlinks (max) |
|-------------------|----------------|---------------------------|
| Under 2,000 | 4 | 3 |
| 2,000-4,000 | 7 | 4 |
| 4,000-6,000 | 9 | 5 |
| Over 6,000 | 10 | 6 |

**Country/city page restriction (Rule 3 addition):** Never link to country or city pages
(the geo-slug list lives in `config.json` and drives the automated check). Only link to
generic money/course pages, category pages, or other content pages. Geo landing pages do
not add value as internal link destinations.

## FAQ count bands (Rule 11)

| Reader word count | FAQ count |
|-------------------|-----------|
| Under 3,000 | 5-6 |
| 3,000-6,000 | 6-8 |
| Over 6,000 | 8-10 |

## Publishing-fields format (so `qa_check.py` can read title/meta length)

The blue publishing-fields box must keep this exact label format:

```
<strong>Meta title (NN/60):</strong> ...
<strong>Meta description (NN/155):</strong> ...
```

`qa_check.py` parses those labels to verify length. Meta title <= 60. Meta description must be
140-160 chars (target ~150-155); the gate accepts 140-160 so valid copy near the cap does not FAIL.

## What `qa_check.py` does NOT check (always do by hand)

- The 50-point checklist re-score (how many points now PASS vs before).
- Article flow and readability.
- Factual accuracy of stats and whether sources actually say what is cited (spot-check 3-4).
- Whether new sections genuinely fill a competitor gap vs padding.
- Cannibalization judgment (the tool cannot know intent).
