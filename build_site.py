#!/usr/bin/env python3
"""
DFD CRRO Manual → GitHub Pages Site Generator
Reads manual.md and generates a complete multi-page static site.
"""
import re
import html as html_mod
from pathlib import Path

SITE_DIR = Path('/home/claude/site')
MD_PATH = SITE_DIR / 'manual.md'

# ═══════════════════════════════════════════
# PAGE DEFINITIONS
# ═══════════════════════════════════════════
# Each page: (filename, nav_label, section_label, start_pattern, part_label)
PAGES = [
    ('index.html', 'Home', None, None, None),
    ('ch01.html', 'Ch 1: DFD Overview', 'PART I — FOUNDATION', r'^# \*\*Chapter 1:', 'Part I: Foundation'),
    ('ch02.html', 'Ch 2: Position Overview', None, r'^# \*\*Chapter 2:', None),
    ('ch03.html', 'Ch 3: Key Relationships', None, r'^# \*\*Chapter 3:', None),
    ('ch04.html', 'Ch 4: CRR Strategy', 'PART II — CRR OPERATIONS', r'^# \*\*Chapter 4:', 'Part II: CRR Operations'),
    ('ch05.html', 'Ch 5: Public Education', None, r'^# \*\*Chapter 5:', None),
    ('ch06.html', 'Ch 6: Newsletters', None, r'^# \*\*Chapter 6:', None),
    ('ch07.html', 'Ch 7: CRR Tech Tools', None, r'^# \*\*Chapter 7:', None),
    ('ch08.html', 'Ch 8: Civil Service', 'PART III — RECRUITMENT & HIRING', r'^# \*\*Chapter 8:', 'Part III: Recruitment'),
    ('ch09.html', 'Ch 9: Hiring Process', None, r'^# \*\*Chapter 9:', None),
    ('ch10.html', 'Ch 10: Candidate Pipeline', None, r'^# \*\*Chapter 10:', None),
    ('ch11.html', 'Ch 11: Special Programs', None, r'^# \*\*Chapter 11:', None),
    ('ch12.html', 'Ch 12: Budget', 'PART IV — ADMINISTRATION', r'^# \*\*Chapter 12:', 'Part IV: Administration'),
    ('ch13.html', 'Ch 13: Weekly Reporting', None, r'^# \*\*Chapter 13:', None),
    ('ch14.html', 'Ch 14: Quarterly Appraisals', None, r'^# \*\*Chapter 14:', None),
    ('ch15.html', 'Ch 15: Accreditation & Pension', None, r'^# \*\*Chapter 15:', None),
    ('ch16.html', 'Ch 16: Digital Platforms', 'PART V — TECHNOLOGY', r'^# \*\*Chapter 16:', 'Part V: Technology'),
    ('ch17.html', 'Ch 17: System Admin', None, r'^# \*\*Chapter 17:', None),
    ('app-a.html', 'App A: Quick Reference', 'APPENDICES', r'^# \*\*Appendix A:', 'Appendices'),
    ('app-b.html', 'App B: CRR Tools Docs', None, r'^# \*\*Appendix B:', None),
    ('app-c.html', 'App C: Newsletter Archive', None, r'^# \*\*Appendix C:', None),
    ('app-d.html', 'App D: Contact Directory', None, r'^# \*\*Appendix D:', None),
    ('app-e.html', 'App E: Version History', None, r'^# \*\*Appendix E:', None),
    ('app-f.html', 'App F: Email Templates', None, r'^# \*\*Appendix F:', None),
    ('app-g.html', 'App G: Vendor Reference', None, r'^# \*\*Appendix G:', None),
    ('app-h.html', 'App H: CRR Calendar', None, r'^# \*\*Appendix H:', None),
    ('app-i.html', 'App I: Recruiting Calendar', None, r'^# \*\*Appendix I:', None),
]

