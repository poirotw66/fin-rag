# Phase 2 Corpus Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close Phase 1 POC, replace excerpt-only raw files with full public-law texts, add a controlled batch of related regulations, and grow the golden set—deferring hybrid retrieval to Phase 3.

**Architecture:** Reuse the existing manifest → raw → `chunk_by_article.py` → `build_index.py` pipeline. Add corpus validation tests and eval baselines so each ingest batch is verifiable. No changes to `Retriever` or agent graph in this plan.

**Tech Stack:** Python 3.11+, existing `fin_rag` corpus module, `scripts/fetch_moj_law.py`, Gemini embeddings (index rebuild only), pytest

**Design doc:** [../specs/2026-07-03-phase-2-corpus-expansion-design.md](../specs/2026-07-03-phase-2-corpus-expansion-design.md)

---

## File map

| File | Role |
|------|------|
| `corpus/manifest.json` | Source metadata, tracks, revision dates |
| `corpus/raw/*` | Full law text (txt or html) |
| `corpus/chunks.jsonl` | Article-level chunks (generated) |
| `corpus/index.jsonl` | Embeddings (generated) |
| `corpus/README.md` | Sources, disclaimer, ingest SOP |
| `scripts/fetch_moj_law.py` | Download MOJ HTML by pcode |
| `scripts/chunk_by_article.py` | Build chunks from raw |
| `scripts/build_index.py` | Embed chunks |
| `scripts/spot_check_corpus.py` | **Create** — verify required articles exist |
| `tests/test_corpus_coverage.py` | **Create** — manifest/raw/chunk invariants |
| `eval/golden.yaml` | Add A6–A7, B6–B7 (batch 1) |
| `eval/baseline-phase1.json` | **Create** — frozen Phase 1 eval snapshot |
| `eval/baseline-phase2a.json` | **Create** — after full-text rebuild |
| `readme-tw.md` | Phase 2 status note |

---

### Task 1: Freeze Phase 1 baseline

**Files:**
- Create: `eval/baseline-phase1.json`
- Modify: `readme-tw.md`

- [ ] **Step 1: Run eval and save baseline**

```bash
cd /path/to/fin-rag
pip install -e .
python eval/run.py
cp eval/last_report.json eval/baseline-phase1.json
```

Expected: `eval/baseline-phase1.json` exists with `citation_hit_rate`, `refusal_accuracy`, `expected_refs_retrieved_rate`.

- [ ] **Step 2: Note baseline in readme-tw.md**

Add under **狀態**:

```markdown
Phase 1 baseline: `eval/baseline-phase1.json`（corpus 節錄版，11 chunks）
```

- [ ] **Step 3: Commit**

```bash
git add eval/baseline-phase1.json readme-tw.md
git commit -m "docs: freeze Phase 1 eval baseline"
```

---

### Task 2: Add corpus coverage tests

**Files:**
- Create: `tests/test_corpus_coverage.py`
- Modify: `corpus/manifest.json` (add `spot_check_articles` optional field per entry — or use separate YAML)

Use a small spot-check config file instead of bloating manifest:

- Create: `corpus/spot_check.yaml`

```yaml
sit-fund-mgmt:
  - "第 10 條"
  - "第 11 條"
sit-biz-rules:
  - "第 20 條"
aml-finst:
  - "第 2 條"
  - "第 7 條"
  - "第 12 條"
  - "第 15 條"
```

- [ ] **Step 1: Write failing coverage test**

`tests/test_corpus_coverage.py`

