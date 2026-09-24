# Modern Search Optimization Playbook (SEO + AEO + GEO + LLM)

The practices every page must apply so it ranks and gets **cited** across all four
surfaces at once, not just the classic ten blue links. Baked into the build step of
`WORKFLOW.md`. Nothing here overrides the 12 hard rules in `AGENTS.md`; it is how you
earn visibility inside them. Wherever this says "the brand", the value comes from `config.json`.

## The four surfaces you are optimizing for
| Surface | What it is | What wins |
|---------|-----------|-----------|
| **SEO** (classic SERP) | Google/Bing ranked results | Relevance, E-E-A-T, links, technical health |
| **AIO** (AI Overviews) | Google's AI answer box atop results | Answer-first blocks, structured data, topical authority |
| **AEO** (answer engines) | People Also Ask, featured snippets, voice, Bing | Concise direct answers, Q&A format, clean structure |
| **GEO / LLM** (generative assistants) | ChatGPT, Gemini, Perplexity, Claude, AI Mode | Citable passages, statistics, quotes, entity clarity, off-site authority |

**The single principle that serves all four:** make the answer to each likely question
**extractable in one self-contained passage**, backed by a **verifiable cited fact**, with
**unambiguous entities** and a **clean heading path** to it. Everything below is that
principle applied.

---

## 1. Foundational SEO (still required, non-negotiable)
AI citation correlates with classic ranking: pages that rank well are far likelier to be
cited. Do not treat GEO as a replacement.
- Primary keyword in title, H1, meta description, URL, first 100 words, conclusion (Rule 2).
- Search intent match: the format mirrors what the top 3 SERP results are (list, guide, comparison).
- Clean H1 > H2 > H3 hierarchy, one H1, no skipped levels. 2026 analyses report that pages
  with a clean, sequential heading structure are cited markedly more often than pages with a
  flat or broken hierarchy (see Sources; figure varies by study).
- Internal links to the topic cluster + money page; external links to authoritative sources.
- Freshness: current-year references, updated date visible, stats from 2024-2026.
- Mobile, fast, indexable, tables in `.table-scroll`.

## 2. AEO - Answer Engine Optimization (win PAA, snippets, AI Overviews)
Goal: be the passage Google lifts into a snippet or AI Overview.
- **Answer-first blocks.** Open each key section with a direct 40-60 word answer to the
  implied question, then expand. An analysis of ~1.2M AI answers found **~44% of citations
  come from the first 30% of the page** (Search Engine Land / Kevin Indig, 2026), so lead with
  the answer, never bury it.
- **"What is X" definitions.** Every core concept gets a clean one-sentence definition a
  machine can lift, as the opening line of each definitional H2.
- **Question-shaped headings.** Phrase some H2/H3s as the actual question a searcher types
  ("How do you measure X?"), then answer immediately below.
- **Snippet-ready formats.** Use the format the SERP feature rewards: numbered steps for
  "how to", a comparison table for "vs", a short definition for "what is", a bulleted list
  for "types of".
- **FAQ targeting real PAA.** Research the actual People Also Ask set (Rule 11); each FAQ
  answers a distinct question in 2-4 self-contained sentences.
- **Query fan-out coverage.** AI engines expand one query into many sub-questions and
  synthesize across them. Map the sub-questions (definition, how-to, cost, comparison,
  examples, mistakes, timeline) and make sure a passage answers each.

## 3. GEO - Generative Engine Optimization (get cited by LLMs)
Goal: be a source the model quotes. Research on generative engines is consistent on what
lifts citation share:
- **Cite statistics.** Adding relevant statistics increased source visibility by up to **40%**
  in the controlled Princeton GEO study (Aggarwal et al., arXiv 2311.09735, KDD 2024; the 40%
  is a relative maximum, not an average). Every claim that can carry a number should.
- **Add citations and quotations.** Direct quotes and cited sources boosted visibility by up
  to **41%** in the same study. Attribute to named authorities (Gallup, McKinsey, Harvard) with the year.
- **Original, verifiable data.** A unique stat, worked example, framework, or table that
  exists nowhere else is the single strongest citation magnet. Give the numbers, the formula,
  the result.
