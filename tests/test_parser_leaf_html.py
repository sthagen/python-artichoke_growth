import pathlib
from bs4 import BeautifulSoup

HTML_LEAF_PAGE_SAMPLE_PATH = pathlib.Path('tests', 'fixtures', 'html', 'leaf_page_sample.html')
HTML_TEXT = ''


def setup():
    global HTML_TEXT
    with open(HTML_LEAF_PAGE_SAMPLE_PATH, "rt", encoding="utf-8") as handle:
        HTML_TEXT = handle.read()


def teardown():
    global HTML_TEXT
    HTML_TEXT = ''


def test_html_leaf_page_parse_fixture():
    # soup = BeautifulSoup(HTML_TEXT, 'html.parser')
    lines = [t for t in HTML_TEXT.split('\n') if t.startswith('<a href="')]
    parsed = []
    for line in lines:
        a, x = line.split('">', 1)
        f, r = x.split('</a>')
        r = r.rstrip()
        d, s, u = r.rsplit(' ', 2)
        d = d.strip()
        parsed.append((f, d, s, u))
    for p in parsed:
        print(p)
        assert len(p) == 4
