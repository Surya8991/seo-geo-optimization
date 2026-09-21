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
- Clean H1 > H2 > H3 hierarchy, one H1, no skipped levels. Strict heading hierarchy strongly
  correlates with getting cited by AI (Seer Interactive / BrightEdge, 2026).
- Internal links to the topic cluster + money page; external links to authoritative sources.
- Freshness: current-year references, updated date visible, stats from 2024-2026.
- Mobile, fast, indexable, tables in `.table-scroll`.

## 2. AEO - Answer Engine Optimization (win PAA, snippets, AI Overviews)
Goal: be the passage Google lifts into a snippet or AI Overview.
- **Answer-first blocks.** Open each key section with a direct 40-60 word answer to the
  implied question, then expand. **44% of LLM citations come from the first 30% of the page**
  (SparkToro, 2026), so lead with the answer, never bury it.
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
- **Cite statistics.** Adding relevant statistics increases AI visibility by roughly **40%**
  (GEO research, Aggarwal et al.). Every claim that can carry a number should.
- **Add citations and quotations.** Direct quotes and cited sources boost visibility by up
  to **41%**. Attribute to named authorities (Gallup, McKinsey, Harvard) with the year.
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
  to their canonical pages so the model can disambiguate.
- **Author + E-E-A-T signals.** Only about 4% of AI-cited content has an attributed author,
  and authored content earns far more citations. Ensure a real author/reviewer with
  credentials is present (Article/Author schema, "reviewed by"). First-hand experience,
  examples, and case studies are the March-2025-core and helpful-content signals.
- **Structured data.** About **68% of AI-cited pages carry structured data (double the web
  average)**. Add it, but note the ranking driver is content quality and structure, not the
  markup type. Use the schema set in section 5.
- **Heading hierarchy as a parse map.** The H1>H2>H3 tree is how a model finds the passage.
  Keep it strict and descriptive so each answer sits under a heading that names its question.
- **Freshness cadence.** About 60% of AI-cited sources rotate month to month; a current
  "last updated" date and 2024-2026 stats keep a page in the citable set.
- **Off-site authority (flag, mostly beyond one page edit).** Roughly **85% of AI citations
  come from third-party / earned media**, not the brand's own site. A single page cannot fix
  this, but note where the topic needs external corroboration and raise it for the wider
  content strategy.
- **llms.txt (site-level, not per-page).** An emerging `/llms.txt` convention exists; Google
  has said it does not use it and schema type does not predict citation volume. Do not block
  a page on it. Note it once for the site owner and move on.

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

## Sources (2026)
- SparkToro, 2026 - 44% of LLM citations come from the first 30% of page content.
- GEO research (Aggarwal et al., "Generative Engine Optimization") - statistics +~40%, citations/quotations +~41%.
- Seer Interactive / BrightEdge, 2026 - strict heading hierarchy correlates with AI citation.
- Presenc AI, 2026 - named/authored content earns ~60% more AI citations than anonymous.
- Muck Rack, 2026 - ~85% of non-paid AI citations come from earned media / third-party pages.
- Search Engine Land, "Generative engine optimization (GEO)", Feb 2026.
- Writer.com, "GEO, AEO, and SEO in 2026", Jul 2026.
