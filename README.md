# DIT v2 Admin Center

A web Admin Center for **DIT v2**, the platform for human-like game bots (the "neural network"). It manages the network and every bot from one place:

- bot status, controls, goals, personality and memory
- the model used per bot, or one model for all bots
- cost, latency and quality logging, plus model bake-offs
- the action and evidence ledger
- kill switches and audit
- per-game learning status
- issues and risks

- Owner: Blizz.
- Hub: DIT v2 at `127.0.0.1:7390` on bansheerealm. Its contracts are owned by the `dit-human-behavior-platform` project.
- Game order: FFXI first, then SWTOR.

See [docs/BRIEF.md](docs/BRIEF.md) for the full brief, security rules and first tasks.

## Status

Scaffolding has not started. The project lead adds the app, tests and the local mock-data dev instance.

## Security

- Owner-only token auth for now.
- Binds to localhost or the tailnet only.
- No secrets in git. Use env vars or untracked `.env.local`.
- Read-only against FFXI data until the owner grants more.
