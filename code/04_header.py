"""Step 4. Render ../header.png (1200x630 social card) with Playwright Chromium.

Fonts: pass a folder holding FrauncesVar.ttf, SourceSerif4-Regular.ttf, IBMPlexMono-Regular.ttf and
IBMPlexMono-Medium.ttf as FONT_DIR (from github.com/google/fonts); otherwise system serif is used.
Coastline: Natural Earth 1:10m land for the British Isles, as extracted for the lighthouse project.
Run: FONT_DIR=/path/to/fonts python3 04_header.py
"""
import json, math, os
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
P = json.load(open(os.path.join(ROOT, "data", "page_data.json")))
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
FD = os.environ.get("FONT_DIR", "")
K = math.cos(math.radians(52.5))
X0, X1, Y0, Y1 = -8.3 * K, 1.9 * K, -58.8, -49.9
Hh = 610; Ww = Hh * (X1 - X0) / (Y1 - Y0)


def pr(lat, lon):
    return (lon * K - X0) / (Y1 - Y0) * Hh, (-lat - Y0) / (Y1 - Y0) * Hh


COAST = os.path.join(ROOT, "..", "did-lighthouses-work", "release", "build", "ne10m_land_british_isles.json")
land = ""
for g in json.load(open(COAST)):
    for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        ring = poly[0]
        if max(q[0] for q in ring) < -10: continue
        land += "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in (pr(q[1], q[0]) for q in ring)) + "Z"
GC = {0: "#7A4E2A", 1: "#1F5A3A", 2: "#B5702A", 3: "#8F8A2C", 9: "#A2402C"}
dots = ""
rows = [dict(zip(P["cols"], r)) for r in P["rows"]]
for r in sorted(rows, key=lambda r: (r["girth"] or 0)):
    x, y = pr(r["lat"], r["lon"]); c = GC.get(r["g"], "#B4B09C" if r["g"] == 18 else "#7E9C86")
    rad = min(2.2 + (r["girth"] or 0) * .55, 9)
    old = r["flags"] & 1
    dots += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rad:.1f}" fill="{c}" fill-opacity="{0.9 if old else 0.55}"{' stroke="#25291E" stroke-width=".8"' if old else ''}/>'
ff = ""
if FD:
    ff = "".join(f"@font-face{{font-family:'{n}';src:url('file://{FD}/{f}');font-weight:{w};}}" for n, f, w in [
        ("Fraunces", "FrauncesVar.ttf", "100 900"), ("Source Serif 4", "SourceSerif4-Regular.ttf", "400"),
        ("IBM Plex Mono", "IBMPlexMono-Regular.ttf", "400"), ("IBM Plex Mono", "IBMPlexMono-Medium.ttf", "500")])
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{ff}
body{{margin:0;width:1200px;height:630px;background:radial-gradient(circle at 78% 50%,#F7F6EC 0%,#F1EFE2 55%,#E4E2CF 100%);color:#25291E;overflow:hidden;position:relative;font-family:'Source Serif 4',Georgia,serif}}
.k{{position:absolute;left:66px;top:62px;font:500 15px/1 'IBM Plex Mono',monospace;letter-spacing:.14em;text-transform:uppercase;color:#636955;display:flex;gap:12px;align-items:center}}
.k b{{background:#1F5A3A;color:#F3F1E6;padding:7px 9px;font-weight:500}}
h1{{position:absolute;left:60px;top:100px;margin:0;font:900 80px/.92 Fraunces,Georgia,serif;letter-spacing:-.02em;color:#25291E;width:660px}}
h1 em{{font-style:normal;color:#7A4E2A}}
p{{position:absolute;left:66px;top:372px;width:600px;margin:0;font-size:26px;line-height:1.36}}
p b{{color:#7A4E2A}}
.f{{position:absolute;left:66px;bottom:40px;font:400 14px/1 'IBM Plex Mono',monospace;letter-spacing:.12em;text-transform:uppercase;color:#636955}}
svg{{position:absolute;right:26px;top:10px}}
</style></head><body>
<div class="k"><b>Data study</b><span>OpenStreetMap × Wikipedia</span></div>
<h1>Where are Britain's <em>oldest trees?</em></h1>
<p><b>{R['counts']['notable']:,}</b> notable trees on the open map, <b>{R['counts']['old_sign']:,}</b> with signs of great age. Oaks dominate; yews hug churches.</p>
<div class="f">Dr Tristan Hotham · Independent researcher</div>
<svg width="{Ww:.0f}" height="{Hh}" viewBox="0 0 {Ww:.0f} {Hh}"><path d="{land}" fill="#E2E0CB" stroke="#C9C7AE" stroke-width="1"/>{dots}</svg>
</body></html>"""
os.makedirs(os.path.join(ROOT, "work"), exist_ok=True)
tmp = os.path.join(ROOT, "work", "header.html"); open(tmp, "w").write(html)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1200, "height": 630})
    pg.goto("file://" + os.path.abspath(tmp)); pg.wait_for_timeout(500)
    pg.screenshot(path=os.path.join(ROOT, "header.png")); b.close()
os.remove(tmp)
print("header.png written")
