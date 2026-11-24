# Jira Plan: Weekly Team Meeting Platform

Nov 21, 2026 · @Azizur Rahaman

This plan breaks the PRD into 12 epics and 45 stories (about 14 hours of core work plus 3 hours of optional bonus), with a Jira project configuration, working agreements and a five-block delivery schedule. Story IDs below (for example `E5-S3`) are planning IDs; Jira assigns the real keys on import.

## 1. Jira Project Setup

| Setting | Value |
| --- | --- |
| Project | Level 10 Meeting Platform, key `L10`, Scrum template (team-managed is fine for a solo project) |
| Issue types | Epic, Story, Task, Sub-task, Bug, Spike (time-boxed research) |
| Hierarchy | Epic (feature area) > Story (user-visible or testable outcome) > Sub-task (engineering step, at most 2 hours) |
| Workflow | Backlog > Ready > In Progress > In Review > In Test > Done. `Blocked` is a flag, not a status |
| Board | Scrum board with swimlanes by Epic, quick filters: `API`, `Web`, `Blocked` |
| Estimation | Story points (1 SP is about 30 minutes of focused work) plus Original Estimate in hours; velocity is tracked in hours because the whole project is one person-sprint |
| Components | `api`, `web`, `db`, `rules`, `realtime`, `devops`, `tests`, `docs` |
| Labels | `must-have`, `bonus`, `security`, `rubric-data`, `rubric-realtime`, `rubric-ux`, `rubric-testing`, `ai-assisted` |
| Custom fields | Requirement ID (FR-xx, BR-xx, NFR-xx), Rubric area (the 7 evaluation areas), AI tool used |
| Versions | `v0.1 Foundation`, `v0.5 Core`, `v1.0 Submission` |
| Priority scheme | Highest = blocks submission; High = rubric-weighted core; Medium = core polish; Low = bonus |
| Sprints | Five time-boxed work blocks (section 7), each with a goal and exit check |

**Working agreements**

- Branch name `L10-<n>-short-slug`; commit messages start with the issue key; one pull request per story.
- Every story links to its PRD requirement ID so coverage is traceable.
- A story is not started until it meets the Definition of Ready, and not closed until it meets the Definition of Done (section 2).
- Stories tagged `ai-assisted` record the tool and what was verified by hand, which feeds the README's AI-usage section.

## 2. Definitions and Templates

**Definition of Ready**

- [ ] Linked to a PRD requirement ID and a parent epic
- [ ] Acceptance criteria written as testable statements
- [ ] Dependencies identified and unblocked
- [ ] Estimated at 5 SP (2.5 hours) or less; larger stories are split

**Definition of Done**

- [ ] Acceptance criteria demonstrated against the seed data
- [ ] Server-side authorization and input validation in place for any new endpoint
- [ ] Automated tests added (rule, API or end-to-end as appropriate) and the full suite passes with one command
- [ ] OpenAPI docs reflect the change; no business rule lives in UI code
- [ ] `docker compose up` still starts cleanly from a fresh volume
- [ ] Pull request reviewed (self-review checklist for a solo project) and merged

**Story template**

```markdown
As a <role>, I want <capability> so that <outcome>.

Requirement: FR-xx / BR-xx
Acceptance criteria (Given / When / Then):
- Given ... when ... then ...
Out of scope: ...
Test notes: seed records and clock value to use
```

**Bug template**

```markdown
Summary:
Steps to reproduce (with APP_NOW):
Expected / Actual:
Seed record ids involved:
Severity: Blocker | Major | Minor
```

## 3. Epic Overview

Core work totals 14.0 hours, the upper end of the 10-14 hour guideline. If time runs short, cut in this order: E9 polish, the Playwright reconnect test, persisting `meeting_summary` snapshots (Brief 2.8 notes describing immutable summaries in the decision record is sufficient), then Rock UI niceties. Never cut E4 (rules), E3 (security) or the two-browser sync.

