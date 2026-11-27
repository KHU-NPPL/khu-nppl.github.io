#!/usr/bin/env python3
"""Build the NPPL website from data/*.yaml into _site/.

    python3 build.py            # build
    python3 build.py --serve    # build and serve at http://localhost:8000
"""
import html
import re
import shutil
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent
OUT = ROOT / '_site'
DATA = ROOT / 'data'

PAGES = [
    ('index.html', 'Home'),
    ('people.html', 'People'),
    ('research.html', 'Research'),
    ('projects.html', 'Projects'),
    ('publications.html', 'Publications'),
    ('patents.html', 'Patents'),
    ('news.html', 'News'),
    ('gallery.html', 'Gallery'),
]

PI_NAMES = ['Bin Lee', 'B. Lee', 'B.Lee', '이빈']


def load(name):
    return yaml.safe_load((DATA / f'{name}.yaml').read_text(encoding='utf8'))


def mark_pi(authors):
    """Escape the author string and bold the PI's name (keeping * and + markers)."""
    s = html.escape(authors or '')
    for n in PI_NAMES:
        s = re.sub(r'(?<![\w.])(' + re.escape(n) + r')(\*?)', r'<strong>\1\2</strong>', s)
    return s


def citation_tail(p):
    parts = []
    if p.get('volume'):
        parts.append(f"Vol. {p['volume']}")
    if p.get('issue'):
        parts.append(f"No. {p['issue']}")
    if p.get('page'):
        pg = p['page']
        parts.append(pg if not re.search(r'\d-\d', pg) else f'pp. {pg}')
    elif p.get('article'):
        parts.append(p['article'])
    if p.get('details'):
        parts.append(p['details'])
    return ', '.join(parts)


def journal_metric(p, journals):
    key = (p.get('journal') or '').strip().lower()
    return journals.get(key)


def main():
    site = load('site')
    pubs = load('publications')['publications']
    jm = load('journals')
    journals = {k.lower(): v for k, v in (jm.get('journals') or {}).items()}

    for p in pubs:
        p['authors_html'] = mark_pi(p.get('authors'))
        p['tail'] = citation_tail(p)
        p['metric'] = journal_metric(p, journals)

    def group(kind):
        items = [p for p in pubs if p['kind'] == kind]
        n = len(items)
        for i, p in enumerate(items):
            p['no'] = n - i
        years = {}
        for p in items:
            label = 'Accepted' if p.get('status') == 'accepted' else str(p.get('year', ''))
            years.setdefault(label, []).append(p)
        return n, list(years.items())

    n_int, intl = group('international')
    n_dom, dom = group('domestic')

    ctx = dict(
        site=site, pages=PAGES, pi=load('pi'), people=load('people'), projects=load('projects'),
        research=load('research'), news=load('news'), gallery=load('gallery'), patents=load('patents'),
        intl=intl, dom=dom, n_int=n_int, n_dom=n_dom, jcr_year=jm.get('jcr_year'),
        recent=[p for p in pubs if p['kind'] == 'international'][:5],
    )

    env = Environment(loader=FileSystemLoader(ROOT / 'templates'), autoescape=select_autoescape(['html']))
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / 'static', OUT)
    for fname, title in PAGES:
        tpl = env.get_template(fname)
        (OUT / fname).write_text(tpl.render(current=fname, title=title, **ctx), encoding='utf8')
    if (ROOT / 'CNAME').exists():
        shutil.copy(ROOT / 'CNAME', OUT / 'CNAME')
    (OUT / '.nojekyll').write_text('')
    print(f'built {len(PAGES)} pages → {OUT}  ({n_int} international, {n_dom} domestic papers)')


if __name__ == '__main__':
    main()
    if '--serve' in sys.argv:
        import functools
        import http.server
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
        print('serving http://localhost:8000')
        http.server.ThreadingHTTPServer(('', 8000), handler).serve_forever()
