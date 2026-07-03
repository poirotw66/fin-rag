# Phase 2 Corpus Expansion Design

## Goal

Close out Phase 1 POC, then expand the public-law corpus from MVP excerpts to full MOJ/FSC texts and a controlled set of related regulations—before any retrieval-quality work (hybrid search, vector DB).

## Context

Phase 1 proved:

- Cited answers from public law text
- Refusal on case-specific penalties and compensation
- Reproducible golden-set eval
- CLI + FastAPI + React demo

Current gap: `corpus/manifest.json` lists 5 documents, but `corpus/raw/*.txt` are **article excerpts** (~11 chunks total). Phase 2 makes the corpus **real and broader**, not smarter retrieval yet.

## Principles

1. **Government public sources only** — MOJ law database, FSC circulars/letters.
2. **No media in corpus** — ETtoday and similar stay as blog anchors and refusal tests only.
3. **One article per chunk** — keep `chunk_strategy: by_article` for citation eval.
4. **Eval leads ingest** — add 2–3 golden questions per new document batch.
5. **Separate tracks** — law golden (A/B/C) stays separate from future enforcement news (track D).
6. **Retrieval optimization is Phase 3** — hybrid BM25, score thresholds, FAISS only after chunk count is materially larger (~100+).

## Phases

```text
Phase 1 closeout     → commit, eval baseline, env docs
Phase 2a complete    → full text for existing 5 docs + rebuild index
Phase 2b expand      → add 3–4 related laws in two batches
Phase 2c eval grow   → golden 12 → ~18 questions, new baseline report
Phase 3 (later)      → hybrid retrieval, low-score refusal, optional FAISS
```

## Corpus inventory

### Existing (complete to full text)

| doc_id | title | MOJ pcode | track |
|--------|-------|-----------|-------|
| sit-fund-mgmt | 證券投資信託基金管理辦法 | G0400082 | sit-related-party |
| sit-biz-rules | 證券投資信託事業管理規則 | G0400081 | sit-related-party |
| sit-material-event | 投信投顧重大偶發事件通報 | FSC letter (manual) | sit-reporting |
| aml-finst | 金融機構防制洗錢辦法 | G0380252 | aml |
| aml-bank-ic | 銀行業…內部控制與稽核制度實施辦法 | manual / MOJ | aml |

### Batch 1 additions (after 2a)

| doc_id | title | MOJ pcode | track | rationale |
|--------|-------|-----------|-------|-----------|
| aml-act | 洗錢防制法 | G0380046 | aml | AML legal basis; spec optional item |
| sit-trust-act | 證券投資信託及顧問法 | G0400006 | sit-related-party | Trust relationship, beneficiary duties |

### Batch 2 additions (optional, after batch 1 eval stable)

| doc_id | title | source | track | rationale |
|--------|-------|--------|-------|-----------|
| privacy-finance | 個人資料保護法（金融客戶資料節錄） | G0370026 subset | cross-law | Links to CDD data retention |
| sit-securities-act | 證券交易法（關係人／董事義務節錄） | G0400001 subset | sit-related-party | Related-party governance |

### Explicitly out of scope (Phase 2)

- Enforcement press releases (`track: enforcement`) — separate eval file later
- Full Bank Act
- Media full text
- Internal bank policies

## Data pipeline (unchanged mechanics)

```text
manifest.json
    → corpus/raw/{doc_id}.txt|.html
    → scripts/chunk_by_article.py → corpus/chunks.jsonl
    → scripts/build_index.py (Gemini embed) → corpus/index.jsonl
    → eval/run.py
```

Optional: `scripts/fetch_moj_law.py <pcode> <doc_id>` for MOJ HTML download; convert or parse to plain text if chunker expects `format: txt`.

## Success criteria

| Milestone | Metric |
|-----------|--------|
| Phase 1 closeout | Git tag or commit; `eval/last_report.json` saved as `eval/baseline-phase1.json` |
| Phase 2a | Chunk count >> 11 (expect 80–200+ for 5 full laws); spot-check articles present |
| Phase 2b batch 1 | +2 docs in manifest; +4–6 golden questions; eval still runnable |
| Phase 2c | `citation_hit_rate` and `refusal_accuracy` ≥ Phase 1 baseline on tracks A/B/C |
| Ready for Phase 3 | Chunk count ≥ 100; documented in `corpus/README.md` |

## Golden set growth (draft)

Keep existing B1–B5, A1–A5, C1–C2. Add:

| id | track | question (draft) | expected_refs |
|----|-------|------------------|---------------|
| A6 | A | 洗錢防制法對金融機構的主要義務為何？ | aml-act 相關條 |
| A7 | A | 防制洗錢主管機關為何？ | aml-act 相關條 |
| B6 | B | 證券投資信託契約應記載哪些受益人權益事項？ | sit-trust-act 相關條 |
| B7 | B | 投信事業負責人對受益人負何種義務？ | sit-trust-act 相關條 |
| E1 | cross-law | 金融機構處理客戶個資應遵循何種原則？ | privacy-finance（batch 2） |

Track C unchanged — still 2 refusal questions.

## Risks

| Risk | Mitigation |
|------|------------|
| MOJ HTML parsing breaks article split | Spot-check script; keep raw + manual txt fallback |
| Full ingest increases embedding cost | One-time `build_index.py`; document chunk count |
| Eval regression after corpus growth | Save phase baselines; fix golden expected_refs to match ingested articles |
| Law revision drift | Update `revision_date` in manifest; note in eval report |

## References

- [spec.md](../../../spec.md) — Phase 2 expansion table, tracks A/B/C
- [readme-tw.md](../../../readme-tw.md) — architecture and demo flow
- [corpus/README.md](../../../corpus/README.md) — corpus disclaimer
