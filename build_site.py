#!/usr/bin/env python3
"""
DFD CRR Officer Operations Manual: static site generator.

manual.md (in this folder) is the single source of truth. Edit it, then run:

    python3 build_site.py

Every page (index.html, ch01-ch17, app-a through app-i) is regenerated from it.
Commit manual.md together with the regenerated HTML.

Markdown conventions the parser understands:
  # **Chapter 6: CRR Newsletters**      page title (starts a new page)
  ## 6.4 Section title                   section heading
  ### 6.4.1 Subsection title             subsection heading
  - item / 1. item                       lists
  | a | b |  followed by |---|---|       tables (rows with FAIL or DNS get highlighted)
  > **Callout title**                    callout box; the next "> " lines are its body
  > [!info] / [!action] / [!danger]      optional first-line tag picks the callout color
  **bold**  *italic*  `code`  [text](url)  <br>
"""
import html as html_mod
import re
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent
MD_PATH = SITE_DIR / 'manual.md'

VERSION = '0.3'
VERSION_DATE = 'October 2026'

# (filename, sidebar label, sidebar section divider, title pattern)
PAGES = [
    ('index.html', 'Home', None, r'^# \*\*Preface'),
    ('ch01.html', 'Ch 1: DFD Overview', 'PART I: FOUNDATION', r'^# \*\*Chapter 1:'),
    ('ch02.html', 'Ch 2: Position Overview', None, r'^# \*\*Chapter 2:'),
    ('ch03.html', 'Ch 3: Key Relationships', None, r'^# \*\*Chapter 3:'),
    ('ch04.html', 'Ch 4: CRR Strategy', 'PART II: CRR OPERATIONS', r'^# \*\*Chapter 4:'),
    ('ch05.html', 'Ch 5: Public Education', None, r'^# \*\*Chapter 5:'),
    ('ch06.html', 'Ch 6: Newsletters', None, r'^# \*\*Chapter 6:'),
    ('ch07.html', 'Ch 7: CRR Tech Tools', None, r'^# \*\*Chapter 7:'),
    ('ch08.html', 'Ch 8: Civil Service', 'PART III: RECRUITMENT & HIRING', r'^# \*\*Chapter 8:'),
    ('ch09.html', 'Ch 9: Hiring Process', None, r'^# \*\*Chapter 9:'),
    ('ch10.html', 'Ch 10: Candidate Pipeline', None, r'^# \*\*Chapter 10:'),
    ('ch11.html', 'Ch 11: Special Programs', None, r'^# \*\*Chapter 11:'),
    ('ch12.html', 'Ch 12: Budget', 'PART IV: ADMINISTRATION', r'^# \*\*Chapter 12:'),
    ('ch13.html', 'Ch 13: Weekly Reporting', None, r'^# \*\*Chapter 13:'),
    ('ch14.html', 'Ch 14: Quarterly Appraisals', None, r'^# \*\*Chapter 14:'),
    ('ch15.html', 'Ch 15: Accreditation & Pension', None, r'^# \*\*Chapter 15:'),
    ('ch16.html', 'Ch 16: Digital Platforms', 'PART V: TECHNOLOGY', r'^# \*\*Chapter 16:'),
    ('ch17.html', 'Ch 17: System Admin', None, r'^# \*\*Chapter 17:'),
    ('app-a.html', 'App A: Quick Reference', 'APPENDICES', r'^# \*\*Appendix A:'),
    ('app-b.html', 'App B: CRR Tools Docs', None, r'^# \*\*Appendix B:'),
    ('app-c.html', 'App C: Newsletter Archive', None, r'^# \*\*Appendix C:'),
    ('app-d.html', 'App D: Contact Directory', None, r'^# \*\*Appendix D:'),
    ('app-e.html', 'App E: Version History', None, r'^# \*\*Appendix E:'),
    ('app-f.html', 'App F: Email Templates', None, r'^# \*\*Appendix F:'),
    ('app-g.html', 'App G: Vendor Reference', None, r'^# \*\*Appendix G:'),
    ('app-h.html', 'App H: CRR Calendar', None, r'^# \*\*Appendix H:'),
    ('app-i.html', 'App I: Recruiting Calendar', None, r'^# \*\*Appendix I:'),
]

