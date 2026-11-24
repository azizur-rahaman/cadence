# Project Proposal and Requirements: Weekly Team Meeting Platform

Nov 21, 2026 · @Azizur Rahaman

## 1. Introduction

The Weekly Team Meeting Platform gives each leadership team one place to track weekly numbers (Measurables), quarterly goals (Rocks), tasks (To-Dos) and problems (Issues), and to run a timed, shared weekly meeting. It is built for company leadership teams following the EOS Level 10 Meeting routine, and its value is a repeatable weekly loop: Measure, Commit, Resolve.

This proposal covers a responsive web application and the backend API that serves it. No mobile app or separate admin panel is included. The stack is Next.js with TypeScript, shadcn/ui and Tailwind on the front end, FastAPI on the back end and Postgres for data. Delivery is phased in four phases, and each phase ends with a working, testable product.

## 2. Scope

The project is delivered in 4 phases.

► Phase 1 — Foundation and Access: Seeded data, sign-in, roles, team switching, deterministic time handling, one-command setup

► Phase 2 — Team Workspace: Scorecard, Issues, To-Dos, Rocks, computed business rules

► Phase 3 — Live Level 10 Meeting: Facilitated meeting, synchronized agenda and timer, ratings, meeting summary

► Phase 4 — Hardening, Rules Report and Handover: Automated tests, rules report, documentation, walkthrough video

## Phase 1 — Foundation and Access: Sign-in, roles, team switching, seeded data, one-command setup

**Goal:** A user can sign in as a seeded person, switch between their teams and see correct access limits, on a stack that starts with one command and a fixed, testable clock.

### Authentication & Access Control

- Sign in as a seeded user via header user switcher backed by a signed session token (`POST /auth/login`)
- Three company-wide roles: Admin, Team Member, Observer
  - Admin: everything a Team Member can do, in every team (including owning To-Dos in any team even without explicit membership rows)
  - Team Member: read and change data in own teams; start, facilitate and rate meetings; own items
  - Observer: read own teams and join meetings; cannot change data, facilitate, rate or own anything
- Roles enforced on the server, not only hidden in the interface
- Access to a team the user does not belong to returns an error, even by guessed ID
- Team switcher in the header listing the user's teams (all teams for Admins)

### Data Foundation

- Seed data loaded on startup: 1 company, 3 teams, 9 users, Measurables with 13 weeks of scores, Q4 2026 Rocks and Milestones, To-Dos, Issues, 2 ended meetings
- Seed can be re-run safely without duplicating data
- Database rules reject invalid data (for example priority outside 1–5, rating outside 1–10)
- Seed IDs preserved (`u1`, `m1`, `t12`, and so on)

### Time Handling

- Company time zone America/Chicago; all timestamps stored in UTC
- Weeks run Monday 00:00:00 to Sunday 23:59:59 company time, named by their Monday
- Calendar quarters; due dates as calendar dates in company time
- "Now" read from `APP_NOW`, default 2026-11-11T15:00:00Z, never the system clock

### Platform Setup

- `docker compose up` starts the full stack with seed data loaded
- Documented REST API with consistent error responses
- Input validation on every API request

*Mobile App — Phase 1: Not in scope (web only).*

## Phase 2 — Team Workspace: Scorecard, Issues, To-Dos, Rocks, computed business rules

**Goal:** A team member can review last week's numbers, turn off-track results into Issues, solve them with follow-up To-Dos and see Rock progress, all with exact computed statuses.

### Scorecard

- Measurables by week for the last 13 weeks, including the current week
  - Each cell shows score and status: on track, off track or pending
  - Names, owners, goals and units shown
- Goal types: at least, at most, between, exactly (boundary values are on track)
- Closed week with no score is off track; current week with no score is pending
- Edit a score inline; last save wins
- Make it an Issue on an off-track cell
  - Creates an Issue titled with the Measurable and week, owned by the user who clicked
  - Returns the existing unsolved Issue instead of creating a duplicate, even for simultaneous clicks

