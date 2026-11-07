#!/usr/bin/env python3
"""
update_heatmap.py - Daily automated runner for GitHub Actions.
Scrapes https://github.com/users/Shreeprasandh/contributions and updates contrib-heatmap.svg
with:
- 4-month calendar slice (17 weeks).
- Uniform #384656 active color for both 0-commit and 1-commit days.
- Smooth cinematic animation: 0.65s duration, out-expo deceleration cubic-bezier(0.16, 1, 0.3, 1),
  gentle diagonal wave cascade.
- Top-aligned single-line motto: "Taming codes, crafting experiences."
- Repositories count (19).
Zero external dependencies (uses standard library only).
"""

import html
import os
import re
import urllib.request

USERNAME = "Shreeprasandh"
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT_SVG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "contrib-heatmap.svg")

BG_DARK = "#0d1117"
BG_GRAD = "#161b22"
FRAME = "#30363d"
TITLE_TEXT = "#8b949e"
MUTED = "#6e7681"
INK = "#c9d1d9"
HIGHLIGHT = "#f0f6fc"

COLOR_0_AND_1 = "#384656"
HEATMAP_TIERS = [
    "#384656",  # 0 & 1 commit (uniform active baseline)
    "#5e7188",  # 2-8 commits
    "#92a8c0",  # 9-18 commits
    "#f0f6fc",  # 19-53 commits (peak radiant silver)
]

def fetch_contributions():
    req = urllib.request.Request(
        URL,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    )
    with urllib.request.urlopen(req) as response:
        return response.read().decode("utf-8")

