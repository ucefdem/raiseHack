# Architecture & Interface Contracts

Monorepo layout for the AI Office Platform hackathon.

## Structure

```
raiseHack/
├── apps/
│   ├── web/          # Next.js + React Three Fiber (Person 1, 3, 4, 5 UI)
│   └── api/          # Hono REST API (Person 2, 3, 4 backend)
├── packages/
│   └── shared/       # Shared TypeScript contracts
└── .env.example
```

## Shared contracts (`@raisehack/shared`)

| Type | Fields | Owner |
|------|--------|-------|
| `Agent` | `id`, `name`, `role`, `departmentId`, `personaPrompt`, `status` | Person 2 |
| `Department` | `id`, `name`, `description`, `floor`, `zone`, `agentIds` | Person 1 |
| `PresenceEvent` | `userId`, `departmentId`, `state`, `timestamp` | Person 3 |
| `MeetLink` | `departmentId`, `agentId?`, `url`, `label` | Person 4 |
| `ChatRequest` | `agentId`, `conversationId?`, `message`, `context?` | Person 2 |
| `OfficeSelectionContext` | selection state + setters for cross-module wiring | Person 1 |

## Selection state (Person 1 → everyone)

The 3D frontend exposes selection via `SelectionProvider` / `useSelection()`:

- `selectedDepartmentId` / `selectedAgentId`
- `selectedDepartment` / `selectedAgent` (resolved objects)
- `setSelectedDepartment`, `setSelectedAgent`, `clearSelection`

Other modules read this hook — no prop drilling required.

## API routes (stubs ready for owners)

| Route | Owner | Status |
|-------|-------|--------|
| `GET /api/departments` | Person 1/5 | Seed data |
| `GET /api/agents` | Person 2 | Seed data |
| `POST /api/chat` | Person 2 | Stub |
| `GET /api/presence` | Person 3 | Stub |
| `GET /api/meet/:departmentId` | Person 4 | Stub |

## Branch strategy

- `main` — stable
- `integration` — merge target at Hour 10 and Hour 18
- Feature branches: `feat/p1-3d-scene`, `feat/p2-chat`, etc.

## Local development

```bash
cp .env.example .env
npm install
npm run dev        # web on :3000
npm run dev:api    # api on :3001
npm run dev:all    # both
```

## Web feature folders (Person 1)

```
apps/web/src/
├── data/departments.ts
├── data/agents.ts
├── features/scene/BuildingScene.tsx
├── features/departments/DepartmentPanel.tsx
├── features/selection/SelectionProvider.tsx
└── features/shell/OfficeShell.tsx
```
