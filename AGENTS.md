# AGENTS.md — Cadence (Level 10) Non-Negotiable Engineering Invariants

> **Project:** Cadence (Level 10) — Weekly Team Meeting Platform (EOS / Level 10)  
> **Target Audience:** All AI Agents, Coding Subagents, and Engineers working in this repository.  
> **Authority:** Absolute & Non-Negotiable. Any code change, commit, or PR violating these invariants must be rejected immediately.

---

## 1. Strict Git Branching & Push Governance (ABSOLUTE RULE)

1. **`main` IS PULL-REQUEST MERGE ONLY (ZERO DIRECT COMMITS OR PUSHES):**
   - **STRICTLY FORBIDDEN:** Never commit directly on `main`. Never run `git push origin main`, `git push <remote> <ref>:main`, or force-push to `main`.
   - `main` may **ONLY** receive changes through Pull Request merges on GitHub (`dev` → `main` via PR), and locally may only be updated via `git pull --ff-only origin main`.
2. **`dev` IS THE ACTIVE INTEGRATION & PUSH BRANCH:**
   - All development pushes go through **`dev`** (and short-lived feature branches cut from `dev`: `<type>/p<phase>-<feature-slug>` → merged into `dev`).
   - Always check `git branch --show-current` before running `git commit` or `git push`. If on `main`, **STOP immediately** and switch to `dev` or a feature branch cut from `dev`.
3. **Conventional Commits & Clean History:**
   - Use Conventional Commits with Jira story keys where applicable (e.g., `feat(scorecard): add atomic make-it-an-issue endpoint (E5-S3)`).
   - Never commit `.env`, `.DS_Store`, or build artifacts (except the committed `artifacts/failure-trace.zip` and `rules_report.json`).

---

## 2. Architecture & Monorepo Invariants

- **Lightweight Polyglot Monorepo (`apps/`):**
  - `apps/api/` — FastAPI (Python), SQLAlchemy 2, Alembic, Pydantic v2, native WebSockets, `pytest`.
  - `apps/web/` — Next.js (App Router), TypeScript, Tailwind CSS, shadcn/ui, TanStack Query & Table, React Hook Form + Zod.
  - `e2e/` — Playwright two-browser E2E suite.
  - **Do NOT add Turborepo, Nx, or pnpm workspaces** — keep Docker builds and fresh-clone setup simple.
- **Two-Page Frontend Scope (`docs/DESIGN_SYSTEM.md` & `docs/PRD.md`):**
  - Only two pages exist: **Team Page** (`/`) and **Live Level 10 Meeting Page** (`/meetings/[id]`).
  - `ScorecardSection` and `IssuesSection` must be built **once** and reused identically on both pages.
  - Do **not** add out-of-scope views (`Dashboard`, `Team Settings`, `Meeting History`, `Notifications`, `Search`).

---

## 3. Deterministic Time, Math & Pure Rules Invariants

- **Clock Service Only — NO Wall-Clock Calls:**
  - **STRICTLY FORBIDDEN:** Never call `datetime.now()`, `datetime.utcnow()`, or `date.today()` anywhere outside `apps/api/app/clock.py`.
  - Live API uses `LiveClock(APP_NOW)` (`APP_NOW + monotonic elapsed`) for meeting timers; `make report` and all automated tests use `FrozenClock(APP_NOW)` (zero elapsed offset).
  - Store all timestamps in UTC (`TIMESTAMPTZ`); compute weeks, quarters, and due dates in `ZoneInfo("America/Chicago")` (never a fixed UTC offset — DST ends Nov 1, 2026).
- **Exact Math — NO `float` or Banker's `round()`:**
  - Store scores and goals as PostgreSQL `NUMERIC` and compute with Python `Decimal`.
  - Always round percentages (whole numbers) and ratings (1 decimal) using `Decimal.quantize(..., rounding=ROUND_HALF_UP)` — never Python's built-in `round()`.
  - Compare To-Do 90% target using exact integer ratio (`done * 10 >= due * 9`), never the rounded percent.
- **Pure Business Rules Module (`apps/api/app/rules/`):**
  - Every business rule lives in `apps/api/app/rules/` with **zero** FastAPI or SQLAlchemy imports.
  - Both the API and `make report` call the exact same `rules/` functions.
  - **Zero business logic in React** — UI renders server-computed statuses, overdue flags, progress %, completion rates, and timer values.

---

## 4. Security, RBAC & Data Integrity Invariants

- **Centralized Server-Side Authorization:**
  - Every route uses `require_team_read` / `require_team_write` in `apps/api/app/auth/deps.py`. Never check roles ad-hoc or rely on hiding UI buttons.
  - Non-member team access returns **`404 Not Found`** (even for guessed IDs); Observer writes/facilitate/rate return **`403 Forbidden`**.
  - For ID-based routes (`/issues/{id}`, `/todos/{id}`, `/meetings/{id}`), always resolve the resource's `team_id` before running the auth check.
  - Eligible To-Do owners = `(all company Admins) ∪ (team's Team Members)`; reject Observers and cross-team members with `422`.
- **Database-Enforced Integrity:**
  - Enforce `CHECK` constraints (roles, priority `1..5`, rating `1..10`, goal shapes, non-empty titles & resolution notes) and both partial unique indexes (`issues` unsolved source + `meetings` one active per team) directly in PostgreSQL migrations.
  - "Make it an Issue" must remain atomic via `INSERT ... ON CONFLICT DO NOTHING` + `SELECT` (`201` created / `200` existing).
- **Standard DTO & Response Envelope Contract (`apps/api/app/dto/`):**
  - Every REST endpoint MUST accept/return explicit Pydantic DTOs from `apps/api/app/dto/` (never raw SQLAlchemy models or bare top-level JSON arrays).
  - Every `2xx` REST response MUST be wrapped in `ApiResponse[T]` (`{success: true, data: T, meta: {request_id, timestamp}}`) via `ok(...)`; every `4xx`/`5xx` error MUST return `ApiErrorResponse` (`{success: false, error: {code, message, fields?}, meta: {request_id, timestamp}}`) with an `X-Request-Id` header.
  - Real HTTP status codes remain the source of truth (`200`, `201`, `401`, `403`, `404`, `409`, `422`). The CLI `make report` JSON stays unwrapped verbatim per starter `README.md`.

---

## 5. Compulsory Verification Gate

Before committing or opening any PR (once tooling is active from Phase 1.1 onward), run:

```bash
make verify
```

Zero tolerance for lint errors (`ruff`), TypeScript compiler errors (`tsc --noEmit`), failing tests (`pytest` / Playwright), or drift in `rules_report.json`. Reference [`docs/PRD.md`](./docs/PRD.md), [`docs/DEVELOPMENT_PLAN.md`](./docs/DEVELOPMENT_PLAN.md), and [`docs/DESIGN_SYSTEM.md`](./docs/DESIGN_SYSTEM.md) before starting any feature slice.
