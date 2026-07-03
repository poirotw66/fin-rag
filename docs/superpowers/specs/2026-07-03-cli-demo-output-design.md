# CLI Demo Output Design

## Goal

Improve `scripts/ask.py` so a demo run shows not only the answer text, but also whether the agent refused, which citations were retrieved, and a short summary of retrieved chunks.

## Scope

- Keep agent retrieval and decision logic unchanged.
- Add presentation-only formatting in the CLI script.
- Show four sections: answer, refusal status, citations, and retrieved chunk summaries.
- Keep output UTF-8 friendly and concise enough for terminal demos.

## Approach

Implement small pure formatting helpers inside `scripts/ask.py` so the behavior is easy to test without calling Gemini. The citations section will be built from `AgentResult.retrieved` rather than reverse-parsing model output, because the retrieved references are already the most reliable demo evidence.

Retrieved chunk summaries will show source identifiers plus a short snippet of chunk text. This makes the CLI more transparent during demos while keeping the implementation isolated from the agent core.

## Verification

- Add unit tests for formatting output with both answered and refused cases.
- Run full `python run_tests.py`.
