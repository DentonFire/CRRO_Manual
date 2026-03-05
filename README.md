# DFD CRR Officer Operations Manual

**Version 0.2 — March 2026**

Static site for the Denton Fire Department Community Risk Reduction Officer Operations Manual.
27 pages covering 17 chapters and 9 appendices (A through I).

## Hosting on GitHub Pages

1. Push this folder to a GitHub repository (or add to existing CRR tools repo)
2. Go to **Settings → Pages**
3. Set source to `main` branch, folder `/` (root) or `/docs`
4. Site will be live at `https://your-username.github.io/repo-name/`

## Structure

- `index.html` — Cover page, preface, table of contents
- `ch01.html` through `ch17.html` — Chapters 1–17
- `app-a.html` through `app-i.html` — Appendices A–I
- `assets/style.css` — DFD-branded styles
- `assets/nav.js` — Sidebar navigation
- `build_site.py` — Site generator (rebuilds from markdown source files)

## Rebuilding the Site

Place chapter markdown files alongside `build_site.py`, then:

```bash
python3 build_site.py
```

This regenerates all HTML pages from the markdown source.

## Local Preview

Open `index.html` in any browser. No server required.
