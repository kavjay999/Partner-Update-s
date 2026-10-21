#!/usr/bin/env python3
"""Pulls Microsoft Partner Center announcements and rebuilds the site.

Source: https://learn.microsoft.com/en-us/partner-center/announcements/
Uses Microsoft Learn's own Markdown version of the page (?accept=text/markdown),
so there is no fragile HTML scraping. Standard library only.

Outputs (next to this script):
  news.json   machine-readable list of announcements
  index.html  the mobile-friendly site people see
"""
import hashlib
import html
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SOURCE = "https://learn.microsoft.com/en-us/partner-center/announcements/"
MD_URL = SOURCE + "?accept=text/markdown"
HERE = Path(__file__).parent
MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], 1)}

SECTION_RE = re.compile(r"([A-Za-z]+)\s+(\d{4})\s+announcements", re.I)
LINK_RE = re.compile(r"\[(.*)\]\((https?://[^)\s]+)\)")
DATE_RE = re.compile(r"([A-Za-z]+)\s+(\d{1,2})")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "PartnerNewsBot/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def parse(md):
    items, year, month = [], None, None
    canon = {}  # merge "Account Settings"/"Account settings" etc.
    for line in md.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        sec = SECTION_RE.search(cells[1])
        if sec and sec.group(1).title() in MONTHS:
            month, year = MONTHS[sec.group(1).title()], int(sec.group(2))
            continue
        link = LINK_RE.search(cells[1])
        if not link or year is None:
            continue
        d = DATE_RE.search(cells[2])
        if not d or d.group(1).title() not in MONTHS:
            continue
        m, day = MONTHS[d.group(1).title()], int(d.group(2))
        y = year - 1 if (m == 12 and month == 1) else year
        items.append({
            "title": link.group(1).replace("\u200b", "").strip(),
            "url": link.group(2),
            "workspace": canon.setdefault(cells[0].casefold(), cells[0][:1].upper() + cells[0][1:]),
            "date": f"{y:04d}-{m:02d}-{day:02d}",
            "note": cells[2],
        })
    items.sort(key=lambda i: i["date"], reverse=True)
    return items


def render(items, updated, config):
    rows = []
    for i in items:
        d = datetime.strptime(i["date"], "%Y-%m-%d")
        rows.append(
            f'<a class="card" href="{html.escape(i["url"])}" target="_blank" rel="noopener" '
            f'data-ws="{html.escape(i["workspace"])}">'
            f'<span class="meta"><b>{html.escape(i["workspace"])}</b> · '
            f'{d.strftime("%d %b %Y").lstrip("0")}</span>'
            f'<span class="t">{html.escape(i["title"])}</span></a>')
    workspaces = sorted({i["workspace"] for i in items})
    chips = "".join(f'<button class="chip" data-f="{html.escape(w)}">{html.escape(w)}</button>'
                    for w in workspaces)
    brand = html.escape(config.get("brand", "Microsoft Partner News"))
    wa = config.get("whatsapp_channel_url", "").strip()
    follow = (f'<a class="wa" href="{html.escape(wa)}" target="_blank" rel="noopener">'
              f'Follow on WhatsApp</a>') if wa else ""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{brand}</title>
