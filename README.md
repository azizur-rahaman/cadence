# Cadence (Level 10) — Weekly Team Meeting Platform

**Measure. Commit. Resolve.**  
A multi-user EOS / Level 10 workspace where leadership teams track weekly Measurables (Scorecard), quarterly Rocks & Milestones, weekly To-Dos, and prioritized Issues — and run a timed, real-time synchronized Level 10 Meeting across browsers.

| Layer | Technology |
| --- | --- |
| **Web Frontend** (`apps/web`) | Next.js (App Router), TypeScript, Tailwind CSS, shadcn/ui, TanStack Query & Table, React Hook Form + Zod, Lucide |
| **Backend API** (`apps/api`) | FastAPI (Python), SQLAlchemy 2, Alembic, Pydantic v2, native WebSockets, pure-Python `rules/` engine |
| **Database** | PostgreSQL 16 (UTC `timestamptz`, `NUMERIC` scores/goals, `CHECK` constraints, partial unique indexes) |
| **Testing & Ops** (`e2e/`, `docs/test/`) | `pytest` (rules, DB constraints, API/RBAC/concurrency), Playwright (2-browser E2E), Docker Compose, `Makefile` |

---

## 1. Quick Start

**Prerequisites:** Docker & Docker Compose (plus Python 3.12+ / Node 20+ only if running local tools outside containers).

```bash
cp .env.example .env          # Default APP_NOW=2026-11-11T15:00:00Z (Wed Nov 11, 2026 09:00 America/Chicago)
docker compose up --build     # Starts Postgres, runs Alembic migrations + idempotent seed, serves API & Web
```

| Service | URL | Notes |
| --- | --- | --- |
| **Web App** | `http://localhost:3000` | Two-page UI: Team Page (`/`) & Live Level 10 Meeting (`/meetings/[id]`) |
| **API & OpenAPI Docs** | `http://localhost:8000/docs` | Interactive Swagger UI for all `/api/v1/*` routes & error schemas |
| **Health Check** | `http://localhost:8000/api/health` | Gated by Docker healthcheck and test driver |

### Operations Commands (`Makefile`)

```bash
make help                                   # List all targets
make up / make down                         # Start or stop the Docker Compose stack
make seed                                   # Re-run idempotent seed loader safely (no duplicates)
make report                                 # Print rules_report JSON for current APP_NOW (frozen clock)
APP_NOW=2026-11-16T15:00:00Z make report    # Run rules report at any alternate date
make test                                   # Unattended full suite (Rules + DB + API + 2-browser Playwright)
make verify                                 # Full gate: ruff + tsc --noEmit + make test + rules_report parity
```

---

## 2. Seeded Personas & Server-Enforced Roles

Use the **User Switcher** in the header (backed by `POST /api/v1/auth/login` signed tokens) and **Team Switcher** to verify RBAC. All permissions are enforced server-side (`401` unauthenticated, `403` Observer write/facilitate/rate, `404` non-member team access even by guessed ID).

| Role | Seeded Users | Teams in `seed.json` | Server-Enforced Capabilities |
| --- | --- | --- | --- |
| **Admin** | `u1` (Avery Admin) | `team_lead` *(accesses all 3)* | Full read/write, own items, start/facilitate/rate meetings in **every** team |
| **Team Member** | `u2`, `u3`, `u4`, `u6`, `u8`, `u9` | `u2`: Lead+Sales; `u4`: Lead+Ops; `u3`: Lead; `u6`: Sales; `u8`/`u9`: Ops | Read/write, own items, start/facilitate/rate meetings in **own teams only** |
| **Observer** | `u5` (Leadership), `u7` (Sales) | Own team only | Read-only team data & join meetings; cannot write, own items, facilitate, or rate |

---

## 3. Repository Layout

Lightweight polyglot monorepo under `apps/` orchestrated by root `docker-compose.yml` and `Makefile` (intentionally omitting Turborepo/Nx to keep Docker builds simple and reliable):

```text
cadence/
├── AGENTS.md                 # Non-negotiable AI-first engineering invariants
├── DECISIONS.md              # 1-page Architecture Decision Record (all 5 required tradeoffs)
├── Makefile                  # Self-documenting ops & verification gates
├── docker-compose.yml        # Postgres 16 + FastAPI + Next.js
├── rules_report.json         # Committed output of `make report` at default APP_NOW
├── apps/
│   ├── api/                  # FastAPI, Alembic, seed/seed.json, pure app/rules/, pytest suites
│   └── web/                  # Next.js App Router, shared ScorecardSection & IssuesSection
├── e2e/                      # Playwright two-browser live meeting E2E suite
├── artifacts/                # Committed Playwright failure trace (failure-trace.zip)
└── docs/                     # PRD, Design System, Development Plan, Jira Plan, docs/test/
```

---

## 4. Testing, Fixture/Clock Strategy & Failure Artifact

Run **`make test`** to execute all four verification layers unattended against a freshly seeded schema with a **frozen clock** pinned to `APP_NOW` (`2026-11-11T15:00:00Z`), generating `docs/test/report/latest-test-report.md`:

