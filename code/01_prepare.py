"""Step 1. Build the tree table from OpenStreetMap and Wikidata.

Reads (in place, one folder up, never copied):
  _data12/wd_osm_bundle12.json.gz   QLever extracts: osm_trees, osm_worship, osm_deerparks, wd_trees, wd_forests
  osnames_gb.tsv                    OS Open Names (populated places) for country, region and county
  did-lighthouses-work/release/build/ne10m_land_british_isles.json   Natural Earth land (Ireland test, land area)
Writes:
  ../data/trees.csv      every OSM tree that passes the "notable" filter, with derived fields
  ../work/*.pkl          intermediate tables for 02_analyse.py (not published)

Notable filter (any one of): a name (not a fruit-variety label in an orchard); denotation natural_monument,
landmark, ancient or veteran; an age tag of veteran, ancient or a number of years; a Wikidata link;
a heritage tag; or a credible girth (circumference) of 3 m or more.
Run: python3 01_prepare.py
"""
import gzip, io, json, os, re
import numpy as np, pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree
from shapely import wkt as W
from shapely.geometry import shape, Point

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, ".."); HIST = os.path.join(ROOT, "..")
WORK = os.path.join(ROOT, "work"); os.makedirs(WORK, exist_ok=True)
B = json.load(gzip.open(os.path.join(HIST, "_data12", "wd_osm_bundle12.json.gz")))
TO_BNG = Transformer.from_crs(4326, 27700, always_xy=True)


def get(k):
    t = pd.read_csv(io.StringIO(B["results"][k]["tsv"]), sep="\t", dtype=str, quoting=3)
    t.columns = [c.lstrip("?") for c in t.columns]
    for c in t.columns:
        t[c] = t[c].str.replace(r'^"(.*)"(@\w+|\^\^.*)?$', r"\1", regex=True)
    return t


def centroid(s):
    try:
        g = W.loads(s)
        c = g if g.geom_type == "Point" else g.representative_point() if g.geom_type in ("Polygon", "MultiPolygon") else g.centroid
        return c.x, c.y
    except Exception:
        return np.nan, np.nan


# ---------- trees ----------
T = get("osm_trees").drop_duplicates("osm").reset_index(drop=True)
T["osm_id"] = T.osm.str.extract(r"openstreetmap.org/(\w+/\d+)")[0]
xy = T.wkt.map(centroid); T["lon"] = [a for a, b in xy]; T["lat"] = [b for a, b in xy]
T = T[T.lat.notna()].reset_index(drop=True)


def parse_girth(s):
    """Circumference tag to metres. OSM default unit is metres; bare numbers above 25 are taken as centimetres."""
    if not isinstance(s, str): return np.nan
    x = s.strip().lower().replace(",", ".")
    m = re.match(r"^[~<>≈ ]*([\d.]+)\s*(cm|mm|m|metres|meters|ft|feet|'|in|\")?", x)
    if not m: return np.nan
    try: v = float(m.group(1))
    except ValueError: return np.nan
    u = m.group(2)
    if u == "cm": v /= 100
    elif u == "mm": v /= 1000
    elif u in ("ft", "feet", "'"): v *= 0.3048
    elif u in ("in", '"'): v *= 0.0254
    elif u is None and v > 25: v /= 100
    return v


T["girth_raw"] = T.circ
T["girth_m"] = T.circ.map(parse_girth)
# bulk-tagged values: the same raw value on 10 or more trees within the same ~1 km cell is a survey default or estimate, not a measurement
cell = (T.lat / 0.01).round().astype(int).astype(str) + "_" + (T.lon / 0.015).round().astype(int).astype(str)
grp = T[T.circ.notna()].groupby([cell[T.circ.notna()], T.circ[T.circ.notna()]]).osm.transform("size")
T["girth_bulk"] = False
T.loc[grp.index, "girth_bulk"] = grp >= 10
has_info = T[["species", "genus", "taxon", "name", "denotation"]].notna().any(axis=1)
bare = T.circ.fillna("").str.strip().str.fullmatch(r"\d+")
named_monument = T.name.notna() | T.denotation.fillna("").str.lower().isin(["natural_monument", "landmark"])
# credible girth: a plausible value, not bulk-tagged, not a bare whole number on a tree with no other information,
# and (for anything over 9 m, which would make it one of the largest trees in Britain) only on a named or monument-tagged tree
T["girth_ok"] = T.girth_m.between(0.1, 16.5) & ~T.girth_bulk & ~(bare & ~has_info) & ~((T.girth_m > 9) & ~named_monument)

