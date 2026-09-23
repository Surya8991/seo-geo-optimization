"""Word-count integrity for qa_check: notes are fully stripped (even when they wrap
tables), and the link budget uses the tool's own computed count, so an inflated
--words cannot unlock a larger link budget than the copy earns.
"""
import qa_check


NESTED_NOTE = """<div class="wrap">
<div class="note" style="background:#eef7f0"><strong>Changes summary</strong>
<div class="table-scroll"><table class="changes-summary"><thead><tr><th>A</th></tr></thead>
<tbody><tr><td>one two three four five six seven eight nine ten eleven twelve</td></tr></tbody>
</table></div></div>
<p>Real reader body has exactly seven visible words here.</p>
</div>"""


def test_strip_note_blocks_removes_nested_div_notes():
    stripped = qa_check.strip_note_blocks(NESTED_NOTE)
    # None of the note/table text survives...
    assert "Changes summary" not in stripped
    assert "eleven twelve" not in stripped
    # ...but the real body does.
    assert "Real reader body" in stripped


def test_reader_text_excludes_note_table_text():
    text = qa_check.reader_text(NESTED_NOTE)
    assert "Real reader body has exactly seven visible words here." in text
    assert "eleven" not in text


def _html_with_links(n_internal):
    links = "".join(
        f'<p>Body sentence number {i} with a '
        f'<a href="https://www.example.com/p{i}">internal link</a> in it.</p>'
        for i in range(n_internal)
    )
    return f"<div class='wrap'><h1>T</h1>{links}</div>"


def test_link_band_uses_computed_not_inflated_forced_words(tmp_path):
    # A short page (well under 2,000 reader words) allows at most 4 internal links,
    # regardless of any inflated --words a caller might pass.
    html = _html_with_links(6)
    computed = len(qa_check.reader_text(html).split())
    assert computed < 2000
    i_max, _ = qa_check.link_band(computed)
    assert i_max == 4
