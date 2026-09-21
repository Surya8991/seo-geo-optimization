"""Integration tests for qa_check.run() against generated HTML fixtures.

These run with the default config (brand "Your Brand", domain example.com,
no country slugs), which is what config_loader falls back to in a fresh checkout.
"""
import qa_check


def _meta_description(target_len=150):
    base = ("Product certification explained for 2026: what it is, how the process "
            "works, what it costs, and how long it takes to earn one in practice today")
    while len(base) < target_len:
        base += " now"
    return base[:target_len]


def _passing_optimize_html():
    desc = _meta_description(150)
    aio = ("Product certification is a formal process that verifies a product meets "
           "defined standards, and this opening paragraph is deliberately written to "
           "exceed thirty words so it satisfies the answer first opening check in the "
           "quality gate without any trouble at all.")
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>Test</title></head>
<body>
<div class="wrap">
<div class="note"><strong>Review copy.</strong> What changed and publish notes.</div>
<div class="note" style="background:#eef4ff">
<strong>Publishing fields</strong><br>
<strong>Meta title (32/60):</strong> Product Certification Guide 2026<br>
<strong>Meta description ({len(desc)}/155):</strong> {desc}<br>
<strong>H1:</strong> Product Certification
</div>
<h1>Product Certification Guide</h1>
<p>{aio}</p>
<p>This context sentence explains why the topic matters. A second sentence covers who benefits.</p>
<h2>What is product certification</h2>
<p>A direct answer opens the section. Readers can review the
<a href="https://www.example.com/product-a/">Product A certification course</a> for the full syllabus.</p>
<div class="new-block"><span class="new-tag">New</span>
<h3>Certification costs in 2026</h3>
<p>A 2026 industry survey put the median cost higher than the prior year, reported by
<a href="https://www.gallup.com/report-2026" rel="nofollow" target="_blank">Gallup</a>.</p>
</div>
<h2>Conclusion</h2>
<p>Strong product certification content rewards a methodical, well documented approach.</p>
<div class="note" style="background:#eef7f0">
<strong>Changes summary</strong>
<div class="table-scroll"><table class="changes-summary">
<thead><tr><th>Area</th><th>Action</th><th>Detail</th></tr></thead>
<tbody><tr><td>Costs</td><td>Added</td><td>2026 stat with source</td></tr></tbody>
</table></div>
</div>
<div class="new-block"><span class="new-tag">FAQ</span>
<h2>Frequently Asked Questions</h2>
<section class="faq" itemscope itemtype="https://schema.org/FAQPage">
<div class="faq-item active" itemscope itemprop="mainEntity" itemtype="https://schema.org/Question">
<div class="faq-question"><p itemprop="name">How long does certification take?</p><span class="toggle-icon"></span></div>
<div class="faq-answer" itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer"><p itemprop="text">Most candidates finish within a few months.</p></div>
</div>
</section>
</div>
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{{"@type":"Question","name":"How long does certification take?","acceptedAnswer":{{"@type":"Answer","text":"Most candidates finish within a few months."}}}}]}}
</script>
</div>
</body></html>"""


def _passing_new_html():
    # New mode: no changes-summary, no removal markers.
    desc = _meta_description(150)
    aio = ("Training ROI measures the financial return of a learning program, and this "
           "opening paragraph is written to exceed thirty words so that the answer first "
           "opening check in the quality gate passes cleanly for a brand new page here.")
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>New</title></head>
<body>
<div class="wrap">
<div class="note" style="background:#eef4ff">
<strong>Publishing fields</strong><br>
<strong>Meta title (28/60):</strong> How to Measure Training ROI
<br><strong>Meta description ({len(desc)}/155):</strong> {desc}<br>
<strong>H1:</strong> How to Measure Training ROI
</div>
<h1>How to Measure Training ROI</h1>
<p>{aio}</p>
<p>This introduction frames the calculation. A second sentence sets up the method below.</p>
<h2>The training ROI formula</h2>
<p>Return equals net benefit divided by cost. A worked example follows in the
<a href="https://www.example.com/product-b/">Product B analytics course</a>.</p>
<h2>Conclusion</h2>
<p>Measured well, training pays for itself.</p>
<section class="faq" itemscope itemtype="https://schema.org/FAQPage">
<div class="faq-item active" itemscope itemprop="mainEntity" itemtype="https://schema.org/Question">
<div class="faq-question"><p itemprop="name">What is a good training ROI?</p><span class="toggle-icon"></span></div>
<div class="faq-answer" itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer"><p itemprop="text">Anything above the program cost is a positive return.</p></div>
</div>
</section>
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{{"@type":"Question","name":"What is a good training ROI?","acceptedAnswer":{{"@type":"Answer","text":"Anything above the program cost is a positive return."}}}}]}}
</script>
</div>
</body></html>"""


