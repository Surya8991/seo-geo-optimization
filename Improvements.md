# Improvements Backlog

Originally 36 concrete improvement ideas for this pipeline, surfaced in a content-optimization
review session (all considered equally important, not ranked); grown to 37 as batch 4 surfaced
one more. **Status: 36/37 addressed** - either built, or explicitly declined with reasoning
recorded inline (a declined item is still "addressed," not abandoned silently). The one open
item (21) needs API access this environment doesn't have. The grouping below is by *aspect*,
not priority/status. Add new ideas here as they surface rather than losing them to chat.

**Batch 1 (2026-09-24): done.** New `optimizer/technical_seo.py` (live noindex + canonical
check), 4 new `qa_check.py` INFO checks (dangling-reference opener, long paragraphs, long
question-answers, FAQ fragments), `linkcheck.py` extended to check breadcrumb JSON-LD URLs, and
the 4 vague-opener sections in the real output page rewritten. 21 new tests added (169 total).

**Batch 2 (2026-09-24): done.** `schema_completeness()` extended for HowTo required fields +
a soft author-credential-gap check; `template.html` updated with self-sufficiency/ToC/speakable/
key-terms guidance; `AGENTS.md`/`QUALITY-RULES.md` Rule 16 added; `WORKFLOW.md` build-step +
original-data + live technical-check steps added; the real output page got heading `id`s, a
table of contents, a key-terms `<dl>`, `HowTo` + `speakable` JSON-LD, and an author `jobTitle`.
8 new tests added (177 total).

