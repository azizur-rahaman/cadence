# PRD: Weekly Team Meeting Platform (EOS / Level 10)

Nov 21, 2026 · @Azizur Rahaman

This PRD defines a multi-user web app that gives each leadership team one place to track weekly numbers, quarterly goals, tasks and problems, and to run a timed, synchronized weekly meeting. It is derived from the recruiter's assessment brief (modelled on Ninety's EOS edition) and is the source of truth for the Jira plan.

## 1. Overview

**Problem.** Leadership teams track metrics, goals and action items in scattered spreadsheets and chats, so weekly meetings drift and follow-ups get lost.

**Product.** Each team gets one workspace built around a weekly loop:

1. **Measure:** Measurables (weekly KPIs) show business health against goals.
2. **Commit:** quarterly Rocks (with Milestones) and weekly To-Dos say who does what, by when.
3. **Resolve:** anything off track becomes an Issue, solved together in a Level 10 Meeting (Scorecard 5 min, IDS 60 min, Conclude 10 min).

**Goals**

- G1: Exact, auditable business-rule computation (status, completion rate, Rock status, Issue order, ratings) in America/Chicago time.
- G2: A live meeting that stays in sync across browsers within about 1 second and recovers from refresh or reconnect.
- G3: Server-enforced roles and team boundaries, proven by tests.
- G4: A one-command setup (`docker compose up`) and one-command tests.

**Success criteria**

- The rules report matches the evaluator's answer key at the default `APP_NOW` and at other dates.
- Concurrent "Make it an Issue" requests create exactly one Issue.
- The two-browser Playwright test passes unattended.
- All five deliverables are submitted and every link opens without access requests.

## 2. Scope

| Area | In scope | Out of scope |
| --- | --- | --- |
| Access | Seeded user switcher or simple login; roles; team switcher | Sign-up, billing, email, integrations |
| Data | Scorecard, Issues, To-Dos, Rocks (read-only), Meetings | Creating or editing teams, users, Measurables, Rocks; Private To-Dos; Long-Term Issues |
| Meetings | Live Level 10 meeting; per-meeting summary API | Meeting history page; facilitator handoff |
| Ops | Docker Compose, idempotent seed, migrations, REST API docs | Production hosting, multi-tenancy at scale |

**Bonus (only after the core is solid):** Make it an Issue from an off-track Rock or overdue To-Do (same no-duplicates rule); lost-update protection for scores and Issue priority; audit trail; a note on supporting 1,000 companies.

**Assumptions**

- A "closed week" is the full Monday-Sunday week before the current one; at the default `APP_NOW` the last closed week is `2026-11-02` and the current week is `2026-11-09`.
- Only unsolved Issues are re-used by "Make it an Issue"; a solved Issue for the same Measurable and week allows a new one. New Issue titles follow the seed convention: `"<Measurable name>, week of <Mon D>"` (for example `"New deals closed, week of Nov 2"`).
- Eligible To-Do owners for any team are `(all company Admins) ∪ (that team's Team Members)`, because Admins can act as Team Members in every team even without explicit `memberships` rows (for example `u1` is only listed in `team_lead` in `seed.json`). Observers and Team Members from other teams are rejected server-side.
- Rocks shown on the Team Page and in `rules_report.json` are filtered to the current calendar quarter (`quarter_of(APP_NOW)` in `America/Chicago`).
- For seeded meetings (`mt1`, `mt2`), which omit `scorecard_week` and `meeting_id` fields in `seed.json`, `scorecard_week` is derived as the last closed week relative to `started_at` in `America/Chicago`, and `issues_solved` / `todos_created` are matched by team and timestamp window `started_at <= ts <= ended_at`.
- Any other unspecified decision is made, then recorded in the README assumptions.

## 3. Users and Roles

Each user has one company-wide role and belongs to one or more teams. Every rule is enforced server-side.

