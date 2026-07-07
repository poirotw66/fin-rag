# Phase 5 Subset Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deepen six existing MOJ subset statutes, add `insurance-act` excerpt, grow golden set to 34 questions, and freeze `eval/baseline-phase5.json` (~520–540 chunks).

**Architecture:** `corpus/subsets.yaml` remains the article source of truth. Re-run `extract_article_subset.py` per subset doc, then existing chunk → index → spot-check → eval pipeline. Update `KNOWN_DOC_IDS` and docs only; no retrieval/agent changes unless eval regresses.

**Tech Stack:** Python 3.10+, `scripts/fetch_moj_law.py`, `scripts/moj_html_to_txt.py`, `scripts/extract_article_subset.py`, Gemini embeddings, pytest, `eval/run.py`

**Design doc:** [../specs/2026-07-07-phase-5-subset-expansion-design.md](../specs/2026-07-07-phase-5-subset-expansion-design.md)

---

## File map

| File | Action |
|------|--------|
| `corpus/subsets.yaml` | Replace article lists with Phase 5 totals |
| `corpus/manifest.json` | Add `insurance-act` entry |
| `corpus/raw/insurance-act.{html,txt,full.txt}` | Fetch + convert + subset |
| `corpus/raw/{subset-doc}.txt` | Re-extract from existing `.full.txt` |
| `corpus/chunks.jsonl`, `corpus/index.*` | Regenerate |
| `corpus/spot_check.yaml` | Add spot-check rows for new articles + `insurance-act` |
| `src/fin_rag/citations.py` | Add `insurance-act` to `KNOWN_DOC_IDS` |
| `eval/golden.yaml` | Add A10–A11, B10–B11, E7–E10 |
| `eval/baseline-phase5.json` | Freeze after eval passes |
| `corpus/README.md`, `readme-tw.md`, `README.md` | Phase 5 stats + disclaimer |

---

### Task 1: Update `corpus/subsets.yaml`

**Files:**
- Modify: `corpus/subsets.yaml`

- [ ] **Step 1: Replace file with merged article lists (existing + new)**

```yaml
privacy-finance:
  source_pcode: I0050021
  track: cross-law
  title: 個人資料保護法（金融客戶資料節錄）
  articles:
    - "第 2 條"
    - "第 3 條"
    - "第 5 條"
    - "第 6 條"
    - "第 7 條"
    - "第 12 條"
    - "第 19 條"
    - "第 20 條"
    - "第 20-1 條"
    - "第 27 條"
    - "第 29 條"
    - "第 30 條"
    - "第 39 條"
    - "第 41 條"
    - "第 48 條"

sit-securities-act:
  source_pcode: G0400001
  track: sit-related-party
  title: 證券交易法（關係人／董事義務節錄）
  articles:
    - "第 14-2 條"
    - "第 14-3 條"
    - "第 14-4 條"
    - "第 14-5 條"
    - "第 14-6 條"
    - "第 26-3 條"
    - "第 43 條"
    - "第 43-1 條"
    - "第 43-5 條"
    - "第 174 條"
    - "第 174-1 條"
    - "第 178 條"

bank-act:
  source_pcode: G0380001
  track: banking
  title: 銀行法（銀行業務與授信節錄）
  articles:
    - "第 2 條"
    - "第 3 條"
    - "第 12 條"
    - "第 25 條"
    - "第 29 條"
    - "第 32 條"
    - "第 33 條"
    - "第 44 條"
    - "第 45 條"
    - "第 61 條"
    - "第 64 條"
    - "第 72 條"
    - "第 125 條"

trust-industry-act:
  source_pcode: G0310027
  track: trust
  title: 信託業法（信託業務節錄）
  articles:
    - "第 3 條"
    - "第 7 條"
    - "第 10 條"
    - "第 16 條"
    - "第 19 條"
    - "第 23 條"
    - "第 24 條"
    - "第 25 條"
    - "第 27 條"
    - "第 35 條"
    - "第 38 條"
    - "第 40 條"
    - "第 46 條"
    - "第 48 條"

fhc-act:
  source_pcode: G0380112
  track: holding
  title: 金融控股公司法（組織與業務節錄）
  articles:
    - "第 4 條"
    - "第 5 條"
    - "第 6 條"
    - "第 9 條"
    - "第 16 條"
    - "第 18 條"
    - "第 25 條"
    - "第 36 條"
    - "第 37 條"
    - "第 41 條"
    - "第 43 條"
    - "第 44 條"
    - "第 51 條"
    - "第 55 條"

futures-act:
  source_pcode: G0400100
  track: futures
  title: 期貨交易法（期貨交易與期貨商節錄）
  articles:
    - "第 3 條"
    - "第 5 條"
    - "第 7 條"
    - "第 18 條"
    - "第 56 條"
    - "第 57 條"
    - "第 64 條"
    - "第 73 條"
    - "第 79 條"
    - "第 88 條"
    - "第 95 條"
    - "第 106 條"
    - "第 112 條"

insurance-act:
  source_pcode: G0390002
  track: insurance
  title: 保險法（保險業與契約節錄）
  articles:
    - "第 1 條"
    - "第 2 條"
    - "第 55 條"
    - "第 136 條"
    - "第 137 條"
    - "第 138 條"
    - "第 143 條"
    - "第 149 條"
    - "第 166 條"
    - "第 174 條"
```

