# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
I was going to have an Owner that has a Pet
Owner will have a name
This Pet will have a Name and Species
These Owners will have Tasks for their Pet
Tasks will have a title, duration and priority
A Schedule wil consist of Tasks with a time (Day of the week, and Time of Day) associated to it
- What classes did you include, and what responsibilities did you assign to each?
Classes: Owner, Pet, Task, and Schedule
Responsiblities above

**b. Design changes**

- Did your design change during implementation?
Yes
- If yes, describe at least one change and why you made it.
I was moving times from the schedule to the idividual tasks
Moving the time to tasks from scheduler 
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?

- How did you decide which constraints mattered most?


**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
Keeping Days as Strings in Scheduler while using lambda key to sort
- Why is that tradeoff reasonable for this scenario?
It was a lightweight and fast implementation of 

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
It was a big help when refactoring code and adding comments to the code
- What kinds of prompts or questions were most helpful?
Being straightforward and direct with prompts 

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
It was when I was implementing the Owner class to the main app.py
- How did you evaluate or verify what the AI suggested?
I read the code present that he changed and saw that it ignored an important part of the code that it should have changed

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
Empty schedule case, Sorting edge cases, Recurring task edge cases, and Conflict detection edge cases
- Why were these tests important?
Since these are core features and common pit falls people would have when using the app
**b. Confidence**

- How confident are you that your scheduler works correctly?
4/5
- What edge cases would you test next if you had more time?
Tests around Ownership / task assignment edge cases due to how owners is designed
---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
The classes and the methods they hold

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
I would have went back to polish the app since I didn't give myself a good amount of time for this
**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
Being clear with how I structure the system. I 
