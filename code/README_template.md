# Where are Britain's oldest trees?

Notable, veteran and churchyard trees in OpenStreetMap. Where do the big old trees on the open map stand, which species are they, why are so many ancient yews in churchyards, do former royal forests hold more of them, and how far does girth tell you a tree's age?

**Interactive version:** https://tristan-hotham.github.io/ancient-trees/

This repository holds the interactive page, derived data and the analysis code for the data study *Where are Britain's oldest trees? Notable, veteran and churchyard trees in OpenStreetMap* by Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349). Paper and archived release: https://doi.org/10.5281/zenodo.23729650

**Not used:** the Woodland Trust Ancient Tree Inventory, the fullest record of old trees in the UK, is not open for reuse, so it is not used or reproduced here. Everything comes from open data, and OpenStreetMap trees reflect where volunteers have mapped, not where trees grow.

## Headline results

- My OpenStreetMap extract has {{counts.osm_trees_extract|int}} UK trees with a name, girth, age or similar tag, mostly council survey trees; {{counts.notable|int}} are notable (named, tagged landmark, natural monument, ancient or veteran, or with a credible girth of 3 m or more) and {{counts.old_sign|int}} show a sign of great age.
- Coverage reflects mappers: {{grid.top10_share|pct0}} of notable trees lie in 10 of the {{grid.squares|int}} occupied 10 km squares; {{habits.n|int}} ({{habits.share|pct0}}) are unnamed trees of unknown species tagged landmark or natural monument by a few local mappers. England has {{country.England.n|int}} notable trees, Scotland {{country.Scotland.n|int}}, Wales {{country.Wales.n|int}} and Northern Ireland {{country.Northern Ireland.n|int}}. {{wikidata.found|int}} of {{wikidata.n|int}} Wikidata remarkable or heritage trees are on the map.
- Species are known for {{counts.species_known|int}} notable trees ({{counts.species_known_share|pct0}}). Oaks are {{sp.oak.share|pct0}} of them and {{sp.oak.old_share|pct0}} of those with a sign of great age.
- Yews hug churches: {{church.yew_share|pct0}} of the {{church.yew_n|int}} yews in the extract stand within {{church.m|int}} m of a Christian place of worship, against {{church.other_share|pct1}} of other trees ({{church.ratio|f1}} times as likely); {{church.notable_yew_within|int}} of {{church.notable_yew_n|int}} notable yews do. {{church.yew_kind.anglican or catholic|int}} of the {{church.yew_within|int}} churchyard yews are nearest an Anglican, Church in Wales or Catholic church.
- Within {{forest.km|int}} km of the {{forest.n_forests|int}} Wikidata royal forest points ({{forest.land_share|pct1}} of the land) lie {{forest.old_share|pct1}} of the trees with a sign of great age ({{forest.old_in|int}} trees), led by Savernake (Big Belly Oak {{big.Big Belly Oak.girth|f2}} m, King of Limbs {{big.King of Limbs.girth|f1}} m, Cathedral Oak {{big.Cathedral Oak.girth|f1}} m) and the New Forest.
- {{girth.n|int}} notable trees carry a credible girth; {{girth.ge10|int}} measure 10 m or more, led by the Queen Elizabeth Oak ({{big.Queen Elizabeth Oak.girth|f2}} m). Mitchell's rule of thumb ({{girth.mitchell_cm|f1}} cm of girth a year) gives about {{big.Queen Elizabeth Oak.years|int}} years for it, but badly underestimates the famous ancient yews: about {{fam.Llangernyw Yew.mitchell_years|int}} years for the Llangernyw Yew against the 4,000 to 5,000 claimed.

## Files

