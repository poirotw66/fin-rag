# Corpus

This corpus is limited to public MOJ/FSC legal and regulatory text. Media reports are not legal sources and are intentionally excluded from retrieval.

The MVP is not legal advice. Answers must cite retrieved public-law text and refuse case-specific penalties, compensation, criminal liability, or unstable news figures.

**Coverage disclaimer:** This is not a complete Taiwan financial law database. Large statutes are ingested as curated article subsets; see `corpus/subsets.yaml`.

## Current Inventory

Phase 4 ingests seventeen public government sources into article-level chunks:

| doc_id | source | chunks (approx.) | track |
|--------|--------|------------------|-------|
| sit-fund-mgmt | MOJ G0400082 | 100 | sit-related-party |
| sit-biz-rules | MOJ G0400078 | 47 | sit-related-party |
| sit-material-event | FSC GL001531 | 3 | sit-reporting |
| aml-finst | MOJ G0380252 | 16 | aml |
| aml-bank-ic | MOJ G0380262 | 11 | aml |
| aml-act | MOJ G0380131 | 58 | aml |
| sit-trust-act | MOJ G0400121 | 102 | sit-related-party |
| privacy-finance | MOJ I0050021 subset | 7 | cross-law |
| sit-securities-act | MOJ G0400001 subset | 4 | sit-related-party |
| sit-advisor-mgmt | MOJ G0400077 | 39 | sit-advisory |
| trust-industry-act | MOJ G0310027 subset | 4 | trust |
| bank-act | MOJ G0380001 subset | 3 | banking |
| insurance-aml-ic | MOJ G0390094 | 10 | aml-insurance |
| fhc-act | MOJ G0380112 subset | 4 | holding |
| futures-act | MOJ G0400100 subset | 3 | futures |

Current total: `409` chunks in `corpus/chunks.jsonl`.

Subset definitions live in `corpus/subsets.yaml`. Full MOJ downloads are kept as `corpus/raw/{doc_id}.full.txt`; working chunk inputs are the extracted `corpus/raw/{doc_id}.txt` files.

## Ingest SOP

### MOJ laws

1. Download the official HTML into `corpus/raw/`:
   - `python scripts/fetch_moj_law.py <pcode> <doc_id>`
2. Convert the MOJ HTML into plain text with standalone article-marker lines:
   - `python scripts/moj_html_to_txt.py <doc_id>`
3. Keep both `{doc_id}.html` and `{doc_id}.txt` under `corpus/raw/`.
4. For subset documents, copy the full text to `{doc_id}.full.txt`, then extract articles:
   - `python scripts/extract_article_subset.py <doc_id> "第 2 條,第 5 條"`

### FSC or other non-MOJ public texts

1. Save the official public text in `corpus/raw/{doc_id}.txt`.
2. Ensure the file uses standalone `第 N 條` heading lines so `chunk_text_by_article()` can split it deterministically.
3. For non-law notices or letters, normalize numbered sections into `第 N 條` headings only when the source does not already provide article markers.

### Rebuild and verify

Run the corpus pipeline from the repository root:

```bash
python scripts/chunk_by_article.py
python scripts/build_index.py
python scripts/spot_check_corpus.py
python -m unittest tests.test_corpus_coverage -v
python eval/run.py
```

`build_index.py` reuses existing embeddings for unchanged chunks and only embeds new or updated articles. It writes:

- `corpus/index.jsonl` — embedding cache for rebuilds
- `corpus/index.faiss` — local FAISS vector index (runtime default when `FIN_RAG_VECTOR_BACKEND=auto`)
- `corpus/index_meta.jsonl` — chunk metadata aligned with the FAISS rows
- `corpus/index_bm25.json` — persisted BM25 lexicon (runtime loads this instead of rebuilding in memory)

Save evaluation baselines when a batch is stable:

```bash
cp eval/last_report.json eval/baseline-phase4.json
```

## Sources

- MOJ laws use `https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=<PCODE>`
- FSC notices use the official FSC law system URL recorded in `corpus/manifest.json`
- `corpus/manifest.json` is the source of truth for `source_url`, `revision_date`, and file format metadata

## Spot-check articles

Required articles for regression checks are listed in `corpus/spot_check.yaml`.

## Baselines

| file | scope |
|------|-------|
| `eval/baseline-phase1.json` | 12 questions, excerpt corpus |
| `eval/baseline-phase2a.json` | 12 questions, five full-text laws |
| `eval/baseline-phase2b.json` | 20 questions, nine statutes (hybrid retrieval; all metrics 1.0) |
| `eval/baseline-phase3.json` | 20 questions, retrieval confidence loop (all metrics 1.0) |
| `eval/baseline-phase4.json` | 26 questions, seventeen statutes (all metrics 1.0) |
