# NPPL website (lbinlab.com)

Static site for the Novel Powder Processing Lab, Kyung Hee University.
Every page is generated from the YAML files in `data/`; edit data, not HTML.

```
data/        site.yaml pi.yaml people.yaml research.yaml projects.yaml
             publications.yaml patents.yaml news.yaml gallery.yaml journals.yaml
templates/   Jinja2 page templates
static/      style.css, img/, video/   (copied as-is)
tools/       add_paper.py, import_index.py
build.py     data + templates → _site/
```

Pushing to `main` builds and deploys to GitHub Pages (`.github/workflows/deploy.yml`).

## Local preview

    pip install pyyaml jinja2
    python3 build.py --serve        # http://localhost:8000

## New paper

    python3 tools/add_paper.py path/to/paper.pdf      # or a DOI
    # then check * (corresponding) and + (equal contribution) markers in data/publications.yaml

The DOI is read from the PDF and metadata comes from Crossref. An entry marked
`status: accepted` with the same title is upgraded in place.

## SCIE badge

    uv run --with openpyxl --with pyyaml python tools/import_index.py 20261116_JournalList_1.xlsx

Reads the yearly SCIE/SSCI/A&HCI journal-list workbook and writes `data/journals.yaml`.
Run it again after adding a paper in a journal not yet listed, or when a new list
arrives. The workbook stays out of git (`/*.xlsx` is ignored).
Impact factors are deliberately not shown.

## Members, news, projects

Edit `data/people.yaml`, `data/news.yaml`, `data/projects.yaml`. Photos go in
`static/img/people/` (square, ≥ 400 px).

## DNS switch day (before 2027-01-20, when the Wix plan expires)

1. Wix → Domains → lbinlab.com → DNS records: A @ → 185.199.108.153 / .109.153 / .110.153 / .111.153, CNAME www → khu-nppl.github.io.
2. Here: `echo lbinlab.com > CNAME`, set `url: https://lbinlab.com` in `data/site.yaml`, commit, push.
3. Repo Settings → Pages → custom domain lbinlab.com, then tick "Enforce HTTPS" once the certificate is issued.
4. Google Search Console: add the property lbinlab.com and submit `https://lbinlab.com/sitemap.xml`.