# ═══════════════════════════════════════════
# MARKDOWN PARSER
# ═══════════════════════════════════════════
def md_to_html(md_text):
    """Convert manual markdown to HTML. Handles tables, lists, headings, bold, italic."""
    lines = md_text.split('\n')
    out = []
    i = 0
    in_list = None  # 'ul' or 'ol'
    in_table = False
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Skip Part header lines (PART I, PART II, etc)
        if stripped.startswith('**PART ') and stripped.endswith('**'):
            i += 1
            continue
        if stripped in ('**FOUNDATION**', '**FOUNDATION**', '') and i > 0 and lines[i-1].strip().startswith('**PART'):
            i += 1
            continue
        # Skip italic sub-headers under PART headers
        if stripped.startswith('*') and stripped.endswith('*') and 'Department Context' in stripped:
            i += 1
            continue
        if stripped.startswith('*') and stripped.endswith('*') and ('Public education' in stripped or 'Civil Service' in stripped or 'Budget management' in stripped or 'All platforms' in stripped or 'Reference materials' in stripped):
            i += 1
            continue
            
        # Table detection
        if '|' in stripped and not stripped.startswith('|  |'):
            # Check if next line is separator
            if i + 1 < len(lines) and re.match(r'^\|[\s\-:|\s]+\|$', lines[i+1].strip()):
                # Parse table
                if in_list:
                    out.append(f'</{in_list}>')
                    in_list = None
                    
                header_cells = [c.strip() for c in stripped.split('|')[1:-1]]
                i += 2  # skip header and separator
                
                out.append('<div class="table-wrapper"><table>')
                out.append('<thead><tr>')
                for cell in header_cells:
                    out.append(f'<th>{inline_format(cell)}</th>')
                out.append('</tr></thead>')
                out.append('<tbody>')
                
                while i < len(lines) and '|' in lines[i] and lines[i].strip():
                    row_stripped = lines[i].strip()
                    if not row_stripped or row_stripped == '|  |':
                        break
                    cells = [c.strip() for c in row_stripped.split('|')[1:-1]]
                    
                    # Check for fail/DNS rows (PAT results)
                    row_class = ''
                    if any('FAIL' in c for c in cells):
                        row_class = ' class="row-fail"'
                    elif any('DNS' in c for c in cells):
                        row_class = ' class="row-dns"'
                    
                    out.append(f'<tr{row_class}>')
                    for cell in cells:
                        out.append(f'<td>{inline_format(cell)}</td>')
                    out.append('</tr>')
                    i += 1
                
                out.append('</tbody></table></div>')
                continue
        
        # Skip bare pipe table lines
        if stripped == '|  |' or stripped == '| :---- |':
            i += 1
            continue
            
        # Empty line
        if not stripped:
            if in_list:
                out.append(f'</{in_list}>')
                in_list = None
            i += 1
            continue
        
        # H1
        if stripped.startswith('# '):
            if in_list:
                out.append(f'</{in_list}>')
                in_list = None
            text = stripped[2:].strip().strip('*').strip()
            # Extract chapter number if present
            ch_match = re.match(r'(Chapter \d+|Appendix [A-G]):\s*(.*)', text)
            if ch_match:
                ch_num = ch_match.group(1)
                ch_title = ch_match.group(2)
                out.append(f'<span class="chapter-number">{html_mod.escape(ch_num)}</span>')
                out.append(f'<h1>{html_mod.escape(ch_title)}</h1>')
            elif text.startswith('Preface'):
                out.append(f'<h1>{html_mod.escape(text)}</h1>')
            else:
                out.append(f'<h1>{html_mod.escape(text)}</h1>')
            i += 1
            continue
        
        # H2
        if stripped.startswith('## '):
            if in_list:
                out.append(f'</{in_list}>')
                in_list = None
            text = stripped[3:].strip().strip('*').strip()
            anchor = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
            out.append(f'<h2 id="{anchor}">{html_mod.escape(text)}</h2>')
            i += 1
            continue
        
        # H3
        if stripped.startswith('### '):
            if in_list:
                out.append(f'</{in_list}>')
                in_list = None
            text = stripped[4:].strip().strip('*').strip()
            anchor = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
            out.append(f'<h3 id="{anchor}">{html_mod.escape(text)}</h3>')
            i += 1
            continue
        
        # Unordered list
        if stripped.startswith('* ') or stripped.startswith('- '):
            if in_list != 'ul':
                if in_list:
                    out.append(f'</{in_list}>')
                out.append('<ul>')
                in_list = 'ul'
            text = stripped[2:]
            out.append(f'<li>{inline_format(text)}</li>')
            i += 1
            continue
        
        # Ordered list
        if re.match(r'^\d+\.\s', stripped):
            if in_list != 'ol':
                if in_list:
                    out.append(f'</{in_list}>')
                out.append('<ol>')
                in_list = 'ol'
            text = re.sub(r'^\d+\.\s', '', stripped)
            out.append(f'<li>{inline_format(text)}</li>')
            i += 1
            continue
        
        # Regular paragraph
        if in_list:
            out.append(f'</{in_list}>')
            in_list = None
        out.append(f'<p>{inline_format(stripped)}</p>')
        i += 1
    
    if in_list:
        out.append(f'</{in_list}>')
    
    return '\n'.join(out)


