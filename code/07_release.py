"""Step 7. Blog post (release/blog/post.html from blog_template.html), blog and Zenodo meta files,
and the Zenodo folder (paper, key CSVs, results.json and a code-and-data zip).
Image placeholders {{IMG|file|alt|caption}} are left for the uploader (numbers inside them are filled).
Run: python3 07_release.py
"""
import json, os, re, shutil, zipfile
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
spec = importlib.util.spec_from_file_location("b", os.path.join(HERE, "03_build_site.py")); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
R = b.R
t = open(os.path.join(HERE, "blog_template.html")).read()
for _ in range(2):  # inner placeholders inside IMG first, then the rest
    t = re.sub(r"\{\{(?!IMG\|)([^{}|]+(?:\|[a-z0-9]+)?)\}\}", b.sub, t)
open(os.path.join(ROOT, "release", "blog", "post.html"), "w").write(t)
for m in re.findall(r"\{\{IMG\|([^|]+)\|", t):
    assert os.path.exists(os.path.join(ROOT, "release", "blog", m)), m

title = "Where Are Britain's Oldest Trees? Notable, Veteran and Churchyard Trees in OpenStreetMap"
c = R["counts"]
meta = dict(
    title="Where are Britain's oldest trees?",
    slug="ancient-trees",
    excerpt=(f"I mapped the {c['notable']:,} notable trees on OpenStreetMap. Oaks dominate, yews hug the old churches, a few giants stand in the old royal forests, "
             f"and the map shows the mappers as much as the trees."),
    seo_description=f"{c['notable']:,} notable trees on the open map: oaks, churchyard yews and royal forest giants, and how far girth tells a tree's age.",
    tags=["trees", "ancient trees", "yews", "oaks", "churchyards", "royal forests", "OpenStreetMap", "maps"],
    header_alt=(f"Title card reading 'Where are Britain's oldest trees?' on pale paper, beside a map of Britain dotted with notable trees from OpenStreetMap, "
                f"brown for oaks and dark green for yews, bigger dots for bigger girths. Text: {c['notable']:,} notable trees on the open map, {c['old_sign']} with signs of great age. "
                f"Oaks dominate; yews hug churches."))
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
json.dump(meta, open(os.path.join(ROOT, "release", "blog", "meta.json"), "w"), indent=2, ensure_ascii=False)

pt = open(os.path.join(ROOT, "release", "paper", "Hotham_Ancient_Trees.tex")).read()
ab = pt.split("\\begin{center}\\textbf{Abstract}\\end{center}")[1].split("\\textbf{Keywords:}")[0].strip()
ab = ab.replace("\\%", "%").replace("``", "“").replace("''", "”")
Z = os.path.join(ROOT, "release", "zenodo"); os.makedirs(Z, exist_ok=True)
zmeta = dict(
    title=title,
    description_html=f"<p>{ab}</p><p>The Woodland Trust Ancient Tree Inventory was not used because it is not open for reuse. Tree data contain OpenStreetMap data (© OpenStreetMap contributors, ODbL 1.0).</p>"
                     f"<p>Interactive version: https://tristan-hotham.github.io/ancient-trees/. Data and code: https://github.com/Tristan-Hotham/ancient-trees. Blog post: to follow.</p>",
    keywords=["ancient trees", "veteran trees", "churchyard yews", "oaks", "royal forests", "OpenStreetMap", "volunteered geographic information", "tree girth", "Britain", "Wikidata"],
    licence="cc-by-sa-4.0",
    related=[
        dict(identifier="https://github.com/Tristan-Hotham/ancient-trees", relation="issupplementedby", resource_type="software"),
        dict(identifier="https://tristan-hotham.github.io/ancient-trees/", relation="issupplementedby", resource_type="other"),
        dict(identifier="https://www.openstreetmap.org/copyright", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.wikidata.org", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://en.wikipedia.org/wiki/Royal_forest", relation="isderivedfrom", resource_type="other"),
        dict(identifier="https://en.wikipedia.org/wiki/Veteran_tree", relation="isderivedfrom", resource_type="other"),
        dict(identifier="https://www.ordnancesurvey.co.uk/products/os-open-names", relation="isderivedfrom", resource_type="dataset"),
    ])
json.dump(zmeta, open(os.path.join(Z, "meta.json"), "w"), indent=2, ensure_ascii=False)
shutil.copy(os.path.join(ROOT, "release", "Hotham_Ancient_Trees.pdf"), Z)
for f in ["trees.csv", "species.csv", "regions.csv", "churchyard.csv", "royal_forests.csv", "famous_trees.csv", "results.json"]:
    shutil.copy(os.path.join(ROOT, "data", f), Z)
with zipfile.ZipFile(os.path.join(Z, "ancient-trees_code_and_data.zip"), "w", zipfile.ZIP_DEFLATED) as zf:
    for sub in ("code", "data"):
        for f in sorted(os.listdir(os.path.join(ROOT, sub))):
            p = os.path.join(ROOT, sub, f)
            if os.path.isfile(p) and not f.endswith(".pyc"): zf.write(p, f"ancient-trees/{sub}/{f}")
    for f in ("README.md", "LICENSE"): zf.write(os.path.join(ROOT, f), f"ancient-trees/{f}")
print("release files written; post words:", len(re.sub(r"<[^>]+>", " ", re.sub(r"\{\{IMG\|.*?\}\}", "", t, flags=re.S)).split()))
