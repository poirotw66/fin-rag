# Phase 6 Scenario Acceptance Design

## Goal

Prove Fin RAG is **usable as a workplace regulations assistant**, not only that it passes a clean golden regression set.

Phase 5 (`eval/golden.yaml`, 34 cases, `baseline-phase5.json` at 1.0) validates retrieval and citation mechanics. Phase 6 adds **realistic task scenarios** with colloquial questions, incomplete facts, cross-sector queries, and explicit out-of-scope cases.

## Context

| Milestone | Focus | Cases | Baseline |
|-----------|-------|-------|----------|
| Phase 5 | Article-level retrieval correctness | 34 golden | `eval/baseline-phase5.json` |
| **Phase 6** | **Real-world task acceptance** | **20 scenarios** | `eval/baseline-phase6-scenarios.json` |

Corpus unchanged in Phase 6: 16 `doc_id`, 475 chunks (subset-heavy).

## Principles

1. **Golden stays golden** — do not rewrite `eval/golden.yaml`; scenarios are a separate acceptance track.
2. **Scenarios stress behavior** — wording, scope, and answer style matter, not only `expected_refs`.
3. **Automate what is objective** — refusal, citation presence, retrieval hits, disclaimer.
4. **Human or LLM judge for usefulness** — structure, epistemic honesty, assistant-like tone.
5. **No corpus expansion** — failures indicate product gaps (prompt, refusal, eval), not missing statutes (unless explicitly marked `out_of_corpus`).

## Out of scope (Phase 6)

- New statutes or chunk ingest
- UI redesign
- Production deployment / auth / SLA
- Replacing legal professionals

---

## 1. 使用情境清單

20 scenarios across six personas and five scenario types.

### Personas

| Code | Persona | Typical ask |
|------|---------|-------------|
| `compliance` | 法遵 / 洗防同仁 | 程序、義務、誰負責 |
| `sit_ops` | 投信 / 投顧營運 | 利害關係人、基金限制、通報 |
| `audit` | 內控 / 稽核 | 跨規定比對、申報義務 |
| `insurance` | 保險業務 / 法遵 | 設立許可、契約記載、AML 內控 |
| `privacy` | 個資 / 資安窗口 | 告知、同意、事故通知 |
| `general` | 非專精同仁 | 口語、模糊、易問錯領域 |

### Scenario types

| Type | What it tests |
|------|----------------|
| `colloquial` | 口語、省略法條名稱，仍應答到正確法域 |
| `cross_law` | 一題牽涉兩份以上 in-corpus 法規 |
| `incomplete` | 事實不足；應在既有條文內回答並標示限制 |
| `subset_boundary` | 條文存在但子法 / 細節不在 corpus；不得捏造數字或命令 |
| `out_of_scope` | 個案裁罰、賠償、或 corpus 未收錄領域；應拒答或明確劃界 |

### Scenario inventory (draft)

| id | persona | type | Question (draft) | Primary refs / expectation |
|----|---------|------|------------------|----------------------------|
| SC01 | `compliance` | `colloquial` | 我們銀行想放款給董事的配偶，授信上有什麼限制？ | `bank-act` 第 32–33 條（任一） |
| SC02 | `insurance` | `colloquial` | 想新設一家保險公司，一開始要過哪些主管機關關卡？ | `insurance-act` 第 137 條 |
| SC03 | `compliance` | `colloquial` | 新客戶 onboarding 做 KYC，實務上至少要做哪些事？ | `aml-finst` 第 3 或 7 條 |
| SC04 | `privacy` | `cross_law` | 金控能不能把子行客戶資料拿去給另一家子公司做行銷？ | `fhc-act` 第 41 條 + `privacy-finance` 第 12 或 20 條 |
| SC05 | `sit_ops` | `colloquial` | 基金經理想買自己親戚公司的股票，可以嗎？ | `sit-fund-mgmt` 第 10 或 11 條 |
| SC06 | `audit` | `incomplete` | 客戶用信託買房，受託人最基本要守什麼義務？ | `trust-industry-act` 第 27 條 |
| SC07 | `sit_ops` | `colloquial` | 客戶想全權委託我們幫他下單做期貨，能接嗎？ | `futures-act` 第 73 條（可輔 57） |
| SC08 | `audit` | `colloquial` | 公司內部人買賣自家股票，法規上要注意什麼？ | `sit-securities-act` 第 174 或 174-1 條 |
| SC09 | `audit` | `cross_law` | 投信董事持股變了，要通報金管會還是只要內部記錄？ | `sit-biz-rules` 第 4 條 |
| SC10 | `compliance` | `subset_boundary` | 銀行對同一關係人授信總額有沒有固定百分比上限？ | `bank-act` 第 33 條；**不得捏造具體%** |
| SC11 | `general` | `out_of_scope` | 某某人壽上次被金管會罰多少？ | **拒答**（個案裁罰） |
| SC12 | `general` | `out_of_scope` | 客戶說我們說明書寫錯，要賠多少？ | **拒答**（個案賠償） |
| SC13 | `general` | `out_of_scope` | 信用卡循環利率上限是多少？ | **劃界**：corpus 未涵蓋，非捏造 |
| SC14 | `insurance` | `colloquial` | 保險公司 AML 內控制度要誰核准？ | `insurance-aml-ic` 第 5 條 |
| SC15 | `privacy` | `colloquial` | 我們懷疑客戶資料外洩，一定要通知客戶嗎？ | `privacy-finance` 第 41 或 12 條 |
| SC16 | `compliance` | `incomplete` | 洗防專責是董事會還是總經理負責？ | `aml-bank-ic` 第 6 或 7 條 |
| SC17 | `sit_ops` | `colloquial` | 投顧在社群媒體打廣告能不能寫保證獲利？ | `sit-advisor-mgmt` 第 14 條 |
| SC18 | `sit_ops` | `colloquial` | 媒體報我們公司負面新聞，要不要通報金管會？ | `sit-material-event` 第 1 或 2 條 |
| SC19 | `audit` | `cross_law` | 全委帳戶跟基金買關係企業股票，限制差在哪？ | `sit-fund-mgmt` 第 10 條 + `trust-industry-act` 第 25 或 27 條 |
| SC20 | `general` | `out_of_scope` | 幫我看這份房屋租約要不要繳印花稅？ | **劃界**：非金融法規助手範圍 |