def inline_format(text):
    """Handle bold, italic, code, links in text."""
    text = html_mod.escape(text)
    # Bold + italic
    text = re.sub(r'\\\*\\\*\\\*(.*?)\\\*\\\*\\\*', r'<strong><em>\1</em></strong>', text)
    # Bold (markdown escaped)
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    # Since html.escape converted * to * (it doesn't), handle raw markdown bold
    # Actually html.escape doesn't touch *, so:
    # Undo the escape for our formatting
    text = text.replace('\\*', '⟪STAR⟫')
    text = text.replace('\\[', '⟪LBRK⟫')
    text = text.replace('\\]', '⟪RBRK⟫')
    
    # Restore escaped chars
    text = text.replace('⟪STAR⟫', '*')
    text = text.replace('⟪LBRK⟫', '[')
    text = text.replace('⟪RBRK⟫', ']')
    
    # Italic
    text = re.sub(r'\*([^*]+?)\*', r'<em>\1</em>', text)
    # Code
    text = re.sub(r'`([^`]+?)`', r'<code>\1</code>', text)
    # Links
    text = re.sub(r'\[([^\]]+?)\]\(([^)]+?)\)', r'<a href="\2">\1</a>', text)
    
    return text


# ═══════════════════════════════════════════
# SPLIT MANUAL INTO SECTIONS
# ═══════════════════════════════════════════
def split_manual():
    """Split the manual markdown into sections by chapter."""
    with open(MD_PATH, 'r') as f:
        full_text = f.read()
    
    lines = full_text.split('\n')
    
    # Find section boundaries using the PAGES patterns
    boundaries = []
    for pg_idx, (filename, label, section, pattern, part) in enumerate(PAGES):
        if pattern is None:
            boundaries.append((pg_idx, 0))  # index page
            continue
        for line_idx, line in enumerate(lines):
            if re.match(pattern, line.strip()):
                boundaries.append((pg_idx, line_idx))
                break
    
    # Sort by line number
    boundaries.sort(key=lambda x: x[1])
    
    sections = {}
    for i, (pg_idx, start_line) in enumerate(boundaries):
        if pg_idx == 0:
            # Index: everything before first chapter
            end_line = boundaries[1][1] if len(boundaries) > 1 else len(lines)
            sections[0] = '\n'.join(lines[:end_line])
        else:
            end_line = boundaries[i+1][1] if i + 1 < len(boundaries) else len(lines)
            sections[pg_idx] = '\n'.join(lines[start_line:end_line])
    
    return sections


# ═══════════════════════════════════════════
# BUILD SIDEBAR NAVIGATION
# ═══════════════════════════════════════════
def build_sidebar(current_file):
    """Generate sidebar HTML."""
    nav_items = []
    
    for filename, label, section_label, pattern, part in PAGES:
        if section_label:
            nav_items.append(f'<div class="nav-divider"></div>')
            nav_items.append(f'<div class="nav-section"><div class="nav-section-label">{section_label}</div></div>')
        
        active = ' active' if filename == current_file else ''
        nav_items.append(f'<a href="{filename}" class="nav-link{active}">{label}</a>')
    
    return '\n    '.join(nav_items)


# ═══════════════════════════════════════════
# PAGE TEMPLATE
# ═══════════════════════════════════════════
def page_template(title, content_html, current_file, prev_page=None, next_page=None):
    """Wrap content in full HTML page."""
    sidebar_html = build_sidebar(current_file)
    
    # Prev/next navigation
    nav_html = ''
    if prev_page or next_page:
        nav_html = '<div class="page-nav">'
        if prev_page:
            nav_html += f'<a href="{prev_page[0]}"><span class="nav-label">← Previous</span>{prev_page[1]}</a>'
        if next_page:
            nav_html += f'<a href="{next_page[0]}" class="nav-next"><span class="nav-label">Next →</span>{next_page[1]}</a>'
        nav_html += '</div>'
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html_mod.escape(title)} — DFD CRR Officer Operations Manual</title>
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>

  <header class="site-header">
    <button class="menu-toggle" aria-label="Toggle navigation">☰</button>
    <a href="index.html" class="header-brand">
      <span class="header-badge">DFD</span>
      <span class="header-title">CRR Officer Operations Manual</span>
    </a>
    <span class="header-subtitle">v0.2 — March 2026</span>
  </header>

  <nav class="sidebar">
    {sidebar_html}
  </nav>
  <div class="sidebar-overlay"></div>

  <main class="main-content">
    <div class="content-wrapper">
      {content_html}
      {nav_html}
    </div>
    <footer class="site-footer">
      Denton Fire Department — CRR Officer Operations Manual v0.2 — March 2026<br>
      Prepared by Captain Hunter Lott, Community Risk Reduction Officer
    </footer>
  </main>

  <script src="assets/nav.js"></script>