<meta name="description" content="Latest Microsoft Partner Center announcements, updated automatically.">
<style>
:root{{--bg:#f6f7f9;--fg:#15181d;--card:#fff;--mut:#5d6672;--acc:#0b6bcb;--bd:#e2e5ea}}
@media(prefers-color-scheme:dark){{:root{{--bg:#101215;--fg:#eceff3;--card:#1a1d22;--mut:#9aa4b2;--acc:#5aa9ff;--bd:#2a2e35}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.45 system-ui,sans-serif}}
main{{max-width:720px;margin:0 auto;padding:16px}}
h1{{font-size:1.4rem;margin:8px 0 2px}}.sub{{color:var(--mut);font-size:.85rem;margin:0 0 14px}}
.wa{{display:inline-block;background:#25d366;color:#04210f;font-weight:600;text-decoration:none;padding:10px 16px;border-radius:999px;margin:0 0 14px}}
input{{width:100%;padding:12px;border-radius:10px;border:1px solid var(--bd);background:var(--card);color:var(--fg);font:inherit;margin-bottom:10px}}
.chips{{display:flex;gap:6px;overflow-x:auto;padding-bottom:10px}}
.chip{{flex:none;border:1px solid var(--bd);background:var(--card);color:var(--fg);border-radius:999px;padding:6px 12px;font:inherit;font-size:.85rem}}
.chip.on{{background:var(--acc);border-color:var(--acc);color:#fff}}
.card{{display:block;background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:12px 14px;margin-bottom:10px;text-decoration:none;color:inherit}}
.meta{{display:block;font-size:.78rem;color:var(--mut);margin-bottom:2px}}.t{{display:block;font-weight:600}}
.card:active{{border-color:var(--acc)}}
#more{{display:block;margin:6px auto 18px;padding:10px 18px;border-radius:999px;border:1px solid var(--bd);background:var(--card);color:var(--fg);font:inherit}}
footer{{color:var(--mut);font-size:.75rem;padding:8px 0 24px}}footer a{{color:var(--acc)}}
</style></head><body><main>
<h1>{brand}</h1>
<p class="sub">Latest Partner Center announcements · updated {updated}</p>
{follow}
<input id="q" type="search" placeholder="Search announcements" aria-label="Search">
<div class="chips"><button class="chip on" data-f="">All</button>{chips}</div>
<div id="list">{"".join(rows)}</div>
<button id="more">Show more</button>
<footer>Unofficial feed. All content belongs to Microsoft. Source:
<a href="{SOURCE}">Partner Center announcements</a>.</footer>
</main>
<script>
var cards=[].slice.call(document.querySelectorAll('.card')),q=document.getElementById('q'),
more=document.getElementById('more'),f='',limit=25;
function apply(){{var t=q.value.toLowerCase(),shown=0,match=0;
cards.forEach(function(c){{var ok=(!f||c.dataset.ws===f)&&c.textContent.toLowerCase().indexOf(t)>-1;
if(ok)match++;var vis=ok&&shown<limit;if(vis)shown++;c.style.display=vis?'':'none'}});
more.style.display=match>shown?'':'none'}}
q.oninput=function(){{limit=25;apply()}};
more.onclick=function(){{limit+=25;apply()}};
document.querySelectorAll('.chip').forEach(function(b){{b.onclick=function(){{
document.querySelectorAll('.chip').forEach(function(x){{x.classList.remove('on')}});
b.classList.add('on');f=b.dataset.f;limit=25;apply()}}}});
apply();
</script></body></html>
"""


def main():
    config_path = HERE / "config.json"
    config = json.loads(config_path.read_text()) if config_path.exists() else {}
    try:
        items = parse(fetch(MD_URL))
    except Exception as e:  # network/HTTP error: keep the existing site untouched
        print(f"Fetch failed: {e}", file=sys.stderr)
        return 1
    if len(items) < 10:  # page layout probably changed; do not wipe the site
        print(f"Only parsed {len(items)} items; refusing to overwrite.", file=sys.stderr)
        return 1

    items = items[: config.get("max_items", 150)]
    digest = hashlib.sha256(json.dumps(items, sort_keys=True).encode()).hexdigest()
    json_path = HERE / "news.json"
    if json_path.exists():
        try:
            if json.loads(json_path.read_text()).get("digest") == digest:
                print("No changes.")
                return 0
        except Exception:
            pass

    updated = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC").lstrip("0")
    json_path.write_text(json.dumps(
        {"digest": digest, "updated": updated, "source": SOURCE, "items": items},
        indent=2, ensure_ascii=False))
    (HERE / "index.html").write_text(render(items, updated, config), encoding="utf-8")
    print(f"Updated: {len(items)} announcements, newest {items[0]['date']}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