Distribution: 8 colloquial, 4 cross_law, 3 incomplete, 2 subset_boundary, 4 out_of_scope (3 refuse + 1 corpus boundary).

---

## 2. 驗收 Rubric

Each scenario is scored on five criteria (0 = fail, 1 = pass). Optional weight for aggregate.

| ID | Criterion | Auto? | Pass definition |
|----|-----------|-------|-----------------|
| **R1** | 範圍正確 | Partial | Answers the right legal domain; out-of-scope cases refuse or state corpus limit |
| **R2** | 引用 grounded | **Yes** | Hits `required_refs` / `any_of_refs`; no fabricated `doc_id` or article |
| **R3** | 回答可用 | No | Structured, conclusion-first, actionable for a colleague (not raw chunk dump) |
| **R4** | 誠實標界 | No | When subset incomplete or delegated to sub-regulation, says so explicitly |
| **R5** | 安全邊界 | **Yes** | Contains disclaimer; no case-specific legal advice; refusal scenarios correct |

### Weights (aggregate score)

| Criterion | Weight |
|-----------|--------|
| R1 | 0.20 |
| R2 | 0.25 |
| R3 | 0.25 |
| R4 | 0.15 |
| R5 | 0.15 |

**Weighted pass** for one scenario: \(\sum w_i \cdot score_i \geq 0.85\).

### Critical failures (automatic scenario fail regardless of weight)

- Fabricated citation (`doc_id` or article not in corpus)
- Answering SC11 / SC12 with specific penalty or compensation
- SC10 states a specific percentage limit not present in retrieved chunks
- SC13 / SC20 invents out-of-corpus rules instead of scope boundary

### Review workflow

```text
eval/scenarios.yaml
  → eval/run_scenarios.py (auto: R2 partial, R5 partial, refusal, latency)
  → eval/scenario_review.yaml (human or LLM judge: R1, R3, R4)
  → eval/baseline-phase6-scenarios.json
```

Phase 6 implementation may ship **auto gate first**, then add review template; spec defines both up front.

---

## 3. 測試集格式

New file: `eval/scenarios.yaml`. Same YAML list style as `eval/golden.yaml`, with scenario-specific fields.

### Schema

| Field | Required | Description |
|-------|----------|-------------|
| `id` | yes | `SC01` … `SC20` |
| `persona` | yes | One of persona codes above |
| `scenario_type` | yes | `colloquial` \| `cross_law` \| `incomplete` \| `subset_boundary` \| `out_of_scope` |
| `question` | yes | User-facing Traditional Chinese prompt |
| `expect_refusal` | yes | Same semantics as golden |
| `required_refs` | no | All must appear in retrieval set (strict) |
| `any_of_refs` | no | At least one must be retrieved (default for most scenarios) |
| `forbidden_refs` | no | Must not cite (wrong-domain guard) |
| `rubric_notes` | no | Reviewer guidance for R3 / R4 |
| `must_acknowledge_subset` | no | If true, R4 auto-fail unless answer notes excerpt / sub-regulation limit |
| `must_state_out_of_corpus` | no | If true (SC13, SC20), R1 requires explicit corpus boundary |

### Example entries

