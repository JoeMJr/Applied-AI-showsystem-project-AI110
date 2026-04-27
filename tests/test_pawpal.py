from datetime import date, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task


def test_task_completion_marks_task_as_completed() -> None:
    pet = Pet(name="Mochi", species="dog")
    task = Task(
        title="Morning walk",
        description="Walk the dog around the block.",
        duration_minutes=30,
        priority="high",
        frequency="daily",
        pet=pet,
    )

    assert task.is_completed is False
    task.mark_completed()
    assert task.is_completed is True


def test_pet_add_task_increases_task_count() -> None:
    pet = Pet(name="Luna", species="cat")
    task = Task(
        title="Feed dinner",
        description="Serve evening meal to the cat.",
        duration_minutes=10,
        priority="medium",
        frequency="daily",
        pet=pet,
    )

    assert len(pet.tasks) == 0
    pet.add_task(task)
    assert len(pet.tasks) == 1
    assert pet.tasks[0] is task
    assert task.pet is pet


def test_scheduler_daily_plan_sorts_by_priority_and_time() -> None:
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)

    task1 = Task(
        title="Late walk",
        description="Evening walk.",
        duration_minutes=20,
        priority="low",
        frequency="daily",
        pet=pet,
    )
    task2 = Task(
        title="Morning walk",
        description="Walk the dog before work.",
        duration_minutes=30,
        priority="high",
        frequency="daily",
        pet=pet,
    )
    task3 = Task(
        title="Midday check",
        description="Check on the pet.",
        duration_minutes=10,
        priority="high",
        frequency="daily",
        pet=pet,
    )

    owner.add_task(task1, pet_name="Mochi")
    owner.add_task(task2, pet_name="Mochi")
    owner.add_task(task3, pet_name="Mochi")

    task1.schedule(day="Monday", time="20:00")
    task2.schedule(day="Monday", time="08:00")
    task3.schedule(day="Monday", time="12:00")

    scheduler = Scheduler(owner=owner)
    ordered_tasks = scheduler.get_daily_plan("Monday")

    assert ordered_tasks[0] is task2
    assert ordered_tasks[1] is task3
    assert ordered_tasks[2] is task1


def test_scheduler_filters_tasks_by_day_and_priority() -> None:
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)

    task1 = Task(
        title="Walk",
        description="Walk the dog.",
        duration_minutes=30,
        priority="high",
        frequency="daily",
        pet=pet,
    )
    task2 = Task(
        title="Feed",
        description="Feed the dog.",
        duration_minutes=10,
        priority="medium",
        frequency="daily",
        pet=pet,
    )

    owner.add_task(task1, pet_name="Mochi")
    owner.add_task(task2, pet_name="Mochi")

    task1.schedule(day="Tuesday", time="09:00")
    task2.schedule(day="Tuesday", time="09:30")

    scheduler = Scheduler(owner=owner)
    filtered = scheduler.get_tasks_by_day_and_priority("Tuesday", "high")

    assert filtered == [task1]


def test_scheduler_filters_tasks_by_completion_status() -> None:
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)

    task1 = Task(
        title="Walk",
        description="Walk the dog.",
        duration_minutes=30,
        priority="high",
        frequency="daily",
        pet=pet,
    )
    task2 = Task(
        title="Feed",
        description="Feed the dog.",
        duration_minutes=10,
        priority="medium",
        frequency="daily",
        pet=pet,
    )

    owner.add_task(task1, pet_name="Mochi")
    owner.add_task(task2, pet_name="Mochi")

    task1.mark_completed()

    scheduler = Scheduler(owner=owner)
    completed_tasks = scheduler.filter_tasks(completed=True)
    pending_tasks = scheduler.filter_tasks(completed=False)

    assert completed_tasks == [task1]
    assert pending_tasks == [task2]


def test_scheduler_filters_tasks_by_pet_name() -> None:
    owner = Owner(name="Jordan")
    dog = Pet(name="Mochi", species="dog")
    cat = Pet(name="Luna", species="cat")
    owner.add_pet(dog)
    owner.add_pet(cat)

    task1 = Task(
        title="Walk",
        description="Walk the dog.",
        duration_minutes=30,
        priority="high",
        frequency="daily",
        pet=dog,
    )
    task2 = Task(
        title="Feed",
        description="Feed the cat.",
        duration_minutes=10,
        priority="medium",
        frequency="daily",
        pet=cat,
    )

    owner.add_task(task1, pet_name="Mochi")
    owner.add_task(task2, pet_name="Luna")

    scheduler = Scheduler(owner=owner)
    dog_tasks = scheduler.filter_tasks(pet_name="Mochi")
    cat_tasks = scheduler.filter_tasks(pet_name="luna")

    assert dog_tasks == [task1]
    assert cat_tasks == [task2]


