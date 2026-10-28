"""Step 2. Every statistic used on the page, in the paper, the blog post and the collage.

Reads ../work/*.pkl from 01_prepare.py, the Natural Earth land outline and the Wikipedia bundle (for the famous trees).
Writes ../data/results.json, ../data/page_data.json, ../data/species.csv, ../data/regions.csv,
../data/churchyard.csv, ../data/royal_forests.csv and ../data/famous_trees.csv.
Run: python3 02_analyse.py
"""
import gzip, json, os, re
import numpy as np, pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree
from shapely.geometry import shape, Point
import shapely
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, ".."); HIST = os.path.join(ROOT, "..")
WORK = os.path.join(ROOT, "work"); DATA = os.path.join(ROOT, "data")
N = pd.read_pickle(os.path.join(WORK, "notable.pkl")); T = pd.read_pickle(os.path.join(WORK, "all_trees.pkl"))
Wp = pd.read_pickle(os.path.join(WORK, "worship.pkl")); RF = pd.read_pickle(os.path.join(WORK, "royal_forests.pkl"))
DP = pd.read_pickle(os.path.join(WORK, "deer_parks.pkl")); WD = pd.read_pickle(os.path.join(WORK, "wd_trees.pkl"))
PL = pd.read_pickle(os.path.join(WORK, "places.pkl"))
TO_BNG = Transformer.from_crs(4326, 27700, always_xy=True)
R = {}
MITCHELL_CM_PER_YEAR = 2.5     # Mitchell's rule of thumb: about 2.5 cm (one inch) of girth a year for an open-grown tree with a full crown
CHURCH_M = 50                  # "churchyard": within 50 m of the centre of a mapped Christian place of worship
FOREST_KM = 5                  # "royal forest": within 5 km of the point Wikidata gives for a former royal forest
r3 = lambda v: None if v is None or (isinstance(v, float) and np.isnan(v)) else round(float(v), 4)

# ---------- counts and coverage ----------
R["counts"] = dict(
    osm_trees_extract=int(len(T)), notable=int(len(N)),
    named=int(N.f_named.sum()), denotation=int(N.f_denot.sum()), age_tag=int(N.f_age.sum()), wikidata=int(N.f_wikidata.sum()), girth3=int(N.f_girth3.sum()),
    girth_any_ok=int(N.girth_ok.sum()), old_sign=int(N.old_sign.sum()),
    species_known=int((~N.group.isin(["unknown"])).sum()), species_known_share=r3((~N.group.isin(["unknown"])).mean()),
    natural_monument=int(N.denotation.fillna("").str.lower().eq("natural_monument").sum()), landmark=int(N.denotation.fillna("").str.lower().eq("landmark").sum()),
    extract_girth_tagged=int(T.circ.notna().sum()), extract_girth_bulk=int(T.girth_bulk.sum()), extract_girth_ok=int(T.girth_ok.sum()),
    extract_age_class=int(T.age.fillna("").str.lower().isin(["mature", "semi-mature", "young", "new planting", "early-mature"]).sum()),
    worship=int(len(Wp)), royal_forests=int(len(RF)), deer_park_polygons=int(len(DP)), deer_park_km2=r3(DP.area_km2.sum()),
    deer_park_trees=int(N.deer_park.sum()), deer_park_old=int((N.deer_park & N.old_sign).sum()))
R["counts"]["old_sign_share"] = r3(N.old_sign.mean())
R["counts"]["extract_not_notable"] = R["counts"]["osm_trees_extract"] - R["counts"]["notable"]

ctry = N.groupby("country").agg(n=("osm_id", "size"), old=("old_sign", "sum")).reindex(["England", "Scotland", "Wales", "Northern Ireland"]).fillna(0).astype(int)
R["country"] = {c: dict(n=int(r.n), old=int(r.old), share=r3(r.n / len(N))) for c, r in ctry.iterrows()}
reg = N.groupby("region").agg(n=("osm_id", "size"), old=("old_sign", "sum"), yew=("group", lambda s: int((s == "yew").sum())), oak=("group", lambda s: int((s == "oak").sum()))).sort_values("n", ascending=False)
reg["share"] = reg.n / len(N)
reg.reset_index().to_csv(os.path.join(DATA, "regions.csv"), index=False)
R["regions"] = [dict(region=k, n=int(r.n), old=int(r.old), yew=int(r.yew), oak=int(r.oak), share=r3(r.share)) for k, r in reg.iterrows()]
cty = N.groupby("county").agg(n=("osm_id", "size"), old=("old_sign", "sum")).sort_values("n", ascending=False)
R["top_counties"] = [dict(county=k, n=int(r.n), old=int(r.old)) for k, r in cty.head(12).iterrows()]

