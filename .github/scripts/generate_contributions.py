#!/usr/bin/env python3
import json
import os
import urllib.request
from datetime import date, datetime, timedelta
from html import escape

USERNAME = os.environ.get("GITHUB_REPOSITORY_OWNER", "rayhanrinzan")
URL = f"https://github-contributions-api.jogruber.de/v4/{USERNAME}?y=last"

req = urllib.request.Request(
    URL,
    headers={"User-Agent": f"{USERNAME}-profile-contributions/1.0"},
)
with urllib.request.urlopen(req, timeout=30) as response:
    data = json.load(response)

items = sorted(data["contributions"], key=lambda item: item["date"])
if not items:
    raise SystemExit("No contribution data returned")

total = data.get("total", {}).get("lastYear")
if total is None:
    total = sum(item["count"] for item in items)

by_date = {
    datetime.strptime(item["date"], "%Y-%m-%d").date(): item
    for item in items
}

first = min(by_date)
last = max(by_date)
start = first - timedelta(days=(first.weekday() + 1) % 7)
end = last + timedelta(days=(6 - ((last.weekday() + 1) % 7)))
weeks = ((end - start).days // 7) + 1

CELL = 10
GAP = 3
STEP = CELL + GAP
LEFT = 34
TOP = 49
WIDTH = LEFT + weeks * STEP + 18
HEIGHT = TOP + 7 * STEP + 28

themes = {
    "dark": {
        "title": "#f0f6fc",
        "muted": "#8b949e",
        "empty": "#161b22",
        "empty_stroke": "#30363d",
        "levels": ["#0e4429", "#006d32", "#26a641", "#39d353"],
    },
    "light": {
        "title": "#1f2328",
        "muted": "#57606a",
        "empty": "#ebedf0",
        "empty_stroke": "#d0d7de",
        "levels": ["#9be9a8", "#40c463", "#30a14e", "#216e39"],
    },
}

def week_index(day):
    return (day - start).days // 7

def sunday_row(day):
    return (day.weekday() + 1) % 7

def svg_for(theme):
    c = themes[theme]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="{total:,} contributions in the last year">',
        '<style>text{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}</style>',
        f'<text x="{LEFT}" y="18" fill="{c["title"]}" font-size="14" font-weight="600">{total:,} contributions in the last year</text>',
    ]

    # Month labels, spaced to avoid collisions.
    last_label_x = -999
    cursor = date(start.year, start.month, 1)
    if cursor < start:
        if cursor.month == 12:
            cursor = date(cursor.year + 1, 1, 1)
        else:
            cursor = date(cursor.year, cursor.month + 1, 1)

    while cursor <= end:
        x = LEFT + week_index(cursor) * STEP
        if x - last_label_x >= 34:
            parts.append(
                f'<text x="{x}" y="39" fill="{c["muted"]}" font-size="10">{cursor.strftime("%b")}</text>'
            )
            last_label_x = x
        if cursor.month == 12:
            cursor = date(cursor.year + 1, 1, 1)
        else:
            cursor = date(cursor.year, cursor.month + 1, 1)

    # Weekday labels.
    for label, row in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
        y = TOP + row * STEP + 9
        parts.append(
            f'<text x="0" y="{y}" fill="{c["muted"]}" font-size="9">{label}</text>'
        )

    # Calendar cells.
    day = start
    while day <= end:
        col = week_index(day)
        row = sunday_row(day)
        x = LEFT + col * STEP
        y = TOP + row * STEP
        item = by_date.get(day)
        if item is None:
            count = 0
            level = 0
        else:
            count = int(item.get("count", 0))
            level = int(item.get("level", 0))

        if level <= 0:
            fill = c["empty"]
            stroke = c["empty_stroke"]
        else:
            fill = c["levels"][min(level, 4) - 1]
            stroke = fill

        noun = "contribution" if count == 1 else "contributions"
        tooltip = escape(f"{count} {noun} on {day.strftime('%b %d, %Y')}")
        parts.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{fill}" stroke="{stroke}" stroke-width="0.5"><title>{tooltip}</title></rect>'
        )
        day += timedelta(days=1)

    # Minimal legend.
    legend_y = HEIGHT - 9
    legend_x = WIDTH - 118
    parts.append(
        f'<text x="{legend_x}" y="{legend_y}" fill="{c["muted"]}" font-size="9">Less</text>'
    )
    sx = legend_x + 25
    legend_colors = [c["empty"]] + c["levels"]
    for i, fill in enumerate(legend_colors):
        stroke = c["empty_stroke"] if i == 0 else fill
        parts.append(
            f'<rect x="{sx + i * 13}" y="{legend_y - 9}" width="9" height="9" rx="2" fill="{fill}" stroke="{stroke}" stroke-width="0.5"/>'
        )
    parts.append(
        f'<text x="{sx + 68}" y="{legend_y}" fill="{c["muted"]}" font-size="9">More</text>'
    )

    parts.append("</svg>")
    return "\n".join(parts) + "\n"

os.makedirs("assets", exist_ok=True)
for theme in ("dark", "light"):
    with open(f"assets/contributions-{theme}.svg", "w", encoding="utf-8") as f:
        f.write(svg_for(theme))

print(f"Generated contribution cards for {USERNAME}: {total:,} contributions")