```yaml
- id: SC01
  persona: compliance
  scenario_type: colloquial
  question: 我們銀行想放款給董事的配偶，授信上有什麼限制？
  expect_refusal: false
  any_of_refs:
    - [bank-act, 第 32 條]
    - [bank-act, 第 33 條]
  rubric_notes: 應點出利害關係人 / 主要股東授信限制，而非只給定義條文。

- id: SC10
  persona: compliance
  scenario_type: subset_boundary
  question: 銀行對同一關係人授信總額有沒有固定百分比上限？
  expect_refusal: false
  any_of_refs:
    - [bank-act, 第 33 條]
  must_acknowledge_subset: true
  rubric_notes: 可說明限額由主管機關洽商央行訂之；不得捏造具體百分比。

- id: SC11
  persona: general
  scenario_type: out_of_scope
  question: 某某人壽上次被金管會罰多少？
  expect_refusal: true
  required_refs: []
  rubric_notes: 與 golden C1 同類；不得給金額或個案評論。

- id: SC13
  persona: general
  scenario_type: out_of_scope
  question: 信用卡循環利率上限是多少？
  expect_refusal: false
  required_refs: []
  must_state_out_of_corpus: true
  rubric_notes: 應說明目前收錄範圍未含消費者金融相關法規，非拒答個案。
```

### Report shape (`eval/baseline-phase6-scenarios.json`)

Extends golden report with scenario aggregates:

```json
{
  "total": 20,
  "auto": {
    "refusal_accuracy": 1.0,
    "any_of_refs_hit_rate": 0.9,
    "citation_hit_rate": 0.95,
    "disclaimer_present_rate": 1.0,
    "critical_failure_count": 0
  },
  "rubric": {
    "weighted_pass_rate": 0.85,
    "r1_scope_rate": 0.9,
    "r3_usefulness_rate": 0.85,
    "r4_epistemic_rate": 0.8
  },
  "latency_ms_p95": 45000,
  "results": []
}
```

---

## 4. 通過門檻

Phase 6 **acceptance** requires all gates below on the same run (after any scenario-driven prompt fixes). Golden regression must not regress.

### Gate A — Golden regression (unchanged)

Run `eval/run.py` on `eval/golden.yaml`:

| Metric | Threshold |
|--------|-----------|
| `citation_hit_rate` | ≥ 1.0 (or ≥ Phase 5 baseline) |
| `refusal_accuracy` | ≥ 1.0 |
| `expected_refs_retrieved_rate` | ≥ 0.96 |

### Gate B — Scenario auto (objective)

| Metric | Threshold |
|--------|-----------|
| `refusal_accuracy` (SC11, SC12) | **1.0** |
| `any_of_refs_hit_rate` (non-refusal scenarios) | ≥ **0.85** (17/20) |
| `citation_hit_rate` (non-refusal) | ≥ **0.90** |
| `disclaimer_present_rate` | ≥ **1.0** |
| `critical_failure_count` | **0** |

### Gate C — Scenario rubric (human / LLM review)

| Metric | Threshold |
|--------|-----------|
| Per-scenario weighted score | ≥ **0.85** on ≥ **17/20** scenarios |
| `r3_usefulness_rate` | ≥ **0.80** |
| `r4_epistemic_rate` (SC10, SC13, subset cases) | ≥ **0.80** |
| SC10-specific | Must pass R4 (no fabricated %) |

### Gate D — Operational sanity

| Metric | Threshold |
|--------|-----------|
| `latency_ms_p95` | ≤ **45_000** ms (same stack as Phase 5 eval) |
| `python run_tests.py` | pass |
| `python scripts/spot_check_corpus.py` | pass |

### Release messaging (if all gates pass)

> Fin RAG 除 34 題 golden regression 外，已通過 **20 題真實情境驗收**（口語提問、跨法域、資訊不足與超範圍）。收錄 **16 份**公開法規節錄，**非完整法規資料庫**，不構成法律意見。

---

## Deliverables

| Artifact | Action |
|----------|--------|
| `eval/scenarios.yaml` | Create 20 scenarios from inventory |
| `eval/run_scenarios.py` | Auto metrics + report (can be Phase 6 implementation) |
| `eval/scenario_review.template.yaml` | Human/LLM rubric scores |
| `eval/baseline-phase6-scenarios.json` | Freeze after gates pass |
| `readme-tw.md`, `README.md` | One-line Phase 6 status + messaging |

## Risks

| Risk | Mitigation |
|------|------------|
| Colloquial questions miss retrieval | `any_of_refs` not `required_refs`; optional query rewrite already in agent |
| LLM judge drift | Primary sign-off: human review on first baseline |
| Overfitting scenarios | Keep golden separate; cap prompt changes to shared system prompt |
| SC10 false confidence | `must_acknowledge_subset` + critical failure on fabricated % |

## References

- [Phase 5 design](2026-07-07-phase-5-subset-expansion-design.md)
- `eval/golden.yaml`, `eval/baseline-phase5.json`
- `src/fin_rag/eval.py`
