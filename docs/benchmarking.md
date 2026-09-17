# Sensum benchmark methodology

Sensum should not publish token-saving or recall claims from synthetic data as if they were
real-world measurements. Synthetic benchmarks are regression tests. Public performance claims
must come from recorded, labelled fixtures.

## Required benchmark tracks

### Browser
Record a reproducible browsing session containing repeated unchanged states and labelled changes
such as navigation, price changes, modal open/close, checkout state and payment status.

### Audio
Record or use redistributable PCM fixtures containing silence, speech boundaries and intentional
barge-in/interruption. Keep personally identifying recordings out of the repository.

### Screen
Record a reproducible sequence of screen observations with both low-value visual churn and
labelled meaningful changes.

### Vision
Use redistributable or generated scenes represented by local CV observations. Raw camera media is
not required for the core benchmark if object/motion observations can be reproduced.

## JSONL fixture format

Each line contains one semantic candidate plus the amount of raw input represented by it:

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

Run:

```bash
python benchmarks/recorded.py path/to/fixture.jsonl
```

## Metrics

Every published benchmark should report at least:

- raw observations and raw bytes;
- semantic candidates after local detection;
- reasoning events emitted by Sensum;
- labelled important events;
- important-event recall;
- precision;
- reasoning-call reduction;
- end-to-end latency where the source supports timestamps;
- CPU and memory for the capture environment when measured.

Token estimates must state the tokenizer/model assumption. Prefer measured API input tokens when a
provider returns usage metadata.

## Baseline

The baseline must process the same observation stream and use the same definition of an important
event. Do not compare Sensum against an artificially inefficient baseline solely to maximize the
reported reduction ratio.

## Reproducibility

Commit fixture generators and labels whenever licensing/privacy permits. Record Sensum version,
attention threshold, sensor configuration, OS, Python version and hardware class with results.
