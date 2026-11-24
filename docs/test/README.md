# Testing, Fixture & Deterministic Clock Strategy

## 1. Deterministic Clock Strategy
- **Zero wall-clock calls:** `datetime.now()`, `datetime.utcnow()`, and `date.today()` are forbidden outside `apps/api/app/clock.py` and enforced by an AST guard test (`apps/api/tests/test_clock.py`).
- **Live API (`CLOCK_MODE=live`):** Uses `LiveClock(APP_NOW)` (`APP_NOW + monotonic elapsed seconds`) so live meeting timers tick smoothly while still anchoring dates/weeks to `APP_NOW` (`2026-11-11T15:00:00Z` by default).
- **Rules Report & Automated Tests (`CLOCK_MODE=frozen`):** Uses `FrozenClock(APP_NOW)` (zero elapsed drift, with manual `.advance(seconds=...)` in timer overrun tests) so `rules_report.json` and every boundary test are 100% deterministic.

## 2. Database Fixture & Isolation Strategy
- `apps/api/tests/conftest.py` applies Alembic migrations once per session and resets PostgreSQL (`TRUNCATE ... RESTART IDENTITY CASCADE`) + reloads `apps/api/seed/seed.json` before every DB-backed test.
- Each test runs against a real PostgreSQL 16 instance (never SQLite), proving `CHECK` constraints, functional case-insensitive email uniqueness, and partial unique indexes (`uq_issues_unsolved_source`, `uq_meetings_one_active_per_team`).
- Concurrency tests (`test_make_issue_from_measurable_20x_concurrent_atomic_dedup`) synchronize 20 threads behind a `threading.Barrier(20)` so all 20 requests hit PostgreSQL simultaneously.

## 3. Running Tests Unattended
```bash
# Full backend + lint + typecheck gate
make verify

# Two-browser Playwright E2E (with stack running via `make up`)
cd e2e && npm test

# Local-only full driver (health wait + pytest + E2E + report parity -> Markdown report)
python3 docs/test/run-all.py
```

## 4. Inspecting the Committed Failure Trace
A real Playwright trace from a deliberately induced assertion failure is committed at [`artifacts/failure-trace.zip`](../../artifacts/failure-trace.zip). Inspect it locally with:

```bash
cd e2e && npx playwright show-trace ../artifacts/failure-trace.zip
```
