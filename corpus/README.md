# Corpus

This corpus is limited to public MOJ/FSC legal and regulatory text. Media reports are not legal sources and are intentionally excluded from retrieval.

The MVP is not legal advice. Answers must cite retrieved public-law text and refuse case-specific penalties, compensation, criminal liability, or unstable news figures.

## Current Inventory

Phase 2a ingests five public government sources into article-level chunks:

- `sit-fund-mgmt`: MOJ `G0400082`, revision date `113-12-25`, `100` chunks
- `sit-biz-rules`: MOJ `G0400078`, revision date `113-11-27`, `47` chunks
- `sit-material-event`: FSC `GL001531`, publication date `104-04-14`, `3` chunks
- `aml-finst`: MOJ `G0380252`, revision date `110-12-14`, `16` chunks
- `aml-bank-ic`: MOJ `G0380262`, revision date `110-12-14`, `11` chunks

Current total: `177` chunks in `corpus/chunks.jsonl`.

## Ingest SOP

### MOJ laws

1. Download the official HTML into `corpus/raw/`:
   - `python scripts/fetch_moj_law.py <pcode> <doc_id>`
2. Convert the MOJ HTML into plain text with standalone article-marker lines:
   - `python scripts/moj_html_to_txt.py <doc_id>`
3. Keep both `{doc_id}.html` and `{doc_id}.txt` under `corpus/raw/`.

### FSC or other non-MOJ public texts

1. Save the official public text in `corpus/raw/{doc_id}.txt`.
2. Ensure the file uses standalone `第 N 條` heading lines so `chunk_text_by_article()` can split it deterministically.
3. For non-law notices or letters, normalize numbered sections into `第 N 條` headings only when the source does not already provide article markers.

### Rebuild and verify

Run the corpus pipeline from the repository root:

```bash
python scripts/chunk_by_article.py
python scripts/build_index.py
python -m unittest tests.test_corpus_coverage -v
python eval/run.py
```

Save the current evaluation baseline when the run is stable:

```bash
cp eval/last_report.json eval/baseline-phase2a.json
```

## Sources

- MOJ laws use `https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=<PCODE>`
- FSC notices use the official FSC law system URL recorded in `corpus/manifest.json`
- `corpus/manifest.json` is the source of truth for `source_url`, `revision_date`, and file format metadata

## Current Baseline

- Coverage check: pass
- Eval `total`: `12`
- Eval `citation_hit_rate`: `0.8333`
- Eval `refusal_accuracy`: `0.8333`
- Eval `expected_refs_retrieved_rate`: `0.6667`

