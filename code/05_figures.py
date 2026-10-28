"""Step 5. Static figures for the paper (release/paper/f_*.png) and the blog (release/blog/b_*.png).
Every value comes from ../data/results.json and ../data/page_data.json. No chart titles inside blog images.
Fonts: FONT_DIR as for the header (Fraunces, Source Serif 4, IBM Plex Mono); falls back to defaults.
Run: python3 05_figures.py
"""
import json, math, os
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json"))); P = json.load(open(os.path.join(ROOT, "data", "page_data.json")))
FD = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts")
MONO, SER = "DejaVu Sans Mono", "DejaVu Serif"
if os.path.isdir(FD):
    for f in os.listdir(FD):
        if f.endswith(".ttf"): fm.fontManager.addfont(os.path.join(FD, f))
    MONO, SER = "IBM Plex Mono", "Source Serif 4"
BG, FG, MUT, RULE = "#F3F1E6", "#25291E", "#636955", "#D8D6C3"
OAK, YEW, CHE, BEE, RED, OTH, UNK, LEAFL, LAND = "#7A4E2A", "#1F5A3A", "#B5702A", "#8F8A2C", "#A2402C", "#7E9C86", "#B4B09C", "#A9C68E", "#E2E0CB"
GC = {0: OAK, 1: YEW, 2: CHE, 3: BEE, 9: RED}
gcol = lambda g: GC.get(g, UNK if g == 18 else OTH)
PAP = os.path.join(ROOT, "release", "paper"); BLOG = os.path.join(ROOT, "release", "blog")
os.makedirs(PAP, exist_ok=True); os.makedirs(BLOG, exist_ok=True)
pct = lambda v, d=0: f"{v * 100:.{d}f}%"
K = math.cos(math.radians(54))
LANDP = []
for g in json.load(open(os.path.join(ROOT, "..", "did-lighthouses-work", "release", "build", "ne10m_land_british_isles.json"))):
    for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        a = np.array(poly[0]); LANDP.append(np.c_[a[:, 0] * K, a[:, 1]])
ROWS = [dict(zip(P["cols"], r)) for r in P["rows"]]


def style(ax, grid="x"):
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    ax.spines["left"].set_color(MUT); ax.spines["bottom"].set_color(MUT)
    ax.tick_params(colors=FG, labelsize=11)
    for t in ax.get_xticklabels() + ax.get_yticklabels(): t.set_family(MONO)
    if grid: ax.grid(axis=grid, color=RULE, lw=.8); ax.set_axisbelow(True)


def save(fig, name, blog):
    out = os.path.join(BLOG if blog else PAP, ("b_" if blog else "f_") + name + ".png")
    fig.savefig(out, dpi=200, facecolor=BG if blog else "white", bbox_inches="tight", pad_inches=.15); plt.close(fig)
    if blog:  # blog images are exactly 1520 px wide
        from PIL import Image
        im = Image.open(out); im.resize((1520, round(im.size[1] * 1520 / im.size[0])), Image.LANCZOS).save(out, optimize=True)


