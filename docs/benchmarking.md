# Sensum benchmark methodology

Sensum should not publish token-saving or recall claims from synthetic data as if they were
real-world measurements. Generated fixtures are regression tests. Public performance claims must
come from captured, labelled fixtures with enough context to reproduce the run.

## Two benchmark layers

Sensum has two deliberately separate benchmark paths.

### Event-level attention benchmark

`benchmark-recorded` starts from already-created semantic events. It answers:

> Given semantic events, does Sensum forward important ones while suppressing low-value ones?

It does **not** measure whether browser/audio/screen sensors correctly detected the event from raw
observations.

```bash
sensum benchmark-recorded path/to/event_fixture.jsonl
```

### Raw sensor benchmark

`benchmark-raw` starts one layer earlier. It accepts browser snapshots, PCM audio frames and screen
change ratios, runs the corresponding local sensor logic, then runs attention on the produced
semantic events. It reports sensor precision/recall separately from reasoning reduction.

```bash
sensum benchmark-raw benchmarks/fixtures/generated_browser.jsonl
sensum benchmark-raw benchmarks/fixtures/generated_audio.jsonl
sensum benchmark-raw benchmarks/fixtures/generated_screen.jsonl
```

The committed `generated_*` fixtures are privacy-safe deterministic regression tests. Their output
must never be presented as real-world benchmark evidence.

## Capture real observations locally

Install only the capture dependencies you need:

```bash
pip install -e '.[capture-browser]'
playwright install chromium

pip install -e '.[capture-audio]'
pip install -e '.[screen]'
```

Or install all capture extras:

```bash
pip install -e '.[capture]'
playwright install chromium
```

Capture browser observations:

```bash
sensum capture-browser https://example.com browser.raw.jsonl --seconds 60
```

By default the browser is visible so the operator can interact with the page during capture. Use
`--headless` only for automated sessions.

Capture screen observations without saving screenshots:

```bash
sensum capture-screen screen.raw.jsonl --seconds 60
```

Only the mean screen-change ratio and byte count are written to the fixture; screenshots are not
persisted by the capture command.

Capture microphone PCM locally:

```bash
sensum capture-audio audio.raw.jsonl --seconds 30
```

Captured files are intentionally **unlabelled**. Running `benchmark-raw` on an unlabelled fixture
will still show raw/semantic/reasoning counts, but sensor precision/recall and important recall are
returned as `null` instead of inventing ground truth.

## Label captured observations

Create a labelled copy interactively:

```bash
sensum label-raw browser.raw.jsonl browser.labelled.jsonl
```

For each observation, enter the expected event kinds and the important subset. Blank expected input
means the observation is explicitly labelled as containing no semantic event.

Then run:

```bash
sensum benchmark-raw browser.labelled.jsonl
```

A result contains an `evidence_class` field:

- `generated`: all rows came from generated fixtures;
- `captured`: all rows came from local capture;
- `mixed`: generated and captured rows were mixed;
- `unclassified`: the fixture did not declare a recognized origin.

Only `captured` plus `fully_labelled: true` should be used for real-world sensor accuracy claims.

## Raw JSONL fixture format

Browser example:

```json
{
  "track": "browser",
  "origin": "captured",
  "raw_bytes": 2813,
  "expected": ["browser.navigated"],
  "important": ["browser.navigated"],
  "observation": {
    "url": "https://example.test/payments",
    "title": "Payments",
    "text": "Payment 42 Status completed"
  }
}
```

Audio observations may contain `pcm16_b64`, `sample_rate`, `channels` and `agent_speaking`.
Generated audio fixtures may use `amplitude` and `samples` as a compact deterministic substitute for
base64 PCM. Screen observations contain `change_ratio` and may include a monitor number.

## Required benchmark tracks

### Browser

Record a reproducible browsing session containing repeated unchanged states and labelled changes
such as navigation, price changes, modal open/close, checkout state and payment status.

### Audio

Record or use redistributable PCM fixtures containing silence, speech boundaries and intentional
barge-in/interruption. Keep personally identifying recordings out of the repository.

### Screen

Record a reproducible sequence of screen observations with both low-value visual churn and
labelled meaningful changes. Prefer the default ratio-only capture mode when screenshots are not
needed.

### Vision

Use redistributable or generated scenes represented by local CV observations. Raw camera media is
not required for the core benchmark if object/motion observations can be reproduced.

## Event-level JSONL fixture format

`benchmark-recorded` uses a different format because the semantic event already exists:

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

## Metrics

Every published benchmark should report at least:

- fixture evidence class and whether every row is labelled;
- raw observations and raw bytes;
- sensor true positives, false positives and false negatives where raw labels exist;
- sensor precision and recall;
- semantic events after local detection;
- reasoning events emitted by Sensum;
- labelled important events and important-event recall;
- reasoning-call reduction;
- end-to-end latency where the source supports timestamps;
- CPU and memory for the capture environment when measured.

Token estimates must state the tokenizer/model assumption. Prefer measured API input tokens when a
provider returns usage metadata.

## Baseline

The baseline must process the same observation stream and use the same definition of an important
event. Do not compare Sensum against an artificially inefficient baseline solely to maximize the
reported reduction ratio.

## Privacy

Captured browser text or microphone audio can contain sensitive information. Capture files stay
local unless the operator explicitly moves them. Scrub or replace sensitive content before
committing fixtures. Never commit customer calls, private pages, credentials or personal data just
to obtain benchmark numbers.

## Reproducibility

Commit fixture generators and labels whenever licensing/privacy permits. Record Sensum version,
attention threshold, sensor configuration, OS, Python version and hardware class with results.