- [ ] **Step 2: Verify YAML parses**

```bash
python -c "import yaml; yaml.safe_load(open('corpus/subsets.yaml'))"
```

Expected: no exception.

---

### Task 2: Fetch and extract raw texts

**Files:**
- Create: `corpus/raw/insurance-act.html`, `insurance-act.txt`, `insurance-act.full.txt`
- Modify: `corpus/raw/bank-act.txt`, `trust-industry-act.txt`, `fhc-act.txt`, `futures-act.txt`, `privacy-finance.txt`, `sit-securities-act.txt`

- [ ] **Step 1: Fetch insurance-act from MOJ**

```bash
python scripts/fetch_moj_law.py G0390002 insurance-act
python scripts/moj_html_to_txt.py insurance-act
head -3 corpus/raw/insurance-act.txt
```

Expected: title contains `保險法`, not another regulation.

- [ ] **Step 2: Save full text backup for insurance-act**

```bash
cp corpus/raw/insurance-act.txt corpus/raw/insurance-act.full.txt
```

- [ ] **Step 3: Re-extract all subset working files**

```bash
python scripts/extract_article_subset.py bank-act "第 2 條,第 3 條,第 12 條,第 25 條,第 29 條,第 32 條,第 33 條,第 44 條,第 45 條,第 61 條,第 64 條,第 72 條,第 125 條"

python scripts/extract_article_subset.py trust-industry-act "第 3 條,第 7 條,第 10 條,第 16 條,第 19 條,第 23 條,第 24 條,第 25 條,第 27 條,第 35 條,第 38 條,第 40 條,第 46 條,第 48 條"

python scripts/extract_article_subset.py fhc-act "第 4 條,第 5 條,第 6 條,第 9 條,第 16 條,第 18 條,第 25 條,第 36 條,第 37 條,第 41 條,第 43 條,第 44 條,第 51 條,第 55 條"

python scripts/extract_article_subset.py futures-act "第 3 條,第 5 條,第 7 條,第 18 條,第 56 條,第 57 條,第 64 條,第 73 條,第 79 條,第 88 條,第 95 條,第 106 條,第 112 條"

python scripts/extract_article_subset.py privacy-finance "第 2 條,第 3 條,第 5 條,第 6 條,第 7 條,第 12 條,第 19 條,第 20 條,第 20-1 條,第 27 條,第 29 條,第 30 條,第 39 條,第 41 條,第 48 條"

python scripts/extract_article_subset.py sit-securities-act "第 14-2 條,第 14-3 條,第 14-4 條,第 14-5 條,第 14-6 條,第 26-3 條,第 43 條,第 43-1 條,第 43-5 條,第 174 條,第 174-1 條,第 178 條"

python scripts/extract_article_subset.py insurance-act "第 1 條,第 2 條,第 55 條,第 136 條,第 137 條,第 138 條,第 143 條,第 149 條,第 166 條,第 174 條"
```

Expected: each command prints `wrote corpus/raw/{doc_id}.txt (N articles requested)` with no stderr errors.

- [ ] **Step 4: Spot-check article counts**

