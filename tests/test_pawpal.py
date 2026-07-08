"""Tests for PawPal+ core classes."""

from pawpal_system import Pet, Task, Priority


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
