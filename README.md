# Sensum

**Perception runtime for always-on AI agents.**

**Give AI senses, not streams.**

Sensum is an open-source, event-driven perception and attention runtime for **AI agents, multimodal AI, voice agents, browser agents and computer-use systems**. It turns continuous audio, screen, browser, vision, file and API signals into compact semantic events — so expensive LLM reasoning runs only when something meaningful changes.

> Continuous perception without continuous LLM inference.

```text
camera ─────┐
microphone ─┤
screen ─────┤
browser ────┤──> local detection -> world state -> attention -> semantic events -> AI
files ──────┤                         │       │
APIs ───────┘                         │       └─ attention budget
                                      ├─ persistence / replay
                                      └─ multimodal fusion
```

Instead of repeatedly sending raw streams to a model, Sensum emits events such as:

```text
USER_INTERRUPTED_AGENT
BROWSER_NAVIGATED
PAYMENT_STATUS pending -> completed
VISION_OBJECT_ENTERED person
FILE_MODIFIED src/payment.py
```

## Why Sensum

Always-on AI agents need continuous awareness, but continuously sending screenshots, audio frames and state snapshots to an LLM is expensive and noisy.

Sensum adds a lightweight perception layer between the world and the model:

- **Local change detection** — filter repeated or irrelevant input before reasoning.
- **Semantic events** — normalize browser, audio, vision, screen, files and APIs into one event model.
- **World state** — maintain compact canonical state plus transition history.
- **Attention routing** — wake expensive AI only when events matter.
- **Multimodal fusion** — correlate events across modalities.
- **Persistence + replay** — inspect what happened and why.
- **Vendor-neutral agent integration** — keep perception independent from the LLM provider.

Sensum is not an LLM and not another agent framework. **It is sensory infrastructure for always-on AI.**

## Core use cases

- voice AI and interruption / barge-in detection
- browser and computer-use agents
- multimodal AI assistants
- local and edge AI perception
- autonomous agents monitoring apps, files and APIs
- robotics, cameras and smart environments
- event-driven enterprise AI monitoring

## Current capabilities

- Sensum Event Protocol
- browser / DOM sensor
- audio VAD and interruption events
- screen-change detection
- file sensor
- vision-observation sensor
- deterministic attention scoring
- rolling attention budgets
- world state + transition history
- SQLite event persistence + replay
- temporal multimodal fusion
- SSE + WebSocket gateway
- live debugging dashboard
- provider-neutral agent adapter API
- sensor plugin registry
- reproducible benchmark harness

The core remains lightweight and dependency-free. Server, screen and future local-perception integrations stay optional.

## Install

```bash
pip install -e .
```

Live gateway and dashboard:

```bash
pip install -e '.[server]'
sensum serve
```

Open `http://127.0.0.1:8765`.

## Minimal example

```python
import asyncio

from sensum import Modality, SensoryEvent, SensumRuntime
from sensum.sensors import ManualSensor


async def main():
    sensor = ManualSensor()
    runtime = SensumRuntime().add_sensor(sensor)
    await runtime.start()

    receive = asyncio.create_task(anext(runtime.events()))
    await asyncio.sleep(0)

    await sensor.emit(
        SensoryEvent(
            kind="payment.completed",
            source="payment-adapter",
            modality=Modality.API,
            entity="payment:42",
            summary="Payment completed",
            novelty=0.9,
            urgency=0.7,
            tags=["payment"],
        )
    )

    event = await receive
    print(event.to_dict())
    await runtime.stop()


asyncio.run(main())
```

## Voice AI

```python
from sensum import SensumRuntime
from sensum.sensors import AgentSpeakingState, AudioVADSensor

agent = AgentSpeakingState(speaking=False)
sensor = AudioVADSensor(my_async_pcm_source, agent_speaking=agent)
runtime = SensumRuntime().add_sensor(sensor)
```

When user speech starts while the agent is speaking, Sensum can emit:

```text
user.interrupted_agent
```

The built-in energy VAD is intentionally small and replaceable by local perception adapters.

## Browser / computer-use agents

```python
from sensum import SensumRuntime
from sensum.sensors import BrowserSensor

sensor = BrowserSensor.from_playwright_page(page)
runtime = SensumRuntime().add_sensor(sensor)
```

Repeated page snapshots stay local. Meaningful navigation, title and content changes become semantic events instead of another full observation sent to the model.

## World state, memory and replay

```python
from sensum import SQLiteEventStore, SensumRuntime

store = SQLiteEventStore("sensum.db")
runtime = SensumRuntime(store=store)

runtime.world.value("payment:42", "status")
runtime.world.history(entity="payment:42", path="status")
```

Sensum can retain semantic observations before attention filtering, enabling debugging, replay and retrospective queries.

## Multimodal attention

```python
from sensum import BudgetedAttention, DEFAULT_RULES, SensumRuntime, TemporalFusionEngine

runtime = SensumRuntime(
    attention=BudgetedAttention(max_events=10, window_seconds=60),
    fusion=TemporalFusionEngine(DEFAULT_RULES),
)
```

The attention layer controls which events reach expensive reasoning, while fusion can correlate related audio, browser, screen and vision events.

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
POST /ingest         external semantic events
```

## Benchmarks

Reference regression suite:

```bash
python benchmarks/reference_suite.py --generate --check
```

Recorded labelled fixture:

```bash
python benchmarks/recorded.py path/to/fixture.jsonl
```

Sensum measures raw observations, semantic events, reasoning events, recall, precision and reasoning-call reduction.

**Synthetic and generated reference results are not real-world performance claims.** Public results should follow `docs/benchmarking.md` with reproducible, privacy-safe datasets.

## Architecture

```text
WORLD / APPS
    ↓
local perception + change detection
    ↓
Sensum Event Protocol
    ↓
World State ──────> Persistence / Replay
    ↓
Multimodal Fusion
    ↓
Attention + Budget
    ↓
important events only
    ↓
AI Agent / LLM
```

## Roadmap

Near-term priorities:

- stronger local perception adapters: VAD, STT, ONNX and vision
- real browser / audio / screen benchmark datasets
- OpenAI, Anthropic, Gemini, Ollama and MCP integrations
- richer world-event relationships
- cross-modal scene understanding
- stable plugin and event protocol ecosystem

See [`docs/roadmap.md`](docs/roadmap.md) for the implementation roadmap.

Rust is intentionally deferred until profiling proves where Python is the bottleneck.

## Privacy and security

Raw media should remain local by default. Sensum events should carry the minimum useful semantic delta instead of forwarding source streams into the reasoning layer.

See [`SECURITY.md`](SECURITY.md) before exposing the gateway outside localhost.

## Keywords

AI agents · multimodal AI · voice AI · computer use · browser agents · event-driven AI · AI perception · local AI · edge AI · world model · attention routing · semantic events · agent infrastructure · LLM infrastructure

## License

Apache-2.0 © 2026 AIZENSOFT
