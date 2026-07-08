import streamlit as st

from pawpal_system import Owner, Pet, Task, Priority, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

# Create the Owner once and keep it in the session "vault" so it (and all
# its pets/tasks) survives Streamlit's re-run on every interaction.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")

owner = st.session_state.owner

st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)

st.divider()

# --- Adding a Pet ---------------------------------------------------------
st.subheader("Pets")
col_a, col_b = st.columns(2)
with col_a:
    pet_name = st.text_input("Pet name", value="Mochi")
with col_b:
    species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add pet"):
    if pet_name.strip():
        owner.add_pet(Pet(name=pet_name.strip(), species=species))
        st.success(f"Added {pet_name}.")
    else:
        st.warning("Please enter a pet name.")

pets = owner.list_pets()
if pets:
    st.write("Current pets:", ", ".join(p.name for p in pets))
else:
    st.info("No pets yet. Add one above.")

st.divider()

# A view-only scheduler for sorting/filtering/conflict-checking the task list.
# available_minutes is irrelevant to those methods, so any value is fine here;
# the real budget is set in the Build Schedule section below.
view_scheduler = Scheduler(available_minutes=1)


def _valid_time(text: str) -> bool:
    """True for "" (anytime) or a well-formed 24-hour HH:MM string."""
    if not text:
        return True
    parts = text.split(":")
    if len(parts) != 2 or not (parts[0].isdigit() and parts[1].isdigit()):
        return False
    hour, minute = int(parts[0]), int(parts[1])
    return 0 <= hour < 24 and 0 <= minute < 60


# --- Scheduling a Task ----------------------------------------------------
st.subheader("Tasks")
st.caption("Add care tasks to a pet. These feed into the scheduler below.")

if pets:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        which_pet = st.selectbox("For pet", [p.name for p in pets])
    with col2:
        task_title = st.text_input("Task", value="Morning walk")
    with col3:
        duration = st.number_input("Minutes", min_value=1, max_value=240, value=20)
    with col4:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    pref_time = st.text_input(
        "Preferred time (HH:MM, 24-hour — leave blank for anytime)", value=""
    )

    if st.button("Add task"):
        if not _valid_time(pref_time.strip()):
            st.warning("Preferred time must be blank or a valid HH:MM (e.g. 08:30).")
        else:
            pet = next(p for p in pets if p.name == which_pet)
            pet.add_task(
                Task(
                    description=task_title,
                    duration_minutes=int(duration),
                    priority=Priority[priority.upper()],
                    preferred_time=pref_time.strip(),
                )
            )
            st.success(f"Added '{task_title}' to {which_pet}.")

    # Show every pet's current tasks, with filter + sort controls that call
    # straight into the Scheduler methods.
    all_tasks = owner.all_tasks()
    if all_tasks:
        st.write("Current tasks:")

        fcol1, fcol2, fcol3 = st.columns(3)
        with fcol1:
            pet_filter = st.selectbox("Filter by pet", ["All"] + [p.name for p in pets])
        with fcol2:
            status_filter = st.selectbox("Status", ["All", "Pending", "Completed"])
        with fcol3:
            sort_by_time = st.checkbox("Sort by preferred time", value=True)

        completed_arg = {"All": None, "Pending": False, "Completed": True}[status_filter]
        pet_arg = None if pet_filter == "All" else pet_filter

        view = view_scheduler.filter_tasks(
            all_tasks, completed=completed_arg, pet_name=pet_arg
        )
        if sort_by_time:
            view = view_scheduler.sort_by_time(view)

        if view:
            st.table(
                [
                    {
                        "pet": t.pet_name,
                        "task": t.description,
                        "preferred_time": t.preferred_time or "anytime",
                        "duration_minutes": t.duration_minutes,
                        "priority": t.priority.name.lower(),
                        "done": "✓" if t.completed else "",
                    }
                    for t in view
                ]
            )
        else:
            st.info("No tasks match these filters.")

        # Conflict warnings run over ALL tasks (not the filtered view), so a
        # cross-pet clash isn't hidden just because you're viewing one pet.
        conflicts = view_scheduler.detect_conflicts(all_tasks)
        if conflicts:
            for warning in conflicts:
                st.warning(warning)
        else:
            st.success("No time conflicts among tasks with a preferred time.")
    else:
        st.info("No tasks yet. Add one above.")
else:
    st.info("Add a pet first, then you can add tasks for it.")

st.divider()

# --- Build Schedule -------------------------------------------------------
st.subheader("Build Schedule")
available = st.number_input(
    "Time available today (minutes)", min_value=10, max_value=600, value=120
)

if st.button("Generate schedule"):
    if not owner.all_tasks():
        st.warning("Add at least one task before generating a schedule.")
    else:
        scheduler = Scheduler(available_minutes=int(available))
        plan = scheduler.build_for(owner)

        if plan.scheduled_items:
            st.success(
                f"Scheduled {len(plan.scheduled_items)} task(s) using "
                f"{plan.total_minutes()} of {int(available)} minutes."
            )
            st.table(
                [
                    {
                        "start": item.start_time.strftime("%H:%M"),
                        "end": item.end_time().strftime("%H:%M"),
                        "pet": item.task.pet_name,
                        "task": item.task.description,
                        "minutes": item.task.duration_minutes,
                        "priority": item.task.priority.name.lower(),
                    }
                    for item in plan.scheduled_items
                ]
            )
        else:
            st.info("No tasks could be scheduled within the available time.")

        # Conflict notices detected while building the plan.
        for warning in plan.warnings:
            st.warning(warning)

        # Tasks that didn't fit the day's time budget.
        if plan.skipped:
            skipped = ", ".join(t.description for t in plan.skipped)
            st.warning(f"Skipped (day full): {skipped}")

        st.caption(plan.explain())
