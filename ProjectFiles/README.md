# PawPal+ (Final Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors
---

## 🤖 New Feature: The Agentic Workflow
The system has evolved from a manual scheduler into an autonomous **PawPalAgent**. This agent manages the entire pet care lifecycle:

* **Profile Gathering:** Collects detailed owner lifestyles and pet-specific data (energy levels, special needs, age).
* **Intelligent Task Generation:** Automatically pulls from species-specific templates (Dog/Cat) and adjusts durations based on the pet's energy level.
* **Adaptive Scheduling:** Injects special-needs tasks (meds, therapy) and infers training stages (Puppy/Kitten vs. Adult).
* **Constraint-Based Optimization:** Fits generated tasks into the owner's specific "available time windows" while respecting priority and duration.
* **Interactive Chat Mode:** Allows users to query the schedule, check for conflicts, or export the final plan via a conversational interface.

---

---

## 📊 System Architecture
The diagram below illustrates the updated relationship between the core `pawpal_system`, the new `PawPalAgent` logic, and the Streamlit interface.

![PawPal+ AI Agent UML Diagram](./pawpal_ai_agent_uml.svg)

---

## Smarter Scheduling

This implementation now includes:

- priority-aware daily planning with time-based ordering
- combined day-and-priority task filtering
- generic task filtering by completion status and pet name
- lightweight conflict detection that returns warnings instead of crashing
- automatic follow-up task creation for recurring daily and weekly tasks

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

### Testing PawPal+
Running Tests
```bash
python -m pytest
```

<a href="/course_images/ai110/your_screenshot_name.png" target="_blank"><img src='Applied-AI-showsystem-project-AI110\diagrams\umldiagram.png' title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>.