</body>
</html>'''


# ═══════════════════════════════════════════
# BUILD INDEX PAGE (special)
# ═══════════════════════════════════════════
def build_index(preface_md):
    """Build the index/home page with cover and preface content."""
    cover_html = '''
<div class="cover-hero">
  <div class="cover-dept">Denton Fire Department — Support Services Division</div>
  <h1>CRR Officer<br>Operations Manual</h1>
  <div class="cover-divider"></div>
  <div class="cover-subtitle">Position Pass-Down Guide &amp; Standard Operating Procedures</div>
  <div class="cover-version">Version 0.2 &nbsp;|&nbsp; March 2026</div>
  <div class="cover-notice">
    This document contains operational procedures and institutional knowledge for the
    CRR Officer position. Handle in accordance with department information security policies.
  </div>
</div>
'''
    
    # Parse preface content (skip the title line and some boilerplate)
    preface_lines = preface_md.split('\n')
    # Find the "Preface" heading and take content from there
    preface_start = 0
    for idx, line in enumerate(preface_lines):
        if 'Preface: How to Use This Manual' in line:
            preface_start = idx
            break
    
    preface_content = '\n'.join(preface_lines[preface_start:])
    # Remove TABLE OF CONTENTS line
    preface_content = preface_content.replace('**TABLE OF CONTENTS**', '')
    # Remove PART header blocks at the end
    for part_header in ['**PART I**', '**PART II**', '**PART III**', '**PART IV**', '**PART V**', '**PART VI**']:
        if part_header in preface_content:
            preface_content = preface_content[:preface_content.index(part_header)]
    
    content_html = md_to_html(preface_content)
    
    # Add TOC
    toc_html = '''
<h2 id="table-of-contents">Table of Contents</h2>

<h3>Part I: Foundation</h3>
<ul>
  <li><a href="ch01.html">Chapter 1: Denton Fire Department Overview</a></li>
  <li><a href="ch02.html">Chapter 2: Position Overview</a></li>
  <li><a href="ch03.html">Chapter 3: Key Relationships and Partners</a></li>
</ul>

<h3>Part II: Community Risk Reduction Operations</h3>
<ul>
  <li><a href="ch04.html">Chapter 4: CRR Strategy and Program Framework</a></li>
  <li><a href="ch05.html">Chapter 5: Public Education Delivery</a></li>
  <li><a href="ch06.html">Chapter 6: CRR Newsletters</a></li>
  <li><a href="ch07.html">Chapter 7: CRR Technology Tools</a></li>
</ul>

<h3>Part III: Recruitment &amp; Hiring Operations</h3>
<ul>
  <li><a href="ch08.html">Chapter 8: Civil Service Framework</a></li>
  <li><a href="ch09.html">Chapter 9: The Hiring Process</a></li>
  <li><a href="ch10.html">Chapter 10: Candidate Pipeline and Outreach</a></li>
  <li><a href="ch11.html">Chapter 11: Special Programs and Future Initiatives</a></li>
</ul>

<h3>Part IV: Administrative Operations</h3>
<ul>
  <li><a href="ch12.html">Chapter 12: Budget and Financial Management</a></li>
  <li><a href="ch13.html">Chapter 13: Weekly Reporting</a></li>
  <li><a href="ch14.html">Chapter 14: Quarterly Program Appraisals</a></li>
  <li><a href="ch15.html">Chapter 15: Accreditation Support and Pension Board Duties</a></li>
</ul>

<h3>Part V: Technology &amp; Systems</h3>
<ul>
  <li><a href="ch16.html">Chapter 16: Digital Platforms &amp; Infrastructure</a></li>
  <li><a href="ch17.html">Chapter 17: System Administration &amp; Succession Planning</a></li>
</ul>

<h3>Appendices</h3>
<ul>
  <li><a href="app-a.html">Appendix A: Quick Reference Cards</a></li>
  <li><a href="app-b.html">Appendix B: CRR Tools Documentation</a></li>
  <li><a href="app-c.html">Appendix C: Newsletter Archive Reference</a></li>
  <li><a href="app-d.html">Appendix D: Contact Directory</a></li>
  <li><a href="app-e.html">Appendix E: Document Version History</a></li>
  <li><a href="app-f.html">Appendix F: Email Templates</a></li>
  <li><a href="app-g.html">Appendix G: Vendor Reference Guide</a></li>
  <li><a href="app-h.html">Appendix H: CRR Annual Calendar</a></li>
  <li><a href="app-i.html">Appendix I: Recruiting Annual Calendar</a></li>