def test_scheduler_detects_conflicting_tasks_at_same_time() -> None:
    owner = Owner(name="Jordan")
    dog = Pet(name="Mochi", species="dog")
    cat = Pet(name="Luna", species="cat")
    owner.add_pet(dog)
    owner.add_pet(cat)

    task1 = Task(
        title="Morning walk",
        description="Walk the dog.",
        duration_minutes=30,
        priority="high",
        frequency="daily",
        pet=dog,
    )
    task2 = Task(
        title="Feed",
        description="Feed the cat.",
        duration_minutes=10,
        priority="medium",
        frequency="daily",
        pet=cat,
    )

    owner.add_task(task1, pet_name="Mochi")
    owner.add_task(task2, pet_name="Luna")

    scheduler = Scheduler(owner=owner)
    warning1 = scheduler.schedule_task(task1, day="Monday", time="08:00")
    warning2 = scheduler.schedule_task(task2, day="Monday", time="08:00")

    assert warning1 is None
    assert warning2 is not None
    assert "conflict" in warning2.lower()
    assert "Morning walk" in warning2
    assert "Feed" in warning2


def test_scheduler_creates_next_daily_occurrence_when_task_completed() -> None:
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)

    task = Task(
        title="Morning walk",
        description="Walk the dog.",
        duration_minutes=30,
        priority="high",
        frequency="daily",
        pet=pet,
    )
    owner.add_task(task, pet_name="Mochi")
    task.schedule(day="Monday", time="08:00")

    scheduler = Scheduler(owner=owner)
    followup = scheduler.complete_task(task)

    expected_day = (date.today() + timedelta(days=1)).strftime("%A")
    assert followup is not None
    assert followup.scheduled_day == expected_day
    assert followup.scheduled_time == "08:00"
    assert followup.frequency == "daily"
    assert followup.pet is pet


def test_scheduler_creates_next_weekly_occurrence_when_task_completed() -> None:
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)

    task = Task(
        title="Brush fur",
        description="Brush the dog.",
        duration_minutes=15,
        priority="low",
        frequency="weekly",
        pet=pet,
    )
    owner.add_task(task, pet_name="Mochi")
    task.schedule(day="Monday", time="20:00")

    scheduler = Scheduler(owner=owner)
    followup = scheduler.complete_task(task)

    expected_day = (date.today() + timedelta(days=7)).strftime("%A")
    assert followup is not None
    assert followup.scheduled_day == expected_day
    assert followup.scheduled_time == "20:00"
    assert followup.frequency == "weekly"
    assert followup.pet is pet


def test_empty_schedule_returns_no_tasks() -> None:
    owner = Owner(name="Jordan")
    scheduler = Scheduler(owner=owner)

    assert scheduler.get_all_tasks() == []
    assert scheduler.get_daily_plan("Monday") == []
    assert scheduler.filter_tasks(completed=False) == []


def test_scheduler_daily_plan_same_priority_orders_by_time() -> None:
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)

    task_early = Task(
        title="Early walk",
        description="Walk the dog early.",
        duration_minutes=20,
        priority="high",
        frequency="daily",
        pet=pet,
    )
    task_late = Task(
        title="Late walk",
        description="Walk the dog later.",
        duration_minutes=20,
        priority="high",
        frequency="daily",
        pet=pet,
    )

    owner.add_task(task_early, pet_name="Mochi")
    owner.add_task(task_late, pet_name="Mochi")

    task_early.schedule(day="Monday", time="08:00")
    task_late.schedule(day="Monday", time="18:00")

    scheduler = Scheduler(owner=owner)
    ordered_tasks = scheduler.get_daily_plan("Monday")

    assert ordered_tasks == [task_early, task_late]