PARTS = [  # table of contents grouping on the home page
    ('Part I: Foundation', ['ch01', 'ch02', 'ch03']),
    ('Part II: Community Risk Reduction Operations', ['ch04', 'ch05', 'ch06', 'ch07']),
    ('Part III: Recruitment &amp; Hiring Operations', ['ch08', 'ch09', 'ch10', 'ch11']),
    ('Part IV: Administrative Operations', ['ch12', 'ch13', 'ch14', 'ch15']),
    ('Part V: Technology &amp; Systems', ['ch16', 'ch17']),
    ('Appendices', [f'app-{c}' for c in 'abcdefghi']),
]


# ─────────────────────────── inline formatting ───────────────────────────
def inline_format(text):
    text = html_mod.escape(text, quote=False)
    text = text.replace('&lt;br&gt;', '<br>')
    text = text.replace('\\|', '|')
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<![\w*])\*([^*\n]+?)\*(?![\w*])', r'<em>\1</em>', text)
    text = re.sub(r'`([^`]+?)`', r'<code>\1</code>', text)
    text = re.sub(r'\[([^\]]+?)\]\(([^)\s]+?)\)', r'<a href="\2">\1</a>', text)
    return text


def anchor(text, seen=None):
    base = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    if seen is None:
        return base
    seen[base] = seen.get(base, 0) + 1
    return base if seen[base] == 1 else f'{base}-{seen[base]}'


def split_row(row):
    cells = re.split(r'(?<!\\)\|', row.strip())[1:-1]
    return [c.strip() for c in cells]


# ─────────────────────────── block parser ───────────────────────────
def md_to_html(md_text):
    lines = md_text.split('\n')
    out, i, in_list = [], 0, None
    seen = {}

    def close_list():
        nonlocal in_list
        if in_list:
            out.append(f'</{in_list}>')
            in_list = None

    while i < len(lines):
        s = lines[i].strip()

        if not s:
            close_list(); i += 1; continue

        # table
        if s.startswith('|') and i + 1 < len(lines) and re.match(r'^\|[\s\-:|]+\|$', lines[i + 1].strip()):
            close_list()
            out.append('<div class="table-wrapper"><table>')
            out.append('<thead><tr>' + ''.join(f'<th>{inline_format(c)}</th>' for c in split_row(s)) + '</tr></thead>')
            out.append('<tbody>')
            i += 2
            while i < len(lines) and lines[i].strip().startswith('|'):
                cells = split_row(lines[i])
                cls = ' class="row-fail"' if any(c == 'FAIL' for c in cells) else (
                      ' class="row-dns"' if any(c == 'DNS' for c in cells) else '')
                out.append(f'<tr{cls}>' + ''.join(f'<td>{inline_format(c)}</td>' for c in cells) + '</tr>')
                i += 1
            out.append('</tbody></table></div>')
            continue

        # callout
        if s.startswith('>'):
            close_list()
            body = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                body.append(lines[i].strip()[1:].strip()); i += 1
            kind = 'warning'
            m = re.match(r'^\[!(\w+)\]\s*', body[0])
            if m:
                kind = m.group(1).lower(); body[0] = body[0][m.end():]
            title = ''
            m = re.match(r'^\*\*(.+)\*\*$', body[0])
            if m:
                title = m.group(1); body = body[1:]
            out.append(f'<div class="callout callout-{kind}">')
            if title:
                out.append(f'<div class="callout-title">{inline_format(title)}</div>')
            out.append(inline_format(' '.join(b for b in body if b)))
            out.append('</div>')
            continue

        # headings
        m = re.match(r'^(#{1,3}) (.*)$', s)
        if m:
            close_list()
            level, text = len(m.group(1)), m.group(2).strip().strip('*').strip()
            if level == 1:
                cm = re.match(r'^(Chapter \d+|Appendix [A-Z]):\s*(.*)$', text)
                if cm:
                    out.append(f'<span class="chapter-number">{html_mod.escape(cm.group(1))}</span>')
                    out.append(f'<h1>{html_mod.escape(cm.group(2))}</h1>')
                else:
                    out.append(f'<h1>{html_mod.escape(text)}</h1>')
            else:
                out.append(f'<h{level} id="{anchor(text, seen)}">{inline_format(text)}</h{level}>')
            i += 1; continue

        # lists
        m = re.match(r'^(?:[-*] |(\d+)\. )(.*)$', s)
        if m:
            kind = 'ol' if m.group(1) else 'ul'
            if in_list != kind:
                close_list(); out.append(f'<{kind}>'); in_list = kind
            out.append(f'<li>{inline_format(m.group(2))}</li>')
            i += 1; continue

        close_list()
        out.append(f'<p>{inline_format(s)}</p>')
        i += 1

    close_list()
    return '\n'.join(out)