| Epic | Name | Goal | PRD refs | Est (h) | Priority | Depends on |
| --- | --- | --- | --- | --- | --- | --- |
| E1 | Foundation and DevOps | One-command stack, config, deterministic clock | NFR-04, NFR-05 | 1.0 | Highest | none |
| E2 | Data model and seed | Constrained schema, migrations, idempotent seed | NFR-03, section 7 | 1.5 | Highest | E1 |
| E3 | Auth, RBAC and validation | Server-enforced roles and team boundaries | Section 3, NFR-01, NFR-02 | 1.0 | Highest | E2 |
| E4 | Rules engine and rules report | Every business rule computed from data; JSON report | Section 5, NFR-04 | 1.5 | Highest | E2 |
| E5 | Scorecard | 13-week grid, inline edit, atomic Make it an Issue | FR-10 to FR-12, BR-60 | 1.5 | High | E3, E4 |
| E6 | Issues and To-Dos | IDS work: Issues, solving, follow-up To-Dos | FR-20 to FR-31 | 1.5 | High | E3, E4 |
| E7 | Rocks | Read-only Rocks with computed status and progress | FR-40, BR-30, BR-31 | 0.5 | Medium | E4 |
| E8 | Live Level 10 meeting | Lifecycle, server timer, WebSocket sync, ratings, summary | FR-50 to FR-57 | 2.5 | High | E5, E6 |
| E9 | Frontend shell | App shell, switchers, data fetching layer, shared components | NFR-09, NFR-10 | 0.5 | High | E3 |
| E10 | Testing and QA | Rule, API and end-to-end suites; fixtures; failure artifact | Section 10 | 1.5 | High | E4 to E8 |
| E11 | Documentation and submission | README, decision record, video, verification | Deliverables 1-5 | 1.0 | Highest | all |
| E12 | Bonus (stretch) | Extra Issue sources, lost-update protection, audit trail, scale note | FR-60 to FR-62 | 3.0 | Low | core done |

## 4. Epics 1-4: Foundation, Data, Security, Rules

### E1 Foundation and DevOps (1.0 h, components `devops`, `api`, `web`)

| ID | Type | Story | Acceptance criteria | Est (h) | SP | Deps |
| --- | --- | --- | --- | --- | --- | --- |
| E1-S1 | Task | Scaffold lightweight monorepo, AGENTS.md and Makefile | Polyglot monorepo (`apps/api/`, `apps/web/`, `e2e/`, `docs/`, `docs/test/`, `artifacts/`) orchestrated by root `docker-compose.yml` and self-documenting `Makefile` (no Turborepo/Nx); Makefile targets `help`, `up`, `down`, `seed`, `report`, `test`, `verify` (`ruff` + `tsc --noEmit` + `test` + report check); root `AGENTS.md` codifying non-negotiable AI engineering invariants; `.env.example` lists `APP_NOW` and DB settings; `seed.json` placed at `apps/api/seed/seed.json` | 0.25 | 1 | none |
| E1-S2 | Story | Docker Compose stack | `docker compose up` from a clean checkout starts Postgres, runs migrations and seed, serves API and web; health checks gate startup order | 0.5 | 3 | E1-S1 |
| E1-S3 | Story | Deterministic Clock service | Live API `Clock.now()` returns `APP_NOW` plus monotonic elapsed time (default `2026-11-11T15:00:00Z`); `make report` and tests use a frozen `Clock(APP_NOW)` (zero elapsed offset) advanceable in tests; no `datetime.now()` elsewhere (lint rule or grep test) | 0.25 | 1 | E1-S1 |

### E2 Data Model and Seed (1.5 h, components `db`, `api`)

