# DFD CRR Officer Operations Manual

**Version 0.3, October 2026**

Static site for the Denton Fire Department Community Risk Reduction Officer Operations Manual,
published at https://dentonfire.github.io/CRRO_Manual/. 27 pages: a home page, 17 chapters, and 9 appendices (A through I).

## How to update the manual

`manual.md` is the single source of truth. Never hand-edit the HTML pages.

1. Edit `manual.md`.
2. Run `python3 build_site.py` (Python 3, no extra packages). Every page is regenerated.
3. Commit `manual.md` and the regenerated HTML together.

To change the version number shown on every page, edit `VERSION` and `VERSION_DATE` at the top of `build_site.py`. Log each version in the Version History table in the Preface and in Appendix E.

The formatting rules the builder understands are listed at the top of `build_site.py`.

## Structure

- `manual.md`: source text for every page
- `build_site.py`: site generator
- `index.html`: cover, preface, table of contents
- `ch01.html` through `ch17.html`: chapters
- `app-a.html` through `app-i.html`: appendices
- `search.html`: full search results page
- `assets/style.css`, `assets/nav.js`: DFD styles and sidebar navigation
- `assets/search.js`, `assets/search-index.js`: search engine and its generated index

## Search

`build_site.py` also writes `assets/search-index.js`, a section-by-section index of the whole manual, and `search.html`. The engine in `assets/search.js` runs in the browser with no server or outside services: ranked full-text search with stemming, acronyms and synonyms (PAT, PHS, VerifEYE, account numbers), typo tolerance, "exact phrases", -exclusions, and filters (`ch:9`, `app:g`, `part:recruitment`). Press `/` or Ctrl+K on any page. Opening a result highlights the matched words on the page.

To teach it a new acronym or synonym, add a line to `SYNONYM_GROUPS` in `assets/search.js`. The index rebuilds automatically every time you run `build_site.py`.

## Publishing

GitHub Pages serves the `main` branch from the repository root. Changes go live a minute or two after each commit.

This site is public. Keep candidate names, passwords, account IDs, and anything else sensitive out of `manual.md`; credentials live in the CRR Credentials Workbook.

## Local preview

Open `index.html` in any browser. No server required.