</ul>
'''
    
    return cover_html + content_html + toc_html


# ═══════════════════════════════════════════
# PAT UPDATE CONTENT (new for v0.2)
# ═══════════════════════════════════════════
PAT_UPDATE_HTML = '''
<h2 id="9-5-step-4-physical-ability-test-pat">9.5 Step 4: Physical Ability Test (PAT)</h2>

<p>The Physical Ability Test is a timed physical assessment of candidate fitness for firefighting duties. The CRR Officer manages all PAT logistics including equipment procurement, venue coordination, staffing, preparation programs, and results documentation. The PAT is administered per the Denton Fire Department Physical Ability Test Instructor Guide.</p>

<h3 id="9-5-1-pat-course-events">9.5.1 PAT Course Events</h3>

<p>The DFD PAT consists of a stair climb (Event 1) followed by five sequential events (Events 2–6). Candidates wear a 50 lb weighted vest throughout. During Event 1, candidates also wear two 12.5 lb shoulder weights. Event 1 and Events 2–6 are timed separately. Remaining time from Event 1 does not carry over to Events 2–6.</p>

<div class="table-wrapper"><table>
<thead><tr><th>Event</th><th>Time Limit</th><th>Description</th></tr></thead>
<tbody>
<tr><td><strong>Event 1</strong></td><td>4:00</td><td>Stair Climb: 3-story stairwell to 4th floor landing, 3 times. 50 lb vest + two 12.5 lb shoulder weights.</td></tr>
<tr><td><strong>Rest Period</strong></td><td>1:30 max</td><td>Between Event 1 and Events 2–6. Transfer shoulder weights to proctor; retain 50 lb vest.</td></tr>
<tr><td><strong>Event 2</strong></td><td>—</td><td>Ladder Raise &amp; Extension: Walk 24ft ladder hand-over-hand, then extend fly section via halyard.</td></tr>
<tr><td><strong>Event 3</strong></td><td>—</td><td>Equipment Carry: Remove two saws, carry 75ft, 180° turn, carry back, replace in compartment.</td></tr>
<tr><td><strong>Event 4</strong></td><td>—</td><td>1-3/4″ Hose Drag: Advance charged hose line, then pull 50ft into marked area from one knee.</td></tr>
<tr><td><strong>Event 5</strong></td><td>—</td><td>Sledge Swing: Swing sledge in chopping motion to move weighted object ~5 feet.</td></tr>
<tr><td><strong>Event 6</strong></td><td>—</td><td>Rescue: Drag ~165 lb mannequin 35ft, 180° around drum, 35ft back to finish.</td></tr>
<tr><td><strong>Events 2–6 Total</strong></td><td><strong>5:30</strong></td><td>Continuous clock across all five events including walking between stations.</td></tr>
</tbody></table></div>

<p><strong>PPE Note:</strong> Candidates wear department-issued helmets and 50 lb weighted vests. Candidates may bring their own gloves; thin gardening or cotton gloves are not permitted. Only one small vest is available, so the waiting line instructor may need to adjust candidate order based on sizing. If a candidate's helmet falls off during an event, allow them to finish the current event before having them put it back on.</p>

<h3 id="9-5-2-staffing-requirements">9.5.2 Staffing Requirements</h3>

<p>PAT events require careful staffing coordination. The CRR Officer serves as lead coordinator for both Practice and Official PAT events.</p>

<div class="table-wrapper"><table>
<thead><tr><th>Role</th><th>Practice PAT</th><th>Official PAT</th><th>Notes</th></tr></thead>
<tbody>
<tr><td>CRR Officer</td><td>1</td><td>1</td><td>Lead coordinator</td></tr>
<tr><td>OT Staff</td><td>0</td><td>4</td><td>Budget-dependent</td></tr>
<tr><td>On-Duty Crews</td><td>As available</td><td>As available</td><td>Per station availability</td></tr>
<tr><td><strong>Minimum Total (Official)</strong></td><td>—</td><td><strong>7</strong></td><td>Hard minimum per Instructor Guide</td></tr>
</tbody></table></div>

<div class="callout callout-warning">
<div class="callout-title">⚠ Budget Note</div>
In FY 25-26, budget constraints eliminated OT for the Practice PAT. Only on-duty crews were used. OT was hired only for the Official PAT (CRR Officer + 4 OT). Future years should budget OT for both events if possible.
</div>