- **Authoritative, specific language.** Concrete, confident, jargon-light prose is quoted
  more than hedged, vague prose (also Rule 10). Say the thing.
- **Self-contained passages (chunk-level writing).** LLMs retrieve isolated chunks, not whole
  pages, and answer without the surrounding context. Each paragraph must stand alone: no
  "as mentioned above", no pronoun that needs the previous sentence, define the term in the
  passage that uses it. Do not artificially fragment content; write naturally but completely.
- **Comparison and data tables.** Tables are disproportionately extracted; convert any
  "X vs Y" or multi-attribute comparison into a `.table-scroll` table.

## 4. LLM / AI-search visibility (the technical + entity layer)
- **Entity clarity.** Name entities explicitly and consistently (full product, company,
  framework, and role names, not pronouns or abbreviations on first use). Link core entities
  to their canonical pages so the model can disambiguate. This is a per-page practice; the
  site-wide version is the brand's own entity clarity - a Wikidata/Wikipedia entry and
  consistent `sameAs` links from the `Organization` schema across pages help a model resolve
  "who is this brand" independently of any one page's content (site-level project, not a
  per-page edit; flag it for the wider content/brand strategy, same as off-site authority below).
- **Author + E-E-A-T signals.** Authored content with verifiable credentials is cited more
  than anonymous content; 2026 analyses find `Person`/author schema appears far more often on
  AI-cited pages than across the web at large. Ensure a real author/reviewer with credentials
  is present (Article/Author schema, "reviewed by"). First-hand experience, examples, and case
  studies are the March-2025-core and helpful-content signals.
- **Structured data.** AI-cited pages carry structured data at well above the web-average rate
  in 2026 analyses. Add it, but note the ranking driver is content quality and structure, not
  the markup type. Use the schema set in section 5.
- **Heading hierarchy as a parse map.** The H1>H2>H3 tree is how a model finds the passage.
  Keep it strict and descriptive so each answer sits under a heading that names its question.
- **Freshness cadence.** A large share of AI-cited sources rotate month to month; a current
  "last updated" date and 2024-2026 stats keep a page in the citable set.
