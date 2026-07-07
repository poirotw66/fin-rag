# Phase 5 Subset Expansion Design

## Goal

Move Fin RAG from a **vertical MVP** toward a **multi-sector financial regulations assistant** by **deepening existing article subsets** (not full-statute ingest). Preserve eval-led ingest, one-article-per-chunk, and hybrid retrieval.

## Context

| Milestone | Statutes (`doc_id`) | Chunks | Golden | Baseline |
|-----------|---------------------|--------|--------|----------|
| Phase 4 | 15 | 409 | 26 | `eval/baseline-phase4.json` (1.0) |
| **Phase 5 target** | **16** | **~520–540** | **~34** | `eval/baseline-phase5.json` |

Phase 4 added six laws mostly as **3–4 article excerpts**; depth per sector is thin. Phase 5 buys **answerable breadth** without bank-act full text (~300+ chunks).

## Principles (unchanged)

1. Government public sources only (MOJ / FSC).
2. **Subset only** for large statutes — no full Bank Act, Insurance Act, etc.
3. One article per chunk; `chunk_strategy: by_article`.
4. **Eval leads ingest** — each batch adds golden questions before baseline freeze.
5. Separate tracks in `manifest.json` (`track` field); no hard-coded retrieval hints.
6. Corpus disclaimer: not a complete law database; not legal advice.

## Approach Options (user chose **balanced A**)

| Option | Per-subset add | New `doc_id` | Est. Δ chunks | Golden Δ | Risk |
|--------|----------------|--------------|---------------|----------|------|
| **5a Conservative** | +8 articles | 0 | ~+55 → ~465 | +6 | Low coverage gain |
| **5b Recommended** | +10 articles | +1 (`insurance-act`) | ~+115 → ~525 | +8 | Balanced ROI |
| **5c Stretch** | +12 articles | +2 | ~+150 → ~560 | +10 | Eval / retrieval tuning |

**Decision: Phase 5b (Recommended).**

Rationale: ~115 new chunks keeps embedding cost modest, clears ~500 chunk psychological bar, and `insurance-act` closes the “有保險 AML 但沒保險法” narrative gap.

## Scope

### In scope

- Expand six existing subset documents (see table below).
- Add **`insurance-act`** as MOJ subset (`G0390002`).
- Update `corpus/subsets.yaml`, `manifest.json`, `spot_check.yaml`, `KNOWN_DOC_IDS`.
- Rebuild `chunks.jsonl` + index; extend `eval/golden.yaml`.
- Freeze `eval/baseline-phase5.json`; update `corpus/README.md`, `readme-tw.md`, `README.md`.

### Out of scope

- Full-text ingest of any major statute.
- New retrieval architecture (track boost, FAISS tuning) unless eval regresses.
- Enforcement news track (track D).
- Web/UI feature work beyond coverage text.

## Subset inventory (Phase 5b)

Existing articles are **retained**; tables list **articles to add**.

### `bank-act` (track: `banking`) — +10 → 13 total

| Article | Theme |
|---------|--------|
| 第 12 條 | Capital / financial business soundness |
| 第 25 條 | Stock holding limits |
| 第 29 條 | Deposit types |
| 第 32 條 | Credit limits to same person / related parties |
| 第 44 條 | Internal control |
| 第 45 條 | Supervisory examination |
| 第 61 條 | Prohibited transactions |
| 第 64 條 | Confidentiality |
| 第 72 條 | Mid-term loan limits |
| 第 125 條 | Penalty framework (general, not case-specific) |

### `trust-industry-act` (track: `trust`) — +10 → 14 total

| Article | Theme |
|---------|--------|
| 第 7 條 | Licensing / establishment |
| 第 10 條 | Business approval |
| 第 19 條 | Segregation of trust property |
| 第 24 條 | Trust contract requirements |
| 第 25 條 | Trustee duties |
| 第 27 條 | Loyalty / care obligations |
| 第 35 條 | AML compliance |
| 第 40 條 | Confidentiality |
| 第 46 條 | Supervision |
| 第 48 條 | Penalties (general) |

### `fhc-act` (track: `holding`) — +10 → 14 total

| Article | Theme |
|---------|--------|
| 第 5 條 | Financial holding company definition |
| 第 6 條 | Application requirements |
| 第 16 條 | Capital |
| 第 18 條 | Merger |
| 第 25 條 | Internal control |
| 第 37 條 | Investment in non-financial businesses |
| 第 41 條 | Customer data sharing limits |
| 第 44 條 | Examination |
| 第 51 條 | Penalties (general) |
| 第 55 條 | Supplementary provisions |

### `futures-act` (track: `futures`) — +10 → 13 total

| Article | Theme |
|---------|--------|
| 第 7 條 | Futures exchanges |
| 第 18 條 | Trading rules |
| 第 57 條 | FCM business scope |
| 第 64 條 | Customer account rules |
| 第 73 條 | Disclosure |
| 第 79 條 | Leverage dealer rules |
| 第 88 條 | Futures association |
| 第 95 條 | Supervision |
| 第 106 條 | Confidentiality |
| 第 112 條 | Penalties (general) |

