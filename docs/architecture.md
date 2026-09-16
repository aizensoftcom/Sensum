# Architecture

Sensum separates perception into four stages so expensive reasoning is not the first component that sees continuous input.

```text
Sensor -> Delta -> Attention -> World state -> Significant event -> Agent / LLM
```

## Sensor
A sensor owns modality-specific capture and cheap change detection. It should avoid forwarding raw continuous data when a local comparison can prove that nothing relevant changed.

## Sensum Event Protocol
All modalities converge on a common event envelope. Events describe semantic deltas and optional state transitions instead of forcing the downstream model to reconstruct them from full snapshots.

## Attention
An `AttentionPolicy` decides whether an event deserves downstream reasoning. The reference policy is deterministic and costs no model tokens.

## World state
`WorldState` applies event deltas to a canonical state. The large model can ask for current state only when necessary rather than rebuilding it from every previous frame.

## Event delivery
Only significant events are published downstream. v0.1 ships an in-process async bus; network gateways remain adapters so the core stays transport-agnostic.

## Design constraint
**Continuous sensing must not imply continuous large-model inference.**