# concentration: 10 km National Grid squares
sq = (N.e // 10000).astype(int).astype(str) + "_" + (N.n // 10000).astype(int).astype(str)
vc = sq.value_counts()
R["grid"] = dict(squares=int(len(vc)), top10_share=r3(vc.head(10).sum() / len(N)), top10_n=int(vc.head(10).sum()), top1_n=int(vc.iloc[0]),
                 half_squares=int((vc.cumsum() < len(N) / 2).sum() + 1), single_tree_squares=int((vc == 1).sum()))
top_sq = vc.index[0]; ts = N[sq == top_sq]
R["grid"]["top1_place"] = ts.near_place.mode().iloc[0] if len(ts) else None
R["grid"]["top1_county"] = ts.county.mode().iloc[0] if len(ts) else None

# mapping habits: unnamed trees of unknown species tagged landmark or natural_monument, by county
hb = N[N.name.isna() & (N.group == "unknown") & N.denotation.fillna("").str.lower().isin(["landmark", "natural_monument"])]
hv = hb.groupby(["county", hb.denotation.str.lower()]).size().sort_values(ascending=False)
R["habits"] = dict(n=int(len(hb)), share=r3(len(hb) / len(N)), top=[dict(county=c, denotation=d, n=int(v)) for (c, d), v in hv.head(5).items()])

# ---------- species ----------
known = N[N.group != "unknown"]
sp = known.groupby("group").agg(n=("osm_id", "size"), old=("old_sign", "sum"), girth_n=("girth_ok", "sum")).sort_values("n", ascending=False)
gstat = N[N.girth_ok].groupby("group").girth_m.agg(["median", "max"])
sp = sp.join(gstat)
sp["share_known"] = sp.n / len(known)
sp["old_share_known"] = sp.old / known.old_sign.sum()
sp.reset_index().to_csv(os.path.join(DATA, "species.csv"), index=False)
R["species"] = [dict(group=k, n=int(r.n), old=int(r.old), share=r3(r.share_known), old_share=r3(r.old_share_known), girth_n=int(r.girth_n),
                     girth_median=r3(r["median"]), girth_max=r3(r["max"])) for k, r in sp.iterrows()]
R["sp"] = {d["group"]: d for d in R["species"]}
R["species_known_old"] = int(known.old_sign.sum())
# species from the name only
R["counts"]["species_from_name"] = int((N.group_from == "name").sum())

# ---------- girth and Mitchell's rule ----------
G = N[N.girth_ok].copy()
G["mitchell_years"] = G.girth_m * 100 / MITCHELL_CM_PER_YEAR
bands = [(3, 4), (4, 5), (5, 6), (6, 8), (8, 10), (10, 17)]
R["girth_bands"] = [dict(lo=lo, hi=hi, n=int(G.girth_m.between(lo, hi, inclusive="left").sum()),
                         oak=int((G.girth_m.between(lo, hi, inclusive="left") & (G.group == "oak")).sum()),
                         years_lo=int(lo * 100 / MITCHELL_CM_PER_YEAR), years_hi=int(hi * 100 / MITCHELL_CM_PER_YEAR)) for lo, hi in bands]
R["girth"] = dict(n=int(len(G)), ge3=int((G.girth_m >= 3).sum()), ge5=int((G.girth_m >= 5).sum()), ge8=int((G.girth_m >= 8).sum()), ge10=int((G.girth_m >= 10).sum()),
                  median_ge3=r3(G[G.girth_m >= 3].girth_m.median()), mitchell_cm=MITCHELL_CM_PER_YEAR,
                  y3=int(300 / MITCHELL_CM_PER_YEAR), y5=int(500 / MITCHELL_CM_PER_YEAR), y8=int(800 / MITCHELL_CM_PER_YEAR), y10=int(1000 / MITCHELL_CM_PER_YEAR))
big = G.sort_values("girth_m", ascending=False)
big = big[big.name.notna()].head(15)
R["biggest"] = [dict(name=r["name"], group=r.group, species=r.species if isinstance(r.species, str) else None, girth=r3(r.girth_m), years=int(r.mitchell_years),
                     county=r.county, place=r.near_place, lat=r3(r.lat), lon=r3(r.lon), osm=r.osm_id, forest=r.forest_name if r.forest_m <= FOREST_KM * 1000 else None)
                for _, r in big.iterrows()]
R["big"] = {b["name"]: b for b in R["biggest"]}

# ---------- churchyards ----------
te, tn = TO_BNG.transform(T.lon.values, T.lat.values)
kw = cKDTree(Wp[["e", "n"]].values)
dT, iT = kw.query(np.c_[te, tn]); T["church_m"] = dT
cy = []
for g, s in T.groupby("group"):
    if len(s) < 40 or g == "unknown": continue
    cy.append(dict(group=g, n=int(len(s)), within25=r3((s.church_m <= 25).mean()), within50=r3((s.church_m <= 50).mean()), within100=r3((s.church_m <= 100).mean())))
cy = sorted(cy, key=lambda d: -d["within50"])
pd.DataFrame(cy).to_csv(os.path.join(DATA, "churchyard.csv"), index=False)
R["churchyard_by_group"] = cy
Y = T[T.group == "yew"]; NY = T[(T.group != "yew") & (T.group != "unknown")]
R["church"] = dict(m=CHURCH_M, yew_n=int(len(Y)), yew_within=int((Y.church_m <= CHURCH_M).sum()), yew_share=r3((Y.church_m <= CHURCH_M).mean()),
                   other_n=int(len(NY)), other_share=r3((NY.church_m <= CHURCH_M).mean()),
                   yew_share25=r3((Y.church_m <= 25).mean()), yew_share100=r3((Y.church_m <= 100).mean()),
                   other_share25=r3((NY.church_m <= 25).mean()), other_share100=r3((NY.church_m <= 100).mean()),
                   oak_share=r3((T[T.group == "oak"].church_m <= CHURCH_M).mean()), oak_n=int((T.group == "oak").sum()))
R["church"]["ratio"] = r3(R["church"]["yew_share"] / R["church"]["other_share"])
# notable yews
NYw = N[N.group == "yew"]
R["church"]["notable_yew_n"] = int(len(NYw)); R["church"]["notable_yew_within"] = int((NYw.church_m <= CHURCH_M).sum())
R["church"]["notable_yew_share"] = r3((NYw.church_m <= CHURCH_M).mean())
R["church"]["notable_all_share"] = r3((N.church_m <= CHURCH_M).mean())
R["church"]["notable_oak_share"] = r3((N[N.group == "oak"].church_m <= CHURCH_M).mean())
R["church"]["notable_yew_old"] = int(NYw.old_sign.sum())
# denomination of the nearest place of worship, for churchyard yews (all yews in the extract)
Yc = Y[Y.church_m <= CHURCH_M].copy(); Yc["kind"] = Wp.denom_kind.values[iT[Yc.index]]
dk = Yc.kind.value_counts()
R["church"]["yew_kind"] = {k: int(v) for k, v in dk.items()}
R["church"]["worship_kind"] = {k: int(v) for k, v in Wp.denom_kind.value_counts().items()}
# churches with a mapped yew within 50 m, by country (yews located with the OS Open Names lookup used for notable trees)
Ye, Yn = TO_BNG.transform(Y.lon.values, Y.lat.values)
O_kd = cKDTree(np.c_[TO_BNG.transform(PL.lon.values, PL.lat.values)])
# country of each place of worship from the nearest OS populated place (towns and villages); Northern Ireland by longitude/latitude box test on the island of Ireland
LAND = json.load(open(os.path.join(HIST, "did-lighthouses-work", "release", "build", "ne10m_land_british_isles.json")))
polys = [p for g in LAND for p in shape(g).geoms]
ireland = [p for p in polys if p.contains(Point(-7, 53.5))][0]
gb = max(polys, key=lambda p: p.area)
_, iw = O_kd.query(Wp[["e", "n"]].values)
Wp["country"] = PL.country.values[iw]
Wp.loc[[ireland.contains(Point(x, y)) for x, y in zip(Wp.lon, Wp.lat)], "country"] = "Northern Ireland"
ky = cKDTree(np.c_[Ye, Yn])
has_yew = np.array([len(ky.query_ball_point([e, n], CHURCH_M)) > 0 for e, n in zip(Wp.e, Wp.n)])
Wp["yew50"] = has_yew
R["church_country"] = {c: dict(churches=int((Wp.country == c).sum()), with_yew=int(((Wp.country == c) & Wp.yew50).sum()),
                               per1000=r3(1000 * ((Wp.country == c) & Wp.yew50).sum() / max(1, (Wp.country == c).sum())))
                       for c in ["England", "Wales", "Scotland", "Northern Ireland"]}
R["church"]["churches_with_yew"] = int(Wp.yew50.sum())
# churchyard yews by region (yews in the extract)
_, iy = O_kd.query(np.c_[Ye, Yn]); Y = Y.assign(country=PL.country.values[iy])
R["church"]["yew_by_country"] = {c: dict(n=int((Y.country == c).sum()), church=int(((Y.country == c) & (Y.church_m <= CHURCH_M)).sum())) for c in ["England", "Wales", "Scotland"]}

# ---------- royal forests ----------
N["in_forest"] = N.forest_m <= FOREST_KM * 1000
to_bng = lambda g: shapely.transform(g, lambda a: np.c_[TO_BNG.transform(a[:, 0], a[:, 1])])
land_bng = to_bng(gb)
circles = unary_union([Point(e, n).buffer(FOREST_KM * 1000, 64) for e, n in zip(RF.e, RF.n)])
forest_land = circles.intersection(land_bng).area
R["forest"] = dict(km=FOREST_KM, n_forests=int(len(RF)), land_share=r3(forest_land / land_bng.area), land_km2=int(forest_land / 1e6), gb_km2=int(land_bng.area / 1e6),
                   notable_in=int(N.in_forest.sum()), notable_share=r3(N.in_forest.mean()),
                   old_in=int((N.in_forest & N.old_sign).sum()), old_share=r3(N[N.old_sign].in_forest.mean()),
                   oak_old_in=int((N.in_forest & N.old_sign & (N.group == "oak")).sum()), oak_old_n=int((N.old_sign & (N.group == "oak")).sum()),
                   oldrate_in=r3(N[N.in_forest].old_sign.mean()), oldrate_out=r3(N[~N.in_forest].old_sign.mean()),
                   girth3_in=int((N.in_forest & N.f_girth3).sum()), girth3_share=r3(N[N.f_girth3].in_forest.mean()),
                   ge8_in=int((N.in_forest & N.girth_ok & (N.girth_m >= 8)).sum()), ge8_n=int((N.girth_ok & (N.girth_m >= 8)).sum()))
R["forest"]["old_ratio_land"] = r3(R["forest"]["old_share"] / R["forest"]["land_share"])
R["forest"]["notable_ratio_land"] = r3(R["forest"]["notable_share"] / R["forest"]["land_share"])
# extract-wide share (mapping intensity proxy): all trees in the extract within the circles
dF, _ = cKDTree(RF[["e", "n"]].values).query(np.c_[te, tn])
R["forest"]["extract_share"] = r3((dF <= FOREST_KM * 1000).mean())
fr = []
for _, f in RF.iterrows():
    m = N.forest_name.eq(f.label) & N.in_forest
    fr.append(dict(forest=f.label, qid=f.qid, lat=r3(f.lat), lon=r3(f.lon), notable=int(m.sum()), old=int((m & N.old_sign).sum()),
                   oaks=int((m & (N.group == "oak")).sum()), biggest=(N[m & N.girth_ok].sort_values("girth_m", ascending=False).name.dropna().head(3).tolist())))
fr = sorted(fr, key=lambda d: (-d["old"], -d["notable"]))
pd.DataFrame(fr).assign(biggest=lambda d: d.biggest.map(lambda v: "; ".join(v))).to_csv(os.path.join(DATA, "royal_forests.csv"), index=False)
R["forests"] = fr
R["forests_with_old"] = int(sum(1 for f in fr if f["old"] > 0))
R["fo"] = {f["forest"]: f for f in fr}
R["fo_top2_old"] = int(sum(f["old"] for f in fr[:2])); R["fo_top2"] = [f["forest"] for f in fr[:2]]

# ---------- famous trees: Wikipedia claims vs Mitchell's rule ----------
# girths and ages exactly as stated in the English Wikipedia articles (retrieved 28 October 2026); coordinates from the article, or from OSM where the article has none
FT = [
    dict(name="Fortingall Yew", species="yew", place="Fortingall, Perthshire", article="Fortingall Yew", girth_ft=56, girth_note="56 ft, measured in 1771; the trunk has since split",
         age_text="2,000 to 3,000 years in some estimates; Forestry and Land Scotland consider it 5,000", age_lo=2000, age_hi=5000, churchyard=True),
    dict(name="Llangernyw Yew", species="yew", place="Llangernyw, Conwy", article="Llangernyw Yew", girth_m=10.75, girth_note="10.75 m at ground level",
         age_text="4,000 to 5,000 years on the churchyard certificate; an alternative view is about 1,500", age_lo=1500, age_hi=5000, churchyard=True),
    dict(name="Crowhurst Yew", species="yew", place="Crowhurst, Surrey", article="Crowhurst Yew", girth_ft=32, girth_note="32 ft at 4 ft high, measured in 2013",
         age_text="thought to be about 4,000 years", age_lo=4000, age_hi=4000, churchyard=True),
    dict(name="Ashbrittle Yew", species="yew", place="Ashbrittle, Somerset", article="Ashbrittle Yew", girth_note="not given as a girth",
         age_text="believed to be over 3,000 years", age_lo=3000, age_hi=3000, churchyard=True),
    dict(name="Defynnog Yew", species="yew", place="Defynnog, Powys", article="Defynnog Yew", girth_note="not given as a figure",
         age_text="3,018 years by one assessment; more probably around 2,500", age_lo=2500, age_hi=3018, churchyard=True),
    dict(name="Ankerwycke Yew", species="yew", place="near Wraysbury, Berkshire", article="Ankerwycke Yew", girth_m=8.0, girth_note="8 m at 0.3 m high",
         age_text="at least 1,400 years, perhaps as much as 2,500", age_lo=1400, age_hi=2500, churchyard=False),
    dict(name="Major Oak", species="oak", place="Sherwood Forest, Nottinghamshire", article="Major Oak", girth_ft=33, girth_note="33 ft in 1999",
         age_text="between 800 and 1,200 years", age_lo=800, age_hi=1200, churchyard=False),
    dict(name="Bowthorpe Oak", species="oak", place="Manthorpe, near Bourne, Lincolnshire", article="Bowthorpe Oak", girth_ft=44, girth_note="about 44 ft",
         age_text="no figure given in the article", age_lo=None, age_hi=None, churchyard=False),
]
A = {}
for f in ["wikipedia_batch12.json.gz", "wikipedia_batch12b.json.gz"]:
    A.update(json.load(gzip.open(os.path.join(HIST, "_data12", f)))["articles"])
OSMN = T[T.name.notna()]
for f in FT:
    a = A[f["article"]]
    if f.get("girth_ft"): f["girth_m"] = round(f["girth_ft"] * 0.3048, 2)
    if a.get("coord"): f["lat"], f["lon"], f["coord_source"] = a["coord"]["lat"], a["coord"]["lon"], "Wikipedia article"
    else:
        o = OSMN[OSMN.name.str.contains(f["name"].split()[0])].iloc[0]; f["lat"], f["lon"], f["coord_source"] = round(o.lat, 6), round(o.lon, 6), "OpenStreetMap " + o.osm_id
    f["mitchell_years"] = int(round(f["girth_m"] * 100 / MITCHELL_CM_PER_YEAR)) if f.get("girth_m") else None
    f["in_osm"] = bool((OSMN.name.str.contains(f["name"].split()[0]) & ((OSMN.lat - f["lat"]).abs() < 0.003) & ((OSMN.lon - f["lon"]).abs() < 0.005)).any())
    f["source"] = "https://en.wikipedia.org/wiki/" + f["article"].replace(" ", "_")
pd.DataFrame(FT).drop(columns=["article"]).to_csv(os.path.join(DATA, "famous_trees.csv"), index=False)
R["famous"] = FT; R["fam"] = {f["name"]: f for f in FT}
R["famous_in_osm"] = int(sum(f["in_osm"] for f in FT))
yr = [(f["age_lo"] / f["mitchell_years"], f["age_hi"] / f["mitchell_years"]) for f in FT if f["species"] == "yew" and f["mitchell_years"] and f["age_lo"]]
R["fam_ratio"] = dict(min=r3(min(a for a, b in yr)), max=r3(max(b for a, b in yr)), n=len(yr))

# ---------- Wikidata remarkable trees: are they on OpenStreetMap? ----------
WD = WD[WD.coord.notna()].copy()
WD["lon"] = WD.coord.str.extract(r"POINT\(([-\d.]+)")[0].astype(float); WD["lat"] = WD.coord.str.extract(r" ([-\d.]+)\)")[0].astype(float)
WD["qid"] = WD.s.str.extract(r"(Q\d+)")[0]
we, wn = TO_BNG.transform(WD.lon.values, WD.lat.values)
ka = cKDTree(np.c_[te, tn]); d, _ = ka.query(np.c_[we, wn])
WD["osm_tree_m"] = d
WD["osm_tagged"] = WD.qid.isin(set(T.wikidata.dropna()))
WD["found"] = WD.osm_tagged | (WD.osm_tree_m <= 150)
R["wikidata"] = dict(n=int(len(WD)), found=int(WD.found.sum()), tagged=int(WD.osm_tagged.sum()), share=r3(WD.found.mean()))

# ---------- examples used in the text ----------
def tree(name):
    s = N[N.name.fillna("") == name]
    if not len(s): return None
    r = s.iloc[0]
    return dict(name=name, girth=r3(r.girth_m) if r.girth_ok else None, years=int(r.girth_m * 100 / MITCHELL_CM_PER_YEAR) if r.girth_ok else None, county=r.county,
                place=r.near_place, forest=r.forest_name if r.in_forest else None, church_m=int(r.church_m), lat=r3(r.lat), lon=r3(r.lon))
R["ex"] = {k: tree(k) for k in ["Queen Elizabeth Oak", "'Cowdray Colossus' Chestnut", "Majesty - the Fredville Oak", "Big Belly Oak", "King of Limbs", "Cathedral Oak",
                                "Capon Tree", "Craigends Yew", "Knightwood Oak", "Major Oak", "Fortingall Yew", "Old Man of Calke", "Mottisfont Oak", "Oak at the Gate of the Dead"]}
R["ex"] = {k: v for k, v in R["ex"].items() if v}

# ---------- page data ----------
GROUPS = ["oak", "yew", "sweet chestnut", "beech", "lime", "ash", "sycamore and maples", "horse chestnut", "cedar", "giant redwoods", "pines and other conifers", "elm", "plane",
          "hawthorn", "holly", "birch, alder and willow", "fruit trees", "other", "unknown"]
gi = {g: i for i, g in enumerate(GROUPS)}
rows = []
for _, r in N.iterrows():
    flags = (1 if r.old_sign else 0) | (2 if r.church_m <= CHURCH_M else 0) | (4 if r.in_forest else 0) | (8 if r.f_wikidata else 0) | (16 if r.deer_park else 0)
    sp_ = r.species if isinstance(r.species, str) else (r.taxon if isinstance(r.taxon, str) else (r.genus if isinstance(r.genus, str) else ""))
    rows.append([round(r.lat, 5), round(r.lon, 5), r["name"] if isinstance(r["name"], str) else "", gi[r.group], round(r.girth_m, 2) if r.girth_ok else None, flags,
                 sp_[:40], (r.denotation or "") if isinstance(r.denotation, str) else "", r.county or "", r.near_place or "", int(r.church_m), r.forest_name if r.in_forest else "", r.osm_id])
places = PL[PL.local_type.isin(["City", "Town", "Village"])].drop_duplicates(["name1", "area"])
P = dict(groups=GROUPS, cols=["lat", "lon", "name", "g", "girth", "flags", "sp", "den", "county", "near", "church_m", "forest", "osm"], rows=rows,
         famous=[dict(name=f["name"], lat=f["lat"], lon=f["lon"], age=f["age_text"], girth=f["girth_note"], sp=f["species"], place=f["place"]) for f in FT],
         forests=[[f["forest"], f["lat"], f["lon"], f["notable"], f["old"]] for f in fr],
         places=[[r.name1, r.area if isinstance(r.area, str) else "", round(r.lat, 4), round(r.lon, 4)] for r in places.itertuples()])
json.dump(P, open(os.path.join(DATA, "page_data.json"), "w"), separators=(",", ":"), ensure_ascii=False)
R["places_n"] = int(len(places))
R["retrieved"] = "28 October 2026"
json.dump(R, open(os.path.join(DATA, "results.json"), "w"), indent=1, ensure_ascii=False, default=lambda o: o.item() if hasattr(o, "item") else str(o))
print(json.dumps({k: R[k] for k in ["counts", "country", "grid", "girth", "church", "church_country", "forest", "wikidata", "famous_in_osm"]}, indent=1, default=str))
print(pd.DataFrame(R["species"]).to_string()); print(pd.DataFrame(cy).to_string()); print(pd.DataFrame(fr).head(15).to_string())
print(os.path.getsize(os.path.join(DATA, "page_data.json")) // 1024, "KB page data")