| Capability | Admin | Team Member | Observer |
| --- | --- | --- | --- |
| Read team data | All teams | Own teams | Own teams |
| Edit scores, create/solve Issues, manage To-Dos | Yes, all teams | Own teams | No |
| Own Measurables, Rocks, To-Dos, Issues | Yes | Yes | No |
| Start / facilitate a meeting | Yes | Yes (own teams) | No |
| Join a meeting | Yes | Yes | Yes (own teams) |
| Rate a meeting | Yes | Yes | No |
| Access an unauthorized team (even by guessed ID) | n/a | Refused | Refused |

Seeded personas for testing: `u1` Admin; `u2`/`u3`/`u4` Team Members in Leadership; `u5` Observer in Leadership; `u6` Team Member and `u7` Observer in Sales; `u8`/`u9` Team Members in Operations. `u2` is also in Sales and `u4` also in Operations.

## 4. Functional Requirements

Priority: P0 = required for the core, P1 = should have, P2 = bonus.

| ID | Requirement | Acceptance criteria | Pri |
| --- | --- | --- | --- |
| FR-01 | Sign in as a seeded user | User switcher or login returns a session; identity is used on every API call | P0 |
| FR-02 | Team switcher | Lists the user's teams (all teams for Admin); unauthorized team ID returns 403/404 | P0 |
| FR-10 | Scorecard grid | Last 13 weeks including current, one cell per Measurable per week with score and status; names, owners, goals, units shown | P0 |
| FR-11 | Edit score inline | Last save wins; invalid values rejected; Observers refused | P0 |
| FR-12 | Make it an Issue | On an off-track cell creates an Issue titled with Measurable and week, owned by the clicker, linked to source; returns existing unsolved Issue if one exists | P0 |
| FR-20 | Issues list | Unsolved Issues in Issue order with title, owner, priority, created time, source Measurable and week; solved Issues viewable separately with time and note | P0 |
| FR-21 | Create Issue | Title required; priority 1-5 optional; owner is the creator | P0 |
| FR-22 | Set priority | Integer 1-5 or none; reorders list | P0 |
| FR-23 | Solve Issue | Resolution note required; sets solved time | P0 |
| FR-24 | Add a To-Do from an Issue | Title, owner from `(all company Admins) ∪ (team's Team Members)` (Observers and non-member Team Members rejected with 422), due in `today + 7 days` (company time), linked to Issue | P0 |
| FR-30 | To-Dos list | Title, owner, due date, done time, source Issue; overdue flagged; last closed week's completion rate shown | P0 |
| FR-31 | Mark done / undo | Sets or clears done time; Observers refused | P0 |
| FR-40 | Rocks | Current quarter's Rocks with owner, computed status and progress; expand to list Milestones (due date, done or not); read-only | P0 |
| FR-50 | Start meeting | Admin or Team Member starts; becomes facilitator; one active meeting per team | P0 |
| FR-51 | Join meeting | Any user who can read the team; late join gets current state; joining records a persistent `meeting_attendee` row (retained for final summary) separate from live WebSocket presence | P0 |
| FR-52 | Agenda and timer | Scorecard 5, IDS 60, Conclude 10 minutes; server-owned timer; overrun shows over time and does not auto-advance | P0 |
| FR-53 | Facilitator control | Only the facilitator advances or ends the meeting, at any time | P0 |
| FR-54 | Live sync | Section, timer and data changes reach all attendees within about 1 second; refresh and reconnect recover state | P0 |
| FR-55 | Reuse sections | Scorecard and IDS in the meeting reuse the Team page components with all actions | P0 |
| FR-56 | Conclude and rate | Shows new To-Dos and ratings; in Conclude, each attending Admin/Team Member rates 1-10 and may change it until end; Observers refused (403) and see ratings read-only; rating an ended meeting returns 409 | P0 |
| FR-57 | Meeting summary | Attendees see statuses for last closed week, Issues solved, To-Dos created, attendees, rating; API returns any ended meeting, including the 2 seeded | P0 |
| FR-60 | Bonus: Make it an Issue from Rock or overdue To-Do | Same no-duplicate rule | P2 |
| FR-61 | Bonus: lost-update protection | Version check on scores and Issue priority | P2 |
| FR-62 | Bonus: audit trail | Who changed what and when | P2 |

