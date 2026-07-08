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

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

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
