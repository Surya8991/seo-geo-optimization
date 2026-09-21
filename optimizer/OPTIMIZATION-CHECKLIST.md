# Page Optimization Checklist - 50 Points

Wherever this says "the brand" or `example.com`, the real values come from `config.json`.

**Scope note (publish / CMS / site layer).** A few points cannot be satisfied inside the
self-contained HTML fragment this pipeline outputs; they live at the CMS, template, or
site-wide layer. Do not score them PASS from the fragment. Instead, note them in the review
copy as "verify at publish": **#26 Image SEO** (real image files, WebP, compression; note that
`qa_check.py` DOES auto-check alt text and generic filenames), **#29 Internal links inbound**
(links FROM other pages, a site-wide task; `interlink.py` finds the sources), **#37 Core Web
Vitals**, **#38 Mobile** (beyond `.table-scroll`), **#39 Indexing/canonical/sitemap**, and
**#40 Page Speed**. The fragment can only prepare for these (alt text, `.table-scroll`,
descriptive filenames in `src`); the measurement happens on the live page.

Now auto-checked by `qa_check.py`: **#25 Heading structure** (one H1, no skipped levels),
**#26** image alt text/filenames, **#28** JSON-LD validity, and **#5/#9** primary-keyword
placement (with `--keyword`). **#23/#24** meta uniqueness across pages: run `meta_audit.py`.

## A. SEARCH VISIBILITY (4 points)
1. **AI Overview Optimization (AIO)** - Clear 40-60 word definitions at top of sections, "What is X" format, structured data
2. **Answer Engine Optimization (AEO)** - Conversational Q&A format, FAQ sections, answer PAA questions in body
3. **Generative Engine Optimization (GEO)** - Citations with sources, stats with links, expert quotes, unique verifiable data
4. **AI Platform Crawlability** - Crawlable by AI bots, structured data present, brand mentions natural

## B. KEYWORD STRATEGY (6 points)
5. **Primary Keyword** - One main keyword in title, H1, first 100 words, URL, meta description
6. **Secondary Keywords** - 3-5 related keywords naturally in H2s and body
7. **Low-Hanging Keywords from GSC** - Queries getting impressions but NOT in content -> add them
8. **Long-Tail Question Keywords** - From PAA, competitors, forums -> add as H2/H3 sections
9. **Keyword Placement Audit** - In title, H1, first para, 2+ H2s, image alt, meta, URL. No stuffing
10. **NLP/Entity Optimization** - Related entities Google expects for this topic

## C. SEARCH INTENT + COMPETITORS (4 points)
11. **Search Intent Match** - Does format match top 3 SERP results?
12. **Competitor Content Gap** - Sections top 3-5 cover that we don't
13. **Competitor Article Structure** - Heading structure, format, word count, visuals of top rankers
14. **SERP Feature + AI Overview Targeting** - Which feature to target (snippet, PAA, video, image pack) AND check the live AI Overview for the keyword: who is cited, what format, and the angle that would earn a citation

## D. CONTENT QUALITY + E-E-A-T (8 points)
15. **Content Depth + Uniqueness** - What we add that competitors don't
16. **E-E-A-T: Experience** - First-hand experience, case studies, practical examples
17. **E-E-A-T: Expertise** - Author bio, credentials, "reviewed by" tag
18. **E-E-A-T: Authority** - Links to research, .gov, .edu, industry reports
19. **E-E-A-T: Trust** - Social proof, testimonials, transparent author info
20. **Readability** - Flesch 60+, short paras, simple words, active voice
21. **Outdated Content + Stats** - Replace stats older than 2 years, add 2025-2026 data
22. **FAQ Section** - 5-8 FAQs from PAA, competitors, Quora/Reddit, GSC queries. FAQ schema

## E. ON-PAGE SEO (6 points)
23. **Title Tag** - Primary keyword + value + under 60 chars. Numbers, year, brackets
24. **Meta Description** - 140-160 chars (target ~150-155), keyword, reason to click, benefit statement
25. **Heading Structure** - H1 with keyword, H2s for subtopics/questions, H3s supporting. Logical
26. **Image SEO** - Descriptive filenames, alt text with keywords, compressed/WebP, custom images
27. **URL Structure** - Short, keyword-rich, no unnecessary words, lowercase, hyphens
28. **Schema Markup** - Article, FAQ, HowTo, BreadcrumbList, Author schema

## F. LINKING STRATEGY (3 points)
29. **Internal Links - Inbound** - Min 5 internal links FROM other pages TO this page (use `optimizer/interlink.py <slug>` to find candidate source pages)
30. **Internal Links - Outbound** - 3-5 links FROM this page to money/course pages, category pages, related content. Each must be **contextually relevant with descriptive anchor text naming the destination topic** (no CTA anchors). **No country/city page links** (e.g., example.com/australia/, example.com/india/). Only link to generic money/course pages (example.com/<slug>/), category pages, or other content pages.
31. **External Links - Outbound** - 3-5 links to high-authority external sources

## G. ENGAGEMENT + CONVERSION (5 points)
32. **Interactive Elements** - Calculators, quizzes, assessments, accordions, comparison tools
33. **Lead Magnets** - Downloadable checklist, template, PDF, toolkit related to topic
34. **Visual Content** - Custom diagrams, charts, comparison tables, process flows, videos
35. **Table of Contents** - Clickable TOC for posts >1500 words
36. **CTA Optimization** - Contextual CTAs to relevant money/course pages and services

## H. TECHNICAL + PAGE EXPERIENCE (4 points)
37. **Core Web Vitals** - LCP <2.5s, CLS <0.1, INP <200ms
38. **Mobile Experience** - Tables scroll, images resize, no overflow
39. **Indexing Check** - No noindex, correct canonical, in sitemap
40. **Page Speed** - Under 3 seconds on mobile

## I. GOOGLE CORE UPDATE ALIGNMENT (5 points)
41. **Helpful Content (HCU)** - Written for humans, every section adds value, no filler
42. **Site Quality** - Remove/improve thin content that drags site quality
43. **AI Content Policy** - Human review, unique insights, no generic AI filler
44. **Link Spam Update** - Only natural relevant links
45. **March 2025 Core** - Real experience signal, case studies, first-hand insights

## J. STRATEGIC + STRUCTURAL (5 points)
46. **Topic Cluster / Topical Authority** - Page belongs to a cluster with pillar page
47. **Content Pruning / Consolidation** - No cannibalization with other pages or blogs; record new sections in the content ledger so future pages do not repeat them
48. **Regional/Local Context** - Local stats/context for location-specific pages
49. **Content Decay Monitoring** - Monthly traffic comparison alert
50. **Publish Date + Freshness** - Updated modified date, "Last updated" visible
