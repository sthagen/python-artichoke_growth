from bs4 import BeautifulSoup
with open("leaf_page_sample.html", "rt", encoding="utf-8") as handle:
    html_text = handle.read()
soup = BeautifulSoup(html_text, 'html.parser')
lines = [t for t in html_text.split('\n') if t.startswith('<a href="')]
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