```bash
for f in bank-act trust-industry-act fhc-act futures-act privacy-finance sit-securities-act insurance-act; do
  echo -n "$f: "; grep -c '^第 ' corpus/raw/$f.txt
done
```

Expected: 13, 14, 14, 13, 15, 12, 10 respectively.

---

### Task 3: Update manifest and citations

**Files:**
- Modify: `corpus/manifest.json`
- Modify: `src/fin_rag/citations.py`

- [ ] **Step 1: Append `insurance-act` to manifest**

Add before the closing `]`:

```json
  {
    "doc_id": "insurance-act",
    "title": "保險法（保險業與契約節錄）",
    "source_url": "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=G0390002",
    "issuer": "金融監督管理委員會",
    "revision_date": "114-06-18",
    "fetched_at": "2026-07-07",
    "format": "txt",
    "chunk_strategy": "by_article",
    "track": "insurance"
  }
```

- [ ] **Step 2: Add `insurance-act` to `KNOWN_DOC_IDS`**

In `src/fin_rag/citations.py`, add `"insurance-act"` in alphabetical order among existing ids.

- [ ] **Step 3: Run citation unit tests**

```bash
python -m unittest tests.test_citations -v
```

Expected: all pass.

---

### Task 4: Update spot-check and rebuild corpus index

**Files:**
- Modify: `corpus/spot_check.yaml`
- Regenerate: `corpus/chunks.jsonl`, `corpus/index.jsonl`, `corpus/index.faiss`, `corpus/index_bm25.json`

- [ ] **Step 1: Extend `corpus/spot_check.yaml`**

Add or extend these entries (keep all existing rows):

```yaml
bank-act:
  - "第 2 條"
  - "第 32 條"
  - "第 33 條"
trust-industry-act:
  - "第 16 條"
  - "第 27 條"
fhc-act:
  - "第 4 條"
  - "第 37 條"
futures-act:
  - "第 3 條"
  - "第 57 條"
privacy-finance:
  - "第 5 條"
  - "第 12 條"
  - "第 19 條"
sit-securities-act:
  - "第 14-2 條"
  - "第 43 條"
insurance-act:
  - "第 55 條"
  - "第 137 條"
```

- [ ] **Step 2: Rebuild chunks and index**

```bash
python scripts/chunk_by_article.py
python scripts/build_index.py
python scripts/spot_check_corpus.py
```

Expected: chunk count between 520 and 540; `OK: spot-check passed`.

- [ ] **Step 3: Run corpus coverage tests**

```bash
python -m unittest tests.test_corpus_coverage -v
```

Expected: all pass.

---

### Task 5: Extend golden set

**Files:**
- Modify: `eval/golden.yaml`

- [ ] **Step 1: Insert eight new cases before `C1`**

```yaml
- id: A10
  track: A
  question: 銀行對同一關係人授信餘額有何比例限制？
  expected_refs:
    - [bank-act, 第 32 條]
  expect_refusal: false

- id: A11
  track: A
  question: 保險業經營業務應經主管機關何種許可？
  expected_refs:
    - [insurance-act, 第 137 條]
  expect_refusal: false

- id: B10
  track: B
  question: 受託人辦理信託業務對委託人負何種義務？
  expected_refs:
    - [trust-industry-act, 第 27 條]
  expect_refusal: false

- id: B11
  track: B
  question: 期貨商受託從事期貨交易之業務範圍為何？
  expected_refs:
    - [futures-act, 第 57 條]
  expect_refusal: false

- id: E7
  track: E
  question: 非公務機關告知當事人個資利用情形有何義務？
  expected_refs:
    - [privacy-finance, 第 12 條]
  expect_refusal: false

- id: E8
  track: E
  question: 公開發行公司大股東持股變動應如何申報？
  expected_refs:
    - [sit-securities-act, 第 43 條]
  expect_refusal: false

- id: E9
  track: E
  question: 金融控股公司投資非金融事業之持股上限為何？
  expected_refs:
    - [fhc-act, 第 37 條]
  expect_refusal: false

- id: E10
  track: E
  question: 保險契約應記載哪些基本事項？
  expected_refs:
    - [insurance-act, 第 55 條]
  expect_refusal: false
```

- [ ] **Step 2: Verify golden loads 34 cases**

