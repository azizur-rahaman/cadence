# Level 10 — Design System

**Product:** Weekly Team Meeting Platform (EOS / Level 10)
**Version:** 1.0
**Design Direction:** Professional Enterprise SaaS
**Status:** Design Standard

---

## 1. Design Philosophy

Level 10 follows a premium B2B SaaS design approach inspired by products such as Linear, Notion, and Stripe.

The interface should feel professional, clean, modern, and highly functional. As a leadership productivity platform, the primary focus is information clarity, operational visibility, and efficient decision-making.

### Design Characteristics

- Minimalist enterprise interface.
- Light-first visual design.
- Neutral backgrounds with subtle borders.
- Strong typography hierarchy.
- Compact, information-dense tables.
- Consistent semantic status colors.
- Subtle interactions and transitions.
- No unnecessary gradients, glassmorphism, or excessive shadows.
- Consistent components throughout the application.

### Core Design Principles

1. **Consistency over creativity:** Components should look and behave consistently across the application.
2. **Information over decoration:** Every visual element should serve a functional purpose.
3. **Clear hierarchy:** Users should understand important information immediately.
4. **Predictable interactions:** Avoid surprising or inconsistent behaviors.
5. **Accessibility first:** Follow accessible color, typography, and interaction standards.
6. **Data accuracy:** Visual representations must reflect actual business rules.
7. **Meeting-first usability:** Prioritize timers, agendas, and collaborative actions during meetings.
8. **Responsive design:** Desktop-first, but fully usable on tablets and mobile browsers.

---

## 2. Brand Identity

### Brand Personality

- Professional
- Confident
- Focused
- Trustworthy
- Minimalist
- Enterprise-oriented

### Brand Colors

| Token         | Hex       | Purpose                         |
| ------------- | --------- | ------------------------------- |
| Primary       | `#2563EB` | Main brand color                |
| Primary Hover | `#1D4ED8` | Primary hover state             |
| Dark          | `#0F172A` | Main headings and dark surfaces |
| Background    | `#F8FAFC` | Application background          |
| Surface       | `#FFFFFF` | Cards and panels                |
| Border        | `#E2E8F0` | Component borders               |

### Brand Messaging

**Measure. Commit. Resolve.**

A better operating rhythm for leadership teams.

---

## 3. Color System

### 3.1 Primary Color Palette

The primary brand color is Professional Blue.

| Token    | Hex       |
| -------- | --------- |
| Blue 50  | `#EFF6FF` |
| Blue 100 | `#DBEAFE` |
| Blue 200 | `#BFDBFE` |
| Blue 300 | `#93C5FD` |
| Blue 400 | `#60A5FA` |
| Blue 500 | `#3B82F6` |
| Blue 600 | `#2563EB` |
| Blue 700 | `#1D4ED8` |
| Blue 800 | `#1E40AF` |
| Blue 900 | `#1E3A8A` |

**Primary color:** `#2563EB`

Usage:

- Primary buttons.
- Active navigation.
- Links.
- Selected states.
- Focus indicators.
- Interactive elements.

### 3.2 Navy Palette

| Token    | Hex       |
| -------- | --------- |
| Navy 50  | `#F1F5F9` |
| Navy 200 | `#CBD5E1` |
| Navy 300 | `#94A3B8` |
| Navy 400 | `#64748B` |
| Navy 500 | `#475569` |
| Navy 600 | `#334155` |
| Navy 800 | `#1E293B` |
| Navy 900 | `#0F172A` |

Usage:

- Headings.
- Sidebar.
- Primary text.
- Important interface elements.

### 3.3 Neutral Palette

