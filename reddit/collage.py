"""r/dataisbeautiful collage for Where are Britain's oldest trees? (ancient-trees). Run from this folder: python3 collage.py
Every number is read from ../data/results.json or ../data/page_data.json."""
import json, math, os
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon, Ellipse

F = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts/")
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]:
    fm.fontManager.addfont(os.path.join(F, f))
DISP = fm.FontProperties(fname=os.path.join(F, "FrauncesVar.ttf"), weight=900)
SER = "Source Serif 4"; MONO = "IBM Plex Mono"
BG = "#F3F1E4"; FG = "#25291E"; MUT = "#636955"; LAND = "#E3E2CC"; OAK = "#7A4E2A"; YEW = "#1F5A3A"; CHE = "#B5702A"; BEE = "#8F8A2C"; RED = "#A2402C"; OTH = "#7E9C86"; UNK = "#BAB6A2"; LEAF = "#5E8C3A"; LEAFL = "#AFCB94"
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
P = json.load(open(os.path.join(ROOT, "data", "page_data.json")))
ROWS = [dict(zip(P["cols"], r)) for r in P["rows"]]
GC = {0: OAK, 1: YEW, 2: CHE, 3: BEE, 9: RED}
gcol = lambda g: GC.get(g, UNK if g == 18 else OTH)
K = math.cos(math.radians(54))
LANDP = []
for g in json.load(open(os.path.join(ROOT, "..", "did-lighthouses-work", "release", "build", "ne10m_land_british_isles.json"))):
    for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        a = np.array(poly[0]); LANDP.append(np.c_[a[:, 0] * K, a[:, 1]])
pct = lambda v, d=0: f"{v * 100:.{d}f}%"
c = R["counts"]; ch = R["church"]; fo = R["forest"]

fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG)
# faint tree rings behind the title, top right
ra = fig.add_axes([0.74, 0.86, 0.3, 0.16]); ra.set_xlim(-1, 1); ra.set_ylim(-1, 1); ra.set_aspect("equal"); ra.axis("off")
rng = np.random.default_rng(7); th = np.linspace(0, 2 * np.pi, 400)
for k in range(1, 34):
    r0 = k / 30; w = r0 * (1 + .03 * np.sin(3 * th + k * .4) + .02 * np.cos(5 * th - k * .9)) * (0.6 + 0.4 * (1 - k / 60))
    ra.plot(np.cos(th) * w - .05 * k / 30, np.sin(th) * w + .03 * k / 30, color=OAK, lw=1.3 if k % 5 == 0 else .7, alpha=.16)
fig.text(0.04, 0.968, "Where are Britain's oldest trees?", fontproperties=DISP, fontsize=42, color=FG, va="top")
fig.text(0.04, 0.915, f"I mapped every notable tree that volunteers have put on OpenStreetMap: {c['notable']:,} trees that are named,\n"
         f"tagged as a landmark or natural monument, or at least 3 m round. Oaks dominate, yews hug the old\nchurches, and the map shows the mappers as much as the trees.",
         family=SER, fontsize=14, color=FG, va="top", linespacing=1.4)

# hero map
ax = fig.add_axes([0.0, 0.315, 0.6, 0.5])
for a in LANDP:
    ax.add_patch(Polygon(a, closed=True, fc=LAND, ec="#C9C7AE", lw=.6, zorder=0))
for r in sorted(ROWS, key=lambda r: -(r["girth"] or 0)):
    old = r["flags"] & 1; s = 7 + (r["girth"] or 0) ** 2 * 2.4
    ax.scatter(r["lon"] * K, r["lat"], s=s, c=gcol(r["g"]), alpha=.92 if old else .55, lw=.8 if old else 0, edgecolors=FG, zorder=2 + (r["girth"] or 0) / 20, rasterized=True)
for f in P["famous"]:
    ax.scatter(f["lon"] * K, f["lat"], marker="*", s=300, c=YEW, edgecolors="white", lw=1, zorder=8)
