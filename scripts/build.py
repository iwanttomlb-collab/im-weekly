"""Render data/<week>.json into digests/<week>.html and rebuild index.html.

Run from anywhere:  python scripts/build.py
Record metadata (journal, DOI, PMC id) comes from data/<week>.records.json,
which fetch_pubmed.py writes.
"""
import glob
import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "Internal Medicine Weekly"
BADGE = {"pos": "Positive", "neg": "Negative", "neu": "Neutral", "desc": "Descriptive"}
e = html.escape


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def page(title, css, body):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<link rel="stylesheet" href="{css}">
</head>
<body>
<main>
{body}
</main>
</body>
</html>
"""


def ul(items, cls=""):
    c = f' class="{cls}"' if cls else ""
    return f"<ul{c}>" + "".join(f"<li>{e(i)}</li>" for i in items) + "</ul>"


def links(rec, pmid):
    out = [f'<a href="https://pubmed.ncbi.nlm.nih.gov/{pmid}/">PubMed</a>']
    if rec.get("doi"):
        out.append(f'<a href="https://doi.org/{e(rec["doi"])}">DOI</a>')
    if rec.get("pmc"):
        out.append(f'<a href="https://pmc.ncbi.nlm.nih.gov/articles/{rec["pmc"]}/">PMC</a>')
    return " | ".join(out)


def render_digest(d, recs):
    def rec(p):
        return recs.get(p, {})

    def jr(p):
        return e(rec(p).get("journal", ""))

    top = ""
    for n, t in enumerate(d["top"], 1):
        labels = t.get("labels") or [jr(p) for p in t["pmids"]]
        refs = " | ".join(f"{e(lb)}: {links(rec(p), p)}" for lb, p in zip(labels, t["pmids"]))
        top += f"""<section class="card">
<h3><span class="num">{n}</span>{e(t["title"])}</h3>
{ul(t["bullets"])}
<p class="cav"><strong>Caveat:</strong> {e(t["caveat"])}</p>
<p class="lk">{refs}</p>
</section>"""

    guides = "<ul class=\"plain\">"
    for g in d["guidelines"]:
        guides += f"""<li class="card"><strong>{e(g["issuer"])}</strong> - {e(g["title"])} <span class="jr">({jr(g["pmid"])})</span>
{ul(g["bullets"])}
<p class="lk">{links(rec(g["pmid"]), g["pmid"])}</p></li>"""
    guides += "</ul>"

    secs = ""
    for s in d["sections"]:
        secs += f"<h3>{e(s['name'])}</h3>"
        for it in s["items"]:
            secs += f"""<section class="card">
<div class="meta"><span class="badge {it["verdict"]}">{BADGE[it["verdict"]]}</span><span>{e(it["design"])}</span><span class="jr">{jr(it["pmid"])}</span></div>
<h4>{e(it["title"])}</h4>
{ul(it["bullets"])}
<p class="cav"><strong>Caveat:</strong> {e(it["caveat"])}</p>
<p class="lk">{links(rec(it["pmid"]), it["pmid"])}</p>
</section>"""

    c = d["counts"]
    body = f"""<nav><a href="../index.html">All digests</a></nav>
<h1>{SITE}</h1>
<p class="sub">{e(d["week"])} | PubMed entries {e(d["range"])} | generated {e(d["generated"])}</p>
<ul class="stats"><li>{c["candidates"]} candidates screened</li><li>{c["abstracts"]} with abstracts</li><li>{c["pmc"]} with PMC record</li></ul>
<h2>At a glance</h2>
{ul(d["glance"])}
<h2>Top 3 this week</h2>
{top}
<h2>New guidelines and statements</h2>
{guides}
<h2>Research by subspecialty</h2>
{secs}
<h2>Method and limits</h2>
{ul(d["method"], "method")}
"""
    return page(f"{SITE} {d['week']}", "../assets/style.css", body)


def render_index(digests):
    rows = ""
    for d in digests:
        rows += f"""<section class="card">
<h3><a href="digests/{e(d["week"])}.html">{e(d["week"])}</a> <span class="jr">{e(d["range"])}</span></h3>
{ul(d["glance"][:3])}
</section>"""
    body = f"""<h1>{SITE}</h1>
<p class="sub">Weekly brief of new internal medicine guidelines and research, summarized from PubMed abstracts.</p>
{rows}
<p class="method">Summaries are abstract-level and AI-assisted; verify against the linked record before citing.</p>
"""
    return page(SITE, "assets/style.css", body)


def main():
    digests = []
    os.makedirs(os.path.join(ROOT, "digests"), exist_ok=True)
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "????-W??.json"))):
        d = load(path)
        rpath = path.replace(".json", ".records.json")
        recs = {r["pmid"]: r for r in load(rpath)} if os.path.exists(rpath) else {}
        out = os.path.join(ROOT, "digests", d["week"] + ".html")
        with open(out, "w", encoding="utf-8") as f:
            f.write(render_digest(d, recs))
        digests.append(d)
        print("wrote", out)
    digests.sort(key=lambda x: x["week"], reverse=True)
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_index(digests))
    print("wrote index.html with", len(digests), "digest(s)")


if __name__ == "__main__":
    main()