```python
from __future__ import annotations

import json
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class CorpusCoverageTests(unittest.TestCase):
    def test_every_manifest_entry_has_raw_file(self) -> None:
        manifest = json.loads((ROOT / "corpus" / "manifest.json").read_text(encoding="utf-8"))
        for entry in manifest:
            raw_path = ROOT / "corpus" / "raw" / f"{entry['doc_id']}.{entry['format']}"
            self.assertTrue(raw_path.exists(), f"missing raw file: {raw_path}")

    def test_spot_check_articles_exist_in_chunks(self) -> None:
        spot_check = yaml.safe_load((ROOT / "corpus" / "spot_check.yaml").read_text(encoding="utf-8"))
        articles_by_doc: dict[str, set[str]] = {}
        for line in (ROOT / "corpus" / "chunks.jsonl").read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            articles_by_doc.setdefault(row["doc_id"], set()).add(row["article"])
        for doc_id, required in spot_check.items():
            found = articles_by_doc.get(doc_id, set())
            for article in required:
                self.assertIn(article, found, f"{doc_id} missing {article}")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test — expect FAIL on excerpt corpus**

```bash
python -m unittest tests.test_corpus_coverage -v
```

Expected: PASS for manifest/raw; may PASS spot-check today (excerpts include those articles). After Task 3 full ingest, re-run to ensure still PASS with more chunks.

- [ ] **Step 3: Add spot_check.yaml and test file**

- [ ] **Step 4: Run tests**

```bash
python run_tests.py
```

Expected: OK

- [ ] **Step 5: Commit**

```bash
git add corpus/spot_check.yaml tests/test_corpus_coverage.py
git commit -m "test: add corpus manifest and spot-check coverage"
```

---

### Task 3: Ingest full text for existing five documents

**Files:**
- Modify: `corpus/raw/sit-fund-mgmt.txt` (or `.html`)
- Modify: `corpus/raw/sit-biz-rules.txt`
- Modify: `corpus/raw/sit-material-event.txt`
- Modify: `corpus/raw/aml-finst.txt`
- Modify: `corpus/raw/aml-bank-ic.txt`
- Modify: `corpus/manifest.json` — set real `revision_date`, fix `aml-bank-ic` `source_url`

- [ ] **Step 1: Download MOJ sources**

```bash
python scripts/fetch_moj_law.py G0400082 sit-fund-mgmt
python scripts/fetch_moj_law.py G0400081 sit-biz-rules
python scripts/fetch_moj_law.py G0380252 aml-finst
```

For `aml-bank-ic`, download from MOJ or FSC and save as `corpus/raw/aml-bank-ic.txt`.

For `sit-material-event`, manually save the FSC 104.04.14 letter full text to `corpus/raw/sit-material-event.txt` (no MOJ pcode).

- [ ] **Step 2: Normalize to chunker input**

If fetch writes `.html`, either:

- Update manifest `format` to `html` and extend `chunk_by_article.py` to strip HTML tags (only if needed), **or**
- Convert to plain text with article markers `第 N 條` and keep `format: txt`.

Prefer **plain text** if MOJ export is available — less parser risk.

- [ ] **Step 3: Update manifest revision dates**

Replace `"revision_date": "待查"` with dates from MOJ page for each entry.

- [ ] **Step 4: Rebuild chunks and index**

```bash
python scripts/chunk_by_article.py
python scripts/build_index.py
```

Expected: `wrote N chunks` where N is much larger than 11 (typically 80–200+).

- [ ] **Step 5: Run coverage tests**

```bash
python -m unittest tests.test_corpus_coverage -v
python eval/run.py
cp eval/last_report.json eval/baseline-phase2a.json
```

- [ ] **Step 6: Update corpus/README.md**

Document: source URLs, fetch date, chunk count, spot-check articles, embedding rebuild command.

- [ ] **Step 7: Commit**

```bash
git add corpus/ eval/baseline-phase2a.json
git commit -m "feat: ingest full text for Phase 1 corpus documents"
```

---

### Task 4: Add spot-check CLI (optional helper)

**Files:**
- Create: `scripts/spot_check_corpus.py`

- [ ] **Step 1: Implement script**

```python
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    spot_check = yaml.safe_load((ROOT / "corpus" / "spot_check.yaml").read_text(encoding="utf-8"))
    articles_by_doc: dict[str, set[str]] = {}
    chunks_path = ROOT / "corpus" / "chunks.jsonl"
    for line in chunks_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        articles_by_doc.setdefault(row["doc_id"], set()).add(row["article"])
    missing = []
    for doc_id, required in spot_check.items():
        found = articles_by_doc.get(doc_id, set())
        for article in required:
            if article not in found:
                missing.append(f"{doc_id} {article}")
    if missing:
        print("MISSING:", *missing, sep="\n  ")
        return 1
    print(f"OK: {sum(len(v) for v in articles_by_doc.values())} chunks, spot-check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run**

```bash
python scripts/spot_check_corpus.py
```

Expected: `OK: ... spot-check passed`

- [ ] **Step 3: Commit**

```bash
git add scripts/spot_check_corpus.py
git commit -m "chore: add corpus spot-check script"
```

---

### Task 5: Batch 1 — add aml-act and sit-trust-act

**Files:**
- Modify: `corpus/manifest.json`
- Create: `corpus/raw/aml-act.txt`
- Create: `corpus/raw/sit-trust-act.txt`
- Modify: `corpus/spot_check.yaml`

- [ ] **Step 1: Append manifest entries**

```json
{
  "doc_id": "aml-act",
  "title": "洗錢防制法",
  "source_url": "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=G0380046",
  "issuer": "行政院",
  "revision_date": "<from MOJ>",
  "fetched_at": "2026-07-03",
  "format": "txt",
  "chunk_strategy": "by_article",
  "track": "aml"
},
{
  "doc_id": "sit-trust-act",
  "title": "證券投資信託及顧問法",
  "source_url": "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=G0400006",
  "issuer": "金融監督管理委員會",
  "revision_date": "<from MOJ>",
  "fetched_at": "2026-07-03",
  "format": "txt",
  "chunk_strategy": "by_article",
  "track": "sit-related-party"
}
```

- [ ] **Step 2: Fetch and normalize raw files**

```bash
python scripts/fetch_moj_law.py G0380046 aml-act
python scripts/fetch_moj_law.py G0400006 sit-trust-act
```

Convert to txt with `第 N 條` markers if needed.

- [ ] **Step 3: Extend spot_check.yaml**

```yaml
aml-act:
  - "第 1 條"
sit-trust-act:
  - "第 1 條"
```

Pick articles that match planned golden questions after spot-reading the text.

- [ ] **Step 4: Rebuild pipeline**

```bash
python scripts/chunk_by_article.py
python scripts/build_index.py
python scripts/spot_check_corpus.py
```

- [ ] **Step 5: Commit**

```bash
git add corpus/
git commit -m "feat: add aml-act and sit-trust-act to corpus"
```

---

### Task 6: Grow golden set for batch 1

**Files:**
- Modify: `eval/golden.yaml`

- [ ] **Step 1: Add questions (adjust articles after ingest)**

```yaml
- id: A6
  track: A
  question: 洗錢防制法所稱洗錢行為包括哪些類型？
  expected_refs:
    - [aml-act, 第 2 條]
  expect_refusal: false

- id: A7
  track: A
  question: 洗錢防制主管機關為何？
  expected_refs:
    - [aml-act, 第 5 條]
  expect_refusal: false

- id: B6
  track: B
  question: 證券投資信託契約應記載哪些事項？
  expected_refs:
    - [sit-trust-act, 第 6 條]
  expect_refusal: false

- id: B7
  track: B
  question: 投信事業對受益人負何種信託責任？
  expected_refs:
    - [sit-trust-act, 第 4 條]
  expect_refusal: false
```

Verify article numbers against ingested text; update `expected_refs` to match actual chunk `article` fields.

- [ ] **Step 2: Run eval**

```bash
python eval/run.py
```

Expected: metrics documented; fix golden if article numbers differ.

- [ ] **Step 3: Commit**

```bash
git add eval/golden.yaml eval/last_report.json
git commit -m "eval: add golden questions for batch 1 corpus"
```

---

### Task 7: Document Phase 2 status and Phase 3 gate

**Files:**
- Modify: `readme-tw.md`
- Modify: `README.md`

- [ ] **Step 1: Add Phase 2 / Phase 3 section to readme-tw.md**

```markdown
## 路線圖

- **Phase 1（完成）**：可引用、可拒答、可 eval、CLI + API + Web demo
- **Phase 2（進行中）**：完整法條 ingest + 跨增相關法規 + golden 擴充
- **Phase 3（待 corpus ≥100 chunks）**：hybrid retrieval（BM25 + embedding）、檢索低分拒答

詳細計畫：`docs/superpowers/plans/2026-07-03-phase-2-corpus-expansion.md`
```

- [ ] **Step 2: Mirror short roadmap in README.md**

- [ ] **Step 3: Commit**

```bash
git add readme-tw.md README.md
git commit -m "docs: add Phase 2 corpus roadmap and Phase 3 gate"
```

---

## Self-review

| Spec requirement | Task |
|------------------|------|
| Full text for existing laws | Task 3 |
| Cross-expand related laws | Task 5 (batch 1); batch 2 in design doc |
| Eval growth | Task 6 |
| No media in corpus | Design principles (no task needed) |
| Defer hybrid retrieval | Explicitly out of scope; Phase 3 gate in Task 7 |
| revision_date tracking | Task 3 manifest update |
| Reproducible pipeline | Existing scripts + spot-check |

## Execution handoff

Plan saved to `docs/superpowers/plans/2026-07-03-phase-2-corpus-expansion.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks
2. **Inline Execution** — run tasks in this session with checkpoints

Which approach?