<h3 id="instructor-positions">Instructor Positions</h3>

<p>The following positions should be staffed during the Official PAT. The Instructor Guide provides detailed responsibilities for each role:</p>

<div class="table-wrapper"><table>
<thead><tr><th>Position</th><th>Count</th><th>Responsibilities</th></tr></thead>
<tbody>
<tr><td>Rovers</td><td>2</td><td>Parking/initial contact; rove between waiting line and events 2–6</td></tr>
<tr><td>Waiting Line</td><td>1</td><td>Check-in, gear sizing, glove evaluation. Manage single small vest.</td></tr>
<tr><td>Stair Climb (Bottom)</td><td>1</td><td>Start timer, enforce no handrails, transfer shoulder weights</td></tr>
<tr><td>Stair Climb (4th Floor)</td><td>1</td><td>Enforce no handrails, confirm wall touch on landing</td></tr>
<tr><td>Walking Instructors</td><td>2–3</td><td>Stay with one candidate through rest period and Events 2–6. Start/record times.</td></tr>
</tbody></table></div>

<h3 id="9-5-3-practice-pat">9.5.3 Practice PAT</h3>

<p>A Practice PAT is held approximately one month before the Official PAT to familiarize candidates with the course layout, events, and pacing. This is not a scored event — it is a preparation opportunity.</p>

<p><strong>FY 25-26 Practice PAT:</strong> Held approximately late January/early February 2026. Originally scheduled for January 31 but rescheduled to February 7 due to ice/sub-freezing conditions at the Station 7 training facility. Staffed with CRR Officer and on-duty crews only (no OT due to budget).</p>

<p><strong>Practice PAT Attendance:</strong> 27 of 40 candidates (68%) attended the Practice PAT. Attendance is tracked on the PAT spreadsheet (column H).</p>

<div class="callout callout-warning">
<div class="callout-title">⚠ Weather Note</div>
PAT events are weather-dependent. Always identify a backup date and communicate rescheduling promptly to candidates and staff.
</div>

<h3 id="9-5-4-official-pat-results">9.5.4 Official PAT — FY 25-26 Results</h3>

<p><strong>Date:</strong> February 28, 2026<br>
<strong>Location:</strong> Station 7 Training Facility<br>
<strong>Candidates Tested:</strong> 40 (39 tested, 1 DNS)<br>
<strong>Passed:</strong> 33<br>
<strong>Failed:</strong> 6 (Chapman, Blancas, Kirkland, Krahl, Munger, Woodall)<br>
<strong>DNS:</strong> 1 (Honea)</p>

<p>Results listed by Civil Service Test Rank. Event 1 limit: 4:00. Events 2–6 limit: 5:30. Failed/DNS candidates shown in bold.</p>