| ID | Type | Story | Acceptance criteria | Est (h) | SP | Deps |
| --- | --- | --- | --- | --- | --- | --- |
| E2-S1 | Story | Schema and Alembic migrations | All entities from PRD section 7; `timestamptz` for instants, `date` for week\_start and due\_date; CHECK on priority 1-5, rating 1-10, goal shape; unique (measurable, week\_start), (meeting, user); partial unique indexes for one unsolved Issue per source and one active meeting per team; invalid inserts rejected by the database in a test | 0.75 | 4 | E1-S2 |
| E2-S2 | Story | Idempotent seed loader | Loads `seed.json` keeping ids (`u1`, `m1`, `t12`); upserts so a second run changes nothing; seeded meetings (`mt1`, `mt2`) derive `scorecard_week` from `started_at` and match `issues_solved`/`todos_created` via `started_at <= ts <= ended_at`; attendees, ratings, resolution notes and source links preserved | 0.5 | 3 | E2-S1 |
| E2-S3 | Task | Seed verification | Script asserts row counts (3 teams, 9 users, 7 Measurables, 7 Rocks, 12 Milestones, 9 Issues, 20 To-Dos, 2 meetings) after two consecutive runs | 0.25 | 1 | E2-S2 |

### E3 Auth, RBAC and Validation (1.0 h, components `api`, labels `security`, `rubric-data`)

| ID | Type | Story | Acceptance criteria | Est (h) | SP | Deps |
| --- | --- | --- | --- | --- | --- | --- |
| E3-S1 | Story | Session and user switcher | `POST /auth/login` with a seeded user id or email returns a signed token; `GET /me` and `GET /teams` honor it; missing or invalid token returns 401 | 0.25 | 1 | E2-S2 |
| E3-S2 | Story | Authorization dependency | One reusable dependency checks role and team membership for every route: Observer writes return 403; non-member team access returns 404 (even for guessed ids); Admin (`u1`) passes for all teams even without membership rows in `team_sales`/`team_ops`; resource ids (issue, todo, meeting) resolve to their team before the check | 0.5 | 3 | E3-S1 |
| E3-S3 | Task | Validation and error envelope | Pydantic models for all bodies; unified `{code, message, fields}` error shape; 422 on invalid priority, empty title, empty resolution note, rating out of range | 0.25 | 1 | E3-S1 |

### E4 Rules Engine and Rules Report (1.5 h, components `rules`, labels `rubric-data`)

All rules are pure functions over data plus `now`, with no database or HTTP imports, so they are trivially testable and reusable by the report.

| ID | Type | Story | Acceptance criteria | Est (h) | SP | Deps |
| --- | --- | --- | --- | --- | --- | --- |
| E4-S1 | Story | Time utilities | `week_start_of(ts)` in America/Chicago (handles DST on Nov 1); `last_13_weeks(now)`; `today(now)`; `quarter_of(date)`; `round_half_up` via Decimal; tested at Sunday 23:59:59 and Monday 00:00:00 local | 0.25 | 1 | E1-S3 |
| E4-S2 | Story | Measurable status | Handles at\_least, at\_most, between, exactly; boundary equals on track; closed week without score is off track; current week without score is pending | 0.25 | 1 | E4-S1 |
| E4-S3 | Story | To-Do completion rate | Done by end of due week; late completion counts as not done; null when none due; `meets_target` uses exact ratio at 90%; rounded percent half up | 0.25 | 1 | E4-S1 |
| E4-S4 | Story | Rock status and progress | Complete, off track (seeded or past-due unfinished Milestone, due today is not past due), else on track; progress percent with no-Milestone cases | 0.25 | 1 | E4-S1 |
| E4-S5 | Story | Issue order and meeting rating | Priority 5 to 1 then oldest first, null priority last; average of submitted ratings to one decimal half up, null when none | 0.25 | 1 | E4-S1 |
| E4-S6 | Story | Rules report command | `make report` uses frozen `Clock(APP_NOW)` and prints exact JSON from starter README for every team; all 13 weeks per Measurable and in `todo_completion` (current week non-null if To-Dos due, null only when 0 due); Rocks filtered to current quarter; plain-string sorted id lists (except `issue_order`); `meetings` nested under `teams.<team_id>` (`{}` when none); output committed as `rules_report.json`; re-runnable with a different `APP_NOW` | 0.25 | 2 | E4-S2 to E4-S5, E2-S2 |

