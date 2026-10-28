"""Step 6. Build the paper PDF: fill paper_template.tex with numbers and tables from data/results.json,
write release/paper/Hotham_Ancient_Trees.tex and compile it with xelatex (figures from 05_figures.py).
Placeholders: {{path|fmt}} as in 03_build_site.py, with % escaped for LaTeX.
Run: python3 06_paper.py
"""
import json, os, re, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Ancient_Trees"


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f == "int": return f"{int(round(v)):,}"
    if f == "pct0": return f"{v * 100:.0f}\\%"
    if f == "pct1": return f"{v * 100:.1f}\\%"
    if f == "f0": return f"{v:.0f}"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}"
    return str(v)


def sub(m):
    path, _, f = m.group(1).partition("|")
    return fmt(get(path.strip()), f.strip() or "raw")


tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("'", "'")
rows = ""
for s in R["species"]:
    if s["group"] == "other": continue
    g = f"{s['girth_median']:.1f} & {s['girth_max']:.1f}" if s["girth_median"] is not None else "& "
    rows += f"{tex(s['group'])} & {s['n']:,} & {s['share'] * 100:.0f} & {s['old']:,} & {s['girth_n']} & {g}\\\\\n"
TS = ("\\begin{table}[tbp]\\centering\\small\\caption{Notable trees with a known species, by group. Old: with a sign of great age. Girths: notable trees with a credible girth (n, median and largest, metres).}\\label{tab:species}"
      "\\begin{tabular}{lrrrrrr}\\toprule Group & Trees & \\% of known & Old & Girths & Median & Largest\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for f in R["famous"]:
    rows += f"{tex(f['name'])} & {tex(f['place'])} & {tex(f['girth_note'])} & {f['mitchell_years'] if f['mitchell_years'] else ''} & {tex(f['age_text'])}\\\\\n"
TF = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{Eight famous ancient trees: girths and ages as stated in their English Wikipedia articles, and the age implied by Mitchell's rule (2.5 cm of girth a year).}\\label{tab:famous}"
      "\\begin{tabular}{p{2.3cm}p{2.9cm}p{3.2cm}rp{4.3cm}}\\toprule Tree & Place & Girth (Wikipedia) & Mitchell & Age (Wikipedia)\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for b in R["biggest"]:
    rows += f"{tex(b['name'])} & {tex(b['group'])} & {tex(b['place'] or '')}, {tex(b['county'] or '')} & {b['girth']:.2f} & {b['years']}\\\\\n"
TB = ("\\begin{table}[tbp]\\centering\\small\\caption{The named trees with the largest credible girths in OpenStreetMap. Girth as tagged; age by Mitchell's rule.}\\label{tab:big}"
      "\\begin{tabular}{p{4.4cm}p{2.6cm}p{4.6cm}rr}\\toprule Tree & Species & Nearest place & Girth (m) & Mitchell (years)\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
s = open(os.path.join(HERE, "paper_template.tex")).read()
s = s.replace("{{TABLE_SPECIES}}", TS).replace("{{TABLE_FAMOUS}}", TF).replace("{{TABLE_BIG}}", TB)
s = re.sub(r"\{\{(.+?)\}\}", sub, s)
assert "{{" not in s
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w").write(s)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
print(r.stdout[-400:])
for ext in (".aux", ".log", ".out"):
    p = os.path.join(OUT, NAME + ext)
    if os.path.exists(p): os.remove(p)
shutil.move(os.path.join(OUT, NAME + ".pdf"), os.path.join(ROOT, "release", NAME + ".pdf"))
