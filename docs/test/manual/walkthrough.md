# Manual QA & Walkthrough Script (≤ 7 Minutes)

Use this persona walkthrough to verify every role boundary and record the two-browser Level 10 demo.

## Personas
| User | Role | Teams | Key Verification |
| --- | --- | --- | --- |
| `u1` (Avery Admin) | Admin | All 3 teams (even without membership rows) | Cross-team access + eligible To-Do owner everywhere |
| `u2` (Blake Brooks) | Team Member | `team_lead` | Facilitator controls, inline score edits, Make it an Issue, Solve, Add To-Do |
| `u3` (Casey Cho) | Team Member | `team_lead` | Second browser live attendee, rating, reload recovery |
| `u5` (Ellis Evans) | Observer | `team_lead` | Read-only banner, can join live meeting, cannot edit/facilitate/rate (`403`) |
| `u6` (Finley Ford) | Team Member | `team_sales` | Isolated to Sales (`404` on `team_lead`) |

## Walkthrough Steps
1. **Team Page (`/`):**
   - Switch to `u2` on `Leadership`.
   - **Scorecard:** Inspect 13-week statuses (`m5` `Nov 9` = On track, `m1..m4` `Nov 9` = Pending). Click an off-track cell to trigger **Make Issue** (already linked cells show `Issue`). Edit a score inline and watch the status recompute server-side.
   - **Issues:** Verify canonical order (`i2, i1, i5, i3, i4`), change priority, add a To-Do (defaults due date to `+7d`), solve an Issue with a required resolution note.
   - **To-Dos:** Verify `90% Target Met` for `2026-11-02` (`9/10`), overdue badges on `t12` & `t31`, toggle done/undo.
   - **Rocks:** Expand `r1` (`on_track`, `33%`) and `r2` (`off_track`, `13%`, `ms5` Past due).
2. **RBAC Spot-Check:**
   - Switch to `u5` (Observer): confirm read-only banner and disabled mutations.
   - Switch to `u6` (Sales): confirm `Leadership` is not listed in Team Switcher.
3. **Two-Browser Live Level 10 Meeting (`/meetings/[id]`):**
   - **Browser 1 (`u2`):** Click **Start Level 10**.
   - **Browser 2 (`u3`):** Click **Join Live Meeting** from header. Confirm both attendees appear with live green dots.
   - **Scorecard → IDS → Conclude → End:** Advance sections in Browser 1, observe sub-second sync in Browser 2, reload Browser 2 mid-meeting to confirm snapshot recovery, submit ratings in both browsers, end meeting, and review the immutable Meeting Summary.
