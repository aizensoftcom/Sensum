# Sensum Event Protocol (SEP) v0.1

SEP is a minimal, modality-agnostic event shape for AI perception systems.

The protocol describes **meaningful state changes**, not raw media streams. A camera implementation may keep frames locally and emit `person.entered`; a screen implementation may emit `screen.changed`; a browser integration may emit `order.status_changed`.

## Design goals

1. **Modality independent** — audio, vision, UI, files and physical sensors use one envelope.
2. **Delta first** — events represent what changed since the previous state.
3. **Attention ready** — every event carries confidence, novelty and urgency signals.
4. **State compatible** — optional `changes` can update a canonical world state.
5. **Model agnostic** — no dependency on a specific LLM, VLM or agent framework.

## Example

```json
{
  "id": "evt-123",
  "occurred_at": "2026-09-17T01:00:00Z",
  "kind": "object.moved",
  "source": "camera.front_door",
  "modality": "vision",
  "summary": "Keys moved from the table to John's hand",
  "entity": "object:keys",
  "changes": [{"path": "location", "before": "table", "after": "john.hand"}],
  "confidence": 0.94,
  "novelty": 0.82,
  "urgency": 0.10,
  "metadata": {},
  "tags": ["movement"]
}
```

## Attention contract

The runtime must be able to suppress low-value observations without invoking a large model. The reference implementation uses deterministic scoring. Future implementations can use tiny local classifiers, rules, embeddings or learned salience models.

## Privacy principle

Raw media should remain local by default. An event may include a reference to raw evidence in `metadata`, but SEP does not require raw audio, video or screenshots to leave the sensor process.