| Token             | Hex       | Usage                       |
| ----------------- | --------- | --------------------------- |
| Background        | `#F8FAFC` | Main application background |
| Surface           | `#FFFFFF` | Cards, dialogs, tables      |
| Surface Secondary | `#F1F5F9` | Secondary panels            |
| Surface Hover     | `#F8FAFC` | Hover states                |
| Border            | `#E2E8F0` | Default borders             |
| Border Strong     | `#CBD5E1` | Emphasized borders          |
| Text Primary      | `#0F172A` | Main text                   |
| Text Secondary    | `#475569` | Supporting text             |
| Text Muted        | `#64748B` | Metadata                    |
| Disabled          | `#94A3B8` | Disabled elements           |

### 3.4 Semantic Colors

Semantic colors must remain consistent throughout the application.

#### Success

| Token              | Hex       |
| ------------------ | --------- |
| Success            | `#15803D` |
| Success Background | `#DCFCE7` |
| Success Text       | `#166534` |

Used for:

- Completed tasks.
- On-track indicators.
- Completed Rocks.
- Successful operations.

#### Warning

| Token              | Hex       |
| ------------------ | --------- |
| Warning            | `#B45309` |
| Warning Background | `#FEF3C7` |
| Warning Text       | `#92400E` |

Used for:

- Pending states.
- Approaching deadlines.
- Attention-required indicators.

#### Danger

| Token             | Hex       |
| ----------------- | --------- |
| Danger            | `#DC2626` |
| Danger Background | `#FEE2E2` |
| Danger Text       | `#991B1B` |

Used for:

- Off-track indicators.
- Overdue tasks.
- Critical warnings.
- Destructive actions.

#### Information

| Token           | Hex       |
| --------------- | --------- |
| Info            | `#2563EB` |
| Info Background | `#DBEAFE` |
| Info Text       | `#1E40AF` |

Used for:

- Informational messages.
- Active states.
- General notifications.

### 3.5 Product-Specific Status Mapping

| Feature   | Status    | Color   |
| --------- | --------- | ------- |
| Scorecard | On Track  | Green   |
| Scorecard | Off Track | Red     |
| Scorecard | Pending   | Amber   |
| Rocks     | Complete  | Green   |
| Rocks     | On Track  | Blue    |
| Rocks     | Off Track | Red     |
| To-Dos    | Completed | Green   |
| To-Dos    | Overdue   | Red     |
| To-Dos    | Upcoming  | Neutral |
| Meeting   | Active    | Green   |
| Meeting   | Over Time | Red     |
| Meeting   | Ended     | Neutral |
| Issues    | Unsolved  | Amber   |
| Issues    | Solved    | Green   |

**Important:** Never communicate status using color alone. Always include descriptive text or an appropriate icon.

---

## 4. Typography System

### Primary Typeface: Inter

Inter is the standard typeface throughout the application.

Font weights:

- Regular: 400
- Medium: 500
- Semibold: 600
- Bold: 700

### Typography Scale

| Element        | Font Size | Weight |
| -------------- | --------: | ------ |
| Page Title     |      24px | 600    |
| Section Title  |      18px | 600    |
| Card Title     |      15px | 600    |
| Body           |      14px | 400    |
| Secondary Body |      13px | 400    |
| Label          |      12px | 500    |
| Caption        |      11px | 400    |
| KPI Number     |   28–32px | 600    |

### Typography Guidelines

- Use sentence case for headings.
- Avoid unnecessary uppercase text.
- Use tabular numerals for KPIs, scores, and timers.
- Maintain approximately 1.5 line height for body text.
- Use consistent font weights.
- Avoid excessive font-size variations.
- Maintain readable text contrast.

---

## 5. Spacing System

Use a 4px base spacing scale.

| Token    | Value |
| -------- | ----: |
| space-1  |   4px |
| space-2  |   8px |
| space-3  |  12px |
| space-4  |  16px |
| space-5  |  20px |
| space-6  |  24px |
| space-8  |  32px |
| space-10 |  40px |
| space-12 |  48px |
| space-16 |  64px |

### Layout Dimensions