- `index.html`: the interactive page (Leaflet map with species, age, churchyard and royal forest filters, place and tree search, charts and tables).
- `header.png`: social card.
- `data/trees.csv`: the {{counts.notable|int}} notable trees, one row per OpenStreetMap node: OSM id, name, species group and tags, denotation, girth as tagged and in metres with a credibility flag, age and start tags, Wikidata id, coordinates, country, region, county and nearest OS Open Names place, distance to the nearest place of worship and its kind, distance to the nearest royal forest point, deer park, and the filter flags. Contains OpenStreetMap data (ODbL).
- `data/species.csv`, `data/regions.csv`, `data/churchyard.csv`, `data/royal_forests.csv`: summary tables.
- `data/famous_trees.csv`: eight famous ancient trees with the girths and ages stated on English Wikipedia, coordinate source and Mitchell's estimate.
- `data/page_data.json`: compact data for the page. `data/results.json`: every number quoted on the page, in the paper, the blog post and the collage.
- `code/`: Python scripts, run in order: `01_prepare.py` (trees, churches, forests, deer parks), `02_analyse.py` (all statistics), `03_build_site.py` (page and README), `04_header.py` (social card), `05_figures.py` (paper and blog figures), `06_paper.py` (paper PDF via xelatex), `07_release.py` (blog post and Zenodo files).
- `release/`: paper PDF and LaTeX source, blog post and figures, Zenodo files. `reddit/`: collage and post text.

## Method in brief

**Trees.** OpenStreetMap natural=tree nodes in the United Kingdom with a name, denotation, age, heritage, Wikidata or circumference tag, retrieved via QLever on {{retrieved|raw}}. Notable: a name (not a fruit variety in an orchard), a denotation of landmark, natural monument, ancient or veteran, an age tag of veteran or 100 years or more, a Wikidata link, a heritage tag, or a credible girth of 3 m or more. Sign of great age: credible girth of 3 m or more, an ancient or veteran tag or an age tag, or a natural monument tag on a named or identified tree.

**Girth.** Circumference tags parsed to metres (bare numbers above 25 read as centimetres). Not credible: outside 0.1 to 16.5 m; ten or more identical values in the same square kilometre (survey defaults; {{counts.extract_girth_bulk|int}} tags); a bare whole number on a tree with no other tags; over 9 m on an unnamed tree without a monument tag. Age by Mitchell's rule of thumb, {{girth.mitchell_cm|f1}} cm of girth a year for an open-grown tree.

**Context.** Churchyard: within {{church.m|int}} m of the centre of one of {{counts.worship|int}} Christian places of worship in OpenStreetMap. Royal forest: within {{forest.km|int}} km of the point Wikidata gives for a former royal forest. Deer parks: OpenStreetMap areas named deer park or tagged historic=deer_park ({{counts.deer_park_polygons|int}} areas). Country, region and county from the nearest OS Open Names populated place.

**Caveats.** OpenStreetMap shows mapped trees, not all trees; regional counts measure mapping effort. Tags are inconsistent. Churchyard and forest tests are distance approximations. Mitchell's rule is a rough guide and fails for ancient trees. Wikipedia's ages are disputed estimates.

## How to rerun

Python 3 with pandas, numpy, scipy, shapely (2.x), pyproj and matplotlib (Playwright for the header, xelatex for the paper). From `code/`: `python3 01_prepare.py && python3 02_analyse.py && python3 03_build_site.py`. Inputs are read one folder up and are not included: `_data12/wd_osm_bundle12.json.gz` (QLever extracts of OpenStreetMap and Wikidata), `_data12/wikipedia_batch12*.json.gz` (English Wikipedia articles), `osnames_gb.tsv` (OS Open Names) and a Natural Earth land outline.

## Sources and licences

- Trees, places of worship and deer parks: © OpenStreetMap contributors, ODbL 1.0, https://www.openstreetmap.org/copyright, retrieved via the QLever OSM endpoint.
- Royal forests and remarkable trees: Wikidata, CC0.
- Famous trees, forest law and veteran trees: English Wikipedia, CC BY-SA 4.0: Fortingall Yew, Llangernyw Yew, Crowhurst Yew, Ashbrittle Yew, Defynnog Yew, Ankerwycke Yew, Major Oak, Bowthorpe Oak, Royal forest, Veteran tree.
- Places: OS Open Names, contains OS data © Crown copyright and database right 2026, Open Government Licence v3.0.
- Coastline: Natural Earth (public domain). Base map tiles on the page: Esri. Map library: Leaflet.
- Not used: Woodland Trust Ancient Tree Inventory (not open for reuse).

`data/trees.csv` contains OpenStreetMap data and is released under the ODbL 1.0. Other derived data, the text and the figures: CC BY-SA 4.0 (they draw on Wikipedia). Code: MIT (see `LICENSE`).

## Citation

Hotham, T. (2026) *Where are Britain's oldest trees? Notable, veteran and churchyard trees in OpenStreetMap*. Zenodo. https://doi.org/10.5281/zenodo.23729650

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
