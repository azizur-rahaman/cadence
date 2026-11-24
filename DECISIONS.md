# Architecture Decisions (`DECISIONS.md`)

Key architectural choices for **Cadence (Level 10)** and their explicit tradeoffs.

---

## 1. Real-Time Meeting Sync & Reconnection
- **Decision:** Native FastAPI WebSockets (`WS /api/v1/meetings/{id}/ws?token=...`) backed by an in-process `MeetingHub` that sends a full authoritative `snapshot` on connect/reconnect and broadcasts `state_updated`, `attendee_joined`, `presence_updated`, and `workspace_updated` events — paired with a 2-second TanStack Query polling fallback whenever the socket is disconnected.
- **Why:** Sub-second sync across browsers with zero extra infrastructure (no Redis/broker container to debug on a fresh `docker compose up`), instant recovery on page reload or Wi-Fi drop via full snapshots, and guaranteed eventual sync even behind restrictive proxies.
- **Tradeoff:** An in-process hub assumes a single API replica; horizontal scaling to multiple API workers would require replacing the broadcast fan-out with Redis Pub/Sub or PostgreSQL `LISTEN/NOTIFY` while keeping the exact same snapshot protocol.

## 2. Server-Owned Timer & Deterministic Clock (`APP_NOW`)
- **Decision:** All wall-clock calls (`datetime.now()`, `datetime.utcnow()`, `date.today()`) are banned outside `apps/api/app/clock.py` (enforced by an AST test). The live API runs `LiveClock(APP_NOW)` (`APP_NOW + monotonic elapsed`), while `make report` and `pytest` inject `FrozenClock(APP_NOW)`. Meeting timers store `section_started_at` in UTC; browsers render a smooth local 1-second tick that snaps to server truth on every snapshot, and timers flag `over_time` without ever auto-advancing sections.
- **Why:** Prevents client clock skew, guarantees identical `rules_report.json` output at default and alternate `APP_NOW` dates, and keeps facilitators in control when discussions run long.
- **Tradeoff:** Requires disciplined dependency injection (`Depends(get_clock)`) across every route and service rather than calling stdlib time helpers directly.

## 3. Atomic Duplicate-Free "Make it an Issue"
- **Decision:** Enforce uniqueness directly in PostgreSQL with a partial unique index (`uq_issues_unsolved_source` on `(source_measurable_id, source_week_start) WHERE solved_at IS NULL AND source_measurable_id IS NOT NULL`), and execute `INSERT ... ON CONFLICT DO NOTHING RETURNING id` followed by a `SELECT` on conflict (`201 Created` vs `200 OK`).
- **Why:** Eliminates TOCTOU race conditions under 20+ simultaneous clicks without application-level locks, while naturally permitting a new Issue if an earlier linked Issue (such as `i6`) was already solved.
- **Tradeoff:** Relies on PostgreSQL-specific `ON CONFLICT ... WHERE` syntax rather than database-agnostic ORM checks (an intentional choice since PostgreSQL 16 is the production and test database).

## 4. Centralized Server-Side RBAC & Team Isolation
- **Decision:** Every route authenticates via HMAC-SHA256 Bearer tokens and delegates authorization to `apps/api/app/auth/deps.py` (`require_team_read`, `require_team_write`, `assert_eligible_team_owner`). Non-member team access returns `404 Not Found` (preventing ID enumeration), Observer writes/facilitate/rate return `403 Forbidden`, and Admins access/own items across all company teams without explicit membership rows. Browser tabs store tokens in `sessionStorage` so two personas can join one meeting side-by-side in the same browser.
- **Why:** Zero ad-hoc role checks scattered across handlers, no reliance on UI button hiding, and effortless multi-persona QA/demos.
- **Tradeoff:** Tab-isolated `sessionStorage` means opening a brand-new tab defaults back to the initial persona rather than sharing a cookie session across tabs — ideal for local multi-user testing, whereas production SSO would use `HttpOnly` cookies.

## 5. Pure-Python Rules Core & Exact `Decimal` Math
- **Decision:** Isolate 100% of business rules inside `apps/api/app/rules/` with zero FastAPI or SQLAlchemy imports (enforced by AST test). Store scores/goals as PostgreSQL `NUMERIC(18,4)`, compute in Python `Decimal` with `ROUND_HALF_UP`, check the 90% To-Do target via exact integer ratio (`done * 10 >= due * 9`), compute calendar boundaries in `ZoneInfo("America/Chicago")`, and render server-computed fields verbatim in React (zero business logic in the frontend).
- **Why:** Guarantees that the REST API, Live Meeting summaries, and `make report` can never disagree, eliminates floating-point and banker's-rounding bugs (`12.5% → 13%`, `8.25 → 8.3`), and handles DST transitions (`Nov 1, 2026`) accurately.
- **Tradeoff:** Slightly more explicit mapping between SQLAlchemy ORM models and pure rule dataclasses, repaid immediately in fast, framework-free unit tests and zero client/server drift.