| Element                | Dimension |
| ---------------------- | --------: |
| Sidebar                |     240px |
| Collapsed Sidebar      |      68px |
| Header                 |      64px |
| Main Content Max Width |    1440px |
| Main Content Padding   |      32px |
| Card Padding           |   20–24px |
| Card Gap               |   16–24px |

The application should maintain consistent spacing across every screen.

---

## 6. Component Design Standards

All reusable components must follow the same visual language.

### Buttons

| Variant     | Appearance                       |
| ----------- | -------------------------------- |
| Primary     | Blue background, white text      |
| Secondary   | White background, gray border    |
| Destructive | Red background, white text       |
| Ghost       | Transparent background           |
| Outline     | Transparent or white with border |

Button heights:

- Small: 32px
- Medium: 40px
- Large: 44px

Button border radius: 8px.

### Inputs

- Default height: 40px.
- Border radius: 8px.
- Border: `#E2E8F0`.
- Focus border: `#2563EB`.
- Background: `#FFFFFF`.
- Clear validation and error states.

### Cards

- Background: `#FFFFFF`.
- Border: `1px solid #E2E8F0`.
- Border radius: 12px.
- Padding: 20–24px.
- Minimal shadow.
- Consistent internal spacing.

### Badges

Use semantic colors with soft backgrounds.

Examples:

- On Track: Green.
- Off Track: Red.
- Pending: Amber.
- In Progress: Blue.

Badges should be compact and consistent.

### Tables

- Compact and readable rows.
- Subtle horizontal dividers.
- Clear column headings.
- Consistent numeric alignment.
- Appropriate hover states.
- Sticky headers when useful.
- Responsive horizontal scrolling where necessary.

### Dialogs

- White background.
- 12px border radius.
- Clear title and description.
- Consistent footer actions.
- Keyboard accessible.
- Confirmation for destructive actions.

### Tabs

- Text-based navigation.
- Blue active indicator.
- Neutral inactive text.
- Consistent spacing.
- Clear keyboard focus.

---

## 7. Shadows, Borders and Radius

### Shadow Tokens

| Token     | Value                           |
| --------- | ------------------------------- |
| Shadow XS | `0 1px 2px rgba(15,23,42,.04)`  |
| Shadow SM | `0 1px 3px rgba(15,23,42,.08)`  |
| Shadow MD | `0 4px 12px rgba(15,23,42,.08)` |

Use borders instead of shadows for most cards.

### Border Radius

| Token       |  Value |
| ----------- | -----: |
| Radius SM   |    4px |
| Radius MD   |    8px |
| Radius LG   |   12px |
| Radius XL   |   16px |
| Radius Full | 9999px |

---

## 8. Application Layout

### Two-Page Architecture (Brief 2.5)

The application intentionally consists of **two pages** so teams stay focused on the weekly loop and zero out-of-scope chrome is introduced:

1. **Team Page:** Displays the selected team's **Scorecard**, **Issues**, **To-Dos**, and **Rocks** sections (via compact in-page section tabs or jump links), plus a primary action to start or join the team's live Level 10 Meeting.
2. **Live Level 10 Meeting Page:** Focused meeting workspace with the server-controlled timer, agenda progress, attendee list, facilitator controls, reused **Scorecard** and **Issues (IDS)** sections from the Team Page, **Conclude** (new To-Dos recap + 1–10 ratings), and **Meeting Summary**.

Out of scope (do not add): Dashboard, Team Settings, Meeting History page, Notifications inbox, and global Search.

#### Header

Header requirements:

- Height: 64px, sticky at top.
- Brand mark / product name (`Level 10`).
- **Team Switcher:** Lists the user's teams (all teams for Admins); unauthorized team IDs return an error state.
- **Live Meeting CTA:** "Start Meeting" (Admins & Team Members when no meeting is active) or "Join Live Meeting" badge/button (all team readers when active).
- **Seeded User Switcher:** Displays active user name and role badge (`Admin`, `Team Member`, `Observer`) and lets evaluators switch seeded personas cleanly.
- Consistent alignment across desktop and mobile.

