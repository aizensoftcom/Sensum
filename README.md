# Sensum

**Give AI senses, not streams.**

Sensum is an open-source sensory runtime for AI systems. It converts continuous signals from the world into small, meaningful events and only wakes expensive reasoning when something matters.

> Continuous perception without continuous LLM inference.

```text
camera ─────┐
microphone ─┤
screen ─────┤
browser ────┤──> sensors -> change detection -> attention -> semantic events -> AI
files ──────┤
APIs ───────┘
```

Instead of sending 30 screenshots per second to a multimodal model, Sensum aims to emit events such as:

```text
PERSON_ENTERED room=kitchen
USER_INTERRUPTED_AGENT
PAYMENT_STATUS pending -> completed
FILE_MODIFIED src/payment.py
OBJECT_MOVED keys:table -> keys:hand
```

## Why

Most AI systems are request/response systems. Continuous agents often compensate by repeatedly sending audio, frames, screenshots or state snapshots to large models. That is expensive, noisy and hard to integrate across modalities.

Sensum introduces a small layer between the world and the model:

1. **Sense** — connect screen, audio, camera, files, browser, APIs or custom sensors.
2. **Detect change** — ignore repeated state before it reaches a model.
3. **Attend** — score novelty, urgency and confidence locally.
4. **Update world state** — maintain a compact canonical state from deltas.
5. **Emit** — publish only meaningful events to GPT, Claude, Qwen, local models or agent frameworks.

Sensum is not an LLM and not an agent framework. It is a perception and attention runtime.

## Status

`v0.1` is the minimal reference core. It includes:

- modality-agnostic **Sensum Event Protocol (SEP)**;
- pluggable asynchronous sensors;
- deterministic zero-LLM attention gate;
- canonical world-state updates;
- in-process async event bus;
- file-system sensor;
- optional low-cost screen-change sensor;
- CLI, tests and JSON Schema.

Camera understanding, audio semantics, browser/DOM adapters and local perception models are roadmap items. The project intentionally starts with the runtime contract before adding heavy dependencies.

## Install

```bash
pip install -e .
```

Optional screen sensor:

```bash
pip install -e '.[screen]'
```

## 30-second demo

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

A large model should not be the first component that sees every raw signal.

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

The long-term goal is a common sensory layer for AI: one event protocol for vision, speech, screens, browsers, software state and physical sensors.

## Roadmap

- [x] Core event protocol
- [x] Attention gate
- [x] World state
- [x] Async sensor runtime
- [x] File sensor
- [x] Screen change detector
- [ ] Browser/DOM sensor
- [ ] Audio VAD + interruption sensor
- [ ] Camera motion/object-event adapter
- [ ] Local semantic perception adapters
- [ ] WebSocket / SSE gateway
- [ ] MCP adapter
- [ ] Event persistence and replay
- [ ] Learned attention policy
- [ ] Cross-modal event fusion
- [ ] Benchmarks: tokens saved vs. important-event recall

## Non-goals

Sensum does **not** claim that semantic perception is solved. The project provides a common runtime, protocol and attention boundary so perception models can improve independently.

## License

Apache-2.0 © 2026 AIZENSOFT
