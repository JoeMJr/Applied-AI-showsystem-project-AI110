"""
Tests for ai_agent_logic.py — PawPal+ AI Agent Features

Covers:
- OwnerProfile / PetProfile data models
- AgentSession state management
- Task template selection (_get_task_templates)
- Energy-level adjustments (_adjust_for_energy_level)
- Special-needs task injection (_adjust_for_special_needs)
- Training-stage inference (_determine_training_stage)
- Full generate_tasks() pipeline
- Full optimize_schedule() pipeline
- Schedule export to JSON
- Conversation-mode command handling
- Edge cases: unknown species, over-capacity warnings, missing pet/time
"""

import json
import os
import tempfile

import pytest

from ai_agent_logic import AgentSession,OwnerProfile,PawPalAgent,PetProfile,TASK_TEMPLATES



# ============================================================================
# HELPERS — reusable profile factories
# ============================================================================

def make_owner_profile(
    name="Jordan",
    work_schedule="9-5",
    windows=(("06:00", "07:00"), ("17:00", "19:00")),
    total_minutes=180,
    lifestyle="none",
    tech_comfort="intermediate",
) -> OwnerProfile:
    return OwnerProfile(
        name=name,
        work_schedule=work_schedule,
        available_time_windows=list(windows),
        total_daily_minutes=total_minutes,
        lifestyle_constraints=lifestyle,
        tech_comfort=tech_comfort,
    )


def make_pet_profile(
    name="Buddy",
    species="dog",
    age=3,
    energy_level="medium",
    health_status="healthy",
    special_needs=None,
    training_stage="adult",
) -> PetProfile:
    return PetProfile(
        name=name,
        species=species,
        age=age,
        energy_level=energy_level,
        health_status=health_status,
        special_needs=special_needs or [],
        training_stage=training_stage,
    )


def make_agent_with_profiles(pet_profile: PetProfile, total_minutes=180) -> PawPalAgent:
    """Return a PawPalAgent pre-loaded with one owner and one pet profile."""
    agent = PawPalAgent()
    agent.session.owner_profile = make_owner_profile(total_minutes=total_minutes)
    agent.session.pet_profiles = [pet_profile]
    return agent


# ============================================================================
# OWNER PROFILE
# ============================================================================

def test_owner_profile_summary_contains_name() -> None:
    profile = make_owner_profile(name="Alex")
    assert "Alex" in profile.summary()


def test_owner_profile_summary_contains_work_schedule() -> None:
    profile = make_owner_profile(work_schedule="variable")
    assert "variable" in profile.summary()


def test_owner_profile_summary_contains_time_windows() -> None:
    profile = make_owner_profile(windows=(("08:00", "09:00"),))
    assert "08:00" in profile.summary()
    assert "09:00" in profile.summary()


def test_owner_profile_summary_contains_total_minutes() -> None:
    profile = make_owner_profile(total_minutes=90)
    assert "90" in profile.summary()


# ============================================================================
# PET PROFILE
# ============================================================================

def test_pet_profile_summary_contains_name_and_species() -> None:
    profile = make_pet_profile(name="Luna", species="cat")
    summary = profile.summary()
    assert "Luna" in summary
    assert "cat" in summary


def test_pet_profile_summary_lists_special_needs() -> None:
    profile = make_pet_profile(special_needs=["medication", "anxiety"])
    summary = profile.summary()
    assert "medication" in summary
    assert "anxiety" in summary


def test_pet_profile_summary_shows_none_when_no_special_needs() -> None:
    profile = make_pet_profile(special_needs=[])
    assert "None" in profile.summary()


def test_pet_profile_summary_contains_energy_level() -> None:
    profile = make_pet_profile(energy_level="high")
    assert "high" in profile.summary()


# ============================================================================
# AGENT SESSION
# ============================================================================

def test_agent_session_starts_empty() -> None:
    session = AgentSession()
    assert session.owner_profile is None
    assert session.pet_profiles == []
    assert session.generated_tasks == []
    assert session.conversation_history == []


def test_agent_session_add_message_appends_to_history() -> None:
    session = AgentSession()
    session.add_message("agent", "Hello!")
    assert len(session.conversation_history) == 1
    assert session.conversation_history[0] == {"role": "agent", "content": "Hello!"}