# ---------- species group ----------
GROUPS = [  # (group, latin genus or species prefixes, English words)
    ("oak", ["quercus"], ["oak"]),
    ("yew", ["taxus"], ["yew"]),
    ("sweet chestnut", ["castanea"], ["sweet chestnut", "spanish chestnut"]),
    ("beech", ["fagus"], ["beech"]),
    ("lime", ["tilia"], ["lime", "linden"]),
    ("ash", ["fraxinus"], [" ash", "ash tree"]),
    ("sycamore and maples", ["acer"], ["sycamore", "maple"]),
    ("horse chestnut", ["aesculus"], ["horse chestnut", "conker"]),
    ("cedar", ["cedrus"], ["cedar"]),
    ("giant redwoods", ["sequoiadendron", "sequoia"], ["sequoia", "wellingtonia", "redwood"]),
    ("elm", ["ulmus"], ["elm"]),
    ("plane", ["platanus"], ["plane"]),
    ("hawthorn", ["crataegus"], ["thorn"]),
    ("pines and other conifers", ["pinus", "abies", "picea", "larix", "pseudotsuga", "chamaecyparis", "cupressus", "taxodium", "thuja", "araucaria", "tsuga", "cupressocyparis", "metasequoia", "juniperus", "cryptomeria", "ginkgo"], ["pine", "fir", "larch", "spruce", "cypress", "monkey puzzle", "ginkgo"]),
    ("fruit trees", ["malus", "pyrus", "prunus", "mespilus", "cydonia", "ficus", "morus", "juglans"], ["apple", "pear", "cherry", "plum", "mulberry", "walnut", "medlar", "quince", "damson", "greengage"]),
    ("birch, alder and willow", ["betula", "alnus", "salix", "populus"], ["birch", "alder", "willow", "poplar", "aspen"]),
    ("holly", ["ilex"], ["holly"]),
]


def group_of(r):
    for col in ("species", "taxon", "genus"):
        v = r[col]
        if isinstance(v, str):
            s = v.lower().strip()
            for g, lat, eng in GROUPS:
                if any(s.startswith(p) for p in lat): return g, col
            for g, lat, eng in GROUPS:
                if any(w.strip() == s or s.startswith(w.strip() + " ") or s.endswith(" " + w.strip()) or w in " " + s for w in eng): return g, col
    v = r["name"]
    if isinstance(v, str):
        s = " " + v.lower() + " "
        for g, lat, eng in GROUPS:
            if any(re.search(r"\b" + re.escape(w.strip()) + r"s?\b", s) for w in eng):
                return g, "name"
    return ("other" if any(isinstance(r[c], str) for c in ("species", "taxon", "genus")) else "unknown"), "none"


gs = T.apply(group_of, axis=1)
T["group"] = [a for a, b in gs]; T["group_from"] = [b for a, b in gs]
# "chestnut" alone is ambiguous: only Castanea or "sweet chestnut" count as sweet chestnut (handled above); plain "chestnut" names fall through to unknown/other