# ─────────────────────────── page assembly ───────────────────────────
def split_manual():
    lines = MD_PATH.read_text(encoding='utf-8').split('\n')
    starts = []
    for idx, (fn, _, _, pat) in enumerate(PAGES):
        hit = next((n for n, l in enumerate(lines) if re.match(pat, l.strip())), None)
        if hit is None:
            raise SystemExit(f'manual.md is missing the title line for {fn} ({pat})')
        starts.append(hit)
    if starts != sorted(starts):
        raise SystemExit('Page title lines in manual.md are out of order')
    starts.append(len(lines))
    return {PAGES[k][0]: '\n'.join(lines[starts[k]:starts[k + 1]]) for k in range(len(PAGES))}


# ─────────────────────────── search index ───────────────────────────
PART_OF = {}
_part = None
for _fn, _label, _divider, _ in PAGES:
    if _divider:
        _part = _divider.split(':', 1)[-1].strip().title().replace('Crr', 'CRR').replace('&', 'and')
    PART_OF[_fn] = _part or 'Home'


def plain(text):
    """Markdown inline text to plain text for the index."""
    text = text.replace('<br>', ' ').replace('\\|', '|')
    text = re.sub(r'\[([^\]]+?)\]\([^)]+?\)', r'\1', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'(?<![\w*])\*([^*\n]+?)\*(?![\w*])', r'\1', text)
    text = text.replace('`', '')
    return re.sub(r'\s+', ' ', text).strip()


def chunk_page(fn, md, title):
    """Split one page into searchable sections: one per ## / ### heading,
    with long sections split again at bold labels (e.g. each month of a calendar)."""
    lines = md.split('\n')[1:]  # skip the page title line
    chunks, cur = [], {'h': title, 'parent': '', 'a': '', 'lines': []}
    h2 = ''
    seen = {}

    def flush():
        body = []
        header = None
        for raw in cur['lines']:
            s = raw.strip()
            if not s:
                continue
            if s.startswith('|'):
                cells = [plain(c) for c in re.split(r'(?<!\\)\|', s)[1:-1]]
                if all(re.fullmatch(r':?-+:?', c) for c in cells if c):
                    continue
                if header is None:
                    header = cells
                    body.append(' | '.join(cells))
                else:
                    pairs = [f'{h}: {c}' if h and c and len(header) > 2 else c for h, c in zip(header, cells)]
                    body.append(' | '.join(p for p in pairs if p))
                continue
            header = None
            s = re.sub(r'^(?:[-*] |\d+\. |> ?)', '', s)
            s = re.sub(r'^\[!\w+\]\s*', '', s)
            body.append(plain(s))
        text = '\n'.join(b for b in body if b)
        if not text and not cur['h']:
            return
        crumbs = [c for c in (cur['parent'],) if c]
        chunks.append({'p': fn, 'pt': title, 'part': PART_OF[fn], 'h': cur['h'],
                       'b': crumbs, 'a': cur['a'], 't': text})

    for raw in lines:
        s = raw.strip()
        m = re.match(r'^(#{2,3}) (.*)$', s)
        if m:
            flush()
            text = m.group(2).strip().strip('*').strip()
            if len(m.group(1)) == 2:
                h2 = text
                cur = {'h': text, 'parent': '', 'a': anchor(text, seen), 'lines': []}
            else:
                cur = {'h': text, 'parent': h2, 'a': anchor(text, seen), 'lines': []}
            continue
        cur['lines'].append(raw)
    flush()

    # split oversized sections at bold labels ("**January**: Civil Service Exam")
    out = []
    for c in chunks:
        if len(c['t'].split()) < 700:
            out.append(c); continue
        parts, buf, label = [], [], None
        for line in c['t'].split('\n'):
            lm = re.match(r'^([A-Z][A-Za-z ()/&-]{2,40}): (.{2,60})$', line)
            if lm and len(buf) > 0 and not line.startswith(('Week', '1 ', '2 ')) and '|' not in line:
                parts.append((label, buf)); buf, label = [], line
            else:
                buf.append(line)
        parts.append((label, buf))
        if len(parts) == 1:
            out.append(c); continue
        for label, buf in parts:
            sub = dict(c)
            if label:
                sub['b'] = c['b'] + [c['h']]
                sub['h'] = label
                sub['t'] = '\n'.join(buf)
            else:
                sub['t'] = '\n'.join(buf)
            out.append(sub)
    return out


