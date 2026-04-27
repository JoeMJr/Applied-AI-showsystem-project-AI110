from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional


@dataclass
class Task:
    title: str
    description: str
    duration_minutes: int
    priority: str
    frequency: str
    pet: Optional[Pet] = None
    scheduled_day: Optional[str] = None
    scheduled_time: Optional[str] = None
    is_completed: bool = False

    def get_details(self) -> str:
        pet_name = self.pet.name if self.pet else "unassigned pet"
        schedule = (
            f"{self.scheduled_day} at {self.scheduled_time}"
            if self.is_scheduled()
            else "not scheduled"
        )
        return (
            f"{self.title} ({self.priority}, {self.duration_minutes}m, {self.frequency}) "
            f"for {pet_name} — {schedule}"
        )

    def mark_completed(self) -> None:
        """Mark this task as completed."""
        self.is_completed = True

    def mark_incomplete(self) -> None:
        """Mark this task as incomplete."""
        self.is_completed = False

    def schedule(self, day: str, time: str) -> None:
        """Assign a scheduled day and time to this task."""
        self.scheduled_day = day
        self.scheduled_time = time

    def clear_schedule(self) -> None:
        """Clear the scheduled day and time for this task."""
        self.scheduled_day = None
        self.scheduled_time = None

    def is_scheduled(self) -> bool:
        """Return whether this task has both a day and time scheduled."""
        return bool(self.scheduled_day and self.scheduled_time)


@dataclass
class Pet:
    name: str
    species: str
    tasks: List[Task] = field(default_factory=list)

    def get_description(self) -> str:
        return f"{self.name} the {self.species}"

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet if it is not already added."""
        if task not in self.tasks:
            task.pet = self
            self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet and clear its pet assignment."""
        if task in self.tasks:
            self.tasks.remove(task)
            task.pet = None

    def get_tasks(self) -> List[Task]:
        """Return a copy of this pet's task list."""
        return list(self.tasks)

    def get_completed_tasks(self) -> List[Task]:
        """Return tasks for this pet that have been completed."""
        return [task for task in self.tasks if task.is_completed]

    def get_pending_tasks(self) -> List[Task]:
        """Return tasks for this pet that are still pending."""
        return [task for task in self.tasks if not task.is_completed]


@dataclass
class Owner:
    name: str
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's collection."""
        if pet not in self.pets:
            self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from this owner's collection."""
        if pet in self.pets:
            self.pets.remove(pet)

    def get_pets(self) -> List[Pet]:
        """Return a copy of this owner's pet list."""
        return list(self.pets)

    def find_pet(self, pet_name: str) -> Optional[Pet]:
        """Find a pet by name, ignoring case."""
        for pet in self.pets:
            if pet.name.lower() == pet_name.lower():
                return pet
        return None

    def add_task(self, task: Task, pet_name: str) -> None:
        """Add a task to a named pet owned by this owner."""
        pet = self.find_pet(pet_name)
        if pet is None:
            raise ValueError(f"No pet found with name '{pet_name}'")
        pet.add_task(task)

    def get_all_tasks(self) -> List[Task]:
        """Return all tasks across all pets owned by this owner."""
        tasks: List[Task] = []
        for pet in self.pets:
            tasks.extend(pet.get_tasks())
        return tasks

    def get_all_pending_tasks(self) -> List[Task]:
        """Return all tasks across pets that are not completed."""
        return [task for task in self.get_all_tasks() if not task.is_completed]

    def get_all_completed_tasks(self) -> List[Task]:
        """Return all tasks across pets that have been completed."""
        return [task for task in self.get_all_tasks() if task.is_completed]

    def get_tasks_for_pet(self, pet_name: str) -> List[Task]:
        """Return the task list for a specific pet by name."""
        pet = self.find_pet(pet_name)
        return pet.get_tasks() if pet else []