def test_agent_session_add_multiple_messages_preserves_order() -> None:
    session = AgentSession()
    session.add_message("user", "First")
    session.add_message("agent", "Second")
    assert session.conversation_history[0]["content"] == "First"
    assert session.conversation_history[1]["content"] == "Second"


# ============================================================================
# TASK TEMPLATE SELECTION
# ============================================================================

def test_get_task_templates_returns_dog_adult_templates() -> None:
    agent = PawPalAgent()
    pet = make_pet_profile(species="dog", training_stage="adult")
    templates = agent._get_task_templates(pet)
    titles = [t["title"] for t in templates]
    assert "Morning walk" in titles
    assert "Morning feeding" in titles


def test_get_task_templates_returns_dog_puppy_templates() -> None:
    agent = PawPalAgent()
    pet = make_pet_profile(species="dog", age=1, training_stage="puppy")
    templates = agent._get_task_templates(pet)
    titles = [t["title"] for t in templates]
    assert "Potty break (midday)" in titles


def test_get_task_templates_returns_dog_senior_templates() -> None:
    agent = PawPalAgent()
    pet = make_pet_profile(species="dog", age=12, training_stage="senior")
    templates = agent._get_task_templates(pet)
    titles = [t["title"] for t in templates]
    assert "Health monitoring" in titles
    assert "Morning walk (gentle)" in titles


def test_get_task_templates_returns_cat_adult_templates() -> None:
    agent = PawPalAgent()
    pet = make_pet_profile(species="cat", training_stage="adult")
    templates = agent._get_task_templates(pet)
    titles = [t["title"] for t in templates]
    assert "Litter box check & clean" in titles


def test_get_task_templates_returns_cat_kitten_templates() -> None:
    agent = PawPalAgent()
    pet = make_pet_profile(species="cat", age=0, training_stage="puppy")
    templates = agent._get_task_templates(pet)
    titles = [t["title"] for t in templates]
    assert "Feeding (lunch)" in titles


def test_get_task_templates_returns_other_species_default() -> None:
    agent = PawPalAgent()
    pet = make_pet_profile(species="rabbit", training_stage="adult")
    templates = agent._get_task_templates(pet)
    titles = [t["title"] for t in templates]
    assert "Enclosure/habitat check" in titles


def test_get_task_templates_unknown_species_falls_back_to_other() -> None:
    agent = PawPalAgent()
    pet = make_pet_profile(species="lizard", training_stage="adult")
    templates = agent._get_task_templates(pet)
    # Should still return something rather than raising
    assert len(templates) > 0


# ============================================================================
# ENERGY-LEVEL ADJUSTMENTS
# ============================================================================

def test_high_energy_increases_walk_duration() -> None:
    agent = PawPalAgent()
    base = [{"title": "Morning walk", "duration_minutes": 30, "priority": "high", "frequency": "daily"}]
    adjusted = agent._adjust_for_energy_level(base, "high")
    assert adjusted[0]["duration_minutes"] > 30


def test_low_energy_decreases_walk_duration() -> None:
    agent = PawPalAgent()
    base = [{"title": "Morning walk", "duration_minutes": 30, "priority": "high", "frequency": "daily"}]
    adjusted = agent._adjust_for_energy_level(base, "low")
    assert adjusted[0]["duration_minutes"] < 30


def test_medium_energy_does_not_change_walk_duration() -> None:
    agent = PawPalAgent()
    base = [{"title": "Morning walk", "duration_minutes": 30, "priority": "high", "frequency": "daily"}]
    adjusted = agent._adjust_for_energy_level(base, "medium")
    assert adjusted[0]["duration_minutes"] == 30


def test_high_energy_increases_play_duration() -> None:
    agent = PawPalAgent()
    base = [{"title": "Afternoon play", "duration_minutes": 20, "priority": "medium", "frequency": "daily"}]
    adjusted = agent._adjust_for_energy_level(base, "high")
    assert adjusted[0]["duration_minutes"] > 20


def test_energy_adjustment_does_not_modify_non_walk_play_tasks() -> None:
    agent = PawPalAgent()
    base = [{"title": "Morning feeding", "duration_minutes": 10, "priority": "high", "frequency": "daily"}]
    adjusted_high = agent._adjust_for_energy_level(base, "high")
    adjusted_low = agent._adjust_for_energy_level(base, "low")
    assert adjusted_high[0]["duration_minutes"] == 10
    assert adjusted_low[0]["duration_minutes"] == 10