# ---------- notable filter ----------
den = T.denotation.fillna("").str.lower()
age = T.age.fillna("").str.lower()
age_years = pd.to_numeric(age.str.extract(r"(\d{2,4})")[0], errors="coerce")
FRUIT = re.compile(r"apple|pear\b|plum|cherry|damson|greengage|quince|medlar|pippin|russet|bramley|cox|pearmain|codlin|seedling|nonpareil|reinette|gage|crab", re.I)
named = T.name.notna()
fruit_label = named & (T.name.fillna("").str.contains(FRUIT) | den.eq("orchard") | (T.group == "fruit trees"))
GENERIC = {g.strip() for g in """oak|english oak|common oak|sessile oak|pedunculate oak|red oak|turkey oak|holm oak|ash|common ash|beech|copper beech|yew|english yew|common yew|irish yew|rowan|
hawthorn|sycamore|sweet chestnut|horse chestnut|chestnut|lime|common lime|small-leaved lime|linden|birch|silver birch|holly|elm|english elm|willow|weeping willow|
alder|cedar|cedar of lebanon|pine|scots pine|maple|field maple|norway maple|cherry|wild cherry|plane|london plane|hornbeam|larch|poplar|walnut|whitebeam|elder|hazel|
spruce|fir|sequoia|giant sequoia|redwood|coast redwood|wellingtonia|monkey puzzle|cypress|magnolia|mulberry|fig|tree|eucalyptus|ginkgo|tulip tree|
lilac|wych elm|horse chestnut|black poplar|blackthorn|crab apple|aspen|juniper|laburnum|cherry plum|bird cherry|false acacia|robinia|catalpa|indian bean|judas|
sweet gum|liquidambar|black pine|corsican pine|douglas fir|norway spruce|sitka spruce|western red cedar|deodar|atlas cedar|swamp cypress|dawn redwood|
leyland cypress|lawson cypress|silver maple|japanese maple|cork oak|white willow|crack willow|goat willow|grey poplar|lombardy poplar|white poplar|downy birch|
common alder|grey alder|large leaved lime|small leaved lime|sorbus|service tree|wild service tree|spindle|dogwood|guelder rose|box|common beech|european beech|
english oak tree|field maple tree|sweet chestnut tree|horse chestnut tree|copper beech tree|hawthorn tree|apple|pear|plum""".split("|")}
nm = T.name.fillna("").str.lower().str.replace("-", " ").str.replace(r"^the\s+|\s+tree$|[^a-z ]", "", regex=True).str.replace(r"\s+", " ", regex=True).str.strip()
GENERIC = {g.replace("-", " ") for g in GENERIC}
generic_name = named & (nm.isin(GENERIC) | (nm == T.species.fillna("#").str.lower()))
# a name that is only a species word ("Oak", "Rowan") is a label, not a sign that the tree is notable
T["f_named"] = named & ~fruit_label & ~generic_name
T["f_denot"] = den.isin(["natural_monument", "landmark", "ancient", "veteran"])
T["f_age"] = age.isin(["veteran", "ancient"]) | (age_years >= 100) | age.str.contains("elizabeth")
T["f_wikidata"] = T.wikidata.notna()
T["f_heritage"] = T.heritage.notna() & ~T.heritage.fillna("").str.lower().eq("no")
T["f_girth3"] = T.girth_ok & (T.girth_m >= 3)
T["notable"] = T[["f_named", "f_denot", "f_age", "f_wikidata", "f_heritage", "f_girth3"]].any(axis=1)
# signs of great age (a stricter subset): veteran-size girth (3 m or more), or an explicit ancient or veteran label or age tag, or a natural monument tag
# (a natural_monument tag counts only on a tree that also has a name or a species: some mappers tag whole surveys of unnamed trees this way)
T["old_sign"] = T.f_girth3 | den.isin(["ancient", "veteran"]) | T.f_age | (den.eq("natural_monument") & (named | T[["species", "genus", "taxon"]].notna().any(axis=1)))
T["age_years_tag"] = age_years.where(age_years >= 100)

N = T[T.notable].copy().reset_index(drop=True)
print("trees", len(T), "notable", len(N), "old_sign", int(N.old_sign.sum()), "girth ok", int(T.girth_ok.sum()), "bulk", int(T.girth_bulk.sum()))

# ---------- country, region, county ----------
O = pd.read_csv(os.path.join(HIST, "osnames_gb.tsv"), sep="\t", usecols=["name1", "type", "local_type", "lat", "lon", "x", "y", "county", "district", "region", "country"], dtype=str)
O = O[O.type == "populatedPlace"].copy()
for c in ("lat", "lon", "x", "y"): O[c] = O[c].astype(float)
O["area"] = O.county.fillna(O.district)
kd = cKDTree(O[["x", "y"]].values)
ex, ey = TO_BNG.transform(N.lon.values, N.lat.values); N["e"] = ex; N["n"] = ey
d, i = kd.query(np.c_[ex, ey])
N["country"] = O.country.values[i]; N["region"] = O.region.values[i]; N["county"] = O.area.values[i]; N["near_place"] = O.name1.values[i]; N["near_place_m"] = d.round()
LAND = json.load(open(os.path.join(HIST, "did-lighthouses-work", "release", "build", "ne10m_land_british_isles.json")))
polys = [p for g in LAND for p in shape(g).geoms]
ireland = [p for p in polys if p.contains(Point(-7, 53.5))][0]
ni = np.array([ireland.contains(Point(x, y)) for x, y in zip(N.lon, N.lat)])
N.loc[ni, ["country", "region", "county"]] = ["Northern Ireland", "Northern Ireland", None]
N.loc[ni, ["near_place", "near_place_m"]] = [None, np.nan]
print(N.country.value_counts())