- **Off-site authority (flag, mostly beyond one page edit).** 2026 earned-media analyses
  report that the large majority (~85% in some studies) of AI citations come from third-party
  / earned media, not the brand's own site. This is the single strongest GEO lever this
  pipeline has NO tooling for - everything here is on-page/content-only. A single page cannot
  fix this, but note where the topic needs external corroboration and raise it for the wider
  content strategy. Closing the gap needs something outside this repo: a mentions-monitoring
  service (Google Alerts, a brand-mentions API, or a PR/comms team's existing tool) tracking
  where the brand is already being cited, so that signal can feed back into which topics/pages
  to prioritize - not a script this codebase can run for you.
- **llms.txt (site-level, not per-page).** An emerging `/llms.txt` convention exists; Google
  has said it does not use it and schema type does not predict citation volume. Do not block
  a page on it. Note it once for the site owner and move on.
- **pricing.md (site-level, not per-page).** AI agents increasingly evaluate and recommend
  services on a buyer's behalf; an agent skips a vendor whose pricing sits behind a
  JS-rendered page or a "contact sales" wall it can't parse. `optimizer/pricing.py` generates
  a `/pricing.md` skeleton (name + URL) from the money pages in `audit.json` - fill in real,
  current price/limits/features by hand and publish it at the site root. Same caveat as
  llms.txt: no confirmed Google ranking effect, but cheap and it helps the agent-driven
  buying-journey case specifically.
- **OKF ("Open Knowledge Format", site-level, not per-page) - deliberately NOT built.** Google
  introduced OKF in 2026 as a markdown-bundle spec for agent-readable site content, but it has
  no confirmed AI-search ranking signal today and is aimed primarily at data-catalog metadata,
  not blog content - treat it like early schema.org registration, not a citation lever. This
  project's inventory is also still thin (see the small-inventory warnings elsewhere), so a
  cross-linked multi-page bundle isn't a good fit yet. Revisit once OKF has a confirmed signal
  or a clearer content-marketing use case, rather than building it speculatively now.

## 5. Schema markup set (per page)
Include as JSON-LD (Google-preferred) alongside the visible content:
- **Article / BlogPosting** - headline, author, datePublished, dateModified, publisher, image.
- **FAQPage** - the FAQ block. HTML items must match the JSON-LD entries exactly (Rule 11).
- **BreadcrumbList** - the category path.
- **HowTo** - only when the page genuinely contains a step sequence.
- **Author / Person** with `sameAs` - links the author entity to LinkedIn or a profile.
The template ships the FAQPage JSON-LD; add the others in the build when applicable.

## 6. AI crawler access (training vs retrieval bots)
This is per-site, but confirm it before blaming content. The AI companies run two separate
crawler classes and confusing them either hides you from AI search or gives content away:
- **Retrieval / search bots build the answers and citations:** `OAI-SearchBot`, `ChatGPT-User`,
  `PerplexityBot`, `Claude-Web`. These must be allowed, or the page cannot be cited.
- **Training bots collect data for future models:** `GPTBot`, `Google-Extended`, `CCBot`,
  `anthropic-ai`. Blocking these has no effect on whether you are cited today; allowing or
  blocking them is a separate call about model training and crawl cost.
Also confirm no blanket "Block AI Bots" toggle (e.g. Cloudflare) is catching the retrieval bots.

## 7. Per-engine differences + AI Overview monitoring
Citation overlap between engines is small, so ranking on one does not transfer to another.
- **Google AI Overviews / AI Mode:** high authority + freshness; AI Mode leans on YouTube and
  community sources. **Check the live AI Overview for each target keyword**: who is cited, in
  what format, and the angle that would earn a citation. Plan an answer-first lead, since about
  44% of AI citations come from the first 30% of the page.
- **ChatGPT:** high-DR publishers, readable content, crawler access.
- **Perplexity:** citation-first, real time; strongly tracks Google's top 10.
- **Gemini:** inherits Google ranking signals; classic SEO is the prerequisite.
- **Claude:** verified, multi-source, balanced content; correlates with Google rank.
Track presence over a set of real buyer prompts, not a single query, since AI output is
probabilistic.

## 8. Strategy, format, off-page, and measurement (AEO course concepts)
The lessons below come from the Ahrefs AEO course. Some are per-page (apply in the build),
some are strategy or off-page (flag for the wider plan, do not block the page edit).

- **BID keyword vetting (per page, Step 3).** Vet the target term on three axes before
  committing: **B**usiness potential (does ranking drive signups/revenue?), **I**ntent (does
  the live SERP format match the page type?), **D**ifficulty (can this domain realistically
  outrank the incumbents?). A weak B or an impossible D is a reason to pivot or de-prioritize.
- **The AI-click trap + tool-keyword exception.** Informational question queries trigger an AI
  Overview that answers without a click a large share of the time, so pure-informational pages
  lose CTR even at rank 1. **Interactive tool intent (calculators, checkers, generators,
  templates, matrices)** is immune, because the user needs the utility. Favor a tool/interactive
  angle or a bottom-of-funnel comparison where the keyword allows (see Checklist #32).
- **Format dominance.** Listicles, product comparisons, and reviews make up roughly **44% of
  cited pages** across ChatGPT and Google AI Overviews. When intent allows, structure the page
  as a numbered list, a comparison, or a review rather than an essay, and put the comparison in
  a `.table-scroll` table.
- **Brand-labeled frameworks (reconciled with Rule 5).** Naming an original framework, metric,
  or method after the brand makes it a citable, ownable entity. This is the best way to "spend"
  the single allowed body brand mention (Rule 5): a brand-labeled proprietary framework counts
  as that one mention, and is preferable to a generic brand drop in the conclusion. Do not add a
  second brand mention for it.
- **3 tiers of brand mentions (off-page, flag).** Citations follow earned mentions: Tier 1
  third-party editorial (high-authority listicles, comparisons, reviews), Tier 2 community
  (Reddit, Quora), Tier 3 owned secondary media (YouTube, podcasts, LinkedIn). A page edit
  cannot create these; note where the topic needs third-party corroboration for the strategy.
- **YouTube as a citation lever (off-page, flag).** Video mentions correlate strongly with
  ChatGPT visibility and appear in AI Overviews / AI Mode. Where a topic warrants it, flag a
  companion video (spoken target keywords, keyworded title + first two description lines +
  chapters) for the content team.
- **Extra technical AEO checks (beyond section 6).** Confirm the live page is server-side
  rendered so retrieval bots that do not run JavaScript still see the content; keep Core Web
  Vitals fast enough that real-time RAG retrieval does not time out. `linkcheck.py` verifies the
  page's own internal links resolve; separately, audit **inbound** AI-referrer 404s (assistants
  hallucinate URLs far more often than Google) and 301-redirect them to live pages.

---

## Bake-in checklist (run during the build step)
- [ ] Opening paragraph leads with a 40-60 word answer-first definition of the primary keyword.
- [ ] Every key H2 opens with a direct, extractable answer before it expands.
- [ ] At least some H2/H3s are phrased as the real question searched.
- [ ] Query fan-out mapped: definition, how-to, cost, comparison, examples, mistakes covered by a passage each.
- [ ] Every factual claim that can carry a number does, with a named source and year (GEO stat lift).
- [ ] At least one quote or cited study from a recognized authority (GEO citation lift).
- [ ] At least one piece of original value: worked example, unique table, or framework.
- [ ] Every paragraph is self-contained (no back-references, no orphan pronouns, term defined in place).
- [ ] Comparisons rendered as `.table-scroll` tables, not prose.
- [ ] Entities named in full and consistently; core entities internally linked.
- [ ] Author / reviewer + credentials present; Article + Author schema planned.
- [ ] Strict H1>H2>H3 hierarchy, no skipped levels.
- [ ] FAQ targets real PAA, new angles only, HTML == JSON-LD (Rule 11).
- [ ] Current "last updated" date; all stats 2024-2026 (Rule 12).
- [ ] JSON-LD: Article + FAQPage + BreadcrumbList (+ HowTo/Author when applicable).
- [ ] Off-site authority gaps noted for the wider strategy (do not block the page).

## Sources

**Read before citing any of these in published copy (Rule 12).** GEO is a fast-moving,
study-heavy field; the peer-reviewed figure below is solid, the rest are third-party 2026
analyses whose exact numbers vary by methodology and sample. Treat them as directional, and
re-verify the specific number against the linked primary source before putting it on a page.

Primary / peer-reviewed:
- **Princeton GEO study** - Aggarwal et al., "GEO: Generative Engine Optimization", arXiv
  2311.09735 (KDD 2024). Statistics and citations/quotations each lifted source visibility by
  up to ~40-41% (a relative maximum on the Position-Adjusted Word Count metric, not an average).
  https://arxiv.org/abs/2311.09735

Third-party 2026 analyses (directional; re-verify before quoting a number):
- **~44% of AI citations come from the first 30% of content** - analysis of ~1.2M AI answers /
  18,012 citations (Kevin Indig; reported by Search Engine Land, 2026).
  https://searchengineland.com/chatgpt-citations-content-study-469483
- **Clean heading hierarchy correlates with more citations** - e.g. pages with a sequential
  H1>H2>H3 structure cited materially more often (Blck Alpaca, 2026).
  https://blckalpaca.at/en/knowledge-base/seo-geo/on-page-seo/heading-hierarchy-28x-more-ai-citations-with-correct-structure
- **Author/`Person` schema over-represented on AI-cited pages; authored content out-cites
  anonymous** - 2026 citation-factor analyses (e.g. The Digital Bloom AI Visibility Report).
  https://thedigitalbloom.com/learn/2025-ai-citation-llm-visibility-report/
- **Majority of AI citations trace to third-party / earned media** (~85% in some studies) -
  2026 earned-media analyses. https://authoritytech.io/curated/jaxon-parrott-earned-media-framework-ai-search-brand-citations-2026
- General GEO/AEO/SEO overviews for context: Search Engine Land's GEO coverage; Writer.com,
  "GEO, AEO, and SEO in 2026".
