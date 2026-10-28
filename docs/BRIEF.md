# DIT v2 Admin Center: project brief

From Blizz (owner), Oct 27 2026, 11:01 PM CT.

## What to build

A web-based **Admin Center for DIT v2**, the platform for human-like bots (the "neural network").

- The DIT v2 hub runs at `127.0.0.1:7390` on bansheerealm.
- FFXI comes first, then SWTOR.
- The sister project is `~/dev/dit-human-behavior-platform`. Its lead owns the hub and its contracts. This project builds against those contracts and does not change them on its own.

The Admin Center manages the neural network and **all bots** from one place.

## Goal

Make the bots as human-like as possible. Use AI and per-game learning wherever they help.

## Features

1. **Bots, games and status.** A list of every bot, the game it's in, and its live status.
2. **Per-bot controls.** Start, stop and pause each bot. Set its goals and personality. View its memory.
3. **LLM choice.** Pick a model per bot, or use one model for all bots, and switch at any time.
   - The design is provider-agnostic: Codex/OpenAI, Claude, Gemini and local models.
   - Use a fast, cheap model for moment-to-moment actions.
   - Use a stronger model for planning.
   - Use plain rules wherever a rule is enough.
4. **Per-call logging and bake-off.** Log cost, latency and quality for every model call. A bake-off tool compares models on real tasks.
5. **Action and evidence ledger view.** Dispatch is not progress: every action goes request, then read result, then verify.
6. **Kill switches and gates.** Gates are OFF by default. Kill switches can stop any bot at once.
7. **Audit log.** A record of every admin action.
8. **Per-game learning and training status.**
   - What each game still needs the bots to learn.
   - Datasets.
   - Whether each policy or set of weights is verified.
9. **Issues and risks panel.** What's missing, which adapters are unfinished, and open problems.

## Security

- Auth is required. For now that is an owner-only token. Banshee Realm accounts come later.
- Bind only to localhost or the tailnet.
- No secrets in this repo. Tokens and keys live in env or untracked local files.
- Stay read-only against FFXI data until Blizz grants more.
- No SBISD accounts or models in this project.

## Concept summaries (from Blizz's DIT v2 concept videos)

- **Native bots.** Bots run natively on the server (CCharEntity TYPE_PC, socketless), separate from the chat hub.
- **Decision loop.** Observe, then Choose, then Act, then reassess.
- **Evidence.** Every action needs evidence.
- **Grounded memory.** Bots remember people and never claim fictional progress.
- **Baseline vs rebuild.** The recorded baseline and the local rebuild are kept separate.
- **Where things stand.**
  - Live: the older hub plus group chat.
  - Local: the r10 contract plus the action ledger.
  - Remaining: the FFXI and PlanetSide adapters, plus research.

## First tasks for the lead

1. **Architecture and API contract.**
   - Read the DIT v2 docs in `~/dev/dit-human-behavior-platform/docs`, which you may read but not modify.
   - Read the concept summaries above.
   - Write `docs/ARCHITECTURE.md` and an API contract (`docs/API.md` or an OpenAPI file) together with the DIT v2 lead. Coordinate through the Devbox coordinator.
   - Prior art you may read but not modify: `~/dev/dit-control-center`, the older Next.js neuronetwork UI.
2. **Scaffold.** Set up the app with tests.
3. **Learning and issues list.** Write `docs/LEARNING-AND-ISSUES.md`: what each game needs to learn, plus open issues and risks.
4. **Local dev instance.** Stand up a local dev instance with mock data. It binds to localhost only.
5. **Commit and report.** Commit often. Report progress to the coordinator in short, plain messages.

## Standing behavior

Work continuously, like the other leads. Stop only for quota or an account swap.

## Rules

- Never touch real game saves or live characters.
- Do not touch the old v1 DIT hub on AX41.
- Box capacity: at most 6 parallel jobs, any one process under about 12 GB, use timeouts, and run one heavy job at a time. Wait if load is above 40 or available memory is below 40 GB.
- Do not commit retail binaries or extracted game data.