### Issues

- Unsolved Issues in Issue order: priority 5 to 1, oldest first within a priority, no priority last
  - Shows title, owner, priority, created time, source Measurable and week
- Create an Issue (title required, priority optional, owner is the creator)
- Set priority
- Solve an Issue with a required resolution note
- View solved Issues separately with solved time and note
- Add a To-Do from an Issue
  - Title, owner chosen from `(all company Admins) ∪ (team's Team Members)` (Observers and non-member Team Members rejected server-side), due in 7 days, linked to the Issue

### To-Dos

- List with title, owner, due date, done time and source Issue
- Overdue flag: not done and due date before today (company time)
- Mark done and undo
- Last closed week's completion rate against the 90% target
  - To-Dos done by end of the week divided by To-Dos due that week
  - Done after the due week counts as not done; no To-Dos due means no rate

### Rocks

- Current quarter's Rocks with owner, status and progress (read-only)
- Status: Complete, Off-track or On-track
  - Off-track if seeded off-track or an unfinished Milestone is past due (due today is not past due)
- Progress: completed Milestones divided by total, as a whole percent
- Expand a Rock to list its Milestones with due date and done state

### Role Behaviour

- Observers see all of the above read-only
- Rounding is half up for all percentages and ratings

*Mobile App — Phase 2: Not in scope (web only).*

## Phase 3 — Live Level 10 Meeting: Facilitated meeting, synchronized agenda and timer, ratings, summary

**Goal:** A team runs a full weekly meeting with two or more people in separate browsers, stays in sync, rates the meeting and later reads its summary.

### Meeting Control

- Admin or Team Member starts a meeting and becomes the facilitator
- One active meeting per team
- Anyone who can read the team can join, including Observers
- Only the facilitator advances sections or ends the meeting, at any time
- Observers cannot start, facilitate or rate

### Agenda & Timer

- Agenda: Scorecard (5 min), IDS (60 min), Conclude (10 min)
- Current section, timer and attendee list visible to everyone
- Timer owned by the server; an overrun section shows as over time and does not advance automatically
- Layout readable under time pressure

### Meeting Sections

- Scorecard: reviews the last closed week with all Phase 2 actions, including Make it an Issue
- IDS: works the Issues list in order with all Phase 2 actions: solve Issues, set priority, add follow-up To-Dos
- Conclude: recap of To-Dos created during the meeting and ratings

### Real-Time Sync

- Section changes and data changes reach all attendees within about 1 second (WebSocket with polling fallback)
- Late joiners, page refreshes and reconnects (including the facilitator) receive the current state
- Persistent `meeting_attendee` records retain everyone who joined for the final summary, separate from live connection presence
- No facilitator handoff needed (per Brief 2.5)

### Rating & Summary

- Each attending Admin or Team Member rates 1 to 10 and can change the rating until the meeting ends
- Meeting rating: average of submitted ratings to one decimal; no ratings means no score
- Summary shown to attendees at the end
  - Measurable statuses for the last closed week
  - Issues solved and To-Dos created during the meeting
  - Attendees and rating
- Summary available through the API for any ended meeting, including the 2 seeded meetings
- Past summaries remain unchanged after later edits

*Mobile App — Phase 3: Not in scope (web only).*

## Phase 4 — Hardening, Rules Report and Handover: Automated tests, rules report, documentation, walkthrough video

**Goal:** The product is verified, documented and ready for review, with every computed value reproducible from a single command.

### Rules Report

