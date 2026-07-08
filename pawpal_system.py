"""PawPal+ core system classes.

Implements the four core objects plus two small helpers:
- Task       : a single care activity
- Pet        : a pet and its tasks
- Owner      : manages many pets, exposes all their tasks
- Scheduler  : the "brain" that retrieves, organizes, and plans tasks
- Plan / ScheduledItem : the scheduler's output (a daily plan)

See diagrams/uml_draft.mmd for the class diagram.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from enum import IntEnum


class Priority(IntEnum):
    """Task priority. IntEnum so higher priority sorts higher automatically."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------
@dataclass
class Task:
    """A single pet care activity (walk, feeding, meds, etc.)."""

    description: str
    duration_minutes: int
    priority: Priority = Priority.MEDIUM
    frequency: str = "daily"        # "daily" | "weekly"
    completed: bool = False
    pet_name: str = ""              # which pet this task belongs to
    preferred_time: str = ""        # when to do it, "HH:MM" (24-hour); "" = no preference
    due_date: date | None = None    # which day this occurrence is for (None = unscheduled)

    def priority_score(self) -> int:
        """Numeric priority so the scheduler can sort (higher = more urgent)."""
        return int(self.priority)

    def mark_complete(self) -> None:
        """Mark this task as done for the day."""
        self.completed = True

    def reset(self) -> None:
        """Clear completion (e.g. at the start of a new day)."""
        self.completed = False

    def is_recurring(self) -> bool:
        """Whether this task repeats and should respawn when completed.

        True for "daily" and "weekly" tasks; False for one-off tasks
        (any other frequency, e.g. "once").
        """
        return self.frequency in ("daily", "weekly")

    def next_occurrence(self) -> "Task | None":
        """Build the next occurrence of a recurring task (fresh, incomplete).

        Returns a brand-new Task with its due_date advanced by one day
        ("daily") or one week ("weekly"). Returns None for one-off tasks,
        which don't repeat.
        """
        if not self.is_recurring():
            return None

        step = timedelta(days=1 if self.frequency == "daily" else 7)
        base_date = self.due_date if self.due_date is not None else date.today()
        return Task(
            description=self.description,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            frequency=self.frequency,
            completed=False,               # the next one starts fresh
            pet_name=self.pet_name,
            preferred_time=self.preferred_time,
            due_date=base_date + step,
        )


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------
@dataclass
class Pet:
    """An animal being cared for, and the tasks it needs."""

    name: str
    species: str = "other"          # "dog" | "cat" | "other"
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet, stamping it with the pet's name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def get_tasks(self) -> list[Task]:
        """Return all tasks for this pet."""
        return list(self.tasks)

    def pending_tasks(self) -> list[Task]:
        """Return only tasks that are not yet completed."""
        return [t for t in self.tasks if not t.completed]

    def mark_task_complete(self, task: Task) -> Task | None:
        """Complete a task and, if it recurs, queue its next occurrence.

        The freshly created next occurrence is appended to this pet's task
        list and also returned so callers can report/display it.

        No-op if the task was already completed, so completing it twice can't
        queue duplicate future occurrences.
        """
        if task.completed:
            return None
        task.mark_complete()
        next_task = task.next_occurrence()
        if next_task is not None:
            self.tasks.append(next_task)
        return next_task


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------
@dataclass
class Owner:
    """The app user; owns pets and holds scheduling preferences."""

    name: str
    pets: list[Pet] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner (ignores duplicates by name)."""
        if any(p.name == pet.name for p in self.pets):
            return
        self.pets.append(pet)

    def list_pets(self) -> list[Pet]:
        """Return all pets owned by this owner."""
        return list(self.pets)

    def all_tasks(self) -> list[Task]:
        """Gather tasks across every pet into one flat list for the scheduler."""
        tasks: list[Task] = []
        for pet in self.pets:
            tasks.extend(pet.get_tasks())
        return tasks

    def pending_tasks(self) -> list[Task]:
        """All not-yet-completed tasks across every pet."""
        return [t for t in self.all_tasks() if not t.completed]

    def mark_task_complete(self, task: Task) -> Task | None:
        """Complete a task by delegating to the pet that owns it.

        Finds the owning pet via task.pet_name so recurring tasks respawn on
        the correct pet's list. Falls back to just completing the task if no
        matching pet is found.
        """
        for pet in self.pets:
            if pet.name == task.pet_name:
                return pet.mark_task_complete(task)
        task.mark_complete()
        return None


# ---------------------------------------------------------------------------
# Scheduler output: Plan + ScheduledItem
# ---------------------------------------------------------------------------
@dataclass
class ScheduledItem:
    """One task placed at a start time inside the daily plan."""

    task: Task
    start_time: time

    def end_time(self) -> time:
        """When this item finishes, based on the task's duration."""
        start = datetime.combine(date.min, self.start_time)
        end = start + timedelta(minutes=self.task.duration_minutes)
        return end.time()


