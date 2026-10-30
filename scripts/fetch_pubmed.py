"""Collect last-N-days PubMed candidates for the weekly internal medicine digest.

Usage:  python scripts/fetch_pubmed.py [--days 7] [--week 2026-W44]

Writes:
  raw/<week>.json            full records with abstracts (gitignored, not republished)
  raw/<week>-titles.txt      one line per record for title screening
  data/<week>.records.json   slim metadata (pmid, journal, title, doi, pmc) used by build.py
"""
import argparse
import datetime
import json
import os
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

JOURNALS = [
    "N Engl J Med", "Lancet", "JAMA", "JAMA Intern Med", "Ann Intern Med", "BMJ", "Nat Med",
    "Lancet Respir Med", "Lancet Infect Dis", "Lancet Diabetes Endocrinol",
    "Lancet Gastroenterol Hepatol", "Lancet Rheumatol", "Lancet Haematol", "Circulation",
    "J Am Coll Cardiol", "Eur Heart J", "Kidney Int", "J Am Soc Nephrol", "Gastroenterology",
    "Hepatology", "Am J Respir Crit Care Med", "Clin Infect Dis", "Diabetes Care",
    "J Clin Endocrinol Metab", "Blood", "J Clin Oncol", "Ann Rheum Dis", "Arthritis Rheumatol",
    "Gut", "J Hepatol",
]
GUIDELINE_TOPICS = (
    "internal medicine OR cardiology OR nephrology OR gastroenterology OR hepatology OR "
    "endocrinology OR infectious OR pulmonary OR rheumatology OR hematology OR diabetes OR hypertension"
)


def get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read()


def search(term, days, retmax):
    q = urllib.parse.urlencode({"db": "pubmed", "term": term, "datetype": "edat",
                                "reldate": days, "retmax": retmax, "retmode": "json"})
    return json.loads(get(BASE + "esearch.fcgi?" + q))["esearchresult"]


def parse(article):
    # PubmedData/ArticleIdList only: a bare .//ArticleIdList also matches reference lists
    ids = {x.get("IdType"): x.text for x in article.findall("./PubmedData/ArticleIdList/ArticleId")}
    abstract = " ".join(
        (x.get("Label") + ": " if x.get("Label") else "") + "".join(x.itertext()).strip()
        for x in article.findall(".//Abstract/AbstractText")
    )
    return {
        "pmid": article.findtext(".//PMID") or "",
        "title": "".join(article.find(".//ArticleTitle").itertext()),
        "journal": article.findtext(".//Journal/ISOAbbreviation") or "",
        "types": [x.text for x in article.findall(".//PublicationType")],
        "doi": ids.get("doi", ""),
        "pmc": ids.get("pmc", ""),
        "abstract": abstract,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--week", help="label like 2026-W44 (default: current ISO week)")
    args = ap.parse_args()
    if not args.week:
        y, w, _ = datetime.date.today().isocalendar()
        args.week = f"{y}-W{w:02d}"

    journals = " OR ".join(f'"{j}"[ta]' for j in JOURNALS)
    a = search(f"({journals}) AND hasabstract", args.days, 1500)
    b = search(f'("Practice Guideline"[pt] OR "Guideline"[pt]) AND ({GUIDELINE_TOPICS})', args.days, 300)
    ids = list(dict.fromkeys(a["idlist"] + b["idlist"]))
    print(f"journal query {a['count']}, guideline query {b['count']}, unique {len(ids)}")

    records = []
    for i in range(0, len(ids), 100):
        q = urllib.parse.urlencode({"db": "pubmed", "id": ",".join(ids[i:i + 100]), "retmode": "xml"})
        root = ET.fromstring(get(BASE + "efetch.fcgi?" + q))
        records += [parse(x) for x in root.findall(".//PubmedArticle")]
        time.sleep(0.4)

    os.makedirs(os.path.join(ROOT, "raw"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    with open(os.path.join(ROOT, "raw", args.week + ".json"), "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=1)
    with open(os.path.join(ROOT, "raw", args.week + "-titles.txt"), "w", encoding="utf-8") as f:
        for r in records:
            types = ",".join(t[:6] for t in r["types"] if t != "Journal Article")
            f.write(f"{r['pmid']} | {r['journal'][:12]} | {types} | {r['title'][:130]}"
                    f"{' | PMC' if r['pmc'] else ''}\n")
    slim = [{k: r[k] for k in ("pmid", "journal", "title", "doi", "pmc")} for r in records]
    with open(os.path.join(ROOT, "data", args.week + ".records.json"), "w", encoding="utf-8") as f:
        json.dump(slim, f, ensure_ascii=False, indent=1)
    print(f"{len(records)} records, {sum(1 for r in records if r['abstract'])} with abstracts, "
          f"{sum(1 for r in records if r['pmc'])} with PMC id -> raw/ and data/ for {args.week}")


if __name__ == "__main__":
    main()
