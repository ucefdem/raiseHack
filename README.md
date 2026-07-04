# raiseHack

AI Office Platform — 3D building with specialized AI agents per department.

## Quick start

```bash
cp .env.example .env
npm install
npm run dev        # Web app → http://localhost:3000
npm run dev:api    # API       → http://localhost:3001
```

## Monorepo

| Package | Description |
|---------|-------------|
| `apps/web` | Next.js + React Three Fiber 3D frontend |
| `apps/api` | Hono REST API (chat, presence, meet stubs) |
| `packages/shared` | Shared TypeScript interface contracts |

See [ARCHITECTURE.md](./ARCHITECTURE.md) for team contracts and folder layout.
See [HACKATHON_PLAN.md](./HACKATHON_PLAN.md) for the full product plan.

## Team

- **Person 1** — 3D scene, department navigation, selection state
- **Person 2** — Agent registry, chat API, personas
- **Person 3** — Realtime presence
- **Person 4** — Google Meet + voice/video POC
- **Person 5** — Integration, auth, CI, demo polish
