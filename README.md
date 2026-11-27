# NPPL website (lbinlab.com)

Static site for the Novel Powder Processing Lab, Kyung Hee University.
Every page is generated from the YAML files in `data/`; edit data, not HTML.

```
data/        site.yaml pi.yaml people.yaml research.yaml projects.yaml
             publications.yaml patents.yaml news.yaml gallery.yaml journals.yaml
templates/   Jinja2 page templates
static/      style.css, img/, video/   (copied as-is)
tools/       add_paper.py, import_jcr.py
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

## Impact factor / JCR rank

    python3 tools/import_jcr.py --list                  # journals that need metrics
    python3 tools/import_jcr.py JCR_export.csv 2025     # import a JCR CSV export

Metrics come only from a Journal Citation Reports export (university library access).
Do not type numbers by hand or copy them from third-party sites. Update once a year
after the June JCR release.

## Members, news, projects

Edit `data/people.yaml`, `data/news.yaml`, `data/projects.yaml`. Photos go in
`static/img/people/` (square, ≥ 400 px).