<div class="table-wrapper"><table>
<thead><tr><th>Rank</th><th>Name</th><th>Event 1</th><th>Evt 2-6</th><th>Result</th><th>Practice</th></tr></thead>
<tbody>
<tr><td>1</td><td>Townsley, Reece</td><td>2:34</td><td>3:01</td><td>Pass</td><td>✓</td></tr>
<tr><td>2</td><td>Sukach, George William</td><td>3:15</td><td>3:51</td><td>Pass</td><td>✓</td></tr>
<tr><td>3</td><td>Jeffries, Tallon A</td><td>2:49</td><td>3:51</td><td>Pass</td><td>✓</td></tr>
<tr><td>4</td><td>Melgares, Emerson Alexander</td><td>2:45</td><td>3:30</td><td>Pass</td><td>✓</td></tr>
<tr><td>6</td><td>Wiseman, Stephen Conner</td><td>2:35</td><td>3:29</td><td>Pass</td><td>✓</td></tr>
<tr><td>7</td><td>Hudson, Declan</td><td>2:45</td><td>3:51</td><td>Pass</td><td>✓</td></tr>
<tr><td>8</td><td>Lewis, Hunter G</td><td>2:33</td><td>3:51</td><td>Pass</td><td>✓</td></tr>
<tr><td>13</td><td>Ivey V, Ben Curtis</td><td>3:13</td><td>5:51</td><td>Pass</td><td>✓</td></tr>
<tr class="row-fail"><td>14</td><td>Chapman, Tyler Wade</td><td>2:51</td><td>—</td><td>FAIL</td><td>—</td></tr>
<tr><td>15</td><td>Brewer, Jordan T.</td><td>2:41</td><td>—</td><td>Pass</td><td>—</td></tr>
<tr><td>17</td><td>Rowan, Ryan Christopher</td><td>2:18</td><td>3:15</td><td>Pass</td><td>✓</td></tr>
<tr><td>18</td><td>Templeton, Lucien R</td><td>3:10</td><td>3:35</td><td>Pass</td><td>—</td></tr>
<tr><td>19</td><td>Gibbons, Eric Chandler</td><td>5:03</td><td>5:09</td><td>Pass</td><td>✓</td></tr>
<tr><td>20</td><td>Howard, Hunter</td><td>3:05</td><td>—</td><td>Pass</td><td>✓</td></tr>
<tr><td>21</td><td>Britten, Caden M</td><td>3:26</td><td>3:07</td><td>Pass</td><td>✓</td></tr>
<tr><td>22</td><td>Muruaga, Javier</td><td>3:45</td><td>3:43</td><td>Pass</td><td>✓</td></tr>
<tr><td>27</td><td>Reid, Jared M</td><td>3:01</td><td>4:23</td><td>Pass</td><td>✓</td></tr>
<tr><td>29</td><td>Nicks, Cooper Alexander</td><td>2:51</td><td>4:44</td><td>Pass</td><td>✓</td></tr>
<tr class="row-fail"><td>30</td><td>Blancas, Adriana</td><td>2:28</td><td>3:20</td><td>FAIL</td><td>—</td></tr>
<tr><td>31</td><td>Torres, Zachary B</td><td>3:08</td><td>5:30</td><td>Pass</td><td>—</td></tr>
<tr><td>33</td><td>Bormes, Logan M</td><td>2:41</td><td>3:05</td><td>Pass</td><td>✓</td></tr>
<tr><td>34</td><td>Brown, Jared</td><td>2:46</td><td>4:57</td><td>Pass</td><td>✓</td></tr>
<tr><td>35</td><td>Cooper, Clayton</td><td>2:47</td><td>—</td><td>Pass</td><td>✓</td></tr>
<tr class="row-fail"><td>37</td><td>Kirkland, Talon R</td><td>3:35</td><td>—</td><td>FAIL</td><td>✓</td></tr>
<tr class="row-fail"><td>38</td><td>Krahl, Emilee</td><td>3:36</td><td>4:25</td><td>FAIL</td><td>✓</td></tr>
<tr><td>44</td><td>Buchanan, Jake Stephen</td><td>3:06</td><td>—</td><td>Pass</td><td>✓</td></tr>
<tr><td>46</td><td>Sumaya, Ray</td><td>3:12</td><td>—</td><td>Pass</td><td>—</td></tr>
<tr><td>48</td><td>Birkinsha, Brandon River</td><td>3:06</td><td>4:26</td><td>Pass</td><td>✓</td></tr>
<tr><td>49</td><td>Carlisle, Pudge L.D.</td><td>—</td><td>—</td><td>Pass</td><td>—</td></tr>
<tr><td>50</td><td>Hartman, Joshuah Jordan</td><td>3:20</td><td>4:26</td><td>Pass</td><td>—</td></tr>
<tr class="row-dns"><td>53</td><td>Honea, Donny Zayne</td><td>DNS</td><td>DNS</td><td>DNS</td><td>—</td></tr>
<tr class="row-fail"><td>54</td><td>Munger, Caleb Thomas</td><td>2:33</td><td>4:40</td><td>FAIL</td><td>—</td></tr>
<tr><td>56</td><td>Roberts, Jorin Haskell</td><td>2:48</td><td>3:55</td><td>Pass</td><td>—</td></tr>
<tr><td>57</td><td>Barzyk, Gavin</td><td>3:09</td><td>3:36</td><td>Pass</td><td>✓</td></tr>
<tr><td>59</td><td>Combs, Ethan</td><td>3:53</td><td>5:15</td><td>Pass</td><td>—</td></tr>
<tr><td>61</td><td>Hall, Bradley Ray</td><td>2:37</td><td>3:31</td><td>Pass</td><td>✓</td></tr>
<tr><td>62</td><td>Helterbrand, Cole</td><td>2:59</td><td>4:18</td><td>Pass</td><td>✓</td></tr>
<tr><td>63</td><td>Lewter, Carson Clay</td><td>2:37</td><td>—</td><td>Pass</td><td>✓</td></tr>
<tr class="row-fail"><td>65</td><td>Woodall, Kolby Todd</td><td>2:55</td><td>4:13</td><td>FAIL</td><td>—</td></tr>
<tr><td>66</td><td>Counts, Tyler R</td><td>2:58</td><td>—</td><td>Pass</td><td>✓</td></tr>
</tbody></table></div>