def test_energy_adjustment_does_not_mutate_original_templates() -> None:
    agent = PawPalAgent()
    original_duration = 30
    base = [{"title": "Morning walk", "duration_minutes": original_duration, "priority": "high", "frequency": "daily"}]
    agent._adjust_for_energy_level(base, "high")
    assert base[0]["duration_minutes"] == original_duration


# ============================================================================
# SPECIAL-NEEDS TASK INJECTION
# ============================================================================

def test_medication_need_adds_medication_task() -> None:
    agent = PawPalAgent()
    result = agent._adjust_for_special_needs([], ["medication"])
    titles = [t["title"] for t in result]
    assert "Medication administration" in titles


def test_training_need_adds_behavior_training_task() -> None:
    agent = PawPalAgent()
    result = agent._adjust_for_special_needs([], ["training"])
    titles = [t["title"] for t in result]
    assert "Behavior training" in titles


def test_anxiety_need_adds_calming_routine_task() -> None:
    agent = PawPalAgent()
    result = agent._adjust_for_special_needs([], ["anxiety"])
    titles = [t["title"] for t in result]
    assert "Calming routine" in titles


def test_medication_task_has_high_priority() -> None:
    agent = PawPalAgent()
    result = agent._adjust_for_special_needs([], ["medication"])
    med_task = next(t for t in result if t["title"] == "Medication administration")
    assert med_task["priority"] == "high"


def test_medication_task_is_daily() -> None:
    agent = PawPalAgent()
    result = agent._adjust_for_special_needs([], ["medication"])
    med_task = next(t for t in result if t["title"] == "Medication administration")
    assert med_task["frequency"] == "daily"


def test_no_special_needs_returns_templates_unchanged() -> None:
    agent = PawPalAgent()
    base = [{"title": "Morning walk", "duration_minutes": 30, "priority": "high", "frequency": "daily"}]
    result = agent._adjust_for_special_needs(base, [])
    assert result == base


def test_multiple_special_needs_adds_all_corresponding_tasks() -> None:
    agent = PawPalAgent()
    result = agent._adjust_for_special_needs([], ["medication", "training", "anxiety"])
    titles = [t["title"] for t in result]
    assert "Medication administration" in titles
    assert "Behavior training" in titles
    assert "Calming routine" in titles


# ============================================================================
# TRAINING STAGE INFERENCE
# ============================================================================

def test_determine_training_stage_puppy_for_young_dog() -> None:
    agent = PawPalAgent()
    assert agent._determine_training_stage("dog", age=1, health_status="healthy") == "puppy"


def test_determine_training_stage_adult_for_middle_aged_dog() -> None:
    agent = PawPalAgent()
    assert agent._determine_training_stage("dog", age=5, health_status="healthy") == "adult"


def test_determine_training_stage_senior_for_old_dog() -> None:
    agent = PawPalAgent()
    assert agent._determine_training_stage("dog", age=11, health_status="healthy") == "senior"


def test_determine_training_stage_senior_overrides_age_when_health_is_senior() -> None:
    agent = PawPalAgent()
    # A 3-year-old dog with senior health status should be treated as senior
    assert agent._determine_training_stage("dog", age=3, health_status="senior") == "senior"


def test_determine_training_stage_boundary_age_2_is_adult() -> None:
    agent = PawPalAgent()
    assert agent._determine_training_stage("dog", age=2, health_status="healthy") == "adult"


def test_determine_training_stage_age_0_is_puppy() -> None:
    agent = PawPalAgent()
    assert agent._determine_training_stage("cat", age=0, health_status="healthy") == "puppy"


# ============================================================================
# FULL GENERATE_TASKS PIPELINE
# ============================================================================

def test_generate_tasks_produces_tasks_for_dog() -> None:
    agent = make_agent_with_profiles(make_pet_profile(species="dog", training_stage="adult"))
    tasks = agent.generate_tasks()
    assert len(tasks) > 0


def test_generate_tasks_stores_tasks_in_session() -> None:
    agent = make_agent_with_profiles(make_pet_profile(species="dog", training_stage="adult"))
    agent.generate_tasks()
    assert len(agent.session.generated_tasks) > 0