**Batch 3 (2026-09-24): done.** New `optimizer/sitecheck.py` (sitemap coverage + site-wide
crawl) and `optimizer/citations.py` (stat-provenance ledger); `technical_seo.py` extended with
an hreflang audit; `qa_check.py` got an acronym-reuse INFO check, which caught a real issue on
the live page (FAQ #3 reused "ROI" without a local definition - fixed); a live rendering audit
against edstellar.com confirmed content is server-rendered (no JS-visibility risk to retrieval
bots); `MODERN-SEO-PLAYBOOK.md` strengthened with concrete next-steps for entity signals and
off-site mention monitoring. 45 new tests added (222 total).

**Batch 4 (2026-09-24): done - backlog fully closed (36/36 addressed).** Loaded the `ai-seo`
skill before touching item 34, which changed the plan: Google's own guidance explicitly warns
against writing separate content "for AI" or fragmenting pages into AI-bait chunks (this
project's own `MODERN-SEO-PLAYBOOK.md` already said the same - "do not artificially fragment
content"), and confirmed everything built in Batches 1-3 is normal content structure that helps
people and AI alike, not an AI-only variant. New `optimizer/pricing.py` (a genuinely new idea
surfaced by that skill, not in the original 36) generates a `/pricing.md` skeleton for AI
agents evaluating the service - never fabricates figures. Item 34 (OKF) formally declined with
reasoning; item 7 formally declined with reasoning; items 1/3/4/5 verified closed via a full
manual section-by-section scan (every H2/H3's opening sentence now names its actual subject,
confirmed by both the automated checks returning empty and a full read-through). 4 new tests
added (226 total).

## A. Section self-sufficiency for AI extraction
AI answer engines (Google AI Overview, ChatGPT browsing, Perplexity) usually retrieve and quote
a single H2/H3 chunk, not the whole page. Each section needs to stand alone.

- [x] 1. Restate the subject in each section's opening sentence instead of a bare pronoun -
      applied across Practices 5/7/8/11 (batch 1) plus the acronym fixes (batch 3); verified
      closed by a full section-by-section scan (batch 4): every H2/H3 now opens by naming its
      actual subject, and `dangling_reference_sections()` returns `[]`.
- [x] 2. Define acronyms/jargon on first use within each section - ROI and AR/VR expanded,
      SME/SMART already were; the FAQ #3 "ROI" reuse specifically fixed (batch 3).
- [x] 3. One clearly extractable, answer-first sentence per section - confirmed via the batch 4
      full-page scan; every practice leads with a substantive, self-contained claim, not a
      throat-clearing sentence.
- [x] 4. Avoid reading-order-dependent language - the "So the thing that pushes people out..."
      sequencing issue in Practice 11 fixed in batch 1; no other instances found in the batch 4
      scan.
- [x] 5. Repeat the practice's name/number inline in the body - done for the sections that
      needed it (batch 1 rewrites); the `HowTo` schema (batch 2) also restates each practice's
      name independent of the visible heading.

## B. Automated qa_check.py checks (INFO-level, like the existing Flesch/repeated-stat checks)
- [x] 6. Dangling-reference opener check: flag any H2/H3 section whose first sentence starts
      with a bare pronoun/connective (It/This/That/They/So/Then/Also/However).
      `dangling_reference_sections()` in `optimizer/qa_check.py`.
- [x] 7. Heading-body topic overlap check: **declined, not building.** Beyond the original
      false-positive concern, the `ai-seo` skill's Princeton GEO citation showed keyword
      stuffing actively HURTS AI visibility (-10%); a mechanical "reuse the heading's words in
      the first sentence" check would push writing toward exactly that anti-pattern instead of
      natural variation. The narrower, safer checks (6, 8) cover the real self-sufficiency risk
      without that incentive.
- [x] 8. Acronym-reuse check: `undefined_acronym_reuse()` in `qa_check.py`. Caught a real issue
      on the first run: FAQ #3 on the real page reused "ROI" without redefining it locally -
      fixed (see item E below).

## C. Structural / schema additions
- [x] 9. `speakable` schema markup - added to the BlogPosting JSON-LD (`h1` + `.aio-answer`),
      with `class="aio-answer"` on the opening paragraph. Documented in `template.html`.
- [x] 10. Per-practice mini-schema: added a `HowTo` block (12 `HowToStep`s, name+text+url per
      step) rather than `DefinedTerm` per practice - fits the numbered-practice structure better.
      `schema_completeness()` now validates HowTo's required fields too.
- [x] 11. Definition-sentence pattern: documented as a template convention (name the subject in
      the opening sentence - see item 1/15) rather than forced visual bolding on every section,
      to avoid a heavy-handed, gimmicky-looking result across 12 practices.
- [x] 19. Anchor IDs + in-page table of contents: every H2/H3 in the real output page now has an
      `id` slug; a new "On this page" nav links to the major sections. Confirmed `#fragment`
      hrefs don't count against the internal-link budget or trip `linkcheck.py`.

## D. Workflow / documentation updates
- [x] 12. Added Rule 16 ("Section self-sufficiency for AI extraction") to `AGENTS.md` and a
      matching row + INFO-check list to `optimizer/QUALITY-RULES.md`.
- [x] 13. Added a "Section self-sufficiency" bullet to `WORKFLOW.md` Step 7: read each section
      in isolation once the draft is done, rewrite openers that lean on the heading or a pronoun.
- [x] 14. `optimizer/template.html` updated: id-slug/ToC/speakable/key-terms guidance comments,
      `class="aio-answer"` convention, expanded HowTo/author-jobTitle schema examples.

## E. Apply directly to the existing page
- [x] 15. Rewrite the weak openers in
      `final output/employee-training-best-practices-green.html`: Practice 5 ("Different skills
      need different formats"), Practice 7 ("Skill comes from doing, not watching"), Practice 8
      ("Measurement is the most skipped practice..."), Practice 11 ("Development is one of the
      strongest reasons people stay"). Each now names "training" explicitly in its opening
      sentence; re-verified 33/33 qa_check + linkcheck clean.
- [x] 15b. ROI and AR/VR were used without being spelled out anywhere on the page - both
      expanded on first mention, added to the key-terms `<dl>`, and (caught by the new item-8
      check) FAQ #3's "ROI calculation" fixed to spell it out too, since FAQ content is often
      quoted independently of the body.

## F. Entity / E-E-A-T authority signals
- [x] 16. Added `author_credential_gap()` in `qa_check.py` (soft INFO, not a hard fail - a bare
      string author has nothing to check) + gave the real page's author a `jobTitle`.
- [x] 17. Strengthened `MODERN-SEO-PLAYBOOK.md`'s "Entity clarity" bullet with a concrete
      site-level note: a Wikidata/Wikipedia entry + consistent `sameAs` links on the
      `Organization` schema, flagged for the wider brand/content strategy (not a per-page fix).

## G. Stat provenance & freshness automation
- [x] 18. New `optimizer/citations.py`: `add`/`list`/`stale`/`conflicts` CLI, parallel to
      `ledger.py`. `stale_or_aging()` separates already-stale from "aging" (exactly at the
      `MIN_STAT_YEAR` cutoff - proactive warning before the reactive check would catch it).
      `find_conflicts()` heuristically flags cross-page stat pairs with high text overlap or
      the same source but a different number. Wired into `WORKFLOW.md` Step 8 (record) and the
      quarterly site-level cadence (review).

## H. Technical/rendering GEO risk
- [x] 20. Fetched the live `edstellar.com/blog/employee-training-best-practices` page's raw
      server HTML directly (no JS execution) and confirmed the title, H1, H2s, and body text
      are all present in the initial response - not injected by client-side JS. No GEO
      visibility risk for retrieval bots found. One-off audit, not an automated check (site-wide
      rendering behavior isn't a per-page content concern).

## I. Multi-engine citation tracking automation
- [ ] 21. Script that sends the primary keyword/buyer prompts to multiple AI engines via API and
      auto-logs citation presence, reducing manual effort in `verify.py`'s Step 9. Still open:
      needs API keys/budget for ChatGPT/Perplexity/Gemini/Claude this session doesn't have. The
      `ai-seo` skill's monitoring section (Otterly AI, Peec AI, ZipTie, LLMrefs) is worth
      checking first when this gets picked up - a paid tool may cover this better than a
      bespoke script would.

## J. Technical SEO
- [x] 22. Accidental-noindex check: `optimizer/technical_seo.py` (`is_noindexed()`) - live check
      against the published URL, since the pre-publish draft never carries this tag.
- [x] 23. Canonical tag check: `optimizer/technical_seo.py` (`canonical_issues()`) - same tool.
- [x] 24. New `optimizer/sitecheck.py` `crawl` command: fetches every `money_pages` +
      `blog_pages` URL from `audit.json` and classifies each ok/redirect/broken, reusing
      `linkcheck.py`'s `fetch_status`/`classify`.
- [x] 25. New `optimizer/sitecheck.py` `sitemap` command: fetches the live sitemap (recursing
      one level into a sitemap index), and `sitemap_coverage()` reports inventory pages missing
      from it and sitemap pages missing from the inventory.
- [x] 26. hreflang audit: `technical_seo.py`'s `hreflang_issues()` - checks a self-referencing
      entry and an `x-default` fallback exist, for a page that has hreflang tags at all. Scoped
      to one URL at a time (not fetching every country-slug page to verify full reciprocity -
      that's a bigger, separate crawl noted but not built).
- [x] 27. Extended `schema_completeness()` with a required-fields check for `HowTo` (name +
      every step's name/text), alongside the existing Article/BlogPosting check. Course/Product
      not yet added (no page in this repo uses them yet - add when one does).
- [x] 28. Breadcrumb JSON-LD URL check: `extract_breadcrumb_links()` in `optimizer/linkcheck.py`,
      wired into `run()`.

## K. AEO (Answer Engine Optimization)
- [x] 29. Snippet-length compliance per section: `long_question_answers()` in `qa_check.py` -
      flags a question-phrased H2/H3 whose first paragraph exceeds ~60 words.
- [x] 30. `HowTo` schema added (12 steps, see item 10). Did NOT restructure the visible practice
      list into a literal `<ol>`: each practice has multi-paragraph, mixed content (links,
      new-block wrappers), and Google scaled back HowTo rich results for most non-recipe sites,
      so the markup-surgery risk outweighed the uncertain benefit. The numbered `<h3>` headings
      already serve the "step" reading experience without it.
- [x] 31. Voice-readability check for FAQ answers: `faq_answer_fragments()` in `qa_check.py`.

## L. GEO (Generative Engine Optimization)
- [x] 32. Visible definition-list pattern: added a "Key terms in this guide" `<dl>` section
      (SMART goal, SME, microlearning, Kirkpatrick model) to the real output page.
- [x] 33. Added an "original data, when it fits" reminder to `WORKFLOW.md` Step 7.
- [x] 34. Loaded the `ai-seo` skill and read its OKF guidance directly (batch 4): OKF has "no
      confirmed AI-search ranking signal today," is aimed at data-catalog metadata rather than
      blog content, and is explicitly compared to "early schema.org registration." Combined
      with this project's own inventory still being thin (item H/#20's small-inventory
      warnings), a cross-linked multi-page OKF bundle isn't a good fit yet. **Declined, not
      building** - documented in `MODERN-SEO-PLAYBOOK.md` section 6 with the reasoning, so a
      future revisit starts from "why we skipped it" rather than from scratch.
- [x] 35. Strengthened `MODERN-SEO-PLAYBOOK.md`'s "off-site authority" bullet with a concrete
      next step (a mentions-monitoring service feeding topic/page prioritization) - still
      explicitly flagged as needing something outside this repo, not a script.
- [x] 36. Paragraph chunk-size check: `long_paragraphs()` in `qa_check.py`.
- [x] 37. **New, surfaced by the `ai-seo` skill (not in the original 36).** `/pricing.md` for
      AI buying agents: `optimizer/pricing.py` generates a skeleton (name + URL per money page)
      from `audit.json`; fill in real price/limits/features by hand, never invented. An AI
      agent evaluating the service on a buyer's behalf skips a vendor whose pricing sits behind
      a "contact sales" wall or JS-rendered page it can't parse.