<p><strong>Pass Rate:</strong> 82.5% (33 of 40 total; 84.6% of the 39 who tested). The top 20 passing candidates by test rank advance to the FINAL eligibility list for panel interviews. Demographic data (EMS cert, Fire cert, Race/Ethnicity, Gender) is recorded on the FINAL tab of the PAT tracking spreadsheet.</p>

<h3 id="9-5-5-pat-equipment-and-budget">9.5.5 PAT Equipment &amp; Budget</h3>

<p><strong>Budget Account:</strong> 320100.7826 (Diversity) — PAT equipment purchased from this account</p>

<p>FY 25-26 PAT Equipment Purchases:</p>
<ul>
<li>Sled for PAT practice — $351.44 (320100.7826)</li>
<li>Weights for PAT practice — $320.66 (320100.7826)</li>
</ul>

<h3 id="9-5-6-pat-administrative-checklist">9.5.6 PAT Administrative Checklist</h3>

<ol>
<li>Schedule Practice PAT (~1 month before Official PAT)</li>
<li>Request OT support from Operations (budget permitting)</li>
<li>Coordinate on-duty crew availability for both events</li>
<li>Inspect all PAT equipment (sled, weights, vests, helmets, mannequin, hose, ladder)</li>
<li>Send Practice PAT notification email to all eligible candidates</li>
<li>Conduct Practice PAT — record attendance</li>
<li>Send Official PAT notification with date, time, location, and instructions</li>
<li>Brief all instructors on positions and responsibilities (use Instructor Guide)</li>
<li>Conduct Official PAT — record all times and pass/fail results</li>
<li>Update PAT tracking spreadsheet (PAT tab and FINAL tab)</li>
<li>Communicate results to candidates and advance passers in NEOGOV</li>
<li>Populate FINAL eligibility list with top passing candidates and demographic data</li>
</ol>

<h3 id="9-5-7-reference-documents">9.5.7 Reference Documents</h3>

<ul>
<li>Denton Fire Department Physical Ability Test Instructor Guide (.docx)</li>
<li>PAT Tracking Spreadsheet: PAT_02_28_26.xlsx (PAT tab + FINAL tab)</li>
<li>Civil Service Test Registration File: 2026_DFD_Civil_Service_Test_Registration_FINAL.xlsx</li>
<li>DFD Hiring Guidelines (Rev. 10/20/2021)</li>
</ul>
'''


# ═══════════════════════════════════════════
# MAIN BUILD
# ═══════════════════════════════════════════
def build():
    sections = split_manual()
    
    print(f"Split manual into {len(sections)} sections")
    
    for pg_idx in range(len(PAGES)):
        filename, label, section_label, pattern, part = PAGES[pg_idx]
        
        # Previous/next
        prev_page = (PAGES[pg_idx-1][0], PAGES[pg_idx-1][1]) if pg_idx > 0 else None
        next_page = (PAGES[pg_idx+1][0], PAGES[pg_idx+1][1]) if pg_idx < len(PAGES) - 1 else None
        
        if filename == 'index.html':
            content_html = build_index(sections.get(0, ''))
            title = 'Home'
        else:
            md_content = sections.get(pg_idx, '')
            if not md_content:
                print(f"  ⚠ No content for {filename}")
                continue
            
            # For Chapter 9, inject PAT update
            if filename == 'ch09.html':
                # Replace the old PAT section (9.5) with the new one
                # Find 9.5 and 9.6 boundaries
                lines = md_content.split('\n')
                pat_start = None
                pat_end = None
                for li, line in enumerate(lines):
                    if '## **9.5 Step 4: Physical Ability Test' in line:
                        pat_start = li
                    if '## **9.6 Step 5: Panel Interviews' in line and pat_start is not None:
                        pat_end = li
                        break
                
                if pat_start is not None and pat_end is not None:
                    before = '\n'.join(lines[:pat_start])
                    after = '\n'.join(lines[pat_end:])
                    before_html = md_to_html(before)
                    after_html = md_to_html(after)
                    content_html = before_html + PAT_UPDATE_HTML + after_html
                else:
                    content_html = md_to_html(md_content)
            else:
                content_html = md_to_html(md_content)
            
            title = label
        
        html = page_template(title, content_html, filename, prev_page, next_page)
        
        out_path = SITE_DIR / filename
        with open(out_path, 'w') as f:
            f.write(html)
        print(f"  ✅ {filename} ({len(content_html)} chars)")
    
    print(f"\n✅ Site built: {len(PAGES)} pages in {SITE_DIR}")


if __name__ == '__main__':
    build()
