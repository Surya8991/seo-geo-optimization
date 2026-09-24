"""Tests for the pure helpers in optimizer/qa_check.py (config-independent bits)."""
import re

import qa_check


class TestDomainPrefix:
    def test_www_prefix_stripped(self):
        assert re.sub(r"^www\.", "", "www.example.com") == "example.com"

    def test_w_leading_domain_not_mangled(self):
        # The old lstrip("www.") turned these into 'ine.com' / 'ashingtonpost.com'.
        assert re.sub(r"^www\.", "", "wine.com") == "wine.com"
        assert re.sub(r"^www\.", "", "washingtonpost.com") == "washingtonpost.com"
        assert re.sub(r"^www\.", "", "weforum.org") == "weforum.org"


class TestBritishSpellings:
    def test_flags_genuine_british(self):
        found = qa_check.find_british_spellings(
            "The colour and behaviour of the organisation under analysis."
        )
        assert "colour" in found
        assert "behaviour" in found
        assert any(w.startswith("organis") for w in found)

    def test_allows_american_ise_words(self):
        # These are correct American English and must NOT be flagged.
        text = ("We advertise and improvise; managers supervise, comprise the board, "
                "exercise judgment, and otherwise revise the enterprise franchise.")
        assert qa_check.find_british_spellings(text) == []

    def test_allows_ise_inflections(self):
        text = "They advertised, supervised, and improvised while advertising the course."
        assert qa_check.find_british_spellings(text) == []

    def test_flags_customise_but_not_customize(self):
        assert "customise" in qa_check.find_british_spellings("You can customise the plan.")
        assert qa_check.find_british_spellings("You can customize the plan.") == []


class TestLinkBand:
    def test_bands(self):
        assert qa_check.link_band(1500) == (4, 3)
        assert qa_check.link_band(3000) == (7, 4)
        assert qa_check.link_band(5000) == (9, 5)
        assert qa_check.link_band(9000) == (10, 6)


class TestFlesch:
    def test_simple_text_scores_higher_than_complex(self):
        simple = "The cat sat on the mat. The dog ran. We went home."
        complex_ = ("Notwithstanding the aforementioned considerations, the "
                    "multidimensional ramifications necessitate comprehensive evaluation.")
        assert qa_check.flesch_reading_ease(simple) > qa_check.flesch_reading_ease(complex_)

    def test_empty_returns_none(self):
        assert qa_check.flesch_reading_ease("") is None


class TestStripTags:
    def test_removes_scripts_styles_tags(self):
        html = "<style>x{}</style><p>Hello <b>world</b></p><script>var a=1;</script>"
        out = qa_check.strip_tags(html)
        assert "Hello" in out and "world" in out
        assert "var a" not in out and "x{}" not in out


class TestJsonLd:
    VALID = ('<script type="application/ld+json">'
             '{"@context":"https://schema.org","@type":"FAQPage"}</script>')
    BROKEN = ('<script type="application/ld+json">'
              '{"@type":"FAQPage",}</script>')  # trailing comma -> invalid JSON

    def test_extract_counts_blocks(self):
        assert len(qa_check.extract_jsonld_blocks(self.VALID + self.BROKEN)) == 2

    def test_valid_block_has_no_errors(self):
        assert qa_check.invalid_jsonld_blocks(self.VALID) == []

    def test_broken_block_is_reported(self):
        bad = qa_check.invalid_jsonld_blocks(self.VALID + self.BROKEN)
        assert len(bad) == 1
        assert bad[0][0] == 2  # the second block is the broken one


class TestHeadingHierarchy:
    def test_levels_extracted_in_order(self):
        html = "<h1>a</h1><h2>b</h2><h3>c</h3><h2>d</h2>"
        assert qa_check.heading_levels(html) == [1, 2, 3, 2]

    def test_valid_hierarchy_has_no_errors(self):
        assert qa_check.heading_hierarchy_errors([1, 2, 3, 2, 2]) == []

    def test_missing_h1_flagged(self):
        errs = qa_check.heading_hierarchy_errors([2, 3])
        assert any("H1" in e for e in errs)

    def test_two_h1_flagged(self):
        errs = qa_check.heading_hierarchy_errors([1, 2, 1])
        assert any("found 2" in e for e in errs)

    def test_skipped_level_flagged(self):
        errs = qa_check.heading_hierarchy_errors([1, 2, 4])
        assert any("skipped" in e for e in errs)

    def test_comments_ignored(self):
        html = "<!-- <h3>x</h3> --><h1>a</h1><h2>b</h2>"
        assert qa_check.heading_levels(html) == [1, 2]


