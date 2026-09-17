# Security

Sensum is designed to sit close to sensitive signals such as microphones, screens, browsers,
files and cameras. The default design principle is therefore **local-first perception and minimal
event disclosure**: raw media should stay at the source whenever possible, while downstream AI
systems receive only the smallest useful semantic delta.

## Reporting a vulnerability

Please do not open a public issue for a vulnerability that could expose credentials, private
content, raw sensory data or remote-code execution. Contact the maintainers privately through the
repository owner's GitHub profile until a dedicated security contact is published.

Include the affected version, reproduction steps, impact and any suggested mitigation. Avoid
including real credentials, customer data or private recordings in reports.

## Deployment guidance

- Bind the development gateway to `127.0.0.1` unless remote access is intentionally configured.
- Put authentication and TLS in front of any remotely reachable gateway.
- Treat `/ingest`, `/events`, `/ws`, `/world`, `/world/history` and `/replay` as sensitive APIs.
- Store SQLite event logs on encrypted storage when events can contain private state.
- Keep raw audio/video out of event metadata by default.
- Give sensors the minimum filesystem, browser and device permissions they need.

The v0.x series is alpha software and has not received a third-party security audit.
