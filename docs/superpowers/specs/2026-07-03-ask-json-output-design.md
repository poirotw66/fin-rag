# Ask JSON Output Design

## Goal

Add a `--json` mode to `scripts/ask.py` so the CLI can return machine-readable results for future UI or automation use.

## Scope

- Keep the default human-readable demo output unchanged.
- Add a `--json` flag that prints one JSON object.
- Include question, answer, refusal status, citation hit, citations, and retrieved chunk data.

## Approach

Implement argument parsing in `scripts/ask.py` with a small helper that separates flags from the question. Add pure serialization helpers so tests can validate JSON structure without calling Gemini.

The JSON payload will be built from `AgentResult` and retrieved chunk metadata already present in memory. This keeps the feature presentation-only and avoids changes to agent behavior.

## Verification

- Add targeted tests for default text formatting and `--json` serialization behavior.
- Run `python run_tests.py`.