def generate_svg(raw_html):
    total_match = re.search(r'([\d,]+)\s+contributions\s+in the last year', raw_html)
    total_contribs = total_match.group(1) if total_match else "1,220"

    tooltips = re.findall(r'<tool-tip[^>]*for=\"([^\"]+)\"[^>]*>(.*?)</tool-tip>', raw_html)
    tt_map = {k: v.strip() for k, v in tooltips}

    tbody_match = re.search(r'<tbody>(.*?)</tbody>', raw_html, re.DOTALL)
    if not tbody_match:
        print("[Error] Failed to find tbody in contributions HTML")
        return

    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tbody_match.group(1), re.DOTALL)
    grid = []
    for r in rows:
        td_matches = re.findall(r'<td\s+([^>]+)>', r)
        row_cells = []
        for td_attrs in td_matches:
            d_m = re.search(r'data-date=\"([^\"]+)\"', td_attrs)
            lvl_m = re.search(r'data-level=\"([^\"]+)\"', td_attrs)
            id_m = re.search(r'id=\"([^\"]+)\"', td_attrs)
            if d_m and lvl_m:
                date = d_m.group(1)
                lvl = int(lvl_m.group(1))
                cid = id_m.group(1) if id_m else ''
                tip = tt_map.get(cid, f"{lvl} level on {date}")
                row_cells.append((date, lvl, tip))
        grid.append(row_cells)

    WEEKS_TO_SHOW = 17
    total_weeks = len(grid[0])
    start_week = max(0, total_weeks - WEEKS_TO_SHOW)

    sliced_grid = []
    for r in grid:
        sliced_grid.append(r[start_week:])

    CANVAS_W = 860
    CANVAS_H = 185
    TITLEBAR_H = 28
    PAD = 16

    BOX_SIZE = 11.2
    BOX_GAP = 3.6
    START_X = PAD + 26
    START_Y = TITLEBAR_H + 24

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" '
        f'viewBox="0 0 {CANVAS_W} {CANVAS_H}" font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, \'Courier New\', monospace">',
        f'<style>',
        f'  .cell {{ opacity: 0; animation: cellIn 0.65s cubic-bezier(0.16, 1, 0.3, 1) forwards; }}',
        f'  @keyframes cellIn {{ from {{ opacity: 0; transform: scale(0.5); }} to {{ opacity: 1; transform: scale(1); }} }}',
        f'  .telemetry {{ opacity: 0; animation: fadeIn 0.5s ease forwards; }}',
        f'  @keyframes fadeIn {{ to {{ opacity: 1; }} }}',
        f'</style>',
        f'<defs><linearGradient id="bg_heat" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG_GRAD}"/><stop offset="1" stop-color="{BG_DARK}"/></linearGradient></defs>',
        f'<rect width="{CANVAS_W}" height="{CANVAS_H}" rx="10" fill="url(#bg_heat)"/>',
        f'<rect x="0.5" y="0.5" width="{CANVAS_W-1}" height="{CANVAS_H-1}" rx="10" fill="none" stroke="{FRAME}" stroke-width="1"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{CANVAS_W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>'
    ]

    for i, dotcol in enumerate(['#ff5f56', '#ffbd2e', '#27c93f']):
        parts.append(f'<circle cx="{PAD + i*13}" cy="{TITLEBAR_H/2}" r="4" fill="{dotcol}"/>')

    parts.append(
        f'<text x="{CANVAS_W/2}" y="{TITLEBAR_H/2 + 4}" fill="{TITLE_TEXT}" font-size="11" text-anchor="middle">shreeprasandh@terminal: ~$ ./contributions.sh --horizon 4m</text>'
    )

    day_labels = [("Mon", 1), ("Wed", 3), ("Fri", 5)]
    for lbl, day_idx in day_labels:
        ly = START_Y + day_idx * (BOX_SIZE + BOX_GAP) + 8.5
        parts.append(f'<text x="{PAD}" y="{ly}" fill="{MUTED}" font-size="9.5">{lbl}</text>')

    for day_row in range(len(sliced_grid)):
        cells = sliced_grid[day_row]
        for week_col in range(len(cells)):
            date, lvl, tip = cells[week_col]
            if lvl <= 1:
                col = COLOR_0_AND_1
            elif lvl == 2:
                col = "#5e7188"
            elif lvl == 3:
                col = "#92a8c0"
            else:
                col = "#f0f6fc"

            x = START_X + week_col * (BOX_SIZE + BOX_GAP)
            y = START_Y + day_row * (BOX_SIZE + BOX_GAP)
            delay = 0.08 + (week_col * 0.040) + (day_row * 0.035)

            safe_tip = html.escape(tip)
            parts.append(
                f'<rect class="cell" x="{x:.1f}" y="{y:.1f}" width="{BOX_SIZE:.1f}" height="{BOX_SIZE:.1f}" '
                f'rx="2.2" fill="{col}" style="animation-delay: {delay:.3f}s; transform-origin: {x+BOX_SIZE/2:.1f}px {y+BOX_SIZE/2:.1f}px;">'
                f'<title>{safe_tip}</title></rect>'
            )

    footer_y = CANVAS_H - 14
    parts.append(
        f'<text x="{PAD}" y="{footer_y}" fill="{MUTED}" font-size="9.5">Jul — Nov (4 Months)</text>'
    )

    legend_start = START_X + 115
    parts.append(f'<text x="{legend_start}" y="{footer_y}" fill="{MUTED}" font-size="9">Less</text>')
    legend_swatches = ["#1b222c", "#384656", "#5e7188", "#92a8c0", "#f0f6fc"]
    for i, col in enumerate(legend_swatches):
        lx = legend_start + 28 + i * 11
        parts.append(f'<rect x="{lx}" y="{footer_y - 8}" width="8" height="8" rx="1.5" fill="{col}"/>')
    parts.append(f'<text x="{legend_start + 28 + len(legend_swatches)*11 + 4}" y="{footer_y}" fill="{MUTED}" font-size="9">More</text>')

    DIVIDER_X = 320
    parts.append(
        f'<line x1="{DIVIDER_X}" y1="{TITLEBAR_H + 14}" x2="{DIVIDER_X}" y2="{CANVAS_H - 14}" stroke="{FRAME}" stroke-width="1" stroke-dasharray="3,3"/>'
    )

    RIGHT_X = DIVIDER_X + 24
    motto_y = START_Y + 11.5

    parts.append(
        f'<g class="telemetry" style="animation-delay: 0.25s;">'
        f'<text x="{RIGHT_X}" y="{motto_y:.1f}">'
        f'<tspan fill="{HIGHLIGHT}" font-size="13.5" font-weight="bold" letter-spacing="0.03em">"Taming codes,</tspan> '
        f'<tspan fill="{TITLE_TEXT}" font-size="13.5" font-weight="bold" font-style="italic" letter-spacing="0.03em">crafting experiences."</tspan>'
        f'</text>'
        f'</g>'
    )

    col1_x = RIGHT_X
    col2_x = RIGHT_X + 160
    col3_x = RIGHT_X + 320

    m_y = motto_y + 35
    parts.append(
        f'<g class="telemetry" style="animation-delay: 0.45s;">'
        f'<text x="{col1_x}" y="{m_y:.1f}" fill="{HIGHLIGHT}" font-size="17" font-weight="bold">{total_contribs}</text>'
        f'<text x="{col1_x}" y="{m_y + 13:.1f}" fill="{MUTED}" font-size="9">ANNUAL COMMITS</text>'
        f'<text x="{col2_x}" y="{m_y:.1f}" fill="{INK}" font-size="17" font-weight="bold">129 DAYS</text>'
        f'<text x="{col2_x}" y="{m_y + 13:.1f}" fill="{MUTED}" font-size="9">ACTIVE CADENCE</text>'
        f'<text x="{col3_x}" y="{m_y:.1f}" fill="{INK}" font-size="17" font-weight="bold">19</text>'
        f'<text x="{col3_x}" y="{m_y + 13:.1f}" fill="{MUTED}" font-size="9">REPOSITORIES</text>'
        f'</g>'
    )

    bar_y = m_y + 32
    bar_w = CANVAS_W - RIGHT_X - PAD

    segments = [
        (0.46, "#c9d1d9"),
        (0.24, "#8b949e"),
        (0.18, "#525d6b"),
        (0.12, "#30363d")
    ]

    parts.append(f'<g class="telemetry" style="animation-delay: 0.6s;">')
    cur_x = RIGHT_X
    for pct, col in segments:
        seg_w = bar_w * pct
        parts.append(f'<rect x="{cur_x:.1f}" y="{bar_y:.1f}" width="{seg_w:.1f}" height="6" rx="1.5" fill="{col}"/>')
        cur_x += seg_w

    leg_y = bar_y + 18
    parts.append(
        f'<circle cx="{RIGHT_X + 4}" cy="{leg_y - 3:.1f}" r="3" fill="#c9d1d9"/>'
        f'<text x="{RIGHT_X + 12}" y="{leg_y:.1f}" fill="{INK}" font-size="9">TypeScript</text>'
        f'<circle cx="{RIGHT_X + 105}" cy="{leg_y - 3:.1f}" r="3" fill="#8b949e"/>'
        f'<text x="{RIGHT_X + 113}" y="{leg_y:.1f}" fill="{TITLE_TEXT}" font-size="9">Next.js</text>'
        f'<circle cx="{RIGHT_X + 190}" cy="{leg_y - 3:.1f}" r="3" fill="#525d6b"/>'
        f'<text x="{RIGHT_X + 198}" y="{leg_y}" fill="{MUTED}" font-size="9">Python</text>'
        f'<circle cx="{RIGHT_X + 265}" cy="{leg_y - 3}" r="3" fill="#30363d"/>'
        f'<text x="{RIGHT_X + 273}" y="{leg_y}" fill="{MUTED}" font-size="9">WebGL / Systems</text>'
        f'</g>'
    )

    parts.append('</svg>')

    with open(OUT_SVG, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print(f"[Success] Updated {OUT_SVG} ({os.path.getsize(OUT_SVG)} bytes)")

if __name__ == "__main__":
    html_data = fetch_contributions()
    generate_svg(html_data)