- One documented command prints every computed rule value as JSON for the current `APP_NOW` (using a frozen clock with zero elapsed offset so `"now"` prints exact `APP_NOW`)
  - Nested under `teams.<team_id>`:
    - `measurable_status` for all 13 weeks ending with the current week
    - `todo_completion` for all 13 weeks (`null` only when 0 To-Dos are due; current week is non-null if To-Dos are due)
    - `overdue_todos` (sorted as plain strings)
    - `rocks` (current calendar quarter, status and half-up progress percent)
    - `issue_order` (unsolved Issues in Issue order)
    - `meetings` (ended meetings for that team, `{}` if none): `scorecard_week`, `measurable_status`, `issues_solved`, `todos_created`, `attendee_ids`, and `rating` (seeded `mt1`/`mt2` derive `scorecard_week` from `started_at` and match solved Issues / created To-Dos by `started_at <= ts <= ended_at`)
- Values computed from data, correct at other dates, output committed as `rules_report.json`

### Automated Testing & Engineering Governance

- Root `AGENTS.md` documents non-negotiable AI-first engineering invariants (Clock-only time, `Decimal` half-up rounding, centralized server-side RBAC, zero business logic in React, compulsory `make verify` gate)
- One command (`make test`) runs all tests unattended against seed data and a frozen clock (with strict `localhost` guard, health-check wait, and auto-generated `docs/test/report/latest-test-report.md`)
- `make verify` enforces zero-error backend lint (`ruff`), frontend typecheck (`tsc --noEmit`), full test suite, and `rules_report.json` parity
- Rule & DB constraint tests (pytest): every business rule with boundary cases + raw Postgres constraint enforcement
- API tests (pytest):
  - Team Member reading another team's data is refused
  - Observer write is refused
  - Concurrent Make it an Issue requests return one Issue
- End-to-end test (Playwright) with two browsers: facilitator advances the agenda and the second browser follows
- `docs/test/README.md` (fixture and clock strategy note), `docs/test/manual/walkthrough.md` (1-page manual walkthrough), and `artifacts/failure-trace.zip` (Playwright trace from a deliberately failing run)

### Documentation & Handover

- README (2 pages or less): setup, test command, assumptions, limitations, AI tools used
- One-page decision record: data model, API design, real-time transport and state recovery, duplicate-free Issues, immutable past summaries
- Walkthrough video (up to 7 minutes) showing the core journey with two browsers and key decisions
- Public repository and links that open without access requests

### Optional Bonus Enhancements (only after core passes)

- Make it an Issue from an off-track Rock or overdue To-Do with the same no-duplicate rule
- Lost-update protection for scores and Issue priority
- Audit trail of changes
- Note on supporting 1,000 companies

*Mobile App — Phase 4: Not in scope (web only).*

## 3. Technology Stack

| Component | Technology |
| --- | --- |
| Web frontend | Next.js, TypeScript, shadcn/ui, Tailwind CSS |
| Mobile frontend | Not in scope |
| Charting | Not required (Scorecard is a status grid) |
| Backend | FastAPI (Python), REST API with OpenAPI documentation |
| Database | PostgreSQL with Alembic migrations |
| CDN / Storage | Not in scope (local Docker Compose stack) |
| AI / Third-party integrations | None (integrations are out of scope) |
| Email | Not in scope |
| Push notifications | Not in scope |
| Hosting | Docker Compose for local and review (production hosting out of scope) |
| CI/CD | Single-command automated test run (`make test`), zero-error `make verify` gate, optional GitHub Actions CI |
| Real-time transport | WebSocket (FastAPI native) with polling fallback, justified in decision record |
| Testing | Playwright (two-browser E2E), pytest (rule and API tests) under one command |

### Development Approach

► **Lightweight monorepo:** Single polyglot repository (`apps/api/`, `apps/web/`, `e2e/`, `docs/`, `artifacts/`) orchestrated by root `docker-compose.yml` and `Makefile`, intentionally omitting heavy monorepo tooling (Turborepo/Nx) to keep Docker builds and fresh-clone setup frictionless.

► **API-first:** The REST API serves every feature and is documented before screens depend on it.

► **Single rules module:** All business rules live in one place and feed both the app and the rules report.

► **Server-side authorization:** Roles and team boundaries are checked in the API on every request.

► **Shared page sections:** Scorecard and Issues are built once and reused on the Team and Meeting pages.

