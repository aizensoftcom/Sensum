# Sensum roadmap

## v0.2 — sensory runtime

- [x] Sensum Event Protocol core
- [x] async sensor runtime
- [x] deterministic attention gate
- [x] world state
- [x] file and screen-change sensors
- [x] browser/DOM snapshot sensor
- [x] audio VAD baseline
- [x] interruption event
- [x] SSE/WebSocket gateway
- [x] live dashboard
- [x] sensor/runtime metrics

## v0.3 — measurable memory and attention

- [x] SQLite event persistence
- [x] replay API
- [x] world-state history
- [x] rolling attention budgets with urgent bypass
- [x] deterministic temporal multimodal fusion
- [x] source-agnostic vision observation sensor
- [x] recorded benchmark harness
- [x] benchmark methodology
- [ ] commit privacy-safe real browser fixture
- [ ] commit privacy-safe real audio fixture
- [ ] commit privacy-safe real screen fixture
- [ ] publish measured benchmark report

## v0.4 — world model

- [x] entity/path state transitions
- [x] transition history
- [x] durable semantic event log
- [ ] relationship graph between entities/events
- [ ] snapshots/checkpoints for fast recovery
- [ ] query API for temporal questions

## v0.5 — multimodal fusion

- [x] deterministic temporal rule engine
- [x] source event provenance in fused events
- [ ] entity correlation across modalities
- [ ] scene lifecycle
- [ ] pluggable learned fusion policy
- [ ] benchmark cross-modal event recall

## v0.6 — local perception

- [x] zero-model energy VAD baseline
- [x] generic vision-observation boundary
- [ ] optional Silero/WebRTC VAD adapters
- [ ] optional faster-whisper adapter
- [ ] optional ONNX classifier adapter
- [ ] optional local object detector adapter

Local model integrations should remain optional extras or separate packages so the core stays light.

## v0.7 — agent integrations

- [x] provider-neutral `AgentAdapter` contract
- [x] callback adapter and event pump
- [ ] OpenAI example integration
- [ ] Anthropic example integration
- [ ] Gemini example integration
- [ ] Ollama example integration
- [ ] MCP adapter

Provider SDKs should not become core dependencies.

## v0.8 — protocol and plugins

- [x] JSON Schema for SEP v0.1
- [x] neutral schema identifier
- [x] in-process plugin registry
- [ ] freeze SEP/1 compatibility rules
- [ ] Python entry-point plugin discovery
- [ ] standalone sensor packages
- [ ] compatibility test kit for third-party sensors

## v0.9 — ecosystem

- [ ] official browser package
- [ ] official audio package
- [ ] official vision package
- [ ] GitHub/Slack/Home Assistant/Stripe adapters
- [ ] community registry / awesome-sensum
- [ ] example applications

## v1.0 — production runtime

Rust is intentionally deferred until profiling demonstrates a Python bottleneck.

- [ ] production benchmark suite
- [ ] durable checkpoints and crash recovery
- [ ] authentication guidance/reference gateway
- [ ] observability/health contracts
- [ ] stable SEP/1
- [ ] performance profile and Rust go/no-go decision
- [ ] Rust hot path only where measurements justify it

## Release principle

A roadmap checkbox means working code or reproducible documentation exists. Performance claims are
not considered complete until backed by a recorded benchmark fixture and published methodology.
