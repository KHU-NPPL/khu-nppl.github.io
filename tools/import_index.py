#!/usr/bin/env python3
"""Mark each journal's citation index (SCIE / SSCI / A&HCI) from a journal-list workbook.

    uv run --with openpyxl --with pyyaml python tools/import_index.py 20261116_JournalList_1.xlsx

The workbook has one sheet per index (SCIE, SSCI, A&HCI) with columns
No, Title, ISSN, E-ISSN, CATEGORY, ... — the list universities circulate each year.
Journals are matched by ISSN first, then by normalised title.
Journals not found get no badge. Keep the workbook out of git (it is ignored).
"""
import re
import sys
from pathlib import Path

import openpyxl
import yaml

ROOT = Path(__file__).resolve().parents[1]
PUBS = ROOT / 'data' / 'publications.yaml'
JOURNALS = ROOT / 'data' / 'journals.yaml'


def norm(s):
    return re.sub(r'[^a-z0-9]', '', (s or '').lower().replace('&', 'and'))


def main(xlsx):
    wb = openpyxl.load_workbook(xlsx)
    idx = {}
    for ws in wb.worksheets:
        for r in list(ws.iter_rows(values_only=True))[2:]:
            if not r or not r[1]:
                continue
            for k in (r[2], r[3]):
                if k:
                    idx.setdefault(k.replace('-', '').upper(), set()).add(ws.title)
            idx.setdefault(norm(r[1]), set()).add(ws.title)
    pubs = yaml.safe_load(PUBS.read_text(encoding='utf8'))['publications']
    journals = {}
    for p in pubs:
        journals.setdefault(p['journal'], set()).update(i.replace('-', '').upper() for i in p.get('issn') or [])
    out, missing = {}, []
    for j, issns in sorted(journals.items()):
        hit = set().union(*(idx.get(i, set()) for i in issns)) or idx.get(norm(j), set())
        if hit:
            out[j.lower()] = {'index': ', '.join(sorted(hit))}
        else:
            missing.append(j)
    JOURNALS.write_text(
        '# Citation index shown next to each publication (tools/import_index.py).\n'
        '# Generated from the journal-list workbook — do not edit by hand.\n'
        + yaml.safe_dump({'source': Path(xlsx).name, 'journals': out}, allow_unicode=True, sort_keys=True),
        encoding='utf8')
    print(f'{len(out)}/{len(journals)} journals indexed')
    for j in missing:
        print('  not in list:', j)


if __name__ == '__main__':
    main(sys.argv[1])