def fig_map(blog):
    fig = plt.figure(figsize=(7.6, 9.4) if blog else (6.6, 8.2), facecolor=BG if blog else "white")
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor(BG if blog else "white")
    for a in LANDP: ax.add_patch(Polygon(a, closed=True, fc=LAND if blog else "#EEEEEA", ec="#C9C7AE" if blog else "#AAAAAA", lw=.5, zorder=0))
    for r in sorted(ROWS, key=lambda r: -(r["girth"] or 0)):
        old = r["flags"] & 1; s = 6 + (r["girth"] or 0) ** 2 * 1.6
        ax.scatter(r["lon"] * K, r["lat"], s=s, c=gcol(r["g"]), alpha=.9 if old else .55, lw=.7 if old else 0, edgecolors=FG, zorder=2 + (r["girth"] or 0) / 20)
    for f in P["famous"]:
        ax.scatter(f["lon"] * K, f["lat"], marker="*", s=230, c=YEW, edgecolors="white", lw=.8, zorder=6)
    lab = {"Fortingall Yew": (8, 4, "left"), "Llangernyw Yew": (-8, 6, "right"), "Major Oak": (8, 2, "left"), "Crowhurst Yew": (8, -8, "left"), "Defynnog Yew": (-8, -6, "right"), "Ashbrittle Yew": (-8, -2, "right"), "Bowthorpe Oak": (8, 2, "left"), "Ankerwycke Yew": (-8, 6, "right")}
    for f in P["famous"]:
        if f["name"] in lab:
            dx, dy, ha = lab[f["name"]]
            ax.annotate(f["name"], (f["lon"] * K, f["lat"]), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center", family=MONO, fontsize=9.5, color=FG, zorder=7,
                        bbox=dict(fc=BG if blog else "white", ec="none", alpha=.8, pad=1))
    ax.set_xlim(-8.3 * K, 1.9 * K); ax.set_ylim(49.85, 58.75); ax.set_aspect("equal"); ax.axis("off")
    items = [(OAK, "oak"), (YEW, "yew"), (CHE, "sweet chestnut"), (BEE, "beech"), (RED, "giant redwood"), (OTH, "other species"), (UNK, "species not recorded")]
    for k, (c, t) in enumerate(items):
        ax.scatter([], [], s=50, c=c, label=t)
    ax.scatter([], [], s=50, c="white", edgecolors=FG, lw=.8, label="ringed: sign of great age")
    ax.scatter([], [], marker="*", s=160, c=YEW, label="famous tree (Wikipedia)")
    lg = ax.legend(loc="upper left", frameon=False, prop=dict(family=MONO, size=9.5), bbox_to_anchor=(0.0, 0.99), labelcolor=FG)
    ax.text(0.0, 0.62, "dot size: girth\nwhere credible", transform=ax.transAxes, family=MONO, fontsize=9.5, color=MUT, va="top")
    save(fig, "map", blog)


def fig_regions(blog):
    V = R["regions"][::-1]
    fig, ax = plt.subplots(figsize=(7.6, 5.0) if blog else (6.6, 4.3), facecolor=BG if blog else "white"); ax.set_facecolor(BG if blog else "white")
    y = np.arange(len(V))
    ax.barh(y, [v["n"] for v in V], color=LEAFL, label="notable trees", height=.7)
    ax.barh(y, [v["old"] for v in V], color=OAK, label="with a sign of great age", height=.7)
    for i, v in enumerate(V): ax.text(v["n"] + 4, i, str(v["n"]), va="center", family=MONO, fontsize=10.5, color=FG)
    ax.set_yticks(y); ax.set_yticklabels([v["region"] for v in V]); style(ax)
    ax.legend(frameon=False, prop=dict(family=MONO, size=10), loc="lower right")
    ax.set_xlabel("notable trees in OpenStreetMap", family=MONO, color=MUT, fontsize=10.5)
    save(fig, "regions", blog)


def fig_species(blog):
    V = [s for s in R["species"] if s["group"] != "other"][:12][::-1]
    fig, ax = plt.subplots(figsize=(7.6, 5.6) if blog else (6.6, 4.8), facecolor=BG if blog else "white"); ax.set_facecolor(BG if blog else "white")
    y = np.arange(len(V))
    ax.barh(y + .2, [v["share"] for v in V], height=.38, color=LEAFL, label=f"all {R['counts']['species_known']:,} notable trees with a known species")
    ax.barh(y - .2, [v["old_share"] for v in V], height=.38, color=[OAK if v["group"] == "oak" else YEW if v["group"] == "yew" else MUT for v in V], label=f"the {R['species_known_old']} with a sign of great age")
    for i, v in enumerate(V): ax.text(max(v["share"], v["old_share"]) + .006, i, f"{v['n']}", va="center", family=MONO, fontsize=10, color=FG)
    ax.set_yticks(y); ax.set_yticklabels([v["group"] for v in V]); style(ax)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v * 100:.0f}%"))
    ax.legend(frameon=False, prop=dict(family=MONO, size=9.5), loc="lower right")
    save(fig, "species", blog)


