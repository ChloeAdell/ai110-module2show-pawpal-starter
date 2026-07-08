# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## ✨ Features

PawPal+ implements the following scheduling algorithms and behaviors (all in
`pawpal_system.py`; see [Smarter Scheduling](#-smarter-scheduling) for details):

- **Priority-based daily planning** — `Scheduler.organize()` drops completed
  tasks and sorts the rest by priority (high → low), breaking ties by shortest
  duration first. `Scheduler.build_schedule()` then packs them back-to-back from
  the day's start time until the available-minutes budget runs out; anything that
  doesn't fit is recorded as *skipped* rather than dropped silently.
- **Sorting by time** — `Scheduler.sort_by_time()` orders tasks chronologically
  by their `preferred_time` (`"HH:MM"`), correctly handling un-padded hours
  (`"9:00"` before `"14:00"`) and sending "anytime" (blank) tasks to the end.
- **Filtering** — `Scheduler.filter_tasks()` narrows a task list by completion
  status and/or pet name, with the two filters combining as a logical AND.
- **Conflict warnings** — `Scheduler.detect_conflicts()` treats each timed task
  as a `[start, end)` interval and flags any overlap — including non-adjacent
  overlaps (a long task colliding with a later one) and clashes across different
  pets. It returns warning strings instead of raising, so the plan still builds.
- **Daily & weekly recurrence** — completing a task via
  `Pet.mark_task_complete()` / `Owner.mark_task_complete()` calls
  `Task.next_occurrence()`, which spawns a fresh copy dated +1 day (daily) or
  +7 days (weekly). One-off tasks don't respawn, completing a task twice won't
  queue duplicates, and future-dated occurrences are kept out of today's plan.
- **Explainable plans** — `Plan.display()` renders the schedule (with start
  times, skipped tasks, and conflict warnings) and `Plan.explain()` states the
  ordering rule and why any tasks were skipped.
- **Multi-pet ownership** — an `Owner` aggregates tasks across all their pets
  (`Owner.all_tasks()`) and routes completions to the correct pet.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🧪 Testing PawPal+

Run the full test suite from the project root:

```bash
python -m pytest
```

The suite (`tests/test_pawpal.py`, 13 tests) covers the behaviors most likely to
break the daily plan:

- **Core task/pet basics** — completing a task flips its status; adding a task
  grows the pet's list.
- **Sorting** — `sort_by_time()` orders tasks chronologically and pushes
  "anytime" (blank) tasks to the end, including un-padded hours (`"9:00"`).
- **Filtering** — covered implicitly via the scheduling tests.
- **Conflict detection** — same-time overlaps, partial overlaps, non-overlapping
  and "anytime" tasks (no false positives), and **non-adjacent overlaps** (a long
  task clashing with a later task, not just the next one).
- **Recurring tasks** — daily respawns +1 day, weekly +7 days, one-off tasks
  don't respawn, and completing a task twice doesn't queue a duplicate occurrence.
- **Edge cases in the plan** — a respawned "tomorrow" occurrence is not scheduled
  into today's plan, and a task whose duration exactly equals the remaining time
  budget still fits (the boundary case).

Sample output from a successful run:

```
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\beaut\ai110_project2\ai110-module2show-pawpal-starter
plugins: anyio-4.14.1
collected 13 items

tests\test_pawpal.py .............                                       [100%]

============================= 13 passed in 0.06s ==============================
```

### Confidence Level: ★★★★☆ (4 / 5)

All 13 tests pass, and the suite covers the core scheduling logic plus several
edge cases that previously hid real bugs (respawned occurrences leaking into
today's plan, non-adjacent conflicts going undetected, and duplicate respawns on
double-completion) — each was verified to fail before its fix, so these tests are
genuinely guarding behavior. Held back from 5 stars because a few known edge
cases remain untested: malformed `preferred_time` strings (e.g. `"8"`) still
raise, tasks that run past midnight wrap in `ScheduledItem.end_time()`, and the
Streamlit UI in `app.py` has no automated coverage.

## 📐 Smarter Scheduling

Beyond the basic priority-based daily plan, PawPal+ adds four "smarter" scheduling
features. Each is implemented in `pawpal_system.py`.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Sorting by time | `Scheduler.sort_by_time()` | Orders tasks chronologically by `Task.preferred_time` ("HH:MM"); blanks last |
| Filtering | `Scheduler.filter_tasks()` | Filters by completion status and/or pet name |
| Conflict detection | `Scheduler.detect_conflicts()` | Warns on overlapping preferred times instead of crashing |
| Recurring tasks | `Task.next_occurrence()`, `Pet.mark_task_complete()` | Respawns daily/weekly tasks on completion |

### Sorting behavior — `Scheduler.sort_by_time()`

Returns tasks ordered by their `preferred_time`, earliest first. The sort key
parses each `"HH:MM"` string into an `(hour, minute)` tuple, so ordering is
correct even when hours aren't zero-padded (`"9:00"` still sorts before
`"14:00"`). Tasks with no preferred time (`""`) sort to the end, since they can
happen anytime. (The core daily plan is ordered separately, by priority then
duration, in `Scheduler.organize()`.)

### Filtering behavior — `Scheduler.filter_tasks()`

Filters a task list by two optional criteria that combine with AND:

- `completed=True/False` — keep only done / not-done tasks (`None` = either)
- `pet_name="Mochi"` — keep only that pet's tasks (`None` = every pet)

Passing neither returns a copy of all tasks. This lets the UI show views like
"still pending" or "just Luna's tasks."

### Conflict detection — `Scheduler.detect_conflicts()`

A lightweight overlap check that **returns a list of warning strings rather than
raising**. Each pending, timed task becomes a `[start, end)` interval
(`end = start + duration_minutes`); tasks are sorted by start time and each is
compared against every *later* task that begins before it ends — so a long task
that overlaps a non-adjacent later task is still caught. Same-time tasks are just
the case where two intervals start at the same minute. It reports conflicts both within one pet and across different pets, and
the resulting warnings are attached to `Plan.warnings` and shown by
`Plan.display()`. `Scheduler._to_minutes()` is the helper that converts `"HH:MM"`
to minutes-since-midnight.

### Recurring task logic — `Task.next_occurrence()` + `Pet.mark_task_complete()`

Tasks carry a `frequency` (`"daily"`, `"weekly"`, or one-off like `"once"`) and a
`due_date`. When a task is completed through `Pet.mark_task_complete()` (or
`Owner.mark_task_complete()`, which delegates to the owning pet), the method marks
it done and then calls `Task.next_occurrence()`. For a recurring task
(`Task.is_recurring()` is True) that returns a fresh, incomplete copy with its
`due_date` advanced by one day (daily) or seven days (weekly), which is appended
to the pet's task list. One-off tasks return `None` and do not respawn.

## 📸 Demo Walkthrough

PawPal+ ships two front ends over the same `pawpal_system.py` logic: an
interactive **Streamlit app** (`app.py`) and a scripted **terminal demo**
(`main.py`).

### The Streamlit app (`streamlit run app.py`)

The UI is organized top-to-bottom into the actions a user performs:

- **Owner** — set the owner's name.
- **Pets** — add a pet (name + species: dog / cat / other) and see the current
  list. Duplicate names are ignored.
- **Tasks** — add a care task for a chosen pet with a description, duration,
  priority, and an optional **preferred time** (`HH:MM`, validated). The task
  list below has live controls: **filter by pet**, **filter by status**
  (all / pending / completed), and a **sort by preferred time** toggle — these
  call `Scheduler.filter_tasks()` and `Scheduler.sort_by_time()` directly. A
  conflict banner (`Scheduler.detect_conflicts()`) appears above the table
  whenever two timed tasks overlap.
- **Build Schedule** — set the day's time budget and generate the plan. The
  result renders as a table of start/end times, with `st.success` for the
  summary and `st.warning` for conflicts and any skipped tasks.

**Example workflow:**

1. Enter the owner's name (e.g. *Jordan*).
2. Add a pet — type `Mochi`, pick `dog`, click **Add pet**.
3. Add a task — for `Mochi`, `Morning walk`, `30` minutes, `high`, preferred
   time `08:00`; click **Add task**.
4. Add a second, clashing task — `Luna`'s `Vet phone call` at `08:00`. The
   conflict banner immediately warns that the two overlap.
5. Toggle **Sort by preferred time** and switch the status filter to *Pending*
   to see the tasks reorder chronologically.
6. Set the time budget (e.g. `120` minutes) and click **Generate schedule** to
   view today's plan, packed by priority and duration.

### The terminal demo (`python main.py`)

`main.py` builds a sample owner (Jordan) with two pets and seven tasks —
deliberately entered out of order and with a built-in 08:00 conflict — then
walks through every Scheduler behavior in sequence: the tasks **as entered**,
**sorted by time**, the **conflict check**, a **filter to one pet**, marking
recurring tasks complete (watch the **respawned future-dated occurrences**), and
finally the **generated daily plan** with its explanation. Note how the plan only
contains tasks due *today* — the +1-day and +7-day respawns are correctly held
back.

Sample output from a full run:

```text
====================================================
Today's Schedule for Jordan
Pets: Mochi, Luna
Time budget: 120 minutes
====================================================

Tasks as entered (unsorted):
  [ ] 2026-07-07   17:00  Mochi: Fetch / play (45 min, once)
  [ ] 2026-07-07   08:00  Mochi: Morning walk (30 min, daily)
  [ ] 2026-07-07    7:30  Mochi: Breakfast (10 min, daily)
  [ ] 2026-07-07 anytime  Luna: Brush coat (20 min, weekly)
  [ ] 2026-07-07   12:00  Luna: Litter box (15 min, daily)
  [ ] 2026-07-07   07:45  Luna: Feed (10 min, daily)
  [ ] 2026-07-07   08:00  Luna: Vet phone call (15 min, once)

Sorted by time (earliest first):
  [ ] 2026-07-07    7:30  Mochi: Breakfast (10 min, daily)
  [ ] 2026-07-07   07:45  Luna: Feed (10 min, daily)
  [ ] 2026-07-07   08:00  Mochi: Morning walk (30 min, daily)
  [ ] 2026-07-07   08:00  Luna: Vet phone call (15 min, once)
  [ ] 2026-07-07   12:00  Luna: Litter box (15 min, daily)
  [ ] 2026-07-07   17:00  Mochi: Fetch / play (45 min, once)
  [ ] 2026-07-07 anytime  Luna: Brush coat (20 min, weekly)

Conflict check:
  [!] Time conflict: Mochi and Luna 'Morning walk' (08:00, 30 min) overlaps 'Vet phone call' (08:00).

Filtered to Mochi's tasks:
  [ ] 2026-07-07    7:30  Mochi: Breakfast (10 min, daily)
  [ ] 2026-07-07   08:00  Mochi: Morning walk (30 min, daily)
  [ ] 2026-07-07   17:00  Mochi: Fetch / play (45 min, once)

Completed 'Morning walk' (daily) -> next occurrence queued for 2026-07-08

Completed 'Brush coat' (weekly) -> next occurrence queued for 2026-07-14

Completed 'Fetch / play' (once) -> one-off, nothing to respawn

Still pending (completed=False) - note the future-dated respawns:
  [ ] 2026-07-07    7:30  Mochi: Breakfast (10 min, daily)
  [ ] 2026-07-07   07:45  Luna: Feed (10 min, daily)
  [ ] 2026-07-08   08:00  Mochi: Morning walk (30 min, daily)
  [ ] 2026-07-07   08:00  Luna: Vet phone call (15 min, once)
  [ ] 2026-07-07   12:00  Luna: Litter box (15 min, daily)
  [ ] 2026-07-14 anytime  Luna: Brush coat (20 min, weekly)

Already done (completed=True):
  [x] 2026-07-07   17:00  Mochi: Fetch / play (45 min, once)
  [x] 2026-07-07   08:00  Mochi: Morning walk (30 min, daily)
  [x] 2026-07-07 anytime  Luna: Brush coat (20 min, weekly)

----------------------------------------------------
Daily plan for 2026-07-07:
  08:00 — Mochi: Breakfast (10 min) [priority: high]
  08:10 — Luna: Feed (10 min) [priority: high]
  08:20 — Luna: Litter box (15 min) [priority: medium]
  08:35 — Luna: Vet phone call (15 min) [priority: medium]
----------------------------------------------------
Tasks are ordered by priority (high first), then by shortest duration, and placed back-to-back until the day's time budget runs out.
Scheduled 4 task(s) using 50 minutes.
All tasks fit within the available time.
```