def test_generate_tasks_all_tasks_have_required_fields() -> None:
    agent = make_agent_with_profiles(make_pet_profile(species="dog", training_stage="adult"))
    tasks = agent.generate_tasks()
    for task in tasks:
        assert task.title
        assert task.duration_minutes > 0
        assert task.priority in ("high", "medium", "low")
        assert task.frequency


def test_generate_tasks_includes_medication_task_when_needed() -> None:
    pet = make_pet_profile(species="dog", training_stage="adult", special_needs=["medication"])
    agent = make_agent_with_profiles(pet)
    tasks = agent.generate_tasks()
    titles = [t.title for t in tasks]
    assert "Medication administration" in titles


def test_generate_tasks_high_energy_walk_is_longer_than_medium() -> None:
    pet_high = make_pet_profile(species="dog", training_stage="adult", energy_level="high")
    pet_med = make_pet_profile(species="dog", training_stage="adult", energy_level="medium")

    agent_high = make_agent_with_profiles(pet_high)
    agent_med = make_agent_with_profiles(pet_med)

    tasks_high = agent_high.generate_tasks()
    tasks_med = agent_med.generate_tasks()

    def walk_duration(tasks):
        walk = next((t for t in tasks if "walk" in t.title.lower()), None)
        return walk.duration_minutes if walk else 0

    assert walk_duration(tasks_high) > walk_duration(tasks_med)


def test_generate_tasks_for_multiple_pets_produces_tasks_for_each() -> None:
    agent = PawPalAgent()
    agent.session.owner_profile = make_owner_profile(total_minutes=300)
    agent.session.pet_profiles = [
        make_pet_profile(name="Buddy", species="dog", training_stage="adult"),
        make_pet_profile(name="Luna", species="cat", training_stage="adult"),
    ]
    tasks = agent.generate_tasks()
    descriptions = " ".join(t.description for t in tasks)
    assert "Buddy" in descriptions
    assert "Luna" in descriptions


def test_generate_tasks_for_cat_includes_litter_box() -> None:
    agent = make_agent_with_profiles(make_pet_profile(species="cat", training_stage="adult"))
    tasks = agent.generate_tasks()
    titles = [t.title for t in tasks]
    assert any("litter" in title.lower() for title in titles)


def test_generate_tasks_for_other_species_does_not_raise() -> None:
    agent = make_agent_with_profiles(make_pet_profile(species="bird", training_stage="adult"))
    tasks = agent.generate_tasks()
    assert len(tasks) > 0


# ============================================================================
# FULL OPTIMIZE_SCHEDULE PIPELINE
# ============================================================================

def _run_full_agent(pet_profile: PetProfile, total_minutes=300) -> PawPalAgent:
    """Helper: generate tasks then optimize schedule."""
    agent = make_agent_with_profiles(pet_profile, total_minutes=total_minutes)
    agent.generate_tasks()
    agent.optimize_schedule()
    return agent


def test_optimize_schedule_creates_scheduler_in_session() -> None:
    agent = _run_full_agent(make_pet_profile(species="dog", training_stage="adult"))
    assert agent.session.scheduler is not None


def test_optimize_schedule_creates_owner_system_in_session() -> None:
    agent = _run_full_agent(make_pet_profile(species="dog", training_stage="adult"))
    assert agent.session.owner_system is not None


def test_optimize_schedule_assigns_tasks_to_monday() -> None:
    agent = _run_full_agent(make_pet_profile(species="dog", training_stage="adult"))
    monday_plan = agent.session.scheduler.get_daily_plan("Monday")
    assert len(monday_plan) > 0


def test_optimize_schedule_assigns_tasks_across_all_seven_days() -> None:
    agent = _run_full_agent(make_pet_profile(species="dog", training_stage="adult"))
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for day in days:
        assert len(agent.session.scheduler.get_daily_plan(day)) > 0, f"No tasks on {day}"


def test_optimize_schedule_all_scheduled_tasks_have_a_time() -> None:
    agent = _run_full_agent(make_pet_profile(species="dog", training_stage="adult"))
    monday_plan = agent.session.scheduler.get_daily_plan("Monday")
    for task in monday_plan:
        assert task.scheduled_time is not None


def test_optimize_schedule_adds_pet_to_owner_system() -> None:
    pet = make_pet_profile(name="Mochi", species="dog", training_stage="adult")
    agent = _run_full_agent(pet)
    pet_names = [p.name for p in agent.session.owner_system.get_pets()]
    assert "Mochi" in pet_names