1. **Rule Tests (`pytest`):** Pure unit tests in `apps/api/tests/test_rules.py` covering every business rule and boundary (all 4 goal types, `America/Chicago` Nov 1 DST transitions `t11`/`t28`/`t29`, exact 90% ratio vs. rounded %, `r2` 12.5% → 13% & `mt2` 8.25 → 8.3 half-up rounding, 0-milestone Rocks, Issue ties/nulls, `mt1`/`mt2` time windows).
2. **DB Constraint Tests (`pytest`):** Raw PostgreSQL inserts proving `CHECK` constraints and partial unique indexes reject invalid/duplicate records at the database layer.
3. **API & Concurrency Tests (`pytest`):** Full RBAC matrix (`u6` → `404` on Leadership, `u5` → `403` on writes, `u1` cross-team ownership), `422` validation, `i5`/`i6` source deduplication, and **20 parallel Make it an Issue requests** returning one Issue ID.
4. **Two-Browser E2E (`Playwright`):** Facilitator (`u2`) starts a meeting and advances Scorecard → IDS → Conclude → End while Browser 2 (`u3`) stays synced within ≤ 2s and recovers state after reload.

- **Clock & Fixture Strategy:** Tests reset to a clean seeded state and inject `FrozenClock(APP_NOW)` (zero drift, manually advanceable via `.advance()` for timer-overrun tests). The live API uses `LiveClock(APP_NOW)` (`APP_NOW + monotonic elapsed`) so meeting timers tick smoothly while starting deterministically. See [`docs/test/README.md`](./docs/test/README.md) for details.
- **Failure Artifact:** Inspect the deliberately captured Playwright failure trace with:
  ```bash
  npx playwright show-trace artifacts/failure-trace.zip
  ```

---

## 5. Assumptions & Known Limitations

### Assumptions

- **Closed vs. Current Week:** Weeks run Monday `00:00:00` to Sunday `23:59:59` in `America/Chicago`; at default `APP_NOW`, the current week is `2026-11-09` and the last closed week is `2026-11-02`.
- **Make it an Issue:** Only **unsolved** linked Issues block creation (`i5` returns `200` with existing Issue; solved `i6` allows a new `201` Issue). Auto-generated titles follow seed convention: `"<Measurable name>, week of <Mon D>"`.
- **Eligible To-Do Owners:** `(all company Admins) ∪ (team's Team Members)`, so Admin `u1` can own items in `team_sales`/`team_ops` despite only having a `team_lead` row in `seed.json`. Observers and non-members are rejected (`422`).
- **Current-Quarter Rocks:** Both the Team Page and `rules_report.json` filter Rocks to `quarter_of(APP_NOW)` in `America/Chicago`.
- **Seeded Meeting Summaries (`mt1`, `mt2`):** Because `seed.json` omits `scorecard_week` and `meeting_id`, `scorecard_week` is derived as the last closed week before `started_at`, and `issues_solved` / `todos_created` match by `started_at <= ts <= ended_at` (excluding `t22` created after `mt1` ended).
- **Observer Ratings & Auth:** Observers view meeting ratings read-only (`403` on submit). Authentication uses a seeded user switcher issuing signed session tokens.

### Known Limitations

- **Single-Instance WebSocket Hub:** Live broadcast uses an in-process FastAPI connection manager (with 2s TanStack Query polling fallback); multi-instance horizontal scaling requires Redis Pub/Sub or Postgres `LISTEN/NOTIFY` (detailed in `DECISIONS.md`).
- **No Facilitator Handoff:** Per spec, if the facilitator disconnects permanently, no transfer flow exists; reconnecting restores full facilitator control.
- **Intentionally Out of Scope:** Sign-up/passwords, email/notifications, billing, third-party integrations, Private To-Dos, Long-Term Issues, CRUD for teams/users/Measurables/Rocks, and a meeting history page.

---

## 6. AI Tools Used & Human Verification

| Area | AI Tool Used | How Used | Verified / Engineered by Hand |
| --- | --- | --- | --- |
| **Architecture & Specs** | Antigravity (Gemini) | Cross-checked PRD, Jira Plan, Design System, and seed traps against brief | Locked two-page scope, DB partial unique indexes, and 5 decision tradeoffs |
| **Rules Engine & Tests** | Antigravity (Gemini) | Drafted pure `apps/api/app/rules/*` functions and pytest suites | Hand-verified every `seed.json` trap (Nov 1 DST, `Decimal` half-up `12.5% → 13%` / `8.25 → 8.3`, exact 90%, `mt1`/`mt2` windows) |
| **API, Real-Time & UI** | Antigravity (Gemini) | Scaffolded FastAPI routers, Alembic schema, WS hub, and shared React sections | Reviewed every RBAC dependency, atomic `ON CONFLICT` SQL, timer ownership, and two-browser Playwright sync |

*(Updated at final submission in Phase 5 to reflect exact final implementation verification notes.)*

---

## 7. Project Documentation

- **[`DECISIONS.md`](./DECISIONS.md)** — 1-page Architecture Decision Record (all 5 required tradeoffs)
- **[`AGENTS.md`](./AGENTS.md)** — AI-first engineering invariants & verification rules
- **[`docs/PRD.md`](./docs/PRD.md)** — Complete product requirements, business rules & `rules_report.json` schema
- **[`docs/DEVELOPMENT_PLAN.md`](./docs/DEVELOPMENT_PLAN.md)** — Phase-wise GitHub feature-branch roadmap
- **[`docs/DESIGN_SYSTEM.md`](./docs/DESIGN_SYSTEM.md)** — Enterprise SaaS design tokens & two-page UI standard
- **[`docs/test/README.md`](./docs/test/README.md)** — Fixture/clock strategy, test runner & manual walkthrough
