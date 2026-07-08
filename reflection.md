# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

The user should be able to add their pets as well as schedule walks for their pets. They should also be able to add and see the tasks for the day.
- Owner should hold the user and their pets.
- Pet should hold the animal.
- Task should hold the care activity with its duration and priority.
- Scheduler should hold the tasks.
- Plan should hold the final schedule.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
I gave Task a pet_name field, because a task had no idea which pet it belonged to. I also noticed the Owner was not connected to the Scheduler, and I wanted the scheduler to be able to list all the tasks across all pets. I added a skipped list to the Plan so the plan can explain which tasks it dropped. I needed to add a start time, since the time of day was never really represented before. Finally, Priority started out as an unvalidated string, so I turned it into an enum (Priority) to make the values safe and sortable.
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

A smaller related tradeoff is that detect_conflicts() reports a separate warning for each overlapping pair rather than merging them, so if three tasks land on the same time I get several warnings instead of one combined message. (Originally I only compared each task to the one right after it in the sorted list, but that missed overlaps between non-adjacent tasks, so I later changed it to compare each task against every later task that starts before it ends — that way a long task can't hide a conflict with something further down the list. I kept the one-warning-per-pair behavior on purpose.) I accepted that because the goal is just to alert the owner, not to produce a perfectly de-duplicated report.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?
I did use Ai tools all the way throught and just coping the extca wording from the page help it with doing the coding and asking questions.

**a2. AI Strategy**

- Which AI coding assistant features were most effective for building your scheduler?

The most effective feature was attaching my actual files (pawpal_system.py, app.py, main.py) so the assistant answered against my real code instead of a generic template. Asking narrow, specific questions worked far better than broad ones: "what edge cases should I test for a scheduler with sorting and recurring tasks?" pointed straight at the weak spots in my logic, and "does my draft UML still match my final code?" produced a concrete list of methods I had added and forgotten to diagram. Having it generate a pytest suite from those edge cases was also very effective, because writing the tests is what actually exposed the bugs in my code. The clickable file/line references made it easy to jump to exactly what changed.

- Give one example of an AI suggestion you rejected or modified to keep your system design clean.

When the AI found the three failing tests, it suggested I could just mark them `@pytest.mark.xfail` so the suite would stay green. I turned that down because it would have hidden real bugs behind a "passing" report, and I had it fix the actual logic in pawpal_system.py instead. I also modified how it presented output in the README: it had left a duplicate, half-broken "Sample Output" block, and I had it consolidate the sample output into one accurate Demo Walkthrough section so the manual stayed clean and truthful.

- How did using separate chat sessions for different phases help you stay organized?

Working in separate sessions per phase (design/UML, core classes, sorting and filtering, testing, then docs) kept each conversation focused on just the files that mattered for that step. The context did not get cluttered with unrelated earlier decisions, so it was easy to attach the right file and get answers that were actually about that phase. It also created a natural checkpoint between phases — I committed my work at the end of each one, which made it clear what was finished and what came next.

- Summarize what you learned about being the "lead architect" when collaborating with powerful AI tools.

I learned that the AI is fast at producing code but it does not own the design — I do. The bugs it helped write looked completely reasonable and still passed a casual read, which taught me that plausible is not the same as correct, and that I have to verify everything by running the tests and the app myself. My job as the lead architect was to make the real decisions (which constraints matter most, how conflicts should behave, whether to fix a bug or hide it) and to keep the system consistent, while using the AI to move quickly on the parts I had already decided. When I stayed in that driver's seat and gave clear, scoped instructions, the collaboration was strong; when I would have just accepted its output, that is exactly where the bugs would have slipped through.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

One moment I did not accept an AI suggestion as-is was when I had it add edge-case tests to my scheduler. Three of the new tests failed, and the AI offered a few ways to handle that: leave them red, mark them as expected-failures (xfail) so the suite would still look green, or actually fix the underlying bugs in pawpal_system.py. The xfail option would have made my test output look clean while the code was still wrong, so I rejected it and told the AI to fix the real bugs instead (a recurring task's next occurrence leaking into today's plan, conflicts only being checked between adjacent tasks, and completing a task twice queuing duplicate copies).

I verified the result instead of trusting it. I ran `python -m pytest` and confirmed all 13 tests passed, and I had the failing tests run against the old code first to prove they were actually catching the bugs and not just passing by luck. I did the same for the terminal demo by running `python main.py` and reading the output to check that the sorting, the 08:00 conflict warning, and the recurring respawns matched what I expected.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

I tested the behaviors the daily plan depends on most. For the basics, I checked that mark_complete() flips a task from incomplete to complete, and that adding a task to a pet grows its task list. For the smarter features, I tested that sort_by_time() orders tasks chronologically and pushes blank ("anytime") times to the end even when the hour is not zero-padded, and that detect_conflicts() catches same-time overlaps, partial overlaps, and non-adjacent overlaps while not flagging tasks that do not actually clash. For recurring tasks, I tested that a daily task respawns one day later, a weekly task seven days later, and a one-off task does not respawn at all, plus that completing the same task twice does not queue a duplicate. I also tested two plan edge cases: that a respawned future occurrence is not scheduled into today's plan, and that a task whose duration exactly equals the remaining time budget still fits.

These tests were important because they cover the exact spots where my logic was most likely to be wrong and three of them actually failed the first time and exposed real bugs. Testing the recurring and conflict logic mattered most, since those were the newest and most complicated parts of the scheduler.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I am fairly confident about 4 out of 5. All 13 tests pass, and the ones that matter most were verified to fail against the old code first, so I know they are really guarding behavior and not just passing by accident. I am not fully at 5 because a few edge cases are still untested. If I had more time, I would test malformed preferred_time strings like "8" or "25:00" (right now a bad time string can still raise an error instead of being handled cleanly), tasks that run past midnight (the end_time() calculation wraps around), and the Streamlit UI in app.py, which has no automated tests yet.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I am most satisfied with the "smarter scheduling" features working together (sorting, filtering, conflict detection, and recurring tasks) and with the fact that my test suite actually caught real bugs instead of just rubber-stamping the code. Being able to run main.py and watch the schedule, the conflict warning, and the future-dated respawns all behave correctly made it feel like the system really worked, not just that it compiled.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

The biggest improvement would be making build_schedule() actually honor preferred_time instead of just packing tasks back-to-back by priority, so the plan places tasks at the times the owner wanted and the conflict warnings line up with the real schedule. I would also add input validation (for Priority, frequency, and time strings) so bad input is rejected cleanly instead of crashing, handle tasks that cross midnight, and add automated tests for the Streamlit UI.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

The most important thing I learned is that I have to stay the decision-maker even when the AI is doing a lot of the typing. It could produce clean-looking code quickly, but it also wrote bugs that looked completely reasonable, so plausible is not the same as correct. Designing the classes myself, choosing which constraints mattered, and verifying everything by running the tests and the app is what actually made the project work.