def test_optimize_schedule_respects_owner_time_windows() -> None:
    """All tasks must be scheduled within or at the start of a declared time window."""
    windows = (("06:00", "07:00"), ("12:00", "13:00"), ("17:00", "19:00"))
    window_starts = {w[0] for w in windows}

    agent = PawPalAgent()
    agent.session.owner_profile = make_owner_profile(windows=windows, total_minutes=180)
    agent.session.pet_profiles = [make_pet_profile(species="dog", training_stage="adult")]
    agent.generate_tasks()
    agent.optimize_schedule()

    monday = agent.session.scheduler.get_daily_plan("Monday")
    for task in monday:
        assert task.scheduled_time in window_starts, (
            f"Task '{task.title}' scheduled at {task.scheduled_time}, "
            f"which is not a declared window start"
        )


# ============================================================================
# EXPORT TO JSON
# ============================================================================

def test_export_schedule_creates_json_file() -> None:
    agent = _run_full_agent(make_pet_profile(species="dog", training_stage="adult"))
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "schedule.json")
        agent.export_schedule_to_json(path)
        assert os.path.exists(path)


def test_export_schedule_json_is_valid() -> None:
    agent = _run_full_agent(make_pet_profile(species="dog", training_stage="adult"))
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "schedule.json")
        agent.export_schedule_to_json(path)
        with open(path) as f:
            data = json.load(f)
        assert isinstance(data, dict)


def test_export_schedule_contains_owner_name() -> None:
    agent = _run_full_agent(make_pet_profile(species="dog", training_stage="adult"))
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "schedule.json")
        agent.export_schedule_to_json(path)
        with open(path) as f:
            data = json.load(f)
        assert data["owner"] == "Jordan"


def test_export_schedule_contains_all_seven_days() -> None:
    agent = _run_full_agent(make_pet_profile(species="dog", training_stage="adult"))
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "schedule.json")
        agent.export_schedule_to_json(path)
        with open(path) as f:
            data = json.load(f)
        for day in days:
            assert day in data["weekly_schedule"], f"{day} missing from export"


def test_export_schedule_task_entries_have_required_keys() -> None:
    agent = _run_full_agent(make_pet_profile(species="dog", training_stage="adult"))
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "schedule.json")
        agent.export_schedule_to_json(path)
        with open(path) as f:
            data = json.load(f)
        monday_tasks = data["weekly_schedule"]["Monday"]
        assert len(monday_tasks) > 0
        for entry in monday_tasks:
            for key in ("time", "title", "pet", "duration_minutes", "priority", "frequency"):
                assert key in entry, f"Key '{key}' missing from exported task"


def test_export_schedule_without_generating_schedule_returns_empty_string() -> None:
    agent = PawPalAgent()
    result = agent.export_schedule_to_json("should_not_be_created.json")
    assert result == ""
    assert not os.path.exists("should_not_be_created.json")


def test_export_schedule_contains_generated_at_timestamp() -> None:
    agent = _run_full_agent(make_pet_profile(species="dog", training_stage="adult"))
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "schedule.json")
        agent.export_schedule_to_json(path)
        with open(path) as f:
            data = json.load(f)
        assert "generated_at" in data
        # Should be a parseable ISO datetime
        datetime.fromisoformat(data["generated_at"])


# ============================================================================
# CONVERSATION-MODE COMMAND HANDLING
# ============================================================================

def test_conversation_help_command_lists_available_commands() -> None:
    agent = PawPalAgent()
    response = agent._handle_conversation_input("help")
    assert "profile" in response
    assert "schedule" in response
    assert "export" in response


def test_conversation_profile_command_returns_owner_summary() -> None:
    agent = PawPalAgent()
    agent.session.owner_profile = make_owner_profile(name="Alex")
    response = agent._handle_conversation_input("profile")
    assert "Alex" in response


def test_conversation_profile_command_without_profile_returns_graceful_message() -> None:
    agent = PawPalAgent()
    response = agent._handle_conversation_input("profile")
    assert "no owner profile" in response.lower() or "not" in response.lower()


def test_conversation_pets_command_returns_all_pet_names() -> None:
    agent = PawPalAgent()
    agent.session.pet_profiles = [
        make_pet_profile(name="Buddy", species="dog"),
        make_pet_profile(name="Luna", species="cat"),
    ]
    response = agent._handle_conversation_input("pets")
    assert "Buddy" in response
    assert "Luna" in response


