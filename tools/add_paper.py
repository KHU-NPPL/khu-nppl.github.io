#!/usr/bin/env python3
"""Add a paper to data/publications.yaml from its PDF (or DOI).

    python3 tools/add_paper.py paper.pdf [more.pdf ...]
    python3 tools/add_paper.py 10.1016/j.jallcom.2026.189878
    python3 tools/add_paper.py paper.pdf --domestic

The DOI is read from the PDF text, metadata comes from Crossref.
An "accepted" entry with the same title is upgraded in place.
Corresponding (*) and equal-contribution (+) markers are NOT in Crossref:
the script prints a reminder — check them against the PDF and edit the yaml.
"""
import difflib
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PUBS = ROOT / 'data' / 'publications.yaml'
UA = {'User-Agent': 'lab-website-builder/0.1'}
DOI_RE = re.compile(r'\b(10\.\d{4,9}/[^\s"<>]+)', re.I)


def doi_from_pdf(pdf):
    txt = subprocess.run(['pdftotext', '-l', '2', str(pdf), '-'], capture_output=True, text=True).stdout
    for m in DOI_RE.finditer(txt):
        d = m.group(1).rstrip('.,;)')
        if not re.search(r'\.s\d{3}$', d):          # skip supplementary-material DOIs
            return d
    return None


def crossref(doi):
    url = 'https://api.crossref.org/works/' + urllib.request.quote(doi)
    it = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30))['message']
    e = {
        'title': re.sub(r'<[^>]+>', '', it['title'][0]).strip(),
        'authors': ', '.join((a.get('given', '') + ' ' + a.get('family', '')).strip() for a in it.get('author', [])),
        'journal': (it.get('container-title') or [''])[0].replace('&amp;', '&'),
    }
    y = (it.get('issued') or it.get('published-online') or {}).get('date-parts', [[None]])[0]
    if y and y[0]:
        e['year'] = y[0]
        if len(y) > 1:
            e['month'] = y[1]
    for f in ('volume', 'issue', 'page'):
        if it.get(f):
            e[f] = str(it[f])
    if it.get('article-number'):
        e['article'] = str(it['article-number'])
    e['doi'] = it['DOI'].lower()
    if it.get('ISSN'):
        e['issn'] = it['ISSN']
    return e


def norm(s):
    return re.sub(r'[^a-z0-9]', '', (s or '').lower())


def main(args):
    domestic = '--domestic' in args
    targets = [a for a in args if not a.startswith('--')]
    data = yaml.safe_load(PUBS.read_text(encoding='utf8'))
    pubs = data['publications']
    dom_journals = {norm(p['journal']) for p in pubs if p['kind'] == 'domestic'}
    for t in targets:
        doi = t if DOI_RE.fullmatch(t) else doi_from_pdf(t)
        if not doi:
            print(f'✗ {t}: no DOI found in the PDF — pass the DOI directly')
            continue
        if any(p.get('doi') == doi.lower() for p in pubs):
            print(f'= {doi}: already listed')
            continue
        e = crossref(doi)
        kind = 'domestic' if domestic or norm(e['journal']) in dom_journals else 'international'
        e = {'kind': kind, **e}
        # upgrade an "accepted" placeholder with the same title
        for i, p in enumerate(pubs):
            if p.get('status') == 'accepted' and difflib.SequenceMatcher(None, norm(p['title']), norm(e['title'])).ratio() > 0.9:
                e['authors'] = p['authors']          # keep the marked-up author string
                pubs[i] = e
                print(f'↑ upgraded accepted entry: {e["title"][:70]}')
                break
        else:
            pubs.insert(0, e)
            print(f'+ {kind}: {e["title"][:70]}\n  {e["journal"]} {e.get("volume", "")} ({e.get("year", "")})')
            print('  ! check corresponding (*) / equal-contribution (+) markers in authors')
    pubs.sort(key=lambda p: (p.get('status') == 'accepted', p.get('year') or 0, p.get('month') or 0), reverse=True)
    PUBS.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=200), encoding='utf8')


if __name__ == '__main__':
    main(sys.argv[1:])