def write_search_index(sections, titles):
    import json
    docs = []
    for fn, _, _, _ in PAGES:
        title = 'Preface: How to Use This Manual' if fn == 'index.html' else titles[fn]
        docs.extend(chunk_page(fn, sections[fn], title))
    payload = {'version': VERSION, 'date': VERSION_DATE,
               'pages': [{'p': fn, 'label': label, 'part': PART_OF[fn]} for fn, label, _, _ in PAGES],
               'docs': docs}
    js = ('/* Generated by build_site.py. Do not edit. */\nwindow.CRRO_SEARCH_INDEX = '
          + json.dumps(payload, ensure_ascii=False, separators=(',', ':')) + ';\n')
    (SITE_DIR / 'assets' / 'search-index.js').write_text(js, encoding='utf-8')
    words = sum(len(d['t'].split()) for d in docs)
    print(f'  indexed {len(docs)} sections, {words:,} words')


SEARCH_PAGE = '''
<span class="chapter-number">Search</span>
<h1>Search the Manual</h1>
<div class="sp-box">
  <input id="sp-input" type="search" autocomplete="off" spellcheck="false"
         placeholder="Try: PAT staffing, VerifEYE admissions, 7726, checkbook monthly" aria-label="Search the manual">
</div>
<div id="sp-facets" class="sp-facets" aria-label="Filter by part"></div>
<div id="sp-status" class="sp-status" role="status" aria-live="polite"></div>
<ol id="sp-results" class="sp-results"></ol>
<details class="sp-tips">
  <summary>Search tips</summary>
  <ul>
    <li><strong>Plain words</strong> find sections that mention all of them first: <code>practice pat weather</code></li>
    <li><strong>Quotes</strong> match an exact phrase: <code>"conditional offer"</code></li>
    <li><strong>Minus</strong> excludes a word: <code>budget -pat</code></li>
    <li><strong>Filters</strong>: <code>ch:9</code>, <code>app:g</code>, or <code>part:recruitment</code></li>
    <li>Acronyms and account numbers work both ways: <code>PHS</code> finds Personal History Statement, <code>7726</code> finds Physicals/Psych</li>
    <li>Typos and partial words are forgiven: <code>verifye</code>, <code>reconcil</code></li>
    <li>Press <kbd>/</kbd> or <kbd>Ctrl</kbd>+<kbd>K</kbd> on any page to search</li>
  </ul>
</details>
'''


def page_titles(sections):
    titles = {}
    for fn, md in sections.items():
        first = md.split('\n', 1)[0]
        titles[fn] = first.lstrip('#').strip().strip('*').strip()
    return titles


def sidebar(current):
    items = []
    for fn, label, divider, _ in PAGES:
        if divider:
            items.append('<div class="nav-divider"></div>')
            items.append(f'<div class="nav-section"><div class="nav-section-label">{html_mod.escape(divider)}</div></div>')
        active = ' active' if fn == current else ''
        items.append(f'<a href="{fn}" class="nav-link{active}">{html_mod.escape(label)}</a>')
        if fn == 'index.html':
            sa = ' active' if current == 'search.html' else ''
            items.append(f'<a href="search.html" class="nav-link{sa}">Search</a>')
    return '\n    '.join(items)