def test_conversation_pets_command_without_pets_returns_graceful_message() -> None:
    agent = PawPalAgent()
    response = agent._handle_conversation_input("pets")
    assert "no pet" in response.lower() or "not" in response.lower()


def test_conversation_tasks_command_returns_task_list() -> None:
    agent = make_agent_with_profiles(make_pet_profile(species="dog", training_stage="adult"))
    agent.generate_tasks()
    response = agent._handle_conversation_input("tasks")
    assert "Morning walk" in response


def test_conversation_tasks_command_without_tasks_returns_graceful_message() -> None:
    agent = PawPalAgent()
    response = agent._handle_conversation_input("tasks")
    assert "no tasks" in response.lower() or "not" in response.lower()


def test_conversation_schedule_command_returns_monday_plan() -> None:
    agent = _run_full_agent(make_pet_profile(species="dog", training_stage="adult"))
    response = agent._handle_conversation_input("schedule monday")
    assert "Monday" in response


def test_conversation_schedule_command_without_schedule_returns_graceful_message() -> None:
    agent = PawPalAgent()
    response = agent._handle_conversation_input("schedule monday")
    assert "not" in response.lower() or "no" in response.lower()


def test_conversation_quit_command_disables_conversation_mode() -> None:
    agent = PawPalAgent()
    agent.conversation_mode = True
    agent._handle_conversation_input("quit")
    assert agent.conversation_mode is False


def test_conversation_unknown_command_returns_fallback_message() -> None:
    agent = PawPalAgent()
    response = agent._handle_conversation_input("xyzzy")
    assert len(response) > 0  # Should never crash, always return something


# ============================================================================
# EDGE CASES
# ============================================================================

def test_generate_tasks_with_no_pet_profiles_returns_empty_list() -> None:
    agent = PawPalAgent()
    agent.session.owner_profile = make_owner_profile()
    agent.session.pet_profiles = []
    tasks = agent.generate_tasks()
    assert tasks == []


def test_senior_dog_templates_have_reduced_intensity_titles() -> None:
    """Senior dog templates should include 'gentle' walk variants."""
    agent = PawPalAgent()
    pet = make_pet_profile(species="dog", age=12, training_stage="senior")
    templates = agent._get_task_templates(pet)
    titles = [t["title"] for t in templates]
    assert any("gentle" in title.lower() for title in titles)


def test_puppy_dog_has_more_daily_tasks_than_adult_dog() -> None:
    """Puppies need more frequent attention — their daily task count should be higher."""
    puppy_templates = TASK_TEMPLATES["dog"]["puppy"]
    adult_templates = TASK_TEMPLATES["dog"]["adult"]
    puppy_daily = [t for t in puppy_templates if t["frequency"] == "daily"]
    adult_daily = [t for t in adult_templates if t["frequency"] == "daily"]
    assert len(puppy_daily) > len(adult_daily)


def test_all_high_priority_tasks_in_templates_have_valid_durations() -> None:
    for species, stages in TASK_TEMPLATES.items():
        for stage, templates in stages.items():
            for t in templates:
                assert t["duration_minutes"] > 0, (
                    f"{species}/{stage}: '{t['title']}' has non-positive duration"
                )


def test_validate_time_window_accepts_valid_format() -> None:
    agent = PawPalAgent()
    assert agent._validate_time_window("06:00-07:00") is True


def test_validate_time_window_rejects_invalid_format() -> None:
    agent = PawPalAgent()
    assert agent._validate_time_window("6am-7am") is False
    assert agent._validate_time_window("06:00") is False
    assert agent._validate_time_window("") is False


def test_calculate_total_minutes_single_window() -> None:
    agent = PawPalAgent()
    total = agent._calculate_total_minutes([("06:00", "07:30")])
    assert total == 90


def test_calculate_total_minutes_multiple_windows() -> None:
    agent = PawPalAgent()
    total = agent._calculate_total_minutes([("06:00", "07:00"), ("17:00", "19:00")])
    assert total == 180


def test_calculate_total_minutes_empty_windows_returns_zero() -> None:
    agent = PawPalAgent()
    total = agent._calculate_total_minutes([])
    assert total == 0