## 5. Business Rules

These have exact answers and are checked against the seed data. All are computed from data and `APP_NOW`, never hard-coded.

| ID | Rule | Definition | Edge cases |
| --- | --- | --- | --- |
| BR-01 | Week | Monday 00:00:00 to Sunday 23:59:59 in America/Chicago; named by its Monday (`week_start`) | Daylight saving ended Nov 1, 2026 (UTC-5 to UTC-6); convert with a tz database, never a fixed offset |
| BR-02 | Quarter | Calendar quarter | Current quarter from `APP_NOW` in company time |
| BR-03 | Today / overdue | Today = date of `APP_NOW` in company time; To-Do overdue when not done and due date is before today | Due today is not overdue |
| BR-04 | Rounding | Half up (12.5% to 13%, 8.25 to 8.3) | Do not use banker's rounding; avoid float error (use Decimal or integer math) |
| BR-10 | Measurable status | Compare the week's score to goal: at\_least, at\_most, between (min-max), exactly | Boundary values are on track; closed week with no score is off track; current week with no score is pending |
| BR-20 | To-Do completion rate | To-Dos done by end of week / To-Dos due that week; target 90% | Exactly 90% meets target (compare exact ratio, not rounded); done after its due week counts as not done; zero due means null |
| BR-30 | Rock status | Complete if seeded status is complete; off track if seeded off\_track or any unfinished Milestone is past due; else on track | Milestone due today is not past due; no Milestones means seeded status only |
| BR-31 | Rock progress | Completed Milestones / total, whole percent | No Milestones: 0%, or 100% once complete |
| BR-40 | Issue order | Priority 5 down to 1; within a priority, oldest first | No priority comes last |
| BR-50 | Meeting rating | Average of submitted ratings, one decimal | Non-raters excluded; no ratings means null |
| BR-60 | No duplicate Issues | Make it an Issue on a Measurable and week with an unsolved linked Issue returns that Issue | Must hold under simultaneous requests |

**Worked examples from the seed (default `APP_NOW`)**

- `m2` Customer churn, week of Sep 7, value 3.0 against at\_most 3.0 is on track (boundary).
- `m3` week of Sep 7, value 4.5 against between 2-4 is off track; week of Aug 24, value 2 is on track (boundary).
- Rock `r2` becomes off track because Milestone `ms5` (due Nov 10) is unfinished and before today (Nov 11), even though its seeded status is on\_track.
- Rock `r1` stays on track because `ms2` is due today (Nov 11), which is not past due.

## 6. Non-Functional Requirements

| ID | Area | Requirement |
| --- | --- | --- |
| NFR-01 | Authorization | Every role and team rule in section 3 is enforced in the API; hiding a button is not authorization. Guessed team IDs are refused. |
| NFR-02 | Validation | All inputs validated at the API (types, ranges, lengths, enums); invalid input returns 422 with field errors. |
| NFR-03 | Data integrity | Database constraints reject invalid data: foreign keys, CHECK on priority 1-5 and rating 1-10, unique (measurable, week) score, unique rating per (meeting, user), partial unique index for one active meeting per team and one unsolved Issue per source. |
| NFR-04 | Time | Store timestamps in UTC (`timestamptz`); read "now" from `APP_NOW` (default `2026-11-11T15:00:00Z`), never the system clock; weeks and dates computed in America/Chicago. |
| NFR-05 | Operations | `docker compose up` starts frontend, API and Postgres with seed loaded; the seed script is idempotent; migrations via Alembic. |
| NFR-06 | API | Documented REST API (OpenAPI served by FastAPI) covering everything in section 4; consistent error shape and status codes. |
| NFR-07 | Real-time | Changes reach attendees within about 1 second; server owns the timer; reconnect restores state. |
| NFR-08 | Testing | One documented command runs rule, API and end-to-end tests unattended against seed data and a fixed clock. |
| NFR-09 | Usability | Core journey is easy to follow; the meeting page is readable under time pressure (large timer, clear current section, minimal clutter). |
| NFR-10 | Maintainability | Typed code (TypeScript, Pydantic), server state handled coherently (for example TanStack Query), small modules, no business rules in UI components. |

