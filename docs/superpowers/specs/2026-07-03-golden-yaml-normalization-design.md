# Golden YAML Normalization Design

## Goal

Normalize `eval/golden.yaml` into real YAML while keeping the evaluation loader backward-compatible with both YAML and JSON-shaped inputs.

## Scope

- Convert the checked-in golden dataset from JSON-subset text to idiomatic YAML.
- Update `load_golden()` to parse YAML safely.
- Preserve compatibility for existing JSON-shaped fixtures because JSON is valid YAML.
- Add tests that prove both YAML and JSON fixture inputs still load correctly.

## Approach

Use `yaml.safe_load()` in `src/fin_rag/eval.py` as the single parser. This keeps the implementation small because valid JSON can still be parsed by the YAML loader, so we do not need a separate branching parser.

The checked-in `eval/golden.yaml` will be rewritten into proper YAML list syntax for readability and easier future editing. Tests will cover both an idiomatic YAML fixture and a compact JSON fixture to guard compatibility.

## Risks

- If the loader assumes JSON-only semantics, switching parsers could change error behavior for malformed files.
- If the checked-in dataset is rewritten incorrectly, eval could break even though parsing support is correct.

## Verification

- Targeted `test_eval` coverage for YAML and JSON fixture loading.
- Full `python run_tests.py`.
