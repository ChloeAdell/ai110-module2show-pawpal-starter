"""PawPal+ core system classes.

Skeleton only: names, attributes, and empty method stubs based on the
UML draft in diagrams/uml_draft.mmd. Logic will be filled in later.

Revised after design review to fix:
- tasks now know which pet they belong to (Task.pet_name)
- Owner can gather all tasks across pets (Owner.all_tasks)
- Plan records both scheduled AND skipped tasks (so it can explain them)
- scheduled items carry a start time (ScheduledItem)
- priority is a validated Enum instead of a free-form string
"""

from dataclasses import dataclass, field
from datetime import date, time
from enum import IntEnum


class Priority(IntEnum):
    """Task priority. IntEnum so higher priority sorts higher automatically."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class Task:
    """A single pet care activity (walk, feeding, meds, etc.)."""

    title: str
    duration_minutes: int
    priority: Priority
    pet_name: str = ""  # which pet this task belongs to

    def priority_score(self) -> int:
        """Return a numeric score so the scheduler can sort by priority."""
        raise NotImplementedError


@dataclass
class Pet:
    """An animal being cared for, and the tasks it needs."""

    name: str
    species: str  # "dog" | "cat" | "other"
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet (stamps task.pet_name)."""
        raise NotImplementedError

    def get_tasks(self) -> list[Task]:
        """Return all tasks for this pet."""
        raise NotImplementedError


@dataclass
class Owner:
    """The app user; owns pets and holds scheduling preferences."""

    name: str
    pets: list[Pet] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        raise NotImplementedError

    def list_pets(self) -> list[Pet]:
        """Return all pets owned by this owner."""
        raise NotImplementedError

    def all_tasks(self) -> list[Task]:
        """Gather tasks across every pet, so the scheduler gets one flat list."""
        raise NotImplementedError


@dataclass
class ScheduledItem:
    """One task placed at a start time inside the daily plan."""

    task: Task
    start_time: time


@dataclass
class Plan:
    """The finished daily schedule shown to the user."""

    day: date
    scheduled_items: list[ScheduledItem] = field(default_factory=list)
    skipped: list[Task] = field(default_factory=list)  # didn't fit; explain why

    def explain(self) -> str:
        """Explain why each task was chosen/ordered and why others were skipped."""
        raise NotImplementedError

    def display(self) -> str:
        """Return a human-readable version of the plan."""
        raise NotImplementedError


class Scheduler:
    """Decides which tasks fit in the day and in what order."""

    def __init__(self, available_minutes: int) -> None:
        # Source of truth for the day's time budget. The caller can pull this
        # from Owner.preferences and pass it in, so it lives in one place.
        self.available_minutes = available_minutes

    def build_schedule(self, tasks: list[Task]) -> Plan:
        """Sort by priority, fit within available_minutes, assign start times.

        Tasks that don't fit go into Plan.skipped instead of being dropped
        silently, so Plan.explain() can report them.
        """
        raise NotImplementedError