## 7. Architecture, Data Model and API (proposed)

**Architecture.** Lightweight polyglot monorepo (`apps/api/`, `apps/web/`, `e2e/`, `docs/`, `artifacts/`) orchestrated by a root `docker-compose.yml` and `Makefile` (intentionally avoiding heavy monorepo build tools like Turborepo or Nx to keep setup simple and Docker builds fast). Next.js (TypeScript, Tailwind, shadcn/ui) talks to a FastAPI service over REST and a WebSocket; FastAPI uses SQLAlchemy with Alembic migrations on Postgres. A pure-Python `rules` module holds every business rule and is shared by the API and the rules-report CLI, so the report and the app can never disagree. All three run from one `docker-compose.yml`.

**Data model**

| Entity | Key fields | Notes |
| --- | --- | --- |
| company | id, name, timezone | One row |
| team, user, membership | role on user; (user, team) unique | Admin sees all teams |
| measurable | team, owner, unit, goal\_type, goal\_value / min / max | CHECK per goal type |
| score | measurable, week\_start (date), value | Unique (measurable, week\_start); UPSERT gives last-save-wins |
| rock, milestone | quarter, seeded status; milestone due\_date, done | Status and progress computed, not stored |
| issue | team, owner, priority 1-5 or null, created\_at, solved\_at, resolution\_note, source\_measurable, source\_week | Partial unique index (source\_measurable, source\_week) where solved\_at is null |
| todo | team, owner, due\_date, done\_at, source\_issue\_id, created\_at, meeting\_id | FK to issue; `meeting_id` set when created during a live meeting (seeded meetings match by `started_at <= created_at <= ended_at`) |
| meeting | team, facilitator, started\_at, ended\_at, scorecard\_week, state | Partial unique index: one unended meeting per team; `scorecard_week` = last closed week relative to `started_at` |
| meeting\_attendee, meeting\_rating | (meeting, user) unique; rating CHECK 1-10 | `meeting_attendee` persists all users who joined (used in summary); live WS presence tracked separately; rating row only for raters |
| meeting\_summary | meeting, snapshot JSON, created\_at | Written once at end (decision 5) |

**Rules report JSON format (exact contract from starter `README.md`)**

`meetings` is nested inside each `teams.<team_id>` object (empty `{}` if the team has no ended meetings). All 13 weeks appear in `measurable_status` and `todo_completion` (`null` only when 0 To-Dos are due that week; current week is non-null if To-Dos are due). All ID arrays are sorted as plain strings (`"t12"` before `"t30"`), except `issue_order` which uses Issue order. `"now"` is the exact `APP_NOW` ISO 8601 UTC string.

```json
{
  "now": "<APP_NOW, ISO 8601 UTC>",
  "teams": {
    "<team_id>": {
      "measurable_status": {"<measurable_id>": {"<week_start>": "on_track | off_track | pending"}},
      "todo_completion": {"<week_start>": "null, or {due, done, rate_percent, meets_target}"},
      "overdue_todos": ["<todo_id>"],
      "rocks": {"<rock_id>": {"status": "on_track | off_track | complete", "progress_percent": 0}},
      "issue_order": ["<issue_id>"],
      "meetings": {
        "<meeting_id>": {
          "scorecard_week": "<week_start>",
          "measurable_status": {"<measurable_id>": "on_track | off_track | pending"},
          "issues_solved": ["<issue_id>"],
          "todos_created": ["<todo_id>"],
          "attendee_ids": ["<user_id>"],
          "rating": "number with one decimal, or null"
        }
      }
    }
  }
}
```

**API outline (all under `/api/v1`)**

