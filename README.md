# Where are Britain's oldest trees?

Notable, veteran and churchyard trees in OpenStreetMap. Where do the big old trees on the open map stand, which species are they, why are so many ancient yews in churchyards, do former royal forests hold more of them, and how far does girth tell you a tree's age?

**Interactive version:** https://tristan-hotham.github.io/ancient-trees/

This repository holds the interactive page, derived data and the analysis code for the data study *Where are Britain's oldest trees? Notable, veteran and churchyard trees in OpenStreetMap* by Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349). Paper and archived release: https://doi.org/10.5281/zenodo.23729650

**Not used:** the Woodland Trust Ancient Tree Inventory, the fullest record of old trees in the UK, is not open for reuse, so it is not used or reproduced here. Everything comes from open data, and OpenStreetMap trees reflect where volunteers have mapped, not where trees grow.

## Headline results

- My OpenStreetMap extract has 70,394 UK trees with a name, girth, age or similar tag, mostly council survey trees; 1,626 are notable (named, tagged landmark, natural monument, ancient or veteran, or with a credible girth of 3 m or more) and 276 show a sign of great age.
- Coverage reflects mappers: 42% of notable trees lie in 10 of the 428 occupied 10 km squares; 655 (40%) are unnamed trees of unknown species tagged landmark or natural monument by a few local mappers. England has 1,497 notable trees, Scotland 92, Wales 27 and Northern Ireland 10. 48 of 90 Wikidata remarkable or heritage trees are on the map.
- Species are known for 579 notable trees (36%). Oaks are 47% of them and 51% of those with a sign of great age.
- Yews hug churches: 18% of the 176 yews in the extract stand within 50 m of a Christian place of worship, against 1.3% of other trees (13.7 times as likely); 21 of 32 notable yews do. 28 of the 32 churchyard yews are nearest an Anglican, Church in Wales or Catholic church.
- Within 5 km of the 38 Wikidata royal forest points (1.3% of the land) lie 4.7% of the trees with a sign of great age (13 trees), led by Savernake (Big Belly Oak 11.18 m, King of Limbs 10.8 m, Cathedral Oak 10.4 m) and the New Forest.
- 150 notable trees carry a credible girth; 10 measure 10 m or more, led by the Queen Elizabeth Oak (13.18 m). Mitchell's rule of thumb (2.5 cm of girth a year) gives about 527 years for it, but badly underestimates the famous ancient yews: about 430 years for the Llangernyw Yew against the 4,000 to 5,000 claimed.

## Files

- `index.html`: the interactive page (Leaflet map with species, age, churchyard and royal forest filters, place and tree search, charts and tables).
- `header.png`: social card.
- `data/trees.csv`: the 1,626 notable trees, one row per OpenStreetMap node: OSM id, name, species group and tags, denotation, girth as tagged and in metres with a credibility flag, age and start tags, Wikidata id, coordinates, country, region, county and nearest OS Open Names place, distance to the nearest place of worship and its kind, distance to the nearest royal forest point, deer park, and the filter flags. Contains OpenStreetMap data (ODbL).
- `data/species.csv`, `data/regions.csv`, `data/churchyard.csv`, `data/royal_forests.csv`: summary tables.
- `data/famous_trees.csv`: eight famous ancient trees with the girths and ages stated on English Wikipedia, coordinate source and Mitchell's estimate.
- `data/page_data.json`: compact data for the page. `data/results.json`: every number quoted on the page, in the paper, the blog post and the collage.
- `code/`: Python scripts, run in order: `01_prepare.py` (trees, churches, forests, deer parks), `02_analyse.py` (all statistics), `03_build_site.py` (page and README), `04_header.py` (social card), `05_figures.py` (paper and blog figures), `06_paper.py` (paper PDF via xelatex), `07_release.py` (blog post and Zenodo files).
- `release/`: paper PDF and LaTeX source, blog post and figures, Zenodo files. `reddit/`: collage and post text.

## Method in brief

**Trees.** OpenStreetMap natural=tree nodes in the United Kingdom with a name, denotation, age, heritage, Wikidata or circumference tag, retrieved via QLever on 28 October 2026. Notable: a name (not a fruit variety in an orchard), a denotation of landmark, natural monument, ancient or veteran, an age tag of veteran or 100 years or more, a Wikidata link, a heritage tag, or a credible girth of 3 m or more. Sign of great age: credible girth of 3 m or more, an ancient or veteran tag or an age tag, or a natural monument tag on a named or identified tree.

**Girth.** Circumference tags parsed to metres (bare numbers above 25 read as centimetres). Not credible: outside 0.1 to 16.5 m; ten or more identical values in the same square kilometre (survey defaults; 1,498 tags); a bare whole number on a tree with no other tags; over 9 m on an unnamed tree without a monument tag. Age by Mitchell's rule of thumb, 2.5 cm of girth a year for an open-grown tree.

**Context.** Churchyard: within 50 m of the centre of one of 38,811 Christian places of worship in OpenStreetMap. Royal forest: within 5 km of the point Wikidata gives for a former royal forest. Deer parks: OpenStreetMap areas named deer park or tagged historic=deer_park (76 areas). Country, region and county from the nearest OS Open Names populated place.

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