#### Optional Compact Section Rail / Tabs (Team Page)

- Desktop may use a compact left section rail (240px, collapsible to 68px) or horizontal top section tabs strictly for jumping between the four Team Page sections: **Scorecard**, **Issues**, **To-Dos**, and **Rocks**.
- On the Live Meeting Page, hide the Team Page rail so the agenda, timer, and active workspace get full focus.
- Clear active state, Lucide icons, and consistent spacing.

#### Main Content

- Maximum width: 1440px.
- Padding: 32px.
- Consistent page title placement.
- Clear section hierarchy.
- Responsive layout.

---

## 9. Feature-Specific Design Guidelines

### 9.1 Team Page Overview

The Team Page is the primary workspace for a team's weekly preparation and review, housing all four sections (Scorecard, Issues, To-Dos, Rocks) without a separate Dashboard or Settings page.

Recommended structure:

- Team header bar showing team name, active user role indicator (with a clear read-only banner for Observers), and Start / Join Live Meeting CTA.
- Compact section navigation (tabs or left rail) switching or scrolling cleanly across Scorecard, Issues, To-Dos, and Rocks.
- Optional compact summary strip showing last closed week's To-Do completion rate vs. the 90% target and open Issue count.

Design guidelines:

- Keep the Team Page uncluttered so users can enter scores, review To-Dos, and triage Issues quickly before the meeting.
- Avoid unnecessary charts or out-of-scope widgets.
- Build Scorecard and Issues as self-contained reusable section components shared directly with the Live Meeting Page.
- Maintain consistent card dimensions and read-only treatment for Observers.

### 9.2 Scorecard

The Scorecard is one of the most important screens.

Requirements:

- Fixed first column for Measurable names.
- Horizontally scrollable weekly columns.
- 13-week view.
- Clear numerical values.
- Small status indicators.
- Inline score editing.
- Distinguishable current-week column.
- Make it an Issue action for off-track cells.

Design guidelines:

- Use compact table cells.
- Keep numeric values visually aligned.
- Use semantic status colors.
- Show status text or accessible tooltips.
- Maintain readability with many Measurables.

### 9.3 Issues

Requirements:

- Priority-based ordering.
- Clearly visible ownership.
- Priority indicators.
- Resolution action.
- Add To-Do action.
- Separate solved and unsolved views.

Design guidelines:

- Use a clean list or table layout.
- Highlight priority without excessive colors.
- Keep issue titles prominent.
- Show source Measurable and week.
- Use a Solve Issue dialog with a **required non-empty resolution note** input (and clear validation feedback).
- Use an Add To-Do dialog pre-set to due in 7 days, limiting the owner selector to the team's eligible owners (`(all company Admins) ∪ (team's Team Members)`).

### 9.4 To-Dos

Requirements:

- Checkbox completion.
- Task title.
- Owner avatar.
- Due date.
- Overdue indicators.
- Completion rate.

Design guidelines:

- Use compact table rows.
- Display overdue states clearly.
- Provide immediate completion feedback.
- Make undo functionality accessible.
- Highlight the 90% completion target.

### 9.5 Rocks

Requirements:

- Rock title.
- Owner.
- Status.
- Progress bar.
- Milestone list.
- Due dates.

Design guidelines:

- Use expandable cards or rows.
- Display progress consistently.
- Highlight past-due unfinished Milestones.
- Maintain a read-only interface according to the PRD.

### 9.6 Live Level 10 Meeting

This screen deserves a dedicated design treatment.

Requirements:

- Large, highly visible timer (server-controlled).
- Current meeting section and agenda progress (Scorecard 5 min, IDS 60 min, Conclude 10 min).
- Attendee list (showing participants and live connection presence).
- Facilitator-only controls (Advance Section, End Meeting — available at any time; hidden/disabled for non-facilitators and enforced server-side).
- Shared **Scorecard** section (highlighting the last closed week with all Team Page actions including inline edit and Make it an Issue).
- Shared **IDS (Issues)** section (reusing Team Page Issues with priority, Solve with note, and Add To-Do actions).
- **Conclude** section: recap of To-Dos created during the meeting + 1–10 meeting rating selector for attending Admins and Team Members (editable until meeting ends; Observers view ratings read-only).
- **Post-Meeting Summary** view (shown to attendees on end and accessible via the summary API): last closed week Measurable statuses, Issues solved, To-Dos created, attendees, and average rating (one decimal, half up, or "No ratings").
- Over-time visual state (warning/danger styling without auto-advancing).

Design guidelines:

- Use a focused interface with minimal distractions.
- Keep the timer visible throughout the meeting.
- Use tabular numerals for timer values.
- Make facilitator-only controls clearly distinguishable.
- Prioritize readability under time pressure.

Meeting sections:

| Section   |   Duration |
| --------- | ---------: |
| Scorecard |  5 minutes |
| IDS       | 60 minutes |
| Conclude  | 10 minutes |

The timer must remain server-controlled. The frontend only displays the server-provided state.

---

## 10. Iconography

### Icon Library: Lucide React

Use Lucide icons consistently.

| Feature        | Icon                     |
| -------------- | ------------------------ |
| Scorecard      | `chart-no-axes-combined` |
| Issues         | `alert-circle`           |
| To-Dos         | `list-checks`            |
| Rocks          | `target`                 |
| Live Meeting   | `video` or `timer`       |
| Team Switcher  | `users`                  |
| User Switcher  | `user-circle`            |
| Clock / Timer  | `clock`                  |
| Check / Solved | `check-circle-2`         |

### Icon Guidelines

- Standard size: 18px.
- Sidebar size: 20px.
- Stroke width: 1.75–2px.
- Avoid mixing icon libraries.
- Avoid decorative icons without functional meaning.
- Use consistent icon sizing throughout the application.

---

## 11. Interaction and Accessibility

Target standard: WCAG 2.2 AA.

Requirements:

- Minimum 4.5:1 contrast for normal text.
- Minimum 3:1 contrast for large text and meaningful UI graphics.
- Visible keyboard focus indicators.
- Keyboard-accessible dialogs and dropdowns.
- Minimum 24 × 24 CSS pixel targets, with 40–44px preferred for primary touch interactions.
- Loading, empty, error, and success states for every data-driven component.
- Confirmation before destructive actions.
- Optimistic updates with rollback on failure.
- Clear real-time connection status.

### Real-Time Meeting Connection States

| State           | Visual Treatment |
| --------------- | ---------------- |
| Connected       | Green indicator  |
| Reconnecting    | Amber indicator  |
| Connection Lost | Red indicator    |

Users should always understand whether their changes have synchronized.

---

## 12. Frontend Technology Standards

The design system should be implemented using the project's specified frontend stack.

| Layer         | Technology             |
| ------------- | ---------------------- |
| Framework     | Next.js                |
| Language      | TypeScript             |
| Styling       | Tailwind CSS           |
| Components    | shadcn/ui              |
| Icons         | Lucide React           |
| Typography    | Inter                  |
| Forms         | React Hook Form + Zod  |
| Tables        | TanStack Table         |
| Server State  | TanStack Query         |
| Charts        | Not required initially |
| Theme         | CSS variables          |
| Accessibility | WCAG 2.2 AA            |

---

## 13. CSS Design Tokens

Use centralized CSS variables to maintain consistency.

```css
:root {
  /* Brand */
  --primary: #2563EB;
  --primary-hover: #1D4ED8;
  --primary-foreground: #FFFFFF;

  /* Backgrounds */
  --background: #F8FAFC;
  --surface: #FFFFFF;
  --surface-secondary: #F1F5F9;

  /* Text */
  --foreground: #0F172A;
  --text-secondary: #475569;
  --text-muted: #64748B;

  /* Borders */
  --border: #E2E8F0;
  --border-strong: #CBD5E1;

  /* Semantic */
  --success: #15803D;
  --success-bg: #DCFCE7;

  --warning: #B45309;
  --warning-bg: #FEF3C7;

  --danger: #DC2626;
  --danger-bg: #FEE2E2;

  --info: #2563EB;
  --info-bg: #DBEAFE;

  /* Layout */
  --sidebar-width: 240px;
  --header-height: 64px;

  /* Radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;

  /* Spacing */
  --page-padding: 32px;
  --card-padding: 24px;

  /* Shadows */
  --shadow-sm: 0 1px 3px rgba(15,23,42,.08);
  --shadow-md: 0 4px 12px rgba(15,23,42,.08);
}
```

---

## 14. Responsive Design

Adopt a desktop-first responsive approach.

Recommended breakpoints:

| Device        | Breakpoint  |
| ------------- | ----------- |
| Mobile        | 0–639px     |
| Tablet        | 640–1023px  |
| Desktop       | 1024–1279px |
| Large Desktop | 1280px+     |

### Mobile Guidelines

- Collapsible sidebar becomes a mobile navigation drawer.
- Tables use horizontal scrolling or appropriate compact layouts.
- Cards stack vertically.
- Primary actions remain accessible.
- Meeting timer stays visible.
- Dialogs adapt to available screen width.
- Avoid horizontal overflow in the main layout.

---

## 15. Implementation Rules

These rules are mandatory for maintaining design consistency.

1. Reuse shadcn/ui components instead of creating unnecessary alternatives.
2. Define global design tokens before building feature screens.
3. Never hardcode brand colors inside individual feature components.
4. Use semantic color tokens for status indicators.
5. Use the same button variants throughout the application.
6. Maintain consistent spacing, typography, and border radius.
7. Every data-driven component must support loading, empty, error, and success states.
8. Keep business logic outside presentation components.
9. Ensure responsive behavior for every major screen.
10. Follow WCAG 2.2 AA accessibility guidelines.
11. Use consistent iconography.
12. Avoid unnecessary animations and decorative visual effects.
13. Do not introduce new colors or component styles without updating the design system.
14. Do not use color alone to communicate important statuses.
15. Validate the interface against the actual PRD requirements.

---

## 16. Final Design Identity

| Property             | Standard                        |
| -------------------- | ------------------------------- |
| Product              | Level 10                        |
| Category             | Enterprise SaaS                 |
| Design Style         | Minimalist, Professional        |
| Primary Color        | `#2563EB`                       |
| Dark Color           | `#0F172A`                       |
| Background           | `#F8FAFC`                       |
| Typeface             | Inter                           |
| Component Library    | shadcn/ui                       |
| Icon Library         | Lucide                          |
| CSS Framework        | Tailwind CSS                    |
| Layout               | Header (Team & User Switchers) + Two-Page Workspace |
| Default Theme        | Light                           |
| Accessibility Target | WCAG 2.2 AA                     |

### Brand Statement

**Measure. Commit. Resolve.**

A professional workspace for leadership teams to track performance, manage accountability, and run effective weekly meetings.

---

**Final Recommendation**

Adopt this document as the official design standard for the Level 10 project.

Before implementing individual screens, establish the global design tokens and reusable components, including:

- Header with Team Switcher, Live Meeting CTA, and Seeded User Switcher.
- Buttons and inputs.
- Cards and badges.
- Tables and data grids.
- Dialogs and dropdowns.
- Loading and empty states.
- Status indicators.

Then build the **Team Page** (Scorecard, Issues, To-Dos, Rocks) and **Live Level 10 Meeting Page** (reusing Scorecard and Issues, plus Conclude and Summary) using the same design system.

The objective is to deliver one cohesive, production-quality enterprise SaaS experience rather than a collection of visually inconsistent screens.