def _write(tmp_path, name, html):
    p = tmp_path / name
    p.write_text(html, encoding="utf-8")
    return str(p)


def test_passing_optimize_doc(tmp_path):
    path = _write(tmp_path, "page-green.html", _passing_optimize_html())
    assert qa_check.run(path, forced_words=1500, is_new=False) == 0


def test_em_dash_fails(tmp_path):
    html = _passing_optimize_html().replace("A direct answer opens the section.",
                                            "A direct answer opens the section — always.")
    path = _write(tmp_path, "page-green.html", html)
    assert qa_check.run(path, forced_words=1500, is_new=False) == 1


def test_cta_anchor_fails(tmp_path):
    html = _passing_optimize_html().replace("Product A certification course", "Learn More")
    path = _write(tmp_path, "page-green.html", html)
    assert qa_check.run(path, forced_words=1500, is_new=False) == 1


def test_missing_changes_summary_fails_in_optimize_mode(tmp_path):
    html = _passing_optimize_html().replace('class="changes-summary"', 'class="something-else"')
    path = _write(tmp_path, "page-green.html", html)
    assert qa_check.run(path, forced_words=1500, is_new=False) == 1


def test_comment_with_div_does_not_break_tag_balance(tmp_path):
    # Regression: template ships commented <div> examples; they must not fail balance.
    html = _passing_optimize_html().replace(
        "<h1>Product Certification Guide</h1>",
        "<!-- Example: <div class=\"new-block\"><h3>x</h3></div> -->\n<h1>Product Certification Guide</h1>",
    )
    path = _write(tmp_path, "page-green.html", html)
    assert qa_check.run(path, forced_words=1500, is_new=False) == 0


def test_broken_jsonld_fails(tmp_path):
    # Introduce a trailing comma into the FAQPage JSON-LD -> invalid JSON.
    html = _passing_optimize_html().replace(
        '"acceptedAnswer":{"@type":"Answer","text":"Most candidates finish within a few months."}}]}',
        '"acceptedAnswer":{"@type":"Answer","text":"Most candidates finish within a few months."}},]}',
    )
    path = _write(tmp_path, "page-green.html", html)
    assert qa_check.run(path, forced_words=1500, is_new=False) == 1


def test_keyword_placement_passes_with_keyword(tmp_path):
    path = _write(tmp_path, "page-green.html", _passing_optimize_html())
    assert qa_check.run(path, forced_words=1500, is_new=False, keyword="product certification") == 0


def test_skipped_heading_level_fails(tmp_path):
    # Turn the H3 into an H4 so H2 -> H4 skips a level.
    html = _passing_optimize_html().replace("<h3>Certification costs in 2026</h3>",
                                            "<h4>Certification costs in 2026</h4>")
    path = _write(tmp_path, "page-green.html", html)
    assert qa_check.run(path, forced_words=1500, is_new=False) == 1


def test_image_without_alt_fails(tmp_path):
    html = _passing_optimize_html().replace(
        "<h2>Conclusion</h2>", '<p><img src="/img/chart.png"></p>\n<h2>Conclusion</h2>')
    path = _write(tmp_path, "page-green.html", html)
    assert qa_check.run(path, forced_words=1500, is_new=False) == 1


def test_passing_new_doc(tmp_path):
    path = _write(tmp_path, "page.html", _passing_new_html())
    assert qa_check.run(path, forced_words=1500, is_new=True) == 0


def test_new_mode_rejects_removal_markers(tmp_path):
    html = _passing_new_html().replace(
        "<h2>Conclusion</h2>",
        '<div class="remove-block"><span class="remove-tag">REMOVE</span><p>old</p></div>\n<h2>Conclusion</h2>',
    )
    path = _write(tmp_path, "page.html", html)
    assert qa_check.run(path, forced_words=1500, is_new=True) == 1