| Resource | Endpoints |
| --- | --- |
| Session | `POST /auth/login`, `GET /me`, `GET /teams` |
| Scorecard | `GET /teams/{id}/scorecard`, `PUT /teams/{id}/measurables/{mid}/scores/{week}` |
| Issues | `GET/POST /teams/{id}/issues`, `PATCH /issues/{id}` (priority), `POST /issues/{id}/solve`, `POST /teams/{id}/issues/from-measurable` |
| To-Dos | `GET/POST /teams/{id}/todos`, `POST /issues/{id}/todos`, `PATCH /todos/{id}` (done/undo) |
| Rocks | `GET /teams/{id}/rocks` |
| Meetings | `POST /teams/{id}/meetings`, `GET /meetings/{id}`, `POST /meetings/{id}/advance`, `POST /meetings/{id}/end`, `PUT /meetings/{id}/rating`, `GET /meetings/{id}/summary`, `WS /meetings/{id}/ws` |

Conventions: JSON; ISO 8601 UTC timestamps; `week_start` as `YYYY-MM-DD`; errors as `{code, message, fields?}`; 401 unauthenticated, 403 forbidden, 404 for teams the user cannot see (avoids leaking existence), 409 conflict, 422 validation.

## 8. Real-Time Meeting and Concurrency (proposed)

**Transport.** A WebSocket per attendee (FastAPI native) with a Postgres-backed meeting row as the source of truth. SSE plus POST is the simpler alternative; WebSocket is chosen for presence and low latency, with a polling fallback if the socket fails.

**State ownership.** The meeting row stores `section`, `section_started_at` and `ended_at` in UTC. The timer is derived on the server as `APP_NOW`-based elapsed time against the section's allotted minutes, so clients never own time. Overrun is a computed flag (`over_time`), and nothing auto-advances.

**Clock design.** `APP_NOW` is the fixed starting instant, so the app uses a single `Clock` service. The live API uses `now = APP_NOW + monotonic seconds since API start` so meeting timers tick smoothly while starting deterministically. The rules report CLI (`make report`) and automated tests use a **frozen** `Clock(APP_NOW)` (zero monotonic offset) so `"now"` prints the exact `APP_NOW` string and date/week boundaries never drift. Wherever the timer text above says it is based on `APP_NOW`, it means this clock.

**Sync flow**

1. A client connects and receives a full state snapshot (section, timer, attendees, new To-Dos, ratings).
2. Every mutation (advance, end, join/leave, rating, Issue or To-Do change) is committed, then a small event is broadcast to the meeting's connections.
3. Clients apply the event or refetch affected queries (TanStack Query invalidation).
4. On reconnect (client or facilitator) the client resends nothing and simply receives a fresh snapshot, so no client-held state needs recovery.

**Scaling note.** An in-process connection manager is enough for one API instance; a Redis or Postgres LISTEN/NOTIFY fan-out is the documented path to multiple instances.

**Duplicate-free Make it an Issue.** A partial unique index on (source\_measurable, source\_week) where `solved_at` is null, combined with `INSERT ... ON CONFLICT DO NOTHING` followed by a SELECT of the existing row, makes the operation atomic. It needs no application locks and holds under any number of concurrent requests.

**Immutable past summaries.** At meeting end, a snapshot (statuses, solved Issues, created To-Dos, attendees, rating) is written to `meeting_summary` as JSON in one transaction. Later edits to scores or Issues never touch it. The two seeded meetings (`mt1`, `mt2`) derive `scorecard_week` from `started_at` and match `issues_solved` / `todos_created` by `started_at <= ts <= ended_at` on import, storing snapshots the same way. (Per Brief 2.8, describing this design in the decision record is sufficient; building `meeting_summary` provides full end-to-end verification.)

## 9. Seed Data Analysis and Edge Cases

The seed holds 1 company, 3 teams, 9 users, 11 memberships, 7 Measurables (12 scores each except `m5`, which has 11), 7 Rocks, 12 Milestones, 9 Issues, 20 To-Dos and 2 ended meetings. The data was built to trip common mistakes:

