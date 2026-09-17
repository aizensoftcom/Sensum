# Sensum Real-World Benchmark

The synthetic benchmark is a regression test. This directory defines the protocol for measuring Sensum on recorded real streams.

## Goal

Measure whether an event-driven sensory runtime can reduce expensive AI reasoning calls while retaining important changes.

## Required inputs

A session is represented as newline-delimited JSON (`.jsonl`). Each record is a raw observation from one source:

```json
{"ts":0.0,"source":"browser","payload":{"url":"https://example.test","title":"Checkout","text":"Total: 120 EUR"}}
{"ts":0.5,"source":"browser","payload":{"url":"https://example.test","title":"Checkout","text":"Total: 70 EUR"}}
{"ts":0.6,"source":"audio","payload":{"rms":0.004}}
{"ts":0.7,"source":"audio","payload":{"rms":0.091}}
```

A matching annotation file marks changes a reasoning model must not miss:

```json
{"start":0.45,"end":0.55,"label":"balance_changed","important":true}
{"start":0.65,"end":0.85,"label":"speech_started","important":true}
```

Do not commit private recordings, credentials, customer data, or raw production conversations.

## Metrics

Sensum reports:

- raw observations
- semantic events
- reasoning events
- sensor reduction
- attention reduction
- total reasoning-call reduction
- important-event precision / recall / F1
- event detection latency (p50 / p95)
- estimated payload bytes before and after filtering

The primary optimization target is **maximum reasoning-call reduction subject to high important-event recall**. Reduction without recall is not a win.

## Baselines

Every public result should compare at least:

1. `continuous`: every raw observation is sent to the reasoning layer.
2. `sensor-only`: local change detection is enabled, attention gating is disabled.
3. `sensum`: local change detection + semantic events + attention gating.

## Public claims

Synthetic results must always be labelled synthetic. Real-world numbers should include the dataset/session description, thresholds, Sensum version, hardware, and benchmark command so results are reproducible.

## First benchmark pack

The first public pack should contain reproducible, non-sensitive sessions for:

- browser: static page, navigation, modal, checkout/status changes
- audio: silence, speech start/stop, interruptions
- mixed: browser change while audio is active

Screen pixels and camera streams will be added after the event protocol and scoring harness are stable.
