#!/usr/bin/env python3
"""Fill data/journals.yaml (impact factor, quartile, rank) from a JCR export.

    python3 tools/import_jcr.py --list                 # journals that need metrics
    python3 tools/import_jcr.py JCR_export.csv 2025    # import (2025 = JCR release year)

Get the CSV from Journal Citation Reports (Clarivate) through the university
library: search the journals printed by --list, then Export → CSV.
Column names differ between JCR exports, so headers are matched loosely:
journal name, ISSN/eISSN, JIF, JIF quartile, JIF rank, category.
Numbers come only from that file — nothing is typed by hand or scraped.
"""
import csv
import io
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PUBS = ROOT / 'data' / 'publications.yaml'
JOURNALS = ROOT / 'data' / 'journals.yaml'


def norm(s):
    return re.sub(r'[^a-z0-9]', '', (s or '').lower().replace('&', 'and'))


def journals_in_use():
    pubs = yaml.safe_load(PUBS.read_text(encoding='utf8'))['publications']
    out = {}
    for p in pubs:
        if p['kind'] != 'international':
            continue
        j = out.setdefault(p['journal'], set())
        for i in p.get('issn') or []:
            j.add(i.replace('-', '').upper())
    return out


def pick(row, *keys):
    for k, v in row.items():
        kk = (k or '').lower()
        if all(x in kk for x in keys):
            return (v or '').strip()
    return ''


def main(args):
    used = journals_in_use()
    if not args or args[0] == '--list':
        data = yaml.safe_load(JOURNALS.read_text(encoding='utf8')) or {}
        have = {k.lower() for k in (data.get('journals') or {})}
        for j in sorted(used):
            print(('✓ ' if j.lower() in have else '· ') + j)
        return
    path, year = Path(args[0]), int(args[1])
    raw = path.read_text(encoding='utf-8-sig')
    lines = raw.splitlines()
    start = next(i for i, l in enumerate(lines) if 'issn' in l.lower() or 'journal' in l.lower())
    rows = list(csv.DictReader(io.StringIO('\n'.join(lines[start:]))))
    data = yaml.safe_load(JOURNALS.read_text(encoding='utf8')) or {}
    out = data.get('journals') or {}
    matched = 0
    for r in rows:
        name = pick(r, 'journal') or pick(r, 'title')
        issns = {pick(r, 'issn').replace('-', '').upper(), pick(r, 'eissn').replace('-', '').upper()} - {''}
        jif = pick(r, 'jif') if not pick(r, 'jif', 'quartile') == pick(r, 'jif') else ''
        jif = next((v for k, v in r.items() if re.fullmatch(r'(\d{4}\s*)?jif', (k or '').strip().lower())), jif)
        quart = pick(r, 'quartile')
        rank = pick(r, 'rank')
        cat = pick(r, 'categor')
        for j, js in used.items():
            if norm(j) == norm(name) or (issns & js):
                out[j.lower()] = {'if': jif, 'quartile': quart, 'rank': rank, 'category': cat}
                matched += 1
    data['jcr_year'] = year
    data['journals'] = out
    JOURNALS.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=True), encoding='utf8')
    missing = [j for j in used if j.lower() not in out]
    print(f'matched {matched} rows; {len(used) - len(missing)}/{len(used)} journals have metrics')
    for j in missing:
        print('  missing:', j)


if __name__ == '__main__':
    main(sys.argv[1:])
