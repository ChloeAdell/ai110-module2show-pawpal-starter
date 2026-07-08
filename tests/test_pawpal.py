"""Tests for PawPal+ core classes."""

from datetime import date, timedelta

from pawpal_system import Pet, Task, Priority, Scheduler


def test_mark_complete_changes_status():
    """Calling mark_complete() should flip the task from incomplete to complete."""
    task = Task("Morning walk", duration_minutes=30, priority=Priority.HIGH)

    assert task.completed is False  # starts incomplete

    task.mark_complete()

    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    """Adding a task to a Pet should grow that pet's task list by one."""
    pet = Pet(name="Mochi", species="dog")

    assert len(pet.get_tasks()) == 0  # starts empty

    pet.add_task(Task("Feed", duration_minutes=10, priority=Priority.HIGH))

    assert len(pet.get_tasks()) == 1


def test_sort_by_time_orders_chronologically():
    """sort_by_time() should order tasks earliest-first and push blanks last."""
    scheduler = Scheduler(available_minutes=120)
    tasks = [
        Task("Evening walk", 30, preferred_time="14:00"),
        Task("Anytime brush", 20, preferred_time=""),      # no preference
        Task("Morning meds", 5, preferred_time="9:00"),    # un-padded hour
        Task("Breakfast", 10, preferred_time="08:30"),
    ]

    ordered = scheduler.sort_by_time(tasks)

    assert [t.description for t in ordered] == [
        "Breakfast",      # 08:30
        "Morning meds",   # 9:00 (un-padded, still sorts before 14:00)
        "Evening walk",   # 14:00
        "Anytime brush",  # "" -> last
    ]


def test_completing_daily_task_respawns_next_day():
    """Completing a daily task should queue a fresh copy due one day later."""
    pet = Pet(name="Mochi", species="dog")
    today = date(2026, 7, 7)
    pet.add_task(Task("Walk", 30, frequency="daily", due_date=today))

    spawned = pet.mark_task_complete(pet.tasks[0])

    assert pet.tasks[0].completed is True          # original marked done
    assert len(pet.tasks) == 2                      # a new occurrence was added
    assert spawned.completed is False               # the new one is fresh
    assert spawned.due_date == today + timedelta(days=1)
    assert spawned.frequency == "daily"


def test_completing_weekly_task_respawns_next_week():
    """A weekly task should respawn seven days out."""
    pet = Pet(name="Luna", species="cat")
    today = date(2026, 7, 7)
    pet.add_task(Task("Brush", 20, frequency="weekly", due_date=today))

    spawned = pet.mark_task_complete(pet.tasks[0])

    assert spawned.due_date == today + timedelta(days=7)


def test_completing_one_off_task_does_not_respawn():
    """A non-recurring task should not create a next occurrence."""
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Vet visit", 60, frequency="once", due_date=date(2026, 7, 7)))

    spawned = pet.mark_task_complete(pet.tasks[0])

    assert spawned is None
    assert len(pet.tasks) == 1                      # nothing added


def test_detect_conflicts_flags_same_time_tasks():
    """Two tasks at the same preferred_time should produce one warning."""
    scheduler = Scheduler(available_minutes=120)
    walk = Task("Morning walk", 30, preferred_time="08:00", pet_name="Mochi")
    call = Task("Vet phone call", 15, preferred_time="08:00", pet_name="Luna")

    warnings = scheduler.detect_conflicts([walk, call])

    assert len(warnings) == 1
    assert "conflict" in warnings[0].lower()


def test_detect_conflicts_returns_empty_when_no_overlap():
    """Non-overlapping (and 'anytime') tasks should raise no warnings."""
    scheduler = Scheduler(available_minutes=120)
    tasks = [
        Task("Walk", 30, preferred_time="08:00", pet_name="Mochi"),
        Task("Feed", 10, preferred_time="09:00", pet_name="Mochi"),  # after walk ends
        Task("Brush", 20, preferred_time="", pet_name="Luna"),       # anytime
    ]

    assert scheduler.detect_conflicts(tasks) == []


def test_detect_conflicts_catches_partial_overlap():
    """A task starting before the previous one ends is a conflict."""
    scheduler = Scheduler(available_minutes=120)
    walk = Task("Long walk", 45, preferred_time="08:00", pet_name="Mochi")  # ends 08:45
    feed = Task("Feed", 10, preferred_time="08:30", pet_name="Mochi")       # starts 08:30

    assert len(scheduler.detect_conflicts([walk, feed])) == 1