```bash
python -c "import sys; sys.path.insert(0,'src'); from fin_rag.eval import load_golden; print(len(load_golden('eval/golden.yaml')))"
```

Expected: `34`

---

### Task 6: Eval, baseline, and regression fix

**Files:**
- Create: `eval/baseline-phase5.json`
- Modify (only if eval fails): `src/fin_rag/prompts/system.md`, `src/fin_rag/agent.py`

- [ ] **Step 1: Run full eval**

```bash
FIN_RAG_RETRIEVAL_MODE=hybrid python eval/run.py
```

Expected: `total: 34`, all three rates ≥ 0.96 (target 1.0). If a procedural question mis-refuses (e.g. A2 CDD), re-run once before changing code.

- [ ] **Step 2: If `expected_refs_retrieved_rate` fails on new questions only**

Run retrieval probe:

```bash
python - <<'EOF'
import sys
sys.path.insert(0, "src")
from fin_rag.config import Settings
from fin_rag.gemini import GeminiClient
from fin_rag.retrieve import Retriever
from fin_rag.eval import load_golden

settings = Settings.from_env()
client = GeminiClient(settings.api_key, settings.generation_model, settings.embedding_model)
r = Retriever(client=client, index_path="corpus/index.jsonl", retrieval_mode="hybrid")
for case in load_golden("eval/golden.yaml"):
    if case.id not in {"A10", "A11", "B10", "B11", "E7", "E8", "E9", "E10"}:
        continue
    refs = {(h.chunk.doc_id, h.chunk.article) for h in r.retrieve(case.question)}
    ok = set(case.expected_refs).issubset(refs)
    print(case.id, "OK" if ok else "MISS", case.expected_refs[:1])
EOF
```

Fix: verify article exists in chunks; adjust question wording only if article is correct but retrieval consistently misses.

- [ ] **Step 3: Freeze baseline**

```bash
cp eval/last_report.json eval/baseline-phase5.json
```

- [ ] **Step 4: Run full test suite**

```bash
python run_tests.py
```

Expected: all pass (Gemini integration skipped without API key).

---

### Task 7: Update documentation

**Files:**
- Modify: `corpus/README.md`, `readme-tw.md`, `README.md`

- [ ] **Step 1: Update inventory table in `corpus/README.md`**

- Total chunks: actual count from `wc -l corpus/chunks.jsonl`
- Add `insurance-act` row; update subset chunk counts for expanded docs
- Add `eval/baseline-phase5.json` to baselines table

- [ ] **Step 2: Update status sections in `readme-tw.md` and `README.md`**

- Phase 5 baseline line
- 16 statutes, ~530 chunks, 34 golden questions
- Coverage disclaimer (subset-heavy, not legal advice)
- Roadmap: Phase 5 complete

- [ ] **Step 3: Commit (only when user requests)**

```bash
git add corpus/ src/fin_rag/citations.py eval/ docs/superpowers/specs/2026-07-07-phase-5-subset-expansion-design.md docs/superpowers/plans/2026-07-07-phase-5-subset-expansion.md readme-tw.md README.md
git commit -m "feat(corpus): Phase 5 subset expansion to 16 statutes and 34 golden questions"
```

---

## Verification checklist

| Check | Command / file |
|-------|----------------|
| 16 manifest entries | `python -c "import json; print(len(json.load(open('corpus/manifest.json'))))"` |
| 520–540 chunks | `wc -l corpus/chunks.jsonl` |
| 34 golden | `load_golden` count |
| Spot-check | `python scripts/spot_check_corpus.py` |
| Tests | `python run_tests.py` |
| Eval | `eval/baseline-phase5.json` all metrics ≥ 0.96 |

## Spec coverage self-review

| Spec requirement | Task |
|------------------|------|
| Expand 6 subsets | Task 1–2 |
| Add insurance-act | Task 2–3 |
| subsets.yaml source of truth | Task 1 |
| spot_check + KNOWN_DOC_IDS | Task 3–4 |
| Golden +8 | Task 5 |
| baseline-phase5 | Task 6 |
| README disclaimer | Task 7 |
| No full-statute ingest | Enforced by subset lists only |
| No retrieval changes unless regression | Task 6 Step 2 conditional only |
