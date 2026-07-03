# Ask JSON Output Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `--json` output mode to `scripts/ask.py` without changing the existing default demo output.

**Architecture:** The CLI script will gain small parsing and serialization helpers. Default runs will still use formatted text output, while `--json` will emit one JSON object derived from `AgentResult` and retrieved chunks.

**Tech Stack:** Python 3.11, json, unittest

---

### Task 1: Add Tests

**Files:**
- Modify: `tests/test_ask_script.py`

- [ ] Write a failing test for JSON serialization shape.
- [ ] Run targeted tests and confirm failure before implementation.

### Task 2: Implement JSON Output

**Files:**
- Modify: `scripts/ask.py`

- [ ] Add helpers for parsing `--json` and serializing result payloads.
- [ ] Keep default text output unchanged.
- [ ] Run targeted tests and confirm they pass.

### Task 3: Final Verification

**Files:**
- Verify only

- [ ] Run `python run_tests.py`.
- [ ] Commit the change.
