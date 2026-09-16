# Contributing

Sensum is intentionally small. Contributions should preserve three principles:

1. **Filter before reasoning.** Do not require a large model for basic change detection.
2. **Emit semantic deltas.** Prefer `door.opened` to repeatedly forwarding the same raw state.
3. **Keep the core model-agnostic.** Provider integrations belong in adapters, not the event model.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest
ruff check .
```

Before adding a new sensor, include tests for its event semantics and document what raw data leaves the local process.