class TestImageIssues:
    def test_missing_alt_flagged(self):
        assert qa_check.image_issues('<img src="/a/good-name.jpg">')  # no alt
        assert qa_check.image_issues('<img src="/a/x.jpg" alt="">')   # empty alt

    def test_good_image_passes(self):
        assert qa_check.image_issues('<img src="/img/scrum-board-example.jpg" alt="A scrum board">') == []

    def test_generic_filename_flagged(self):
        issues = qa_check.image_issues('<img src="/up/IMG_1234.jpg" alt="A chart">')
        assert any("generic" in i for i in issues)


class TestKeywordPlacement:
    HTML = ("<h1>Product Certification Guide</h1>"
            "<p>Product certification is a formal process.</p>"
            "<h2>Conclusion</h2><p>Choose product certification wisely.</p>")
    TEXT = ("Product certification is a formal process. Choose product certification wisely.")

    def test_reports_placement(self):
        kp = qa_check.keyword_placement(self.HTML, self.TEXT, "Product Certification Guide",
                                        "Product Certification Guide 2026", "product certification")
        assert kp["in_h1"] is True
        assert kp["in_title"] is True
        assert kp["in_first_100"] is True
        assert kp["in_conclusion"] is True
        assert kp["count"] == 2  # counted in reader text (H1 is separate)

    def test_conclusion_none_when_absent(self):
        kp = qa_check.keyword_placement("<h1>X</h1><p>x product certification</p>",
                                        "x product certification", "X", "X", "product certification")
        assert kp["in_conclusion"] is None


class TestStaleStats:
    def test_flags_pre2024_year_near_stat(self):
        assert qa_check.stale_stat_years("A 2021 study found 45% growth.") == [2021]

    def test_ignores_historical_year_without_stat_signal(self):
        assert qa_check.stale_stat_years("The company was founded in 1998 in Boston.") == []

    def test_current_years_not_flagged(self):
        assert qa_check.stale_stat_years("A 2026 survey reported 60% adoption.") == []

    def test_multiple_flagged_sorted_unique(self):
        assert qa_check.stale_stat_years("2019 data and 2021 data, plus 2019 report.") == [2019, 2021]


class TestAcronymReuse:
    def test_definition_pattern_detected(self):
        assert qa_check.acronym_definitions("Subject matter experts (SMEs) keep it real.") == {"SMEs"}

    def test_no_definition_pattern_is_empty(self):
        assert qa_check.acronym_definitions("No parenthetical acronym here at all.") == set()

    def test_reuse_in_later_section_without_redefinition_is_flagged(self):
        html = ("<h3>One</h3><p>Subject matter experts (SMEs) keep content accurate.</p>"
                "<h3>Two</h3><p>Bring in SMEs early for the best results.</p>")
        flagged = qa_check.undefined_acronym_reuse(html)
        assert flagged == [("Two", "SMEs")]

    def test_redefined_locally_is_not_flagged(self):
        html = ("<h3>One</h3><p>Subject matter experts (SMEs) keep content accurate.</p>"
                "<h3>Two</h3><p>Subject matter experts (SMEs) again, redefined here.</p>")
        assert qa_check.undefined_acronym_reuse(html) == []

    def test_acronym_never_defined_via_parens_is_not_flagged(self):
        # ROI is used but never defined via the "(ACRONYM)" pattern anywhere -
        # deliberately not flagged, to avoid noise on common business acronyms.
        html = "<h3>One</h3><p>Track training ROI carefully.</p><h3>Two</h3><p>ROI matters.</p>"
        assert qa_check.undefined_acronym_reuse(html) == []

    def test_same_section_reuse_of_its_own_definition_not_flagged(self):
        html = "<h3>One</h3><p>Subject matter experts (SMEs) help. SMEs add context too.</p>"
        assert qa_check.undefined_acronym_reuse(html) == []


class TestRepeatedStats:
    def test_flags_value_repeated_three_plus_times(self):
        text = "40% of skills fade. Later, 40% of roles change. Again, 40% is cited."
        assert qa_check.repeated_percent_stats(text) == {"40%": 3}

    def test_two_occurrences_not_flagged(self):
        text = "40% here. And 40% there."
        assert qa_check.repeated_percent_stats(text) == {}

    def test_distinct_values_not_conflated(self):
        text = "71% adoption. 195% growth. 71% again. 195% again. 71% a third time."
        result = qa_check.repeated_percent_stats(text)
        assert result == {"71%": 3}

    def test_no_percent_signals_returns_empty(self):
        assert qa_check.repeated_percent_stats("No stats mentioned here at all.") == {}