@dataclass
class Plan:
    """The finished daily schedule shown to the user."""

    day: date
    scheduled_items: list[ScheduledItem] = field(default_factory=list)
    skipped: list[Task] = field(default_factory=list)  # didn't fit; explained below
    warnings: list[str] = field(default_factory=list)  # e.g. time-conflict notices

    def total_minutes(self) -> int:
        """Total minutes of scheduled care."""
        return sum(item.task.duration_minutes for item in self.scheduled_items)

    def display(self) -> str:
        """Human-readable version of the plan."""
        if not self.scheduled_items and not self.skipped:
            return f"No tasks planned for {self.day.isoformat()}."

        lines = [f"Daily plan for {self.day.isoformat()}:"]
        for item in self.scheduled_items:
            t = item.task
            who = f"{t.pet_name}: " if t.pet_name else ""
            lines.append(
                f"  {item.start_time.strftime('%H:%M')} — {who}{t.description} "
                f"({t.duration_minutes} min) [priority: {t.priority.name.lower()}]"
            )
        for t in self.skipped:
            who = f"{t.pet_name}: " if t.pet_name else ""
            lines.append(f"  (skipped) {who}{t.description} — not enough time")
        for warning in self.warnings:
            lines.append(f"  [!] {warning}")
        return "\n".join(lines)

    def explain(self) -> str:
        """Explain why tasks were chosen/ordered and why others were skipped."""
        lines = [
            "Tasks are ordered by priority (high first), then by shortest "
            "duration, and placed back-to-back until the day's time budget "
            "runs out."
        ]
        lines.append(
            f"Scheduled {len(self.scheduled_items)} task(s) using "
            f"{self.total_minutes()} minutes."
        )
        if self.skipped:
            names = ", ".join(t.description for t in self.skipped)
            lines.append(
                f"Skipped {len(self.skipped)} task(s) because the day was full: "
                f"{names}."
            )
        else:
            lines.append("All tasks fit within the available time.")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Scheduler (the "brain")
