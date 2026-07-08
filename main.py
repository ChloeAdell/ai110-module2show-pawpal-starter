"""PawPal+ terminal demo.

Builds an owner with a couple of pets and some care tasks, then prints
today's generated schedule to the terminal.

It also demonstrates the Scheduler's helper methods:
- sort_by_time() : order tasks chronologically by their "HH:MM" preferred_time
- filter_tasks() : filter by completion status and/or pet name

Run with:  python main.py
"""

from datetime import date

from pawpal_system import Owner, Pet, Task, Priority, Scheduler


def build_demo_owner() -> Owner:
    """Create a sample owner with two pets and several tasks.

    Tasks are intentionally added OUT OF ORDER (times jump around) so the
    sorting method has something real to fix.
    """
    owner = Owner(name="Jordan", preferences={"available_minutes": 120})

    mochi = Pet(name="Mochi", species="dog")
    luna = Pet(name="Luna", species="cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    today = date.today()

    # Added deliberately out of chronological order.
    # "Fetch / play" is a one-off (frequency="once") so it should NOT respawn.
    mochi.add_task(Task("Fetch / play", 45, Priority.LOW,
                        frequency="once", preferred_time="17:00", due_date=today))
    mochi.add_task(Task("Morning walk", 30, Priority.HIGH,
                        frequency="daily", preferred_time="08:00", due_date=today))
    mochi.add_task(Task("Breakfast", 10, Priority.HIGH,
                        frequency="daily", preferred_time="7:30", due_date=today))

    luna.add_task(Task("Brush coat", 20, Priority.LOW,
                       frequency="weekly", preferred_time="", due_date=today))  # weekly
    luna.add_task(Task("Litter box", 15, Priority.MEDIUM,
                       frequency="daily", preferred_time="12:00", due_date=today))
    luna.add_task(Task("Feed", 10, Priority.HIGH,
                       frequency="daily", preferred_time="07:45", due_date=today))

    # Deliberate CONFLICT: Luna's vet call is at 08:00, the same time as
    # Mochi's morning walk above — the scheduler should warn about this.
    luna.add_task(Task("Vet phone call", 15, Priority.MEDIUM,
                       frequency="once", preferred_time="08:00", due_date=today))

    return owner


def print_tasks(title: str, tasks: list[Task]) -> None:
    """Print a labeled list of tasks, one per line."""
    print(title)
    if not tasks:
        print("  (none)")
        return
    for t in tasks:
        when = t.preferred_time or "anytime"
        done = "x" if t.completed else " "
        day = t.due_date.isoformat() if t.due_date else "----------"
        print(
            f"  [{done}] {day} {when:>7}  {t.pet_name}: {t.description} "
            f"({t.duration_minutes} min, {t.frequency})"
        )


def main() -> None:
    owner = build_demo_owner()
    available = owner.preferences.get("available_minutes", 120)
    scheduler = Scheduler(available_minutes=available)

    print("=" * 52)
    print(f"Today's Schedule for {owner.name}")
    print(f"Pets: {', '.join(p.name for p in owner.list_pets())}")
    print(f"Time budget: {available} minutes")
    print("=" * 52)

    all_tasks = owner.all_tasks()

    # 1) Tasks as entered (out of order).
    print_tasks("\nTasks as entered (unsorted):", all_tasks)

    # 2) Same tasks, sorted chronologically.
    print_tasks("\nSorted by time (earliest first):",
                scheduler.sort_by_time(all_tasks))

    # 2.5) Conflict detection: warn (don't crash) on overlapping times.
    conflicts = scheduler.detect_conflicts(all_tasks)
    print("\nConflict check:")
    if conflicts:
        for warning in conflicts:
            print(f"  [!] {warning}")
    else:
        print("  No time conflicts found.")

    # 3) Filter: only Mochi's tasks (still time-sorted for readability).
    mochi_tasks = scheduler.filter_tasks(all_tasks, pet_name="Mochi")
    print_tasks("\nFiltered to Mochi's tasks:",
                scheduler.sort_by_time(mochi_tasks))

    # 4) Complete tasks via mark_task_complete(): recurring ones respawn.
    walk = owner.pets[0].tasks[1]   # Mochi: Morning walk (daily)
    brush = owner.pets[1].tasks[0]  # Luna: Brush coat (weekly)
    fetch = owner.pets[0].tasks[0]  # Mochi: Fetch / play (one-off)

    for done_task in (walk, brush, fetch):
        spawned = owner.mark_task_complete(done_task)
        if spawned is not None:
            print(f"\nCompleted '{done_task.description}' ({done_task.frequency}) "
                  f"-> next occurrence queued for {spawned.due_date.isoformat()}")
        else:
            print(f"\nCompleted '{done_task.description}' ({done_task.frequency}) "
                  f"-> one-off, nothing to respawn")

    # Re-read the (now longer) task list to see the respawned occurrences.
    all_tasks = owner.all_tasks()
    print_tasks("\nStill pending (completed=False) - note the future-dated respawns:",
                scheduler.sort_by_time(scheduler.filter_tasks(all_tasks, completed=False)))
    print_tasks("\nAlready done (completed=True):",
                scheduler.filter_tasks(all_tasks, completed=True))

    # 5) The generated plan (priority-ordered, packed into the time budget).
    plan = scheduler.build_for(owner)
    print("\n" + "-" * 52)
    print(plan.display())
    print("-" * 52)
    print(plan.explain())


if __name__ == "__main__":
    main()