► **Server-owned meeting state:** Section, timer and attendees live on the server and are restored on reconnect.

► **Deterministic time:** `APP_NOW` and UTC storage make results repeatable at any date.

► **Database-enforced integrity:** Constraints and unique indexes reject invalid and duplicate data.

► **Phased delivery:** Each phase ends with a working product tested against the seed data.

## 4. Infrastructure Architecture

### 4.1 Deployment Architecture

```text
+---------------------------------------------+
| CLIENT LAYER                                |
| Web browsers (Admin, Team Member, Observer) |
+----------------------+----------------------+
                       |
                       v
+---------------------------------------------+
| WEB APP  (Next.js, TypeScript, Tailwind)    |
+----------------------+----------------------+
                       | REST + WebSocket (with polling fallback)
                       v
+---------------------------------------------+
| API  (FastAPI)                              |
|  - Authorization (role + team)              |
|  - Pure-Python business rules module        |
|  - Meeting state + server timer             |
+-----------+---------------------------------+
            |
            v
+----------------------+   +------------------+
| PostgreSQL           |   | External APIs    |
| (migrations, seed)   |   | None in scope    |
+----------------------+   +------------------+
```

All components start together with `docker compose up`.

### 4.2 Security & Scalability

► **Authentication:** Every API call and live meeting WebSocket connection requires a signed-in seeded user token.

► **RBAC:** Admin, Team Member and Observer rules enforced on the server; team boundaries checked even for guessed IDs (404 for unauthorized teams, 403 for forbidden writes).

► **File upload security:** Not applicable; the product has no file uploads.

► **Input validation:** Every API input validated via Pydantic for type, range and required fields; consistent `{code, message, fields?}` 422 error responses.

► **Data integrity:** Database constraints and partial unique indexes reject invalid and duplicate records atomically.

► **Horizontal scaling:** Stateless REST API with state in PostgreSQL; in-process WebSocket hub for single-instance review, with Redis / Postgres `LISTEN/NOTIFY` fan-out documented as the multi-instance path.

► **Production ops (HTTPS, backups, monitoring):** Out of scope for the local Docker Compose assessment deliverable.

## 5. Deliverables

| Deliverable | Platform |
| --- | --- |
| Web application (Team page and Meeting page) | Web |
| Backend REST API | Server |
| API documentation (OpenAPI) | Server |
| Database schema and migrations | PostgreSQL |
| Idempotent seed script with seed data | PostgreSQL / Server |
| Rules report command and `rules_report.json` | Server |
| Automated tests (rule, API, end-to-end) with fixture and clock note and failure artifact | Server / Web |
| Deployment configuration (`docker compose up`) | All |
| Source code in a public Git repository with README | All |
| One-page decision record | Documentation |
| Walkthrough video (up to 7 minutes) | Documentation |
| Mobile apps | Not in scope |
| Admin panel | Not in scope |

## Resolved Decisions (to document in README / Decision Record)

1. **Sign-in method:** Seeded user switcher issuing a signed session token.
2. **Real-time transport:** Native FastAPI WebSocket with snapshot-on-connect and polling fallback (justified in the decision record).
3. **Facilitator disconnect:** Reconnect restores full state; no facilitator handoff needed (per Brief 2.5).
4. **Solved Issue re-creation:** Only unsolved Issues block Make it an Issue; a solved linked Issue (like `i6`) allows creating a new Issue for that Measurable and week.
5. **Observer visibility of ratings:** Observers see meeting ratings read-only and are refused (`403`) if they attempt to submit a rating.
6. **Immutable past summaries:** Implemented via `meeting_summary` snapshot JSON written once at meeting end (and explained in the decision record; per Brief 2.8, describing this is sufficient).
7. **Out of scope:** Mobile app, admin panel, meeting history page, email, billing, integrations, and production hosting/CDN/backups/monitoring.
8. **Optional bonus enhancements:** Deferred until all core requirements, tests, and deliverables pass cleanly.