## 5. Epics 5-8: Scorecard, Issues and To-Dos, Rocks, Live Meeting

### E5 Scorecard (1.5 h, components `api`, `web`, labels `rubric-realtime`)

| ID | Type | Story | Acceptance criteria | Est (h) | SP | Deps |
| --- | --- | --- | --- | --- | --- | --- |
| E5-S1 | Story | Scorecard API | `GET /teams/{id}/scorecard` returns every team Measurable with 13 weeks ending at the current week, each cell with value, status and week\_start; names, owners, goals, units included; matches rules report values | 0.25 | 1 | E3-S2, E4-S2 |
| E5-S2 | Story | Edit score inline | `PUT .../scores/{week}` upserts (last save wins); rejects non-numeric values; Observer refused; updates status in the response | 0.25 | 1 | E5-S1 |
| E5-S3 | Story | Make it an Issue (atomic) | `POST .../issues/from-measurable` only for off-track cells; title is `"<Measurable name>, week of <Mon D>"`; owner is the clicker; `INSERT ... ON CONFLICT DO NOTHING` on the partial unique index then SELECT; returns existing unsolved Issue (200, e.g. `i5` for `m1`/`2026-11-02`) or creates new (201, including when prior linked Issue like `i6` is solved); no duplicate under 20 parallel calls | 0.5 | 3 | E5-S1, E2-S1 |
| E5-S4 | Story | Scorecard UI | Grid of Measurables by 13 weeks; status colors plus text labels (not color alone); inline edit with optimistic update; Make it an Issue button only on off-track cells; read-only for Observers; section component is reused by the meeting page | 0.5 | 3 | E5-S1, E9-S1 |

### E6 Issues and To-Dos (1.5 h, components `api`, `web`)

