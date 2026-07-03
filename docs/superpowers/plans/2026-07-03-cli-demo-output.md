# CLI Demo Output Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve `scripts/ask.py` so terminal demos show answer text, refusal status, citations, and retrieved chunk summaries.

**Architecture:** The CLI script will gain pure formatting helpers that transform `AgentResult` into a readable multi-section string. These helpers will read from already-available retrieved chunk metadata and will not change retrieval, generation, or refusal logic.

**Tech Stack:** Python 3.11, unittest

---

### Task 1: Add Formatting Tests

**Files:**
- Create: `tests/test_ask_script.py`

- [ ] Write a failing test for answered output with citations and chunk summaries.
- [ ] Write a failing test for refused output status.
- [ ] Run targeted tests and confirm failure before implementation.

### Task 2: Implement CLI Formatting

**Files:**
- Modify: `scripts/ask.py`

- [ ] Add pure helpers for formatting result sections.
- [ ] Keep `main()` behavior the same except for richer output.
- [ ] Run targeted tests and confirm they pass.

### Task 3: Final Verification

**Files:**
- Verify only

- [ ] Run `python run_tests.py`.
- [ ] Commit the CLI demo output improvement.