# ---------- churches ----------
Wp = get("osm_worship")
xy = Wp.wkt.map(centroid); Wp["lon"] = [a for a, b in xy]; Wp["lat"] = [b for a, b in xy]
Wp = Wp[Wp.lat.notna()].reset_index(drop=True)
we, wn = TO_BNG.transform(Wp.lon.values, Wp.lat.values); Wp["e"] = we; Wp["n"] = wn
OLDDEN = {"anglican", "church_in_wales", "church_of_england", "roman_catholic", "catholic", "episcopal", "scottish_episcopal"}
Wp["denom_kind"] = np.where(Wp.denom.fillna("").str.lower().isin(OLDDEN), "anglican or catholic",
                     np.where(Wp.denom.notna(), "nonconformist or other", "not tagged"))
kw = cKDTree(Wp[["e", "n"]].values)
d, i = kw.query(N[["e", "n"]].values)
N["church_m"] = d.round(); N["church_name"] = Wp.name.values[i]; N["church_denom"] = Wp.denom.values[i]; N["church_kind"] = Wp.denom_kind.values[i]

# ---------- royal forests (Wikidata) and deer parks (OSM) ----------
F = get("wd_forests")
RF = F[(F.clsl == "royal forest") & F.coord.notna()].drop_duplicates("s").copy()
RF["lon"] = RF.coord.str.extract(r"POINT\(([-\d.]+)")[0].astype(float); RF["lat"] = RF.coord.str.extract(r" ([-\d.]+)\)")[0].astype(float)
re_, rn_ = TO_BNG.transform(RF.lon.values, RF.lat.values); RF["e"] = re_; RF["n"] = rn_
RF["qid"] = RF.s.str.extract(r"(Q\d+)")[0]
kf = cKDTree(RF[["e", "n"]].values)
d, i = kf.query(N[["e", "n"]].values)
N["forest_m"] = d.round(); N["forest_name"] = RF.label.values[i]
P = get("osm_deerparks")
P = P[P.wkt.str.startswith(("POLYGON", "MULTIPOLYGON"))]
P = P[(P.name.fillna("").str.contains("deer park", case=False) | P.historic.eq("deer_park")) & ~P.name.fillna("").str.contains(r"\b(?:Road|Drive|Way|Avenue|Close|Lane|Court|Crescent|Gardens|Street|Farm|Primary|School|Golf)\b", case=False, regex=True)]
from shapely.strtree import STRtree
import shapely
pg = [shapely.transform(W.loads(s), lambda a: np.c_[TO_BNG.transform(a[:, 0], a[:, 1])]) for s in P.wkt]
P = P.assign(area_km2=[g.area / 1e6 for g in pg]); keep = (P.area_km2 >= 0.05).values
P = P[keep].reset_index(drop=True); pg = [g for g, k in zip(pg, keep) if k]
st = STRtree(pg)
inpark = np.zeros(len(N), bool); parkname = [None] * len(N)
for j, (x, y) in enumerate(zip(N.e, N.n)):
    for k in st.query(Point(x, y)):
        if pg[k].contains(Point(x, y)): inpark[j] = True; parkname[j] = P.name.iloc[k]; break
N["deer_park"] = inpark; N["deer_park_name"] = parkname
print("deer park polygons", len(P), "area km2", round(P.area_km2.sum(), 1), "trees inside", inpark.sum())

N.to_pickle(os.path.join(WORK, "notable.pkl")); T.to_pickle(os.path.join(WORK, "all_trees.pkl"))
Wp.to_pickle(os.path.join(WORK, "worship.pkl")); RF.to_pickle(os.path.join(WORK, "royal_forests.pkl"))
P.assign(geom=[g.wkt for g in pg]).to_pickle(os.path.join(WORK, "deer_parks.pkl"))
WD = get("wd_trees").drop_duplicates("s"); WD.to_pickle(os.path.join(WORK, "wd_trees.pkl"))
O[O.local_type.isin(["City", "Town", "Village"])][["name1", "local_type", "lat", "lon", "x", "y", "area", "country"]].to_pickle(os.path.join(WORK, "places.pkl"))

cols = ["osm_id", "name", "group", "species", "genus", "taxon", "denotation", "girth_raw", "girth_m", "girth_ok", "age", "start", "wikidata",
        "lat", "lon", "country", "region", "county", "near_place", "church_m", "church_name", "church_kind", "forest_m", "forest_name", "deer_park", "deer_park_name",
        "f_named", "f_denot", "f_age", "f_wikidata", "f_heritage", "f_girth3", "old_sign"]
out = N[cols].copy(); out["lat"] = out.lat.round(6); out["lon"] = out.lon.round(6); out["girth_m"] = out.girth_m.round(2)
out.to_csv(os.path.join(ROOT, "data", "trees.csv"), index=False)
print("trees.csv", len(out))