| Trap | Where | Correct handling |
| --- | --- | --- |
| Daylight saving ended Nov 1 | All week bucketing after Oct 31 | Convert UTC to America/Chicago with a tz database |
| Done just before the week ends | `t28` done `2026-11-09T05:59Z` = Sun Nov 8 23:59 local | Done within week of Nov 2 |
| Done just after the week ends | `t29` done `2026-11-09T06:01Z` = Mon Nov 9 00:01 local | Not done for week of Nov 2 |
| Done after midnight UTC, still prior week local | `t11` done `2026-11-02T05:30Z` = Sun Nov 1 23:30 local, due Oct 30 | Counts in week of Oct 26 |
| Missing closed-week scores | `m5` has no score for Oct 19 or Nov 2 | Off track (closed week, no score) |
| Current week score present | `m5` has a score for Nov 9 | Evaluated against goal, not pending |
| Current week empty | All other Measurables have no Nov 9 score | Pending; the grid must still show all 13 weeks |
| Goal boundaries | `m2` 3.0, `m3` 2 and 4, `m1` 10, `m6` 50, `m7` 2 | On track |
| Exactly goal | `m4` has 0 and 2 against exactly 1 | Off track |
| Milestone due today | `ms2` due Nov 11 | Not past due |
| Past-due milestone on an on-track Rock | `r2` / `ms5` due Nov 10 | Rock `r2` computed off track |
| Rock with no done Milestones | `r6` (`ms12` undone) | `0%` progress |
| Rocks with zero Milestones | `r3` (`complete`), `r4` (`off_track`), `r5`/`r7` (`on_track`) | `r3` is `100%`; `r4`/`r5`/`r7` are `0%`; status uses seeded status alone |
| Half-up rounding on Rock progress | `r2`: 1 of 8 milestones done = `12.5%` | Rounds half up to `13%` (not banker's `12%`) |
| Half-up rounding on meeting rating | `mt2`: ratings `[8, 9, 8, 8]` = `8.25` | Rounds half up to `8.3` (not banker's `8.2`) |
| Exact 90% To-Do completion target | `team_lead` week `2026-11-02`: 9 of 10 done (`t20`–`t29`; `t28` in, `t29` late) | `rate_percent: 90`, `meets_target: true` |
| Current week with To-Dos due | `team_lead` week `2026-11-09`: `t30`, `t31`, `t32` due, 0 done | `{due: 3, done: 0, rate_percent: 0, meets_target: false}` (not `null`) |
| Issue without priority | `i4` | Sorts last |
| Same-priority ordering | `i2` (Oct 14) before `i1` (Oct 20) | Oldest first |
| Existing source-linked Issues | `i5` (unsolved: `m1`, `2026-11-02`); `i6` (solved: `m4`, `2026-10-26`) | Clicking Make it an Issue returns `i5` for `m1`/`2026-11-02`, but creates a new Issue for `m4`/`2026-10-26` |
| Non-raters & seeded meeting windows | `mt1` (`10-28 15:00–16:15Z`, `scorecard_week: 2026-10-19`, 3/5 rated = `8.0`); `mt2` (`11-04 15:00–16:20Z`, `scorecard_week: 2026-10-26`, 4/5 rated = `8.3`) | Average of raters only; `mt1` solves `["i7"]`, creates `["t20"]` (excludes `t22` created `21:00Z`); `mt2` solves `["i6"]`, creates `["t30"]` |
| Overdue vs due-today To-Dos | `t12` (due Nov 1), `t31` (due Nov 10), `t30` (due Nov 11) | `overdue_todos: ["t12", "t31"]`; `t30` due today is not overdue |
| Admin without membership rows | `u1` (Admin) only in `team_lead` membership | Full read/write/ownership access across `team_sales` and `team_ops` |
| Seeded solved Issues | `i6`, `i7` linked to To-Dos `t30`, `t20` | Source links preserved |

The Scorecard must always return 13 weeks per Measurable (Aug 17 to Nov 9 at the default clock), even though the seed stores at most 12 scores each. The rules report is also run at other `APP_NOW` values, so nothing may be tied to Nov 11.

## 10. Testing, Deliverables, Risks and Open Questions

**Test strategy.** One documented command (`make test`) runs all layers unattended against the freshly seeded local stack with a frozen clock (`APP_NOW`), enforcing strictly local targets (`localhost`/`127.0.0.1`), gating on service health checks, and emitting a Markdown verification summary at `docs/test/report/latest-test-report.md`. A companion `make verify` quality gate runs backend lint (`ruff`), zero-error frontend TypeScript typecheck (`tsc --noEmit`), full `make test`, and a `rules_report.json` consistency check before every commit.

| Layer | Minimum coverage |
| --- | --- |
| Rule tests (pytest) | Every rule in section 5 with at least one boundary case: goal types, DST week edges, 90% exactly, milestone due today, ratings with non-raters, Issue order ties |
| DB constraint tests (pytest) | Raw SQL/ORM inserts prove PostgreSQL rejects invalid priority, rating, goal shape, duplicate scores, duplicate unsolved source Issues, and two active meetings per team |
| API tests (pytest) | Team Member reading another team is refused; Observer write refused; concurrent Make it an Issue (for example 20 parallel requests) returns one Issue; validation errors |
| End-to-end (Playwright) | Two browsers in one meeting: facilitator advances, the second follows; reconnect test if time allows |

Also required and included under `docs/test/` + repo root:
- `AGENTS.md`: 1-page non-negotiable engineering invariants for AI-first governance (Clock-only time, `Decimal` half-up rounding, centralized RBAC dependency, zero business logic in React, compulsory `make verify` gate).
- `docs/test/README.md`: short note on fixture & clock strategy and instructions to inspect the failure artifact.
- `docs/test/manual/walkthrough.md`: short manual verification guide with exact seeded personas (`u1`, `u2`, `u5`, `u6`) and expected outcomes.
- `docs/test/report/latest-test-report.md`: auto-generated Markdown verification summary from `make test`.
- `artifacts/failure-trace.zip`: committed Playwright trace from a deliberately failing test run.

**Deliverables checklist**

- [ ] Public Git repo with README (2 pages or less): setup, test command, assumptions, limitations, AI tools used and where
- [ ] Working app via `docker compose up` with seed loaded
- [ ] Rules report command plus committed `rules_report.json`
- [ ] One-page decision record covering the five decisions
- [ ] Video of 7 minutes or less showing the core journey with two browsers and the main decisions
- [ ] All links open without requesting access

**Evaluation mapping**

| Area | Weight | Where this PRD addresses it |
| --- | --- | --- |
| Data model and API design | 20% | Sections 7 and 9 |
| Real-time, concurrency, rule correctness | 20% | Sections 5 and 8 |
| Usability | 15% | NFR-09, FR-50 to FR-57 |
| Security | 15% | Section 3, NFR-01, NFR-02 |
| Testing | 15% | Section 10 |
| Frontend code quality | 10% | NFR-10 |
| Documentation and video | 5% | Deliverables checklist |

**Risks**

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Time zone or DST bug in week bucketing | Wrong report values | Single `week_of(ts)` helper, tested on Nov 1 boundary and seed edge records |
| Real-time sync flakiness | Failed E2E, poor demo | Snapshot-on-connect design; polling fallback; test early |
| Scope too wide for 10-14 hours | Shaky core | Build rules engine first; bonus items only after core passes |
| Floating-point or banker's rounding | Wrong percentages | Integer math and explicit half-up function |
| Auth only in the UI | Security score loss | Central dependency enforcing role and team on every route |

**Open questions (decide and record in the README)**

- Should a user switcher or a password login be used? Recommended: user switcher with a signed session token.
- Does Make it an Issue return 200 or 201 when the Issue already exists? Recommended: 201 on create, 200 on existing, same body.
- Do Observers see meeting ratings? Recommended: yes, read-only.
- Is a solved Issue's source link still blocking a new Issue for that week? Recommended: no, only unsolved Issues block.