lab = {"Fortingall Yew": (10, 0, "left"), "Llangernyw Yew": (-10, 6, "right"), "Major Oak": (10, 0, "left"), "Crowhurst Yew": (10, -10, "left"), "Defynnog Yew": (-10, -4, "right"), "Ashbrittle Yew": (-10, 0, "right")}
for f in P["famous"]:
    if f["name"] in lab:
        dx, dy, ha = lab[f["name"]]
        ax.annotate(f["name"], (f["lon"] * K, f["lat"]), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center", family=MONO, fontsize=10.5, color=FG, zorder=9, bbox=dict(fc=BG, ec="none", alpha=.85, pad=1.2))
for nm, (dx, dy, ha) in {"Queen Elizabeth Oak": (12, -14, "left"), "Big Belly Oak": (16, 22, "left")}.items():
    b = R["big"][nm]
    ax.annotate(f"{nm}\n{b['girth']:.1f} m round", (b["lon"] * K, b["lat"]), xytext=(dx, dy), textcoords="offset points", ha=ha, va="top" if dy < 0 else "bottom", family=MONO, fontsize=10, color=OAK, zorder=9,
                bbox=dict(fc=BG, ec="none", alpha=.85, pad=1.2), arrowprops=dict(arrowstyle="-", color=OAK, lw=.8))
ax.set_xlim(-8.3 * K, 1.95 * K); ax.set_ylim(49.85, 58.75); ax.set_aspect("equal"); ax.axis("off")
# key
key = [(OAK, "oak"), (YEW, "yew"), (CHE, "sweet chestnut"), (BEE, "beech"), (RED, "giant redwood"), (OTH, "other species"), (UNK, "species not recorded")]
for i, (col, t) in enumerate(key):
    x0 = 0.04 + (i % 4) * 0.135 + (0.025 if i % 4 == 3 else 0); y0 = 0.838 - (i // 4) * 0.018
    fig.patches.append(Ellipse((x0 + .006, y0), .009, .009 * 12 / 15, transform=fig.transFigure, fc=col, ec=col))
    fig.text(x0 + .016, y0, t, va="center", family=MONO, fontsize=10.5, color=FG)
fig.text(0.62, 0.838, "dark ring: sign of great age", family=MONO, fontsize=10.5, color=MUT, va="center")
fig.text(0.62, 0.820, "dot size: girth", family=MONO, fontsize=10.5, color=MUT, va="center")
fig.lines.append(matplotlib.lines.Line2D([0.792], [0.820], marker="*", markersize=13, color=YEW, transform=fig.transFigure))
fig.text(0.802, 0.820, "famous tree", family=MONO, fontsize=10.5, color=MUT, va="center")

# headline numbers
tx = fig.add_axes([0.62, 0.315, 0.36, 0.48]); tx.axis("off")
notes = [(f"{ch['ratio']:.0f}×", YEW, f"as likely as other trees: a yew stands\nwithin {ch['m']} m of a church {pct(ch['yew_share'])} of the\ntime ({ch['yew_within']} of {ch['yew_n']}); other trees {pct(ch['other_share'], 1)}."),
         (pct(R['sp']['oak']['share']), OAK, f"of notable trees with a known species\nare oaks, and {pct(R['sp']['oak']['old_share'])} of those with a\nsign of great age."),
         (f"{R['girth']['ge10']}", OAK, f"named trees at least 10 m round. Top:\nthe Queen Elizabeth Oak, {R['big']['Queen Elizabeth Oak']['girth']:.2f} m\n(about {R['big']['Queen Elizabeth Oak']['years']} years by Mitchell's rule)."),
         (pct(R["grid"]["top10_share"]), MUT, f"of notable trees sit in 10 of {R['grid']['squares']}\nten-km squares. This is a map of\nwhere people have looked.")]
for (big, col, small), y in zip(notes, [1.0, 0.75, 0.5, 0.25]):
    tx.text(0, y, big, fontproperties=DISP, fontsize=38, color=col, va="top", transform=tx.transAxes)
    tx.text(0, y - 0.085, small, family=SER, fontsize=12.5, color=FG, va="top", transform=tx.transAxes, linespacing=1.3)

# small multiple 1: churchyard share by species
fig.text(0.04, 0.285, f"SHARE OF TREES WITHIN {ch['m']} M OF A CHURCH", family=MONO, fontsize=10.5, color=MUT)
bx = fig.add_axes([0.2, 0.13, 0.3, 0.135]); bx.axis("off")
V = R["churchyard_by_group"]; pick = ["yew", "holly", "lime", "oak", "beech", "ash"]
V = [v for v in V if v["group"] in pick]
for i, v in enumerate(V):
    y = 1 - i / (len(V) - 1)
    bx.text(-0.02, y, v["group"], family=MONO, fontsize=10.5, color=FG, ha="right", va="center", transform=bx.transAxes)
    bx.barh([y], [v["within50"] / .2 * .8], left=0, height=.1, color=YEW if v["group"] == "yew" else UNK, transform=bx.transAxes)
    bx.text(v["within50"] / .2 * .8 + .02, y, pct(v["within50"], 1), family=MONO, fontsize=10.5, color=FG, va="center", transform=bx.transAxes)

# small multiple 2: Mitchell vs claimed
fig.text(0.55, 0.285, "AGE: GIRTH RULE (DOT) vs WIKIPEDIA (BAR)", family=MONO, fontsize=10.5, color=MUT)
cx = fig.add_axes([0.71, 0.145, 0.26, 0.125])
FT = [f for f in R["famous"] if f["mitchell_years"] and f["age_lo"]]
for i, f in enumerate(FT[::-1]):
    col = YEW if f["species"] == "yew" else OAK
    cx.barh(i, max(f["age_hi"] - f["age_lo"], 80), left=f["age_lo"] - (40 if f["age_hi"] == f["age_lo"] else 0), height=.45, color=col, alpha=.4)
    cx.scatter(f["mitchell_years"], i, s=55, c=col, zorder=3, edgecolors="white", lw=.8)
    cx.text(-150, i, f["name"], family=MONO, fontsize=10.5, color=FG, ha="right", va="center")
cx.set_xlim(0, 5200); cx.set_ylim(-.6, len(FT) - .4); cx.set_yticks([]); cx.set_facecolor(BG)
for sp in ("top", "right", "left"): cx.spines[sp].set_visible(False)
cx.spines["bottom"].set_color(MUT); cx.tick_params(labelsize=10, colors=FG)
cx.set_xticks([0, 2500, 5000]); cx.set_xticklabels(["0", "2,500", "5,000"]); cx.set_xlabel("years", family=MONO, fontsize=10, color=MUT, labelpad=2); [t.set_family(MONO) for t in cx.get_xticklabels()]

fig.text(0.04, 0.069, f"Notable: OSM tree with a name, a landmark, natural monument, ancient or veteran tag, or a credible girth of 3 m+.\n"
         f"OpenStreetMap shows mapped trees, not all trees. The Woodland Trust Ancient Tree Inventory is not open for reuse and\n"
         f"was not used. Church: within {ch['m']} m of a mapped place of worship. Mitchell's rule: {R['girth']['mitchell_cm']:.1f} cm of girth a year.",
         family=MONO, fontsize=9.5, color=MUT, linespacing=1.45)
fig.text(0.04, 0.012,
         f"Data: © OpenStreetMap contributors (ODbL), via QLever, retrieved {R['retrieved']}. Wikidata (CC0). English Wikipedia articles on the famous trees,\n"
         "Royal forest and Veteran tree (CC BY-SA 4.0). OS Open Names (Contains OS data © Crown copyright and database right 2026, OGL v3). Natural Earth.\n"
         "Analysis and chart: Tristan Hotham, with Python and matplotlib.  tristan-hotham.github.io/ancient-trees",
         family=MONO, fontsize=8.8, color=MUT, linespacing=1.45)
fig.savefig(os.path.join(HERE, "where_are_britains_oldest_trees.png"), facecolor=BG, dpi=200)
print("ok")