def page_template(title, content, current, prev_page, next_page):
    nav = ''
    if prev_page or next_page:
        nav = '<div class="page-nav">'
        if prev_page:
            nav += f'<a href="{prev_page[0]}"><span class="nav-label">&larr; Previous</span>{html_mod.escape(prev_page[1])}</a>'
        if next_page:
            nav += f'<a href="{next_page[0]}" class="nav-next"><span class="nav-label">Next &rarr;</span>{html_mod.escape(next_page[1])}</a>'
        nav += '</div>'
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html_mod.escape(title)} | DFD CRR Officer Operations Manual</title>
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>

  <header class="site-header">
    <button class="menu-toggle" aria-label="Toggle navigation">&#9776;</button>
    <a href="index.html" class="header-brand">
      <span class="header-badge">DFD</span>
      <span class="header-title">CRR Officer Operations Manual</span>
    </a>
    <span class="header-subtitle">v{VERSION} | {VERSION_DATE}</span>
    <div class="hs" role="search">
      <button class="hs-open" type="button" aria-label="Search the manual">
        <svg viewBox="0 0 20 20" width="16" height="16" aria-hidden="true"><circle cx="8.5" cy="8.5" r="5.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M13 13l4.5 4.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
      </button>
      <div class="hs-field">
        <svg class="hs-icon" viewBox="0 0 20 20" width="16" height="16" aria-hidden="true"><circle cx="8.5" cy="8.5" r="5.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M13 13l4.5 4.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
        <input class="hs-input" type="search" autocomplete="off" spellcheck="false" placeholder="Search the manual"
               role="combobox" aria-expanded="false" aria-controls="hs-list" aria-autocomplete="list" aria-label="Search the manual">
        <kbd class="hs-key">/</kbd>
      </div>
      <div class="hs-panel" id="hs-panel" hidden>
        <ul class="hs-list" id="hs-list" role="listbox"></ul>
        <div class="hs-foot"></div>
      </div>
    </div>
  </header>

  <nav class="sidebar">
    {sidebar(current)}
  </nav>
  <div class="sidebar-overlay"></div>

  <main class="main-content">
    <div class="content-wrapper">
      {content}
      {nav}
    </div>
    <footer class="site-footer">
      Denton Fire Department | CRR Officer Operations Manual v{VERSION} | {VERSION_DATE}<br>
      Prepared by Captain Hunter Lott, Community Risk Reduction Officer
    </footer>
  </main>

  <script src="assets/nav.js"></script>
  <script src="assets/search-index.js" defer></script>
  <script src="assets/search.js" defer></script>
</body>
</html>
'''


def index_content(preface_md, titles):
    cover = f'''
<div class="cover-hero">
  <div class="cover-dept">Denton Fire Department | Support Services Division</div>
  <h1>CRR Officer<br>Operations Manual</h1>
  <div class="cover-divider"></div>
  <div class="cover-subtitle">Position Pass-Down Guide &amp; Standard Operating Procedures</div>
  <div class="cover-version">Version {VERSION} &nbsp;|&nbsp; {VERSION_DATE}</div>
  <div class="cover-notice">
    This document contains operational procedures and institutional knowledge for the
    CRR Officer position. Handle in accordance with department information security policies.
  </div>
</div>
'''
    toc = ['<h2 id="table-of-contents">Table of Contents</h2>']
    for part, stems in PARTS:
        toc.append(f'<h3>{part}</h3>\n<ul>')
        for stem in stems:
            toc.append(f'  <li><a href="{stem}.html">{html_mod.escape(titles[stem + ".html"])}</a></li>')
        toc.append('</ul>')
    return cover + md_to_html(preface_md) + '\n' + '\n'.join(toc)


def build():
    sections = split_manual()
    titles = page_titles(sections)
    for k, (fn, label, _, _) in enumerate(PAGES):
        prev_page = (PAGES[k - 1][0], PAGES[k - 1][1]) if k > 0 else None
        next_page = (PAGES[k + 1][0], PAGES[k + 1][1]) if k + 1 < len(PAGES) else None
        if fn == 'index.html':
            content, title = index_content(sections[fn], titles), 'Home'
        else:
            content, title = md_to_html(sections[fn]), label
        (SITE_DIR / fn).write_text(page_template(title, content, fn, prev_page, next_page), encoding='utf-8')
        print(f'  built {fn}')
    (SITE_DIR / 'search.html').write_text(
        page_template('Search', SEARCH_PAGE, 'search.html', None, None), encoding='utf-8')
    print('  built search.html')
    write_search_index(sections, titles)
    print(f'Done: {len(PAGES)} pages, v{VERSION} ({VERSION_DATE})')


if __name__ == '__main__':
    build()
