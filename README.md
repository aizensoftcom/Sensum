# Sensum

**Give AI senses, not streams.**

Sensum is an open-source sensory runtime for AI systems. It converts continuous world signals into small semantic events and only wakes expensive reasoning when something matters.

> Continuous perception without continuous LLM inference.

```text
camera ─────┐
microphone ─┤
screen ─────┤
browser ────┤──> local detection -> world state -> attention -> events -> AI
files ──────┤                         │       │
APIs ───────┘                         │       └─ attention budget
                                      ├─ persistence / replay
                                      └─ multimodal fusion
```

Example events:

```text
SPEECH_STARTED
USER_INTERRUPTED_AGENT
BROWSER_NAVIGATED
PAYMENT_STATUS pending -> completed
VISION_OBJECT_ENTERED person
FILE_MODIFIED src/payment.py
```

## Why

Continuous agents should not need to send every audio frame, screenshot or state snapshot to a large model. Sensum puts a cheap, local and inspectable attention layer between raw signals and expensive reasoning.

Sensum is not an LLM and not an agent framework. It is sensory infrastructure.

## v0.3 alpha

The current development line includes:

- modality-agnostic Sensum Event Protocol;
- browser/DOM, audio VAD, interruption, file, screen-change and vision-observation sensors;
- deterministic attention scoring;
- rolling attention budgets with urgent-event bypass;
- canonical world state plus transition history;
- SQLite semantic event persistence and replay;
- deterministic temporal multimodal fusion;
- SSE and WebSocket gateway;
- HTTP ingest, world state, history, replay and metrics APIs;
- live debugging dashboard;
- provider-neutral agent adapter contract;
- sensor plugin registry;
- synthetic regression benchmark;
- recorded/labelled benchmark harness for real datasets.

The core remains dependency-free. FastAPI/Uvicorn and screen capture are optional extras.

## Install

```bash
pip install -e .
```

Optional screen sensor:

```bash
pip install -e '.[screen]'
```

Live gateway and dashboard:

```bash
pip install -e '.[server]'
sensum serve
```

Open `http://127.0.0.1:8765`.

## Gateway

```text
GET  /               dashboard
GET  /health         health check
GET  /stats          runtime + sensor metrics
GET  /world          canonical world state
GET  /world/history  state transition history
GET  /replay         persisted semantic events
GET  /events         SSE event stream
WS   /ws             WebSocket event stream
POST /ingest         push external semantic events
```

The development server binds to localhost by default. Put authentication and TLS in front of any remotely reachable deployment.

## Browser sensor

```python
from sensum import SensumRuntime
from sensum.sensors import BrowserSensor

sensor = BrowserSensor.from_playwright_page(page)
runtime = SensumRuntime().add_sensor(sensor)
```

Repeated snapshots stay local. URL, title and meaningful text changes become semantic deltas.

## Audio + interruption

```python
from sensum import SensumRuntime
from sensum.sensors import AgentSpeakingState, AudioVADSensor

agent = AgentSpeakingState(speaking=False)
sensor = AudioVADSensor(my_async_pcm_source, agent_speaking=agent)
runtime = SensumRuntime().add_sensor(sensor)
```

When the agent is speaking and user speech starts, Sensum emits `user.interrupted_agent`.

The built-in `EnergyVAD` is a portable zero-model baseline, not a state-of-the-art VAD claim. Silero/WebRTC adapters can replace it without changing the event contract.

## Vision boundary

Sensum does not require raw camera frames in the reasoning layer. A cheap local CV component can provide object/motion observations:

```python
from sensum.sensors import VisionEventSensor, VisionObservation

async def observe():
    return VisionObservation(
        objects=frozenset({"person", "package"}),
        motion_score=0.72,
        scene="front-door",
    )

sensor = VisionEventSensor(observe)
```

## Persistence + replay

```python
from sensum import SQLiteEventStore, SensumRuntime

store = SQLiteEventStore("sensum.db")
runtime = SensumRuntime(store=store)
```

Every semantic event can be retained before attention filtering, making debugging and retrospective queries possible.

## World-state history

```python
runtime.world.value("payment:42", "status")
runtime.world.history(entity="payment:42", path="status")
```

## Multimodal fusion

```python
from sensum import DEFAULT_RULES, SensumRuntime, TemporalFusionEngine

fusion = TemporalFusionEngine(DEFAULT_RULES)
runtime = SensumRuntime(fusion=fusion)
```

The first implementation is deterministic and temporal. It preserves source-event provenance in fused events so learned fusion can be added later without hiding why an event exists.

## Attention budgets

```python
from sensum import BudgetedAttention, SensumRuntime

runtime = SensumRuntime(
    attention=BudgetedAttention(max_events=10, window_seconds=60, bypass_urgency=0.9)
)
```

Normal reasoning events can be capped while alarms/interruption-level events bypass the quota.

## Agent adapters

```python
from sensum import AgentEventPump, CallbackAgentAdapter

async def send_to_agent(event):
    ...

pump = AgentEventPump(CallbackAgentAdapter(send_to_agent))
await pump.run(runtime.events())
```

This deliberately avoids making OpenAI, Anthropic, Gemini, Ollama or other provider SDKs core dependencies.

## Benchmarks

Synthetic regression benchmark:

```bash
sensum benchmark --observations 10000 --seed 7
```

Recorded labelled fixture:

```bash
python benchmarks/recorded.py path/to/fixture.jsonl
```

The recorded harness reports raw observations/bytes, semantic events, reasoning events, recall, precision and reasoning-call reduction.

**Synthetic results are not real-world performance claims.** Public performance numbers should use the methodology in `docs/benchmarking.md` and privacy-safe recorded fixtures.

## Python SDK

```python
import asyncio
from sensum import Modality, SensoryEvent, SensumRuntime, StateChange
from sensum.sensors import ManualSensor

async def main():
    sensor = ManualSensor()
    runtime = SensumRuntime().add_sensor(sensor)
    await runtime.start()

    receive = asyncio.create_task(anext(runtime.events()))
    await asyncio.sleep(0)
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

    event = await receive
    print(event.to_dict())
    await runtime.stop()

asyncio.run(main())
```

## Roadmap

See `docs/roadmap.md` for the implementation-level roadmap. Near-term work is intentionally evidence-driven: privacy-safe browser/audio/screen fixtures, a measured benchmark report, richer world relationships and optional local perception adapters.

Rust is deferred until profiling shows where Python is actually the bottleneck.

## Privacy and security

Raw media should remain local by default. Events should carry the minimum useful semantic delta. See `SECURITY.md` before exposing the gateway outside localhost.

## License

Apache-2.0 © 2026 AIZENSOFT
