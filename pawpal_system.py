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

    def priority_score(self) -> int:
        """Numeric priority so the scheduler can sort (higher = more urgent)."""
        return int(self.priority)

    def mark_complete(self) -> None:
        """Mark this task as done for the day."""
        self.completed = True

    def reset(self) -> None:
        """Clear completion (e.g. at the start of a new day)."""
        self.completed = False


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

        ordered = self.organize(tasks)
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