def fig_church(blog):
    V = R["churchyard_by_group"][::-1]
    fig, ax = plt.subplots(figsize=(7.6, 5.6) if blog else (6.6, 4.8), facecolor=BG if blog else "white"); ax.set_facecolor(BG if blog else "white")
    y = np.arange(len(V))
    ax.barh(y, [v["within50"] for v in V], color=[YEW if v["group"] == "yew" else UNK for v in V], height=.7)
    for i, v in enumerate(V): ax.text(v["within50"] + .002, i, f"{v['within50'] * 100:.1f}%  (n={v['n']:,})", va="center", family=MONO, fontsize=9.5, color=FG)
    ax.set_yticks(y); ax.set_yticklabels([v["group"] for v in V]); style(ax)
    ax.set_xlim(0, .25); ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v * 100:.0f}%"))
    ax.set_xlabel(f"share within {R['church']['m']} m of a Christian place of worship", family=MONO, color=MUT, fontsize=10.5)
    save(fig, "church", blog)


def fig_girth(blog):
    V = R["girth_bands"]
    fig, ax = plt.subplots(figsize=(9.6, 4.8) if blog else (8.4, 4.2), facecolor=BG if blog else "white"); ax.set_facecolor(BG if blog else "white")
    x = np.arange(len(V))
    ax.bar(x, [v["n"] for v in V], color=LEAFL, width=.75, label="all species")
    ax.bar(x, [v["oak"] for v in V], color=OAK, width=.75, label="oaks")
    for i, v in enumerate(V): ax.text(i, v["n"] + .8, str(v["n"]), ha="center", family=MONO, fontsize=10.5, color=FG)
    ax.set_xticks(x); ax.set_xticklabels([("10 m+" if v["hi"] == 17 else f"{v['lo']} to {v['hi']} m") + "\n" + ("400+\nyears" if v["hi"] == 17 else f"{v['years_lo']} to {v['years_hi']}\nyears") for v in V])
    style(ax, "y"); [t.set_fontsize(10) for t in ax.get_xticklabels()]; ax.set_ylabel("notable trees", family=MONO, color=MUT, fontsize=10.5)
    ax.legend(frameon=False, prop=dict(family=MONO, size=10))
    save(fig, "girth", blog)


def fig_famous(blog):
    V = R["famous"][::-1]
    fig, ax = plt.subplots(figsize=(7.6, 4.6) if blog else (6.6, 4.0), facecolor=BG if blog else "white"); ax.set_facecolor(BG if blog else "white")
    for i, v in enumerate(V):
        c = YEW if v["species"] == "yew" else OAK
        if v["age_lo"] is not None:
            lo, hi = v["age_lo"], v["age_hi"]
            ax.barh(i, max(hi - lo, 60), left=lo - (30 if hi == lo else 0), height=.42, color=c, alpha=.4)
        if v["mitchell_years"]:
            ax.scatter(v["mitchell_years"], i, s=70, c=c, zorder=3, edgecolors="white", lw=.8)
    ax.scatter([], [], s=60, c=MUT, label="Mitchell's rule from the stated girth")
    ax.barh([-5], [1], color=MUT, alpha=.4, label="age range stated on Wikipedia")
    ax.set_ylim(-.6, len(V) - .4)
    ax.set_yticks(range(len(V))); ax.set_yticklabels([v["name"] for v in V]); style(ax)
    ax.set_xlim(0, 5300); ax.set_xlabel("age in years", family=MONO, color=MUT, fontsize=10.5)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
    ax.legend(frameon=False, prop=dict(family=MONO, size=9.5), loc="lower right")
    save(fig, "famous", blog)


def fig_forest(blog):
    F = R["forest"]
    V = [("land area", F["land_share"], UNK), ("notable trees", F["notable_share"], LEAFL), ("sign of great age", F["old_share"], OAK)][::-1]
    fig, ax = plt.subplots(figsize=(7.6, 2.8) if blog else (6.6, 2.4), facecolor=BG if blog else "white"); ax.set_facecolor(BG if blog else "white")
    for i, (n, v, c) in enumerate(V):
        ax.barh(i, v, color=c, height=.6); ax.text(v + .0008, i, pct(v, 1), va="center", family=MONO, fontsize=11, color=FG)
    ax.set_yticks(range(3)); ax.set_yticklabels([v[0] for v in V]); style(ax)
    ax.set_xlim(0, .06); ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v * 100:.0f}%"))
    ax.set_xlabel(f"share within {F['km']} km of a former royal forest point (Wikidata)", family=MONO, color=MUT, fontsize=10.5)
    save(fig, "forest", blog)


for blog in (False, True):
    for f in (fig_map, fig_regions, fig_species, fig_church, fig_girth, fig_famous, fig_forest): f(blog)
print("figures written")