| ID | Type | Story | Acceptance criteria | Est (h) | SP | Deps |
| --- | --- | --- | --- | --- | --- | --- |
| E6-S1 | Story | Issues API | List unsolved in Issue order, solved listed separately with time and note; create (title required, optional priority 1-5, owner is creator); set priority; solve requires a non-empty note and sets `solved_at` | 0.5 | 3 | E3-S2, E4-S5 |
| E6-S2 | Story | To-Dos API | List with owner, due date, done time, source Issue and overdue flag; last closed week's completion rate; create from an Issue (title, owner from `(all company Admins) ∪ (team's Team Members)` — Observers and non-member Team Members rejected with 422 — due `today + 7 days`, linked to Issue); mark done and undo | 0.5 | 3 | E3-S2, E4-S3 |
| E6-S3 | Story | Issues UI | Ordered list with priority control, source badge, solve dialog requiring a note, solved Issues tab, Add a To-Do dialog; reused in the meeting | 0.25 | 2 | E6-S1, E9-S1 |
| E6-S4 | Story | To-Dos UI | Table with overdue flag, done toggle and undo, completion rate with 90% target indicator | 0.25 | 2 | E6-S2, E9-S1 |

### E7 Rocks (0.5 h, components `api`, `web`)

| ID | Type | Story | Acceptance criteria | Est (h) | SP | Deps |
| --- | --- | --- | --- | --- | --- | --- |
| E7-S1 | Story | Rocks API | Current-quarter Rocks with owner, computed status, progress percent and Milestones (due date, done); `r2` returns off track at default `APP_NOW` | 0.25 | 1 | E3-S2, E4-S4 |
| E7-S2 | Story | Rocks UI | Read-only list; each Rock expands to Milestones; past-due unfinished Milestones highlighted | 0.25 | 1 | E7-S1, E9-S1 |

### E8 Live Level 10 Meeting (2.5 h, components `api`, `web`, `realtime`, labels `rubric-realtime`)

| ID | Type | Story | Acceptance criteria | Est (h) | SP | Deps |
| --- | --- | --- | --- | --- | --- | --- |
| E8-S1 | Story | Meeting lifecycle API | Start (Admin or Team Member, becomes facilitator, 409 if the team already has an active meeting); join (any team reader, persists `meeting_attendee` for summary separate from live WS presence); advance and end (facilitator only, any time); Observers cannot start or facilitate | 0.5 | 3 | E3-S2 |
| E8-S2 | Story | Server-owned timer | Section and `section_started_at` stored in UTC; API returns remaining seconds and `over_time`; overrun does not auto-advance; allotments 5, 60 and 10 minutes | 0.25 | 1 | E8-S1, E1-S3 |
| E8-S3 | Story | WebSocket hub with snapshot | `WS /meetings/{id}/ws` authenticates and authorizes; sends full state on connect and reconnect; broadcasts events on advance, join, leave, rating, Issue and To-Do changes within about 1 second; polling fallback | 0.5 | 3 | E8-S1 |
| E8-S4 | Story | Meeting page UI | Agenda with current section, large timer with over-time state, attendee list, facilitator-only controls; Scorecard and IDS reuse the Team page sections with all actions; readable at a glance | 0.5 | 3 | E8-S3, E5-S4, E6-S3 |
| E8-S5 | Story | Conclude and rating | Shows To-Dos created during the meeting and ratings; in Conclude, each attending Admin or Team Member rates 1-10 and may change it until end; Observers cannot rate (403, read-only view); rating an ended meeting returns 409 | 0.25 | 1 | E8-S4 |
| E8-S6 | Story | Summary snapshot and API | At end, one transaction writes an immutable snapshot (last closed week statuses, solved Issues, created To-Dos, attendees, rating); `GET /meetings/{id}/summary` works for any ended meeting including seeded `mt1` and `mt2`; summary view shown to attendees | 0.5 | 3 | E8-S1, E4-S5 |

## 6. Epics 9-12: Frontend Shell, Testing, Submission, Bonus

### E9 Frontend Shell (0.5 h, components `web`, labels `rubric-ux`)

| ID | Type | Story | Acceptance criteria | Est (h) | SP | Deps |
| --- | --- | --- | --- | --- | --- | --- |
| E9-S1 | Story | App shell and data layer | Next.js app with Tailwind and shadcn/ui; typed API client generated from OpenAPI or hand-typed; TanStack Query for server state; header with user switcher and team switcher; error and loading states; 403 and 404 pages | 0.5 | 3 | E3-S1 |

### E10 Testing and QA (1.5 h, components `tests`, labels `rubric-testing`)

| ID | Type | Story | Acceptance criteria | Est (h) | SP | Deps |
| --- | --- | --- | --- | --- | --- | --- |
| E10-S1 | Story | Rule test suite | Every rule in PRD section 5 has at least one boundary case: all four goal types; `m2` 3.0 and `m3` 2 and 4; DST week edges for `t11`, `t28`, `t29`; exact 90% (`team_lead` `2026-11-02`); current week due (`2026-11-09` non-null); zero due (`null`); overdue `t12`/`t31` vs due-today `t30`; `ms2` due today; `r2` off track + `12.5% -> 13%`; `r3` 0-milestone complete (`100%`) and `r4`/`r5`/`r7` (`0%`); Issue order ties and null priority; `mt1`/`mt2` timestamp windows (`t22` excluded from `mt1`) and ratings (`8.25 -> 8.3`) with non-raters | 0.5 | 3 | E4-S1 to E4-S5 |
| E10-S2 | Story | API test suite | Team Member (for example `u6`) reading Leadership data is refused; Observer (`u5`) writes refused on score, Issue, To-Do and meeting routes (including rating 403); Admin (`u1`) reaches and owns To-Dos in `team_sales`/`team_ops`; Observer/non-member rejected as To-Do owner (422); Make it an Issue returns existing `i5` (`m1`/`2026-11-02`), creates new despite solved `i6` (`m4`/`2026-10-26`), and 20 concurrent calls return one Issue id; validation 422 cases | 0.5 | 3 | E3-S2, E5-S3, E6-S1 |
| E10-S3 | Story | Two-browser Playwright test | Facilitator starts a meeting, second browser joins, facilitator advances to IDS, second browser shows IDS within 2 seconds; optional reconnect case; runs headless in one command | 0.35 | 2 | E8-S4 |
| E10-S4 | Task | Test driver, fixture/clock note, report and failure artifact | `docs/test/README.md` documents fixture & frozen-clock strategy and how to inspect `artifacts/failure-trace.zip`; `docs/test/manual/walkthrough.md` provides a 1-page manual persona walkthrough; one committed Playwright trace from a deliberately failing run; `make test` enforces strictly local targets, waits on `/api/health`, runs all layers unattended, and emits `docs/test/report/latest-test-report.md`; `make verify` enforces 0-error `ruff` + `tsc --noEmit` + tests | 0.15 | 1 | E10-S1 to E10-S3 |

### E11 Documentation and Submission (1.0 h, components `docs`)

| ID | Type | Story | Acceptance criteria | Est (h) | SP | Deps |
| --- | --- | --- | --- | --- | --- | --- |
| E11-S1 | Task | README (2 pages or less) | Setup, test command, assumptions, known limitations, AI tools used and where | 0.25 | 1 | all core |
| E11-S2 | Task | One-page decision record | The five decisions from the brief (data model, API design, real-time transport and state recovery, duplicate-free Make it an Issue, immutable past summaries), each with tradeoffs | 0.25 | 1 | E8, E5-S3 |
| E11-S3 | Task | API documentation check | OpenAPI shows every endpoint with schemas and error responses; link in README | 0.1 | 1 | E8 |
| E11-S4 | Task | Walkthrough video (7 minutes or less) | Two browsers in one meeting, core journey end to end, main decisions and limitations; unlisted link that opens without access | 0.35 | 2 | E10-S3 |
| E11-S5 | Task | Submission verification | Fresh clone, `docker compose up`, `make test`, `make report` all work; `rules_report.json` committed and matches live output; every link tested in a private window | 0.05 | 1 | E11-S1 to E11-S4 |

### E12 Bonus (3.0 h, stretch only after core passes, label `bonus`)

| ID | Type | Story | Acceptance criteria | Est (h) | SP | Deps |
| --- | --- | --- | --- | --- | --- | --- |
| E12-S1 | Story | Make it an Issue from Rock or overdue To-Do | Same no-duplicates guarantee via a generalized source key; tests for concurrency | 1.0 | 5 | E5-S3 |
| E12-S2 | Story | Lost-update protection | Version column with `If-Match` or `expected_version` on scores and Issue priority; 409 on conflict; UI shows conflict message | 0.75 | 4 | E5-S2, E6-S1 |
| E12-S3 | Story | Audit trail | Append-only table of who changed what and when for scores, Issues and To-Dos; read endpoint | 0.75 | 4 | E3-S2 |
| E12-S4 | Task | Scale note for 1,000 companies | One paragraph in the decision record: tenant key on every table, row-level security or schema strategy, indexes, WebSocket fan-out via Redis | 0.5 | 2 | E11-S2 |

## 7. Sprint Plan and Critical Path

There are five time-boxed blocks totalling 14.0 hours. Rules and security come first because they carry the most weight and every later feature depends on them. The meeting comes after the Team page because it reuses its sections.

| Block | Sprint goal | Stories | Hours | Exit check |
| --- | --- | --- | --- | --- |
| 1 Foundation | Stack boots with seed; roles enforced; shell renders | E1-S1 to S3, E2-S1 to S3, E3-S1 to S3, E9-S1 | 4.0 | `docker compose up` from clean checkout; 401, 403 and 404 behave; switcher works |
| 2 Rules | All rules correct, report committed | E4-S1 to S6, E10-S1 | 2.0 | Rule tests green; `rules_report.json` reviewed by hand against the seed traps |
| 3 Team page | Journey steps 1, 2 and 4-5 work for one user | E5-S1 to S4, E6-S1 to S4, E7-S1 to S2 | 3.5 | Make it an Issue idempotent; Issue to To-Do flow works in the UI |
| 4 Meeting | Two browsers stay in sync end to end | E8-S1 to S6 | 2.5 | Advance, refresh and rejoin recover state; summary visible for new and seeded meetings |
| 5 Hardening and submit | Tests, docs, video, verification | E10-S2 to S4, E11-S1 to S5 | 2.0 | Fresh-clone run passes; all links open in a private window |

**Critical path:** E1 > E2 > E3 > E4 > E5-S3 > E8-S1 > E8-S3 > E8-S4 > E10-S3 > E11-S4 > E11-S5. Any slip on this path moves the submission date.

**Parallelizable work:** E7, E6-S3 and E6-S4, and the documentation drafts can move within their blocks if a dependency is waiting.

**Block ceremonies (kept lightweight):** a 5-minute planning check at the start (confirm the goal and the first story), a demo against the seed at the end (the exit check), and a short retro note added to the decision record's limitations list.

## 8. Risks, Release Checklist, JQL and Dashboards

**RAID log (risks and dependencies)**

| ID | Risk or dependency | Likelihood | Impact | Mitigation | Owner |
| --- | --- | --- | --- | --- | --- |
| R1 | Time zone or DST mistake in week bucketing | Medium | High | Single tested helper; test the Nov 1 boundary and `t11`, `t28`, `t29` | You |
| R2 | Fixed `APP_NOW` freezes the meeting timer | High | High | Clock service adds monotonic elapsed time; tests use a controllable clock | You |
| R3 | WebSocket sync flaky in Docker or test | Medium | High | Snapshot on connect; polling fallback; build E8-S3 early in Block 4 | You |
| R4 | Authorization gaps on id-based routes (issue, todo, meeting) | Medium | High | Resolve resource to team before check; one parametrized test per route | You |
| R5 | Scope exceeds 14 hours | High | Medium | Cut order in section 3; bonus only after exit check of Block 5 | You |
| R6 | Rules report mismatches the evaluator's key | Medium | High | Hand-verify seed traps; run at several `APP_NOW` values; cross-check with a second independent script | You |
| R7 | AI-generated code not understood in the follow-up call | Medium | High | Review each module; mark `ai-assisted`; keep the decision record in your own words | You |
| D1 | Docker, Playwright browsers and package registries available on the machine | Low | Medium | Pin versions; test a clean build early in Block 1 | You |

**Release checklist (v1.0 Submission)**

- [ ] Fresh clone: `docker compose up` loads seed and serves the app
- [ ] `make test` passes unattended; failure artifact committed
- [ ] `make report` output equals the committed `rules_report.json`
- [ ] Report re-run with two other `APP_NOW` values produces sane output
- [ ] Two-browser walkthrough completed manually once
- [ ] README is 2 pages or less and the decision record is 1 page
- [ ] Repo public, video unlisted; both open in a private browser window
- [ ] Reply email contains all five deliverable links

**Useful JQL filters**

```text
Open core work:      project = L10 AND labels != bonus AND statusCategory != Done ORDER BY priority DESC, rank
Blocked or at risk:  project = L10 AND (flagged = Impediment OR status = Blocked)
Security coverage:   project = L10 AND labels = security ORDER BY status
AI-assisted work:    project = L10 AND labels = ai-assisted
Critical path:       project = L10 AND key in (E1-S1, E2-S1, E3-S2, E5-S3, E8-S1, E8-S3, E8-S4, E10-S3, E11-S4)
```

**Dashboards**

| Gadget | Purpose |
| --- | --- |
| Sprint burndown (hours) | Shows whether the current block will finish |
| Epic progress | Percent complete per epic, so core epics are visible at a glance |
| Rubric coverage | Issue count by `rubric-*` label and status, mapped to the evaluation weights |
| Open bugs by severity | Keeps blockers visible before submission |

**Import note.** The story tables convert directly to Jira's CSV import (columns: Summary, Issue Type, Epic Link, Description, Original Estimate, Story Points, Components, Labels, Priority). I can generate that CSV on request.
