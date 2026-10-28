## Title

[OC] Where are Britain's oldest trees? I mapped the 1,626 notable trees on OpenStreetMap: yews are 14 times as likely as other trees to stand by a church (18% vs 1.3%), oaks are 47% of trees with a known species, and 42% of the map sits in just 10 of 428 ten-km squares

## Body

I pulled every notable tree in OpenStreetMap for the UK (named, tagged as a landmark, natural monument, ancient or veteran tree, or at least 3 m round) and set them against churches, royal forests and the famous trees on Wikipedia.

Yews hug churches: 32 of the 176 mapped yews stand within 50 m of one, almost all by Anglican or Catholic churches rather than chapels. The biggest girth on the map is the Queen Elizabeth Oak in West Sussex at 13.18 m. The usual girth rule of thumb (2.5 cm a year) makes the Llangernyw Yew about 430 years old; its churchyard certificate says 4,000 to 5,000.

Caveat: this is a map of where volunteers have looked, not of all old trees. The Woodland Trust's Ancient Tree Inventory is not open for reuse, so I did not use it.

Interactive map (find the notable trees near you): https://tristan-hotham.github.io/ancient-trees/

## Source comment

Source: OpenStreetMap natural=tree nodes in the UK, © OpenStreetMap contributors (ODbL 1.0), retrieved 28 October 2026 via QLever; Christian places of worship and deer parks from OpenStreetMap (ODbL); royal forests and remarkable trees from Wikidata (CC0); girths and ages of famous trees from the English Wikipedia articles Fortingall Yew, Llangernyw Yew, Crowhurst Yew, Ashbrittle Yew, Defynnog Yew, Ankerwycke Yew, Major Oak and Bowthorpe Oak, plus Royal forest and Veteran tree (CC BY-SA 4.0); OS Open Names (Contains OS data © Crown copyright and database right 2026, Open Government Licence v3.0); Natural Earth coastline (public domain). Mitchell's rule of thumb from A. Mitchell, A Field Guide to the Trees of Britain and Northern Europe (Collins, 1974). The Woodland Trust Ancient Tree Inventory was not used (not open for reuse).

Tools: Python (pandas, numpy, scipy, shapely, pyproj, matplotlib).

Interactive version: https://tristan-hotham.github.io/ancient-trees/
Blog post: https://blog.tristanhotham.com/2026/10/28/ancient-trees/
Paper and data: https://doi.org/10.5281/zenodo.23729650
