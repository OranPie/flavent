# Performance Baseline (Initial)

Date: 2026-02-18

These numbers are local baseline measurements to compare future optimization work.

## Commands
- `python3 -m pytest -q`
- `python3 -m pytest -q tests/test_runtime_determinism.py`
- `python3 -m flavent check examples/minimal.flv --strict`

## Results
- Full test suite: `8.102s` wall time (`278 passed in 7.14s` reported by pytest).
- Runtime determinism tests: `0.557s` wall time (`5 passed in 0.16s` reported by pytest).
- Compiler check (minimal example): `0.208s` wall time.

## Notes
- Measurements include Python process startup overhead.
- Use these values as a relative baseline only (not cross-machine absolute targets).