class Scheduler:
    PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

    def __init__(self, owner: Owner) -> None:
        """Create a scheduler for a given owner."""
        self.owner = owner

    def get_all_tasks(self) -> List[Task]:
        """Return all tasks visible to this scheduler."""
        return self.owner.get_all_tasks()

    def get_tasks_by_priority(self, priority: str) -> List[Task]:
        """Return tasks filtered by priority."""
        return [task for task in self.get_all_tasks() if task.priority.lower() == priority.lower()]

    def get_tasks_by_day(self, day: str) -> List[Task]:
        """Return tasks scheduled for a specific day."""
        return [task for task in self.get_all_tasks() if task.scheduled_day and task.scheduled_day.lower() == day.lower()]

    def get_tasks_by_day_and_priority(self, day: str, priority: str) -> List[Task]:
        """Return tasks for a specific day filtered by priority."""
        return [
            task
            for task in self.get_tasks_by_day(day)
            if task.priority.lower() == priority.lower()
        ]

    def get_tasks_for_pet(self, pet_name: str) -> List[Task]:
        """Return all tasks for a specific pet."""
        return self.owner.get_tasks_for_pet(pet_name)

    def filter_tasks(self, completed: Optional[bool] = None, pet_name: Optional[str] = None) -> List[Task]:
        """Filter tasks by completion status and/or pet name."""
        tasks = self.get_all_tasks()
        if completed is not None:
            tasks = [task for task in tasks if task.is_completed == completed]
        if pet_name is not None:
            tasks = [
                task
                for task in tasks
                if task.pet and task.pet.name.lower() == pet_name.lower()
            ]
        return tasks

    def check_conflict(self, task: Task) -> Optional[str]:
        """Detect scheduling conflicts and return a warning message.

        A conflict occurs when another task is already scheduled for the same
        day and time. This method is lightweight: it does not raise an error,
        it returns a descriptive warning string for the caller to handle.
        """
        if not task.scheduled_day or not task.scheduled_time:
            return None

        conflicts = [
            other
            for other in self.get_all_tasks()
            if other is not task
            and other.scheduled_day
            and other.scheduled_time
            and other.scheduled_day.lower() == task.scheduled_day.lower()
            and other.scheduled_time == task.scheduled_time
        ]

        if not conflicts:
            return None

        task_titles = ", ".join([task.title] + [other.title for other in conflicts])
        pet_names = ", ".join(
            other.pet.name if other.pet else "unknown"
            for other in [task] + conflicts
        )
        return (
            f"Warning: scheduling conflict on {task.scheduled_day} at {task.scheduled_time} "
            f"for tasks [{task_titles}] assigned to pets [{pet_names}]"
        )

    def _get_next_occurrence_day(self, frequency: str) -> str:
        """Return the weekday name for the next occurrence based on frequency.

        For daily tasks, this is today + 1 day. For weekly tasks, this is
        today + 7 days.
        """
        if frequency.lower() == "daily":
            next_date = date.today() + timedelta(days=1)
        elif frequency.lower() == "weekly":
            next_date = date.today() + timedelta(days=7)
        else:
            raise ValueError(f"Unsupported frequency '{frequency}' for recurrence")
        return next_date.strftime("%A")

    def _create_followup_task(self, task: Task) -> Optional[Task]:
        """Create a new follow-up task for recurring daily or weekly tasks.

        The new task copies title, description, duration, priority, and frequency
        from the completed task. It also preserves the same scheduled time,
        but updates the scheduled day to the next occurrence.
        """
        if task.frequency.lower() not in {"daily", "weekly"}:
            return None
        if not task.scheduled_time or not task.pet:
            return None

        next_day = self._get_next_occurrence_day(task.frequency)
        followup = Task(
            title=task.title,
            description=task.description,
            duration_minutes=task.duration_minutes,
            priority=task.priority,
            frequency=task.frequency,
            pet=task.pet,
        )
        followup.schedule(next_day, task.scheduled_time)
        return followup

    def schedule_task(self, task: Task, day: str, time: str) -> Optional[str]:
        """Schedule a task and return a conflict warning if one exists."""
        task.schedule(day, time)
        return self.check_conflict(task)

    def unschedule_task(self, task: Task) -> None:
        """Remove scheduling information from a task."""
        task.clear_schedule()

    def complete_task(self, task: Task) -> Optional[Task]:
        """Mark a task as complete and create the next occurrence for recurring tasks."""
        task.mark_completed()
        followup_task = self._create_followup_task(task)
        if followup_task and task.pet:
            task.pet.add_task(followup_task)
        return followup_task

    def get_daily_plan(self, day: str) -> List[Task]:
        """Return the day's scheduled tasks, sorted by priority and time."""
        tasks = self.get_tasks_by_day(day)
        return sorted(
            tasks,
            key=lambda task: (
                self.PRIORITY_ORDER.get(task.priority.lower(), 3),
                int(task.scheduled_time[:2]) * 60 + int(task.scheduled_time[3:])
                if task.scheduled_time
                else 24 * 60,
            ),
        )

    def get_pending_tasks(self) -> List[Task]:
        """Return all incomplete tasks across all pets."""
        return [task for task in self.get_all_tasks() if not task.is_completed]

    def _sort_key(self, task: Task) -> tuple:
        """Return a sort key for tasks based on priority and scheduled time."""
        priority_rank = self.PRIORITY_ORDER.get(task.priority.lower(), 3)
        time_key = task.scheduled_time or ""
        return (priority_rank, time_key)