def test_scheduler_daily_plan_same_time_orders_by_priority() -> None:
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)

    high_priority = Task(
        title="High priority",
        description="Important task.",
        duration_minutes=15,
        priority="high",
        frequency="daily",
        pet=pet,
    )
    low_priority = Task(
        title="Low priority",
        description="Less important task.",
        duration_minutes=15,
        priority="low",
        frequency="daily",
        pet=pet,
    )

    owner.add_task(high_priority, pet_name="Mochi")
    owner.add_task(low_priority, pet_name="Mochi")

    high_priority.schedule(day="Monday", time="09:00")
    low_priority.schedule(day="Monday", time="09:00")

    scheduler = Scheduler(owner=owner)
    ordered_tasks = scheduler.get_daily_plan("Monday")

    assert ordered_tasks == [high_priority, low_priority]


def test_scheduler_daily_plan_unknown_priority_sorts_last() -> None:
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)

    normal_task = Task(
        title="Normal task",
        description="Regular priority.",
        duration_minutes=15,
        priority="low",
        frequency="daily",
        pet=pet,
    )
    unknown_task = Task(
        title="Unknown task",
        description="Unknown priority.",
        duration_minutes=15,
        priority="urgent",
        frequency="daily",
        pet=pet,
    )

    owner.add_task(normal_task, pet_name="Mochi")
    owner.add_task(unknown_task, pet_name="Mochi")

    normal_task.schedule(day="Monday", time="09:00")
    unknown_task.schedule(day="Monday", time="09:00")

    scheduler = Scheduler(owner=owner)
    ordered_tasks = scheduler.get_daily_plan("Monday")

    assert ordered_tasks == [normal_task, unknown_task]


def test_complete_recurring_task_without_time_does_not_create_followup() -> None:
    pet = Pet(name="Mochi", species="dog")
    task = Task(
        title="Morning walk",
        description="Walk the dog.",
        duration_minutes=30,
        priority="high",
        frequency="daily",
        pet=pet,
    )

    owner = Owner(name="Jordan")
    scheduler = Scheduler(owner=owner)

    followup = scheduler.complete_task(task)

    assert followup is None


def test_complete_recurring_task_without_pet_does_not_create_followup() -> None:
    task = Task(
        title="Morning walk",
        description="Walk the dog.",
        duration_minutes=30,
        priority="high",
        frequency="daily",
    )
    task.schedule(day="Monday", time="08:00")

    owner = Owner(name="Jordan")
    scheduler = Scheduler(owner=owner)

    followup = scheduler.complete_task(task)

    assert followup is None


def test_complete_non_recurring_task_does_not_create_followup() -> None:
    pet = Pet(name="Mochi", species="dog")
    owner = Owner(name="Jordan")
    owner.add_pet(pet)

    task = Task(
        title="One-time groom",
        description="Groom the dog once.",
        duration_minutes=30,
        priority="medium",
        frequency="one-time",
        pet=pet,
    )
    owner.add_task(task, pet_name="Mochi")
    task.schedule(day="Monday", time="10:00")

    scheduler = Scheduler(owner=owner)
    followup = scheduler.complete_task(task)

    assert followup is None


def test_check_conflict_does_not_report_conflict_for_same_task() -> None:
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)

    task = Task(
        title="Morning walk",
        description="Walk the dog.",
        duration_minutes=30,
        priority="high",
        frequency="daily",
        pet=pet,
    )
    owner.add_task(task, pet_name="Mochi")
    task.schedule(day="Monday", time="08:00")

    scheduler = Scheduler(owner=owner)
    warning = scheduler.check_conflict(task)

    assert warning is None


def test_unscheduled_task_never_reports_conflict() -> None:
    owner = Owner(name="Jordan")
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)

    scheduled_task = Task(
        title="Morning walk",
        description="Walk the dog.",
        duration_minutes=30,
        priority="high",
        frequency="daily",
        pet=pet,
    )
    owner.add_task(scheduled_task, pet_name="Mochi")
    scheduled_task.schedule(day="Monday", time="08:00")

    unscheduled_task = Task(
        title="Unscheduled play",
        description="Play with the dog later.",
        duration_minutes=20,
        priority="medium",
        frequency="daily",
        pet=pet,
    )
    owner.add_task(unscheduled_task, pet_name="Mochi")

    scheduler = Scheduler(owner=owner)
    warning = scheduler.check_conflict(unscheduled_task)

    assert warning is None
