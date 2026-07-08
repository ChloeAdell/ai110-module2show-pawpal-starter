# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

User should be able to add theirs pets as well as schudule walks for their pets. They should also be able to add and see the task for the day.
Owner should hold the user and there pets
Pet should hold the animal
Task should hold the care activy with the duration and priority
Scheduler should hold the task
Plan should hold final schedule

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
Give task a pet_name field, made this change because task has no idea what pet it belongs to. As well Owner is not connected to the Scheduler. I want to have the scheduler list all the task for all pets.Should add skipped and unschduled list to plan so plan can explain what it dropped. Need to add a start time, the time is never really representated. Priority has an unvalidate string.
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

My scheduler considers a few constraints: the total time budget for the day (available_minutes), each task's priority, how long each task takes (duration_minutes), and whether the task is already completed so finished tasks get dropped. It also looks at the owner's preferred_time for a task when it checks for conflicts, and it uses frequency (daily/weekly) to respawn recurring tasks after they are done. I decided priority mattered most because a pet owner cares more about important care like feeding and meds than optional stuff like brushing, so those get scheduled first. Time was the next most important constraint because there are only so many minutes in the day, so once the budget runs out the lower-priority tasks get skipped instead of forcing everything in. I put preferred_time lower in importance because it is more of a "nice to have" for the owner, which is why I used it for warnings rather than letting it override the priority ordering.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

One tradeoff is that the scheduler separates conflict detection from actually placing the tasks. My detect_conflicts() method does check for real overlapping durations (it turns each task into a start/end interval using preferred_time + duration_minutes, not just exact time matches), so if a 30 min walk at 08:00 overlaps a vet call at 08:00 it warns me. But when build_schedule() makes the actual plan, it ignores preferred_time and just packs tasks back-to-back from day_start in priority order. So the plan itself never really double-books, but it also does not put tasks at the time the owner wanted. Instead of crashing or refusing to build, it just prints a warning message and still gives a full plan.

This is reasonable for a pet owner because the point is to get a usable to-do list for the day without the program blowing up over a scheduling clash. The owner is a person who can look at the warning and decide which task to move, so a soft warning is more helpful than a hard error. It keeps the scheduler simple, which mattered for finishing the project, and I left honoring preferred_time in the plan as a clear next step if I had more time.

A smaller related tradeoff: detect_conflicts() only compares each task to the next one after sorting, so if three tasks land on the same time I get two separate warnings instead of one combined message. I accepted that because the goal is just to alert the owner, not to produce a perfectly de-duplicated report.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?
I did use Ai tools all the way throught and just coping the extca wording from the page help it with doing the coding and asking questions.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