### `privacy-finance` (track: `cross-law`) — +8 → 15 total

| Article | Theme |
|---------|--------|
| 第 3 條 | Territorial scope |
| 第 7 條 | Special non-public agency duties |
| 第 12 條 | Notice / consent |
| 第 29 條 | Rights to access / copy |
| 第 30 條 | Rights to correct / delete |
| 第 39 條 | Security measures |
| 第 41 條 | Breach notification |
| 第 48 條 | Civil liability (general) |

### `sit-securities-act` (track: `sit-related-party`) — +8 → 12 total

| Article | Theme |
|---------|--------|
| 第 14-4 條 | Audit committee |
| 第 14-6 條 | Compensation committee |
| 第 43 條 | Major shareholder reporting |
| 第 43-1 條 | Disclosure format |
| 第 43-5 條 | Short-swing profit disgorgement |
| 第 174 條 | Insider trading prohibition |
| 第 174-1 條 | Insider definition |
| 第 178 條 | Penalties (general) |

### `insurance-act` (NEW, track: `insurance`) — 10 articles

MOJ pcode: `G0390002`. Title: **保險法（保險業與契約節錄）**.

| Article | Theme |
|---------|--------|
| 第 1 條 | Scope / classification |
| 第 2 條 | Definition of insurance |
| 第 55 條 | Policy mandatory clauses |
| 第 136 條 | Insurance industry scope |
| 第 137 條 | Establishment permit |
| 第 138 條 | Capital / fund requirements |
| 第 143 條 | Business rules |
| 第 149 條 | Supervision |
| 第 166 條 | Penalties (general) |
| 第 174 條 | Supplementary |

## Data pipeline

```text
subsets.yaml (source of truth for article lists)
    → ensure corpus/raw/{doc_id}.full.txt exists (fetch if missing)
    → scripts/extract_article_subset.py per subset doc
    → scripts/chunk_by_article.py
    → scripts/build_index.py (incremental embeddings)
    → scripts/spot_check_corpus.py
    → eval/run.py → baseline-phase5.json
```

For `insurance-act`:

```bash
python scripts/fetch_moj_law.py G0390002 insurance-act
python scripts/moj_html_to_txt.py insurance-act
cp corpus/raw/insurance-act.txt corpus/raw/insurance-act.full.txt
python scripts/extract_article_subset.py insurance-act "<article list>"
```

## Golden set growth (draft +8 → 34 total)

| id | track | question (draft) | expected_refs |
|----|-------|------------------|---------------|
| A10 | A | 銀行對同一關係人授信餘額有何比例限制？ | bank-act 第 32 條 |
| A11 | A | 保險業經營業務應經主管機關何種許可？ | insurance-act 第 137 條 |
| B10 | B | 受託人辦理信託業務對委託人負何種義務？ | trust-industry-act 第 27 條 |
| B11 | B | 期貨商受託從事期貨交易之業務範圍為何？ | futures-act 第 57 條 |
| E7 | E | 非公務機關告知當事人個資利用情形有何義務？ | privacy-finance 第 12 條 |
| E8 | E | 公開發行公司大股東持股變動應如何申報？ | sit-securities-act 第 43 條 |
| E9 | E | 金融控股公司投資非金融事業之持股上限為何？ | fhc-act 第 37 條 |
| E10 | E | 保險契約應記載哪些基本事項？ | insurance-act 第 55 條 |

Track C (refusal) unchanged: C1, C2.

## Success criteria

| Metric | Target |
|--------|--------|
| Chunk count | 520–540 |
| `doc_id` count | 16 |
| Golden questions | 34 |
| `citation_hit_rate` | ≥ Phase 4 baseline (1.0) |
| `refusal_accuracy` | ≥ 1.0 |
| `expected_refs_retrieved_rate` | ≥ 0.96 (allow minor LLM flake; re-run if below) |
| `spot_check_corpus.py` | pass |
| `run_tests.py` | pass |

## External messaging (post Phase 5)

> Fin RAG 收錄 **16 份** MOJ/FSC 公開法規（**~530 條文 chunks**），涵蓋投信／投顧、AML、銀行授信、保險（含 AML 內控與保險法節錄）、信託、金控、期貨、個資與證交法董事義務等。**多數大法為精選條文子集，非全文。** 不構成法律意見。

## Risks

| Risk | Mitigation |
|------|------------|
| Retrieval noise as corpus grows | Keep subsets curated; eval per batch; no full bank act |
| Golden / citation flake (CDD-style) | Existing policy-misrefusal retry; add procedure markers if needed |
| Article numbering drift (e.g. 第 43-5 條) | `spot_check.yaml` + `extract_articles` tests |
| insurance-act fetch wrong pcode | Verify title after `moj_html_to_txt.py` |
| Chunk count overshoot | Cap at listed articles; defer 5c stretch items |

## References

- [Phase 2 design](2026-07-03-phase-2-corpus-expansion-design.md)
- `corpus/subsets.yaml`, `corpus/manifest.json`
- `eval/baseline-phase4.json`