class TestFreshness:
    def test_jsonld_datemodified_counts(self):
        html = '<script type="application/ld+json">{"dateModified":"2026-09-01"}</script>'
        assert qa_check.has_freshness_signal(html, "") is True

    def test_visible_updated_line_counts(self):
        assert qa_check.has_freshness_signal("", "Last updated September 2026.") is True

    def test_old_date_does_not_count(self):
        assert qa_check.has_freshness_signal('{"dateModified":"2021-01-01"}', "updated in 2021") is False

    def test_no_signal(self):
        assert qa_check.has_freshness_signal("<p>no dates here</p>", "no dates here") is False


class TestSchemaCompleteness:
    ARTICLE_OK = ('<script type="application/ld+json">{"@type":"Article",'
                  '"headline":"x","author":"y","datePublished":"2026-01-01",'
                  '"dateModified":"2026-09-01"}</script>')

    def test_complete_article_has_no_missing(self):
        missing, absent = qa_check.schema_completeness(self.ARTICLE_OK)
        assert missing == []
        assert "Article/BlogPosting" not in absent

    def test_incomplete_article_reports_missing(self):
        html = '<script type="application/ld+json">{"@type":"Article","headline":"x"}</script>'
        missing, _ = qa_check.schema_completeness(html)
        assert "author" in missing and "dateModified" in missing

    def test_absent_types_listed_when_no_article(self):
        _, absent = qa_check.schema_completeness('<script type="application/ld+json">{"@type":"FAQPage"}</script>')
        assert "Article/BlogPosting" in absent and "BreadcrumbList" in absent

    def test_complete_howto_has_no_missing(self):
        html = ('<script type="application/ld+json">{"@type":"HowTo","name":"Guide",'
                '"step":[{"@type":"HowToStep","name":"Step 1","text":"Do X"},'
                '{"@type":"HowToStep","name":"Step 2","text":"Do Y"}]}</script>')
        missing, _ = qa_check.schema_completeness(html)
        assert missing == []

    def test_howto_missing_name_and_empty_steps_flagged(self):
        html = '<script type="application/ld+json">{"@type":"HowTo","step":[]}</script>'
        missing, _ = qa_check.schema_completeness(html)
        assert "HowTo.name" in missing
        assert any("no steps" in m for m in missing)

    def test_howto_step_missing_text_flagged(self):
        html = ('<script type="application/ld+json">{"@type":"HowTo","name":"Guide",'
                '"step":[{"@type":"HowToStep","name":"Step 1"}]}</script>')
        missing, _ = qa_check.schema_completeness(html)
        assert any("step[1]" in m for m in missing)


class TestAuthorCredentialGap:
    def test_string_author_not_flagged(self):
        html = ('<script type="application/ld+json">{"@type":"Article","headline":"x",'
                '"author":"y","datePublished":"2026-01-01","dateModified":"2026-09-01"}</script>')
        assert qa_check.author_credential_gap(html) is False

    def test_person_author_without_credentials_flagged(self):
        html = ('<script type="application/ld+json">{"@type":"Article","headline":"x",'
                '"author":{"@type":"Person","name":"Jane Doe"},'
                '"datePublished":"2026-01-01","dateModified":"2026-09-01"}</script>')
        assert qa_check.author_credential_gap(html) is True

    def test_person_author_with_jobtitle_not_flagged(self):
        html = ('<script type="application/ld+json">{"@type":"Article","headline":"x",'
                '"author":{"@type":"Person","name":"Jane Doe","jobTitle":"L&D Lead"},'
                '"datePublished":"2026-01-01","dateModified":"2026-09-01"}</script>')
        assert qa_check.author_credential_gap(html) is False

    def test_person_author_with_description_not_flagged(self):
        html = ('<script type="application/ld+json">{"@type":"Article","headline":"x",'
                '"author":{"@type":"Person","name":"Jane Doe","description":"L&D writer"},'
                '"datePublished":"2026-01-01","dateModified":"2026-09-01"}</script>')
        assert qa_check.author_credential_gap(html) is False

    def test_no_article_returns_false(self):
        assert qa_check.author_credential_gap('<script type="application/ld+json">{"@type":"FAQPage"}</script>') is False
