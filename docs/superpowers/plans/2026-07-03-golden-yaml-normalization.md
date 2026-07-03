# Golden YAML Normalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the checked-in golden dataset to real YAML and keep the eval loader compatible with both YAML and JSON fixture inputs.

**Architecture:** `src/fin_rag/eval.py` will switch from JSON-only parsing to `yaml.safe_load()`, allowing one parsing path for both YAML and JSON-shaped content. `eval/golden.yaml` will become idiomatic YAML, and tests will verify both fixture styles still load into `GoldenCase`.

**Tech Stack:** Python 3.11, PyYAML, unittest

---

### Task 1: Lock In Loader Behavior With Tests

**Files:**
- Modify: `tests/test_eval.py`

- [ ] Add a YAML fixture test for `load_golden()`.
- [ ] Run the targeted eval test and verify the YAML case fails before implementation.
- [ ] Add or keep a JSON fixture compatibility assertion in the same test module.

### Task 2: Implement YAML-Backed Loading

**Files:**
- Modify: `src/fin_rag/eval.py`

- [ ] Replace the JSON-only parser with `yaml.safe_load()`.
- [ ] Keep the returned `GoldenCase` structure unchanged.
- [ ] Run targeted eval tests and verify they pass.

### Task 3: Normalize The Checked-In Dataset

**Files:**
- Modify: `eval/golden.yaml`

- [ ] Rewrite the checked-in golden dataset from JSON-subset text to proper YAML list syntax.
- [ ] Re-run targeted eval tests to confirm the checked-in file still loads.

### Task 4: Final Verification

**Files:**
- Verify only

- [ ] Run `python run_tests.py`.
- [ ] Confirm no unexpected regressions.