# ---------------------------------------------------------------------------
class Scheduler:
    """Retrieves, organizes, and manages tasks across pets into a daily Plan."""

    def __init__(self, available_minutes: int, day_start: time = time(8, 0)) -> None:
        """Set the day's time budget and the time the schedule starts."""
        # Source of truth for the day's time budget. The caller can pull this
        # from Owner.preferences and pass it in, so it lives in one place.
        self.available_minutes = available_minutes
        self.day_start = day_start

    @staticmethod
    def _to_minutes(preferred_time: str) -> int | None:
        """Convert an 'HH:MM' string to minutes-since-midnight, or None if blank."""
        if not preferred_time:
            return None
        hour, minute = (int(part) for part in preferred_time.split(":"))
        return hour * 60 + minute

    def detect_conflicts(self, tasks: list[Task]) -> list[str]:
        """Return warning messages for tasks whose preferred times overlap.

        Lightweight strategy: each pending task with a preferred_time becomes a
        [start, end) interval (end = start + duration). Sort by start, then
        compare each task against every *later* task that begins before it ends
        — not just the immediately following one, so a long task that overlaps
        a non-adjacent later task is still caught. Tasks with no preferred_time
        ("anytime") are ignored since they can slot in anywhere.

        Returns an empty list when there are no conflicts — it never raises,
        so callers can print the warnings and carry on.
        """
        timed = [
            t for t in tasks
            if not t.completed and self._to_minutes(t.preferred_time) is not None
        ]
        timed.sort(key=lambda t: self._to_minutes(t.preferred_time))

        warnings: list[str] = []
        for i, current in enumerate(timed):
            start_cur = self._to_minutes(current.preferred_time)
            end_cur = start_cur + current.duration_minutes
            for nxt in timed[i + 1:]:
                start_nxt = self._to_minutes(nxt.preferred_time)
                if start_nxt >= end_cur:
                    break  # sorted by start, so nothing further can overlap either
                same_pet = current.pet_name == nxt.pet_name
                who = (
                    f"{current.pet_name}'s" if same_pet
                    else f"{current.pet_name} and {nxt.pet_name}"
                )
                warnings.append(
                    f"Time conflict: {who} '{current.description}' "
                    f"({current.preferred_time}, {current.duration_minutes} min) "
                    f"overlaps '{nxt.description}' ({nxt.preferred_time})."
                )
        return warnings

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by their preferred_time ("HH:MM"), earliest first.

        The key parses each "HH:MM" string into an (hour, minute) tuple so
        sorting is correct even if hours aren't zero-padded ("9:00" vs "14:00").
        Tasks with no preferred_time ("") sort to the end, since they can go
        anywhere in the day.
        """
        def time_key(task: Task) -> tuple[int, int]:
            if not task.preferred_time:
                return (24, 0)  # no preference -> after any real clock time
            hour, minute = (int(part) for part in task.preferred_time.split(":"))
            return (hour, minute)

        return sorted(tasks, key=time_key)

    def filter_tasks(
        self,
        tasks: list[Task],
        completed: bool | None = None,
        pet_name: str | None = None,
    ) -> list[Task]:
        """Return the tasks matching the given filters.

        Both filters are optional and combine with AND:
        - completed=True/False keeps only done / not-done tasks (None = either).
        - pet_name="Mochi" keeps only that pet's tasks (None = every pet).

        Passing neither returns a copy of all tasks.
        """
        result = list(tasks)
        if completed is not None:
            result = [t for t in result if t.completed == completed]
        if pet_name is not None:
            result = [t for t in result if t.pet_name == pet_name]
        return result

    def organize(self, tasks: list[Task]) -> list[Task]:
        """Drop completed tasks and sort by priority (desc), then duration (asc)."""
        pending = [t for t in tasks if not t.completed]
        return sorted(
            pending,
            key=lambda t: (-t.priority_score(), t.duration_minutes),
        )

    def build_schedule(self, tasks: list[Task], day: date | None = None) -> Plan:
        """Sort by priority, fit within available_minutes, and assign start times.

        Tasks that don't fit go into Plan.skipped rather than being dropped
        silently, so Plan.explain() can report them.
        """
        plan_day = day if day is not None else date.today()
        plan = Plan(day=plan_day)

        # Only tasks meant for this day: unscheduled ones (due_date is None)
        # slot in anywhere, but occurrences dated for another day (e.g. a
        # recurring task's respawned "tomorrow" copy) must not leak in.
        todays = [t for t in tasks if t.due_date is None or t.due_date == plan_day]

        plan.warnings = self.detect_conflicts(todays)

        ordered = self.organize(todays)
        used_minutes = 0
        cursor = datetime.combine(plan_day, self.day_start)

        for task in ordered:
            if used_minutes + task.duration_minutes <= self.available_minutes:
                plan.scheduled_items.append(
                    ScheduledItem(task=task, start_time=cursor.time())
                )
                cursor += timedelta(minutes=task.duration_minutes)
                used_minutes += task.duration_minutes
            else:
                plan.skipped.append(task)

        return plan

    def build_for(self, owner: "Owner", day: date | None = None) -> Plan:
        """Convenience: plan the day for every pet an owner has."""
        return self.build_schedule(owner.all_tasks(), day=day)
