# Sensum

**Give AI senses, not streams.**

Sensum is an open-source sensory runtime for AI systems. It converts continuous signals from the world into small, meaningful events and only wakes expensive reasoning when something matters.

> Continuous perception without continuous LLM inference.

```text
camera ─────┐
microphone ─┤
screen ─────┤
browser ────┤──> local change detection -> Sensum attention -> semantic events -> AI
files ──────┤
APIs ───────┘
```

Instead of continuously forwarding raw streams, Sensum aims to emit events such as:

```text
SPEECH_STARTED
BROWSER_NAVIGATED
PAYMENT_STATUS pending -> completed
FILE_MODIFIED src/payment.py
SCREEN_CHANGED
```

## Why

Most AI systems are request/response systems. Continuous agents often compensate by repeatedly sending audio, frames, screenshots or state snapshots to large models. That is expensive, noisy and hard to integrate across modalities.

Sensum introduces a small layer between the world and the model:

1. **Sense** — connect screen, audio, camera, files, browser, APIs or custom sensors.
2. **Detect change locally** — ignore repeated state before it reaches a model.
3. **Attend** — score novelty, urgency and confidence without an LLM by default.
4. **Update world state** — maintain compact canonical state from deltas.
5. **Emit** — publish only meaningful events to a reasoning model or agent.

Sensum is not an LLM and not an agent framework. It is a perception and attention runtime.

## v0.2 alpha

The `feat/v0.2-benchmark` branch adds the first end-to-end sensory pipeline on top of the v0.1 core:

- browser/DOM snapshot sensor with URL, title and content-change deltas;
- Playwright page adapter without making Playwright a core dependency;
- audio PCM sensor with a portable zero-model energy VAD;
- `speech.started` and `speech.stopped` events;
- per-sensor `raw_observations` and `semantic_events` counters;
- deterministic synthetic benchmark for reasoning-call reduction and important-event recall.

The audio and browser APIs are source-agnostic: PCM may come from a microphone, SIP, WebRTC or a file; browser snapshots may come from Playwright, Electron or another host.

## Install

```bash
pip install -e .
```

Optional screen sensor:

```bash
pip install -e '.[screen]'
```

Development dependencies:

```bash
pip install -e '.[dev]'
pytest -q
```

## 30-second demo

Watch a directory and receive meaningful file deltas:

```bash
sensum watch-files ./my-project
```

Example event:

```json
{
  "kind": "file.modified",
  "modality": "file",
  "summary": "File modified: src/payment.py",
  "entity": "file:src/payment.py",
  "changes": [{"path": "size", "before": 8120, "after": 8344}],
  "novelty": 0.72,
  "urgency": 0.1
}
```

## Browser sensor

```python
from sensum import SensumRuntime
from sensum.sensors import BrowserSensor

sensor = BrowserSensor.from_playwright_page(page)
runtime = SensumRuntime().add_sensor(sensor)
```

The sensor compares compact page snapshots locally. Repeated snapshots do not become reasoning events.

## Audio sensor

```python
from sensum import SensumRuntime
from sensum.sensors import AudioVADSensor

sensor = AudioVADSensor(my_async_pcm_source)
runtime = SensumRuntime().add_sensor(sensor)
```

The built-in `EnergyVAD` is intentionally tiny and portable. It is a baseline gate, not a claim of state-of-the-art speech detection. Silero/WebRTC/local-model adapters can replace it while keeping the same Sensum event contract.

## Benchmark

Sensum now contains a deterministic synthetic regression benchmark. It exists to prevent us from replacing measurements with marketing claims.

```bash
python benchmarks/synthetic.py --observations 10000 --seed 7
```

It reports:

- raw observations;
- semantic events after local detection;
- events sent to the reasoning layer;
- labelled important events;
- important-event recall;
- reasoning-call reduction.

**Important:** synthetic results are regression data, not real-world performance claims. Real browser/audio/screen datasets are the next benchmark milestone.

## Python SDK

```python
import asyncio
from sensum import Modality, SensoryEvent, SensumRuntime, StateChange
from sensum.sensors import ManualSensor

async def main():
    sensor = ManualSensor()
    runtime = SensumRuntime().add_sensor(sensor)
    await runtime.start()

    await sensor.emit(SensoryEvent(
        kind="payment.completed",
        source="stripe-adapter",
        modality=Modality.API,
        entity="payment:42",
        summary="Payment completed",
        changes=[StateChange("status", "pending", "completed")],
        novelty=0.9,
        urgency=0.7,
        tags=["payment"],
    ))

    event = await anext(runtime.events())
    print(event.to_dict())
    print(runtime.world.snapshot())

asyncio.run(main())
```

## The core idea

```text
RAW WORLD
   ↓
cheap/local detection
   ↓
semantic delta
   ↓
attention gate
   ↓ only if meaningful
reasoning model / agent
```

A large model should not be the first component that sees every raw signal.

## Roadmap

- [x] Core event protocol
- [x] Attention gate
- [x] World state
- [x] Async sensor runtime
- [x] File sensor
- [x] Screen change detector
- [x] Browser/DOM snapshot sensor
- [x] Audio VAD baseline
- [x] Sensor-level reduction metrics
- [x] Synthetic regression benchmark
- [ ] Audio interruption detection with agent speaking-state input
- [ ] Real browser/audio/screen benchmark dataset
- [ ] Camera motion/object-event adapter
- [ ] Local semantic perception adapters
- [ ] WebSocket / SSE gateway
- [ ] MCP adapter
- [ ] Event persistence and replay
- [ ] Learned attention policy
- [ ] Cross-modal event fusion

## Non-goals

Sensum does **not** claim that semantic perception is solved. The project provides a common runtime, protocol and attention boundary so perception models can improve independently.

Raw media should remain local by default. Sensum events should carry the minimum useful semantic delta rather than copying source streams into the reasoning layer.

## License

Apache-2.0 © 2026 AIZENSOFT
