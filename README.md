# Internal Medicine Weekly

Static site: a weekly bullet-style brief of new internal medicine guidelines and research, built from PubMed.

## Layout

| Path | Purpose |
|---|---|
| `index.html` | Archive page, generated |
| `digests/<week>.html` | One page per week, generated |
| `data/<week>.json` | Hand-curated digest content (bullets, caveats, PMIDs) |
| `data/<week>.records.json` | Slim PubMed metadata (journal, DOI, PMC id) |
| `scripts/fetch_pubmed.py` | Collects the last 7 days of candidates |
| `scripts/build.py` | Renders `data/` into `digests/` and `index.html` |
| `raw/` | Full abstracts, gitignored (not republished) |

## Weekly workflow

1. Collect candidates (Python 3.9+, no dependencies):

   ```bash
   python scripts/fetch_pubmed.py
   ```

2. Screen `raw/<week>-titles.txt`, then ask Claude to read the abstracts in `raw/<week>.json` for the chosen PMIDs and write `data/<week>.json` in the same schema as `data/2026-W44.json` (glance, top, guidelines, sections, counts, method).
3. Build:

   ```bash
   python scripts/build.py
   ```

4. Commit and push; Pages republishes.

## Publish on GitHub Pages

1. Create an empty repository on GitHub (for example `im-weekly`).
2. From this folder:

   ```bash
   git init
   git add .
   git commit -m "Initial digest site"
   git branch -M main
   git remote add origin https://github.com/<your-user>/im-weekly.git
   git push -u origin main
   ```

3. Repository Settings, Pages, Source: Deploy from a branch, Branch: `main`, folder `/ (root)`.
4. Site appears at `https://<your-user>.github.io/im-weekly/`.

All links are relative, so the site works under the repository sub-path. `.nojekyll` disables Jekyll processing.

## Notes

- Summaries are abstract-level and AI-assisted; each entry links to PubMed, DOI, and PMC (when available).
- Full abstracts are kept out of the repository (`raw/` is gitignored) because abstracts are publisher content.
- The page text states its own limits: scope exclusions (oncology, neurology, pediatrics) and unsearched sources (preprints, society sites without PubMed indexing).
