"""PawPal+ terminal demo.

Builds an owner with a couple of pets and some care tasks, then prints
today's generated schedule to the terminal.

Run with:  python main.py
"""

from pawpal_system import Owner, Pet, Task, Priority, Scheduler


def build_demo_owner() -> Owner:
    """Create a sample owner with two pets and several tasks."""
    owner = Owner(name="Jordan", preferences={"available_minutes": 120})

    mochi = Pet(name="Mochi", species="dog")
    luna = Pet(name="Luna", species="cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Three+ tasks with different durations and priorities.
    mochi.add_task(Task("Morning walk", duration_minutes=30, priority=Priority.HIGH))
    mochi.add_task(Task("Breakfast", duration_minutes=10, priority=Priority.HIGH))
    mochi.add_task(Task("Fetch / play", duration_minutes=45, priority=Priority.LOW))

    luna.add_task(Task("Feed", duration_minutes=10, priority=Priority.HIGH))
    luna.add_task(Task("Litter box", duration_minutes=15, priority=Priority.MEDIUM))
    luna.add_task(Task("Brush coat", duration_minutes=20, priority=Priority.LOW))

    return owner


def main() -> None:
    owner = build_demo_owner()

    available = owner.preferences.get("available_minutes", 120)
    scheduler = Scheduler(available_minutes=available)
    plan = scheduler.build_for(owner)

    print("=" * 44)
    print(f"Today's Schedule for {owner.name}")
    print(f"Pets: {', '.join(p.name for p in owner.list_pets())}")
    print(f"Time budget: {available} minutes")
    print("=" * 44)
    print(plan.display())
    print("-" * 44)
    print(plan.explain())


if __name__ == "__main__":
    main()
