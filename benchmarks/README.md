# Sensum Benchmarks

Sensum keeps two benchmark classes deliberately separate.

## 1. Reference / regression suite

The reference suite is deterministic, privacy-safe generated data used by CI. It is designed to
catch regressions in attention policy and benchmark plumbing. **It is not real-world evidence and
must never be presented as field performance.**

Run:

```bash
python benchmarks/reference_suite.py --generate --check
```

The generator creates four tracks under `benchmarks/fixtures/reference/`:

- **browser** — repeated DOM-equivalent observations plus navigation, modal, price and payment-state candidates;
- **audio** — a synthetic 16 kHz mono WAV made only from silence/sine tones, plus labelled semantic candidates;
- **screen** — low-value visual churn plus meaningful view/error candidates;
- **vision** — source-agnostic local-CV observations such as motion, person entry and object placement.

The suite reports raw observations represented by each semantic candidate, represented raw bytes,
semantic candidates, reasoning events, labelled important events, recall, precision and reasoning-
event reduction. CI currently checks minimum reference recall, precision and reduction thresholds.

## 2. Field / recorded benchmarks

Field benchmarks are the evidence track for public performance claims. Capture a real or
redistributable source stream, run the relevant local detector/sensor, then store the resulting
labelled semantic candidates in the JSONL format documented in `docs/benchmarking.md`.

Run one labelled fixture:

```bash
python benchmarks/recorded.py /path/to/fixture.jsonl
```

A candidate record contains the event plus how much raw input it represents:

```json
{
  "important": true,
  "raw_observations": 120,
  "raw_bytes": 384000,
  "event": {
    "kind": "user.interrupted_agent",
    "source": "audio",
    "modality": "audio",
    "summary": "User interrupted the agent",
    "confidence": 0.98,
    "novelty": 0.96,
    "urgency": 0.95,
    "tags": ["interrupt", "important"]
  }
}
```

For public field results, record dataset/session provenance, Sensum version, local detector and
sensor configuration, attention threshold, OS/Python version, hardware class, capture method and
latency methodology. Do not commit private recordings, credentials, customer data or production
conversations.

The primary optimization target is **maximum reasoning-call reduction subject to high important-
event recall**. Reduction without recall is not a win.
