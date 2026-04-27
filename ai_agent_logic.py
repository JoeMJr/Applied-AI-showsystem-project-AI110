"""
AI Agent Logic for PawPal+ - Phase 1 Implementation

This module implements the agentic workflow for intelligent pet care scheduling.
It handles:
1. Owner/pet profile collection via structured prompts
2. Task generation from species-based templates
3. Constraint-based schedule optimization
4. Schedule export and presentation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime
from pawpal_system import Owner, Pet, Task, Scheduler


# ============================================================================
# DATA MODELS FOR AGENT STATE
# ============================================================================

@dataclass
class OwnerProfile:
    """Represents collected owner information."""
    name: str
    work_schedule: str  # e.g., "9-5", "variable", "remote"
    available_time_windows: List[Tuple[str, str]]  # [(start_time, end_time), ...]
    total_daily_minutes: int
    lifestyle_constraints: str  # e.g., "commute 1 hour daily"
    tech_comfort: str  # "beginner", "intermediate", "advanced"

    def summary(self) -> str:
        """Return a human-readable summary of the owner profile."""
        window_str = ", ".join([f"{start}-{end}" for start, end in self.available_time_windows])
        return (
            f"Owner: {self.name}\n"
            f"Work Schedule: {self.work_schedule}\n"
            f"Available Time Windows: {window_str}\n"
            f"Total Daily Minutes Available: {self.total_daily_minutes}\n"
            f"Lifestyle Constraints: {self.lifestyle_constraints}\n"
            f"Tech Comfort Level: {self.tech_comfort}"
        )


@dataclass
class PetProfile:
    """Represents collected pet information."""
    name: str
    species: str
    age: int
    energy_level: str  # "low", "medium", "high"
    health_status: str  # "healthy", "senior", "has_conditions"
    special_needs: List[str]  # ["allergies", "medication_needed", "training_needed"]
    training_stage: str  # "puppy", "adult", "senior"

    def summary(self) -> str:
        """Return a human-readable summary of the pet profile."""
        return (
            f"Pet: {self.name} (Age: {self.age} years)\n"
            f"Species: {self.species}\n"
            f"Energy Level: {self.energy_level}\n"
            f"Health Status: {self.health_status}\n"
            f"Special Needs: {', '.join(self.special_needs) if self.special_needs else 'None'}\n"
            f"Training Stage: {self.training_stage}"
        )


@dataclass
class AgentSession:
    """Maintains agent state during a scheduling session."""
    owner_profile: Optional[OwnerProfile] = None
    pet_profiles: List[PetProfile] = field(default_factory=list)
    generated_tasks: List[Task] = field(default_factory=list)
    owner_system: Optional[Owner] = None
    scheduler: Optional[Scheduler] = None
    conversation_history: List[Dict[str, str]] = field(default_factory=list)

    def add_message(self, role: str, content: str) -> None:
        """Add a message to conversation history."""
        self.conversation_history.append({"role": role, "content": content})


# ============================================================================
# TASK TEMPLATE KNOWLEDGE BASE
# ============================================================================

TASK_TEMPLATES = {
    "dog": {
        "puppy": [
            {"title": "Morning walk", "duration_minutes": 20, "priority": "high", "frequency": "daily"},
            {"title": "Potty break (midday)", "duration_minutes": 10, "priority": "high", "frequency": "daily"},
            {"title": "Lunch feeding", "duration_minutes": 15, "priority": "high", "frequency": "daily"},
            {"title": "Training session", "duration_minutes": 20, "priority": "medium", "frequency": "daily"},
            {"title": "Afternoon play", "duration_minutes": 30, "priority": "medium", "frequency": "daily"},
            {"title": "Evening walk", "duration_minutes": 25, "priority": "high", "frequency": "daily"},
            {"title": "Dinner feeding", "duration_minutes": 15, "priority": "high", "frequency": "daily"},
            {"title": "Bedtime routine", "duration_minutes": 10, "priority": "medium", "frequency": "daily"},
            {"title": "Grooming", "duration_minutes": 30, "priority": "low", "frequency": "weekly"},
            {"title": "Vet checkup", "duration_minutes": 60, "priority": "high", "frequency": "monthly"},
        ],
        "adult": [
            {"title": "Morning walk", "duration_minutes": 30, "priority": "high", "frequency": "daily"},
            {"title": "Morning feeding", "duration_minutes": 10, "priority": "high", "frequency": "daily"},
            {"title": "Midday enrichment", "duration_minutes": 20, "priority": "medium", "frequency": "daily"},
            {"title": "Evening walk", "duration_minutes": 30, "priority": "high", "frequency": "daily"},
            {"title": "Dinner feeding", "duration_minutes": 10, "priority": "high", "frequency": "daily"},
            {"title": "Play/training", "duration_minutes": 25, "priority": "medium", "frequency": "daily"},
            {"title": "Grooming", "duration_minutes": 40, "priority": "low", "frequency": "weekly"},
            {"title": "Nail trim", "duration_minutes": 15, "priority": "low", "frequency": "bi-weekly"},
        ],
        "senior": [
            {"title": "Morning walk (gentle)", "duration_minutes": 20, "priority": "high", "frequency": "daily"},
            {"title": "Morning feeding", "duration_minutes": 10, "priority": "high", "frequency": "daily"},
            {"title": "Afternoon rest check", "duration_minutes": 10, "priority": "medium", "frequency": "daily"},
            {"title": "Evening walk (gentle)", "duration_minutes": 20, "priority": "high", "frequency": "daily"},
            {"title": "Dinner feeding", "duration_minutes": 10, "priority": "high", "frequency": "daily"},
            {"title": "Health monitoring", "duration_minutes": 15, "priority": "high", "frequency": "daily"},
            {"title": "Grooming", "duration_minutes": 30, "priority": "medium", "frequency": "weekly"},
            {"title": "Vet checkup", "duration_minutes": 60, "priority": "high", "frequency": "quarterly"},
        ],
    },
    "cat": {
        "puppy": [  # Young kitten
            {"title": "Feeding (breakfast)", "duration_minutes": 10, "priority": "high", "frequency": "daily"},
            {"title": "Play session (morning)", "duration_minutes": 20, "priority": "medium", "frequency": "daily"},
            {"title": "Feeding (lunch)", "duration_minutes": 10, "priority": "high", "frequency": "daily"},
            {"title": "Litter box check", "duration_minutes": 5, "priority": "high", "frequency": "daily"},
            {"title": "Play session (evening)", "duration_minutes": 20, "priority": "medium", "frequency": "daily"},
            {"title": "Feeding (dinner)", "duration_minutes": 10, "priority": "high", "frequency": "daily"},
            {"title": "Training session", "duration_minutes": 15, "priority": "medium", "frequency": "daily"},
            {"title": "Grooming", "duration_minutes": 20, "priority": "low", "frequency": "weekly"},
        ],
        "adult": [
            {"title": "Feeding (breakfast)", "duration_minutes": 10, "priority": "high", "frequency": "daily"},
            {"title": "Play/enrichment (morning)", "duration_minutes": 15, "priority": "medium", "frequency": "daily"},
            {"title": "Litter box check & clean", "duration_minutes": 10, "priority": "high", "frequency": "daily"},
            {"title": "Feeding (dinner)", "duration_minutes": 10, "priority": "high", "frequency": "daily"},
            {"title": "Interactive play (evening)", "duration_minutes": 20, "priority": "medium", "frequency": "daily"},
            {"title": "Grooming", "duration_minutes": 20, "priority": "low", "frequency": "weekly"},
            {"title": "Vet checkup", "duration_minutes": 60, "priority": "high", "frequency": "annual"},
        ],
        "senior": [
            {"title": "Feeding (breakfast, soft food)", "duration_minutes": 10, "priority": "high", "frequency": "daily"},
            {"title": "Litter box check", "duration_minutes": 5, "priority": "high", "frequency": "daily"},
            {"title": "Health monitoring", "duration_minutes": 10, "priority": "high", "frequency": "daily"},
            {"title": "Feeding (dinner)", "duration_minutes": 10, "priority": "high", "frequency": "daily"},
            {"title": "Gentle play (optional)", "duration_minutes": 10, "priority": "low", "frequency": "daily"},
            {"title": "Grooming", "duration_minutes": 15, "priority": "medium", "frequency": "weekly"},
            {"title": "Vet checkup", "duration_minutes": 60, "priority": "high", "frequency": "quarterly"},
        ],
    },
    "other": {
        "default": [
            {"title": "Feeding (morning)", "duration_minutes": 15, "priority": "high", "frequency": "daily"},
            {"title": "Enclosure/habitat check", "duration_minutes": 10, "priority": "high", "frequency": "daily"},
            {"title": "Feeding (evening)", "duration_minutes": 15, "priority": "high", "frequency": "daily"},
            {"title": "Enrichment activity", "duration_minutes": 20, "priority": "medium", "frequency": "daily"},
            {"title": "Cleaning", "duration_minutes": 30, "priority": "medium", "frequency": "weekly"},
            {"title": "Health check", "duration_minutes": 15, "priority": "high", "frequency": "weekly"},
        ],
    },
}


# ============================================================================
# AI AGENT IMPLEMENTATION
# ============================================================================

class PawPalAgent:
    """Main AI Agent for PawPal+ scheduling."""

    def __init__(self):
        """Initialize the agent."""
        self.session = AgentSession()
        self.conversation_mode = False

    # ========================================================================
    # STAGE 1: OWNER PROFILE GATHERING
    # ========================================================================

    def gather_owner_profile(self) -> OwnerProfile:
        """Gather owner information through a structured interview."""
        print("\n" + "="*70)
        print("STEP 1: OWNER PROFILE - Let's learn about you!")
        print("="*70)

        owner_name = self._prompt_user("What is your name?")

        print("\n📅 Work Schedule Information:")
        work_schedule = self._prompt_user(
            "What is your typical work schedule? (e.g., '9-5', 'variable', 'remote', '7-3')"
        )

        print("\n⏰ Available Time Windows:")
        print("Enter your daily available time windows for pet care.")
        print("Example: morning 6-7am, lunch 12-1pm, evening 5-7pm")

        available_windows = []
        while True:
            time_window = self._prompt_user(
                "Enter a time window (HH:MM-HH:MM) or 'done' to finish"
            )
            if time_window.lower() == "done":
                break
            if self._validate_time_window(time_window):
                available_windows.append(tuple(time_window.split("-")))
            else:
                print("⚠️  Invalid format. Please use HH:MM-HH:MM (e.g., 06:00-07:00)")

        total_minutes = self._calculate_total_minutes(available_windows)

        print("\n🏠 Lifestyle Information:")
        lifestyle = self._prompt_user(
            "Any lifestyle constraints? (e.g., '1hr commute', 'family commitments', 'none')"
        )

        print("\n💻 Tech Comfort Level:")
        tech_level = self._prompt_user(
            "How comfortable are you with technology? (beginner/intermediate/advanced)"
        )

        owner_profile = OwnerProfile(
            name=owner_name,
            work_schedule=work_schedule,
            available_time_windows=available_windows,
            total_daily_minutes=total_minutes,
            lifestyle_constraints=lifestyle,
            tech_comfort=tech_level,
        )

        self.session.owner_profile = owner_profile
        self.session.add_message("agent", f"Owner profile saved for {owner_name}")

        print("\n✅ Owner profile created!")
        print(owner_profile.summary())

        return owner_profile

    # ========================================================================
    # STAGE 1B: PET PROFILE GATHERING
    # ========================================================================

    def gather_pet_profiles(self) -> List[PetProfile]:
        """Gather information about all pets."""
        print("\n" + "="*70)
        print("STEP 2: PET PROFILES - Tell me about your pet(s)!")
        print("="*70)

        pet_profiles = []
        pet_count = 1

        while True:
            print(f"\n🐾 Pet #{pet_count}")
            pet_name = self._prompt_user("Pet name?")
            species = self._prompt_user(
                "Species? (dog/cat/rabbit/bird/other)"
            ).lower()

            age = int(self._prompt_user("Age (in years)?", default="1"))

            energy_level = self._prompt_user(
                "Energy level? (low/medium/high)",
                default="medium"
            ).lower()

            health_status = self._prompt_user(
                "Health status? (healthy/senior/has_conditions)",
                default="healthy"
            ).lower()

            training_stage = self._determine_training_stage(species, age, health_status)

            print("\n📋 Special needs (enter 'none' if N/A):")
            special_needs = []
            needs_input = self._prompt_user(
                "Special needs? (allergies/medication/training/anxiety/other or 'none')"
            ).lower()
            if needs_input != "none":
                special_needs = [item.strip() for item in needs_input.split(",")]

            pet_profile = PetProfile(
                name=pet_name,
                species=species,
                age=age,
                energy_level=energy_level,
                health_status=health_status,
                special_needs=special_needs,
                training_stage=training_stage,
            )

            pet_profiles.append(pet_profile)
            self.session.pet_profiles.append(pet_profile)

            print(f"\n✅ Pet profile created for {pet_name}!")
            print(pet_profile.summary())

            add_another = self._prompt_user(
                "Add another pet? (yes/no)",
                default="no"
            ).lower()
            if add_another != "yes":
                break

            pet_count += 1

        self.session.add_message("agent", f"Pet profiles saved for {len(pet_profiles)} pets")
        return pet_profiles

    # ========================================================================
    # STAGE 2: INTELLIGENT TASK GENERATION
    # ========================================================================

    def generate_tasks(self) -> List[Task]:
        """Generate task recommendations based on pet profiles and owner constraints."""
        print("\n" + "="*70)
        print("STEP 3: GENERATING TASK RECOMMENDATIONS")
        print("="*70)

        generated_tasks = []

        for pet_profile in self.session.pet_profiles:
            print(f"\n🎯 Generating tasks for {pet_profile.name} ({pet_profile.species})...")

            # Get base templates
            templates = self._get_task_templates(pet_profile)

            # Adjust for energy level
            adjusted_templates = self._adjust_for_energy_level(
                templates, pet_profile.energy_level
            )

            # Adjust for special needs
            final_templates = self._adjust_for_special_needs(
                adjusted_templates, pet_profile.special_needs
            )

            # Create Task objects
            for template in final_templates:
                task = Task(
                    title=template["title"],
                    description=f"{template['title']} for {pet_profile.name}",
                    duration_minutes=template["duration_minutes"],
                    priority=template["priority"],
                    frequency=template["frequency"],
                    pet=None,  # Will be set when pet is created
                )
                generated_tasks.append(task)
                print(
                    f"  ✓ {task.title} ({task.priority}, {task.duration_minutes}min, {task.frequency})"
                )

        self.session.generated_tasks = generated_tasks
        self.session.add_message(
            "agent", f"Generated {len(generated_tasks)} tasks"
        )

        total_daily_minutes = sum(
            [t.duration_minutes for t in generated_tasks if t.frequency == "daily"]
        )
        print(
            f"\n📊 Summary: {total_daily_minutes} minutes/day needed, "
            f"{self.session.owner_profile.total_daily_minutes} minutes available"
        )

        if total_daily_minutes > self.session.owner_profile.total_daily_minutes:
            print(
                f"⚠️  WARNING: Tasks exceed available time by "
                f"{total_daily_minutes - self.session.owner_profile.total_daily_minutes} minutes!"
            )
            print("    Consider: reducing task frequency or adjusting priorities")

        return generated_tasks

    # ========================================================================
    # STAGE 3: SCHEDULE OPTIMIZATION
    # ========================================================================

    def optimize_schedule(self) -> Scheduler:
        """Create an optimized schedule based on owner constraints."""
        print("\n" + "="*70)
        print("STEP 4: OPTIMIZING SCHEDULE")
        print("="*70)

        # Create Owner object
        owner = Owner(name=self.session.owner_profile.name)
        self.session.owner_system = owner

        # Create Pet objects and attach tasks
        pet_map = {}
        for pet_profile in self.session.pet_profiles:
            pet = Pet(name=pet_profile.name, species=pet_profile.species)
            pet_map[pet_profile.name] = pet
            owner.add_pet(pet)

            # Add tasks to pet
            for task in self.session.generated_tasks:
                if pet_profile.name in task.description:
                    pet.add_task(task)

        # Create scheduler
        scheduler = Scheduler(owner)
        self.session.scheduler = scheduler

        # Assign tasks to time slots
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        window_idx = 0
        time_windows = self.session.owner_profile.available_time_windows

        daily_tasks = [t for t in self.session.generated_tasks if t.frequency == "daily"]

        for day in days:
            window_idx = 0
            for task in sorted(daily_tasks, key=lambda x: self.session.scheduler.PRIORITY_ORDER.get(x.priority.lower(), 3)):
                if window_idx < len(time_windows):
                    start_time = time_windows[window_idx][0]
                    conflict_warning = scheduler.schedule_task(task, day, start_time)
                    if conflict_warning:
                        print(f"  ⚠️  {conflict_warning}")
                    window_idx = (window_idx + 1) % len(time_windows)

        self.session.add_message("agent", "Schedule optimized")
        print("\n✅ Schedule optimized!")

        return scheduler

    # ========================================================================
    # STAGE 4: SCHEDULE PRESENTATION & EXPORT
    # ========================================================================

    def display_schedule(self, day: str = "Monday") -> None:
        """Display the generated schedule for a specific day."""
        if not self.session.scheduler:
            print("❌ Schedule not yet generated. Run optimize_schedule() first.")
            return

        daily_plan = self.session.scheduler.get_daily_plan(day)

        print("\n" + "="*70)
        print(f"📅 SCHEDULE FOR {day.upper()}")
        print("="*70)

        if not daily_plan:
            print(f"No tasks scheduled for {day}")
            return

        for task in daily_plan:
            pet_name = task.pet.name if task.pet else "Unknown"
            print(
                f"  {task.scheduled_time} | {task.title:30} | "
                f"{task.duration_minutes:3}min | {task.priority:6} | {pet_name}"
            )

        print("="*70)

    def export_schedule_to_json(self, filename: str = "pawpal_schedule.json") -> str:
        """Export the full schedule to JSON format."""
        if not self.session.scheduler:
            print("❌ Schedule not yet generated.")
            return ""

        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        schedule_data = {
            "generated_at": datetime.now().isoformat(),
            "owner": self.session.owner_profile.name,
            "owner_profile": {
                "work_schedule": self.session.owner_profile.work_schedule,
                "available_time_windows": [
                    f"{start}-{end}"
                    for start, end in self.session.owner_profile.available_time_windows
                ],
                "total_daily_minutes": self.session.owner_profile.total_daily_minutes,
            },
            "pets": [
                {
                    "name": pet.name,
                    "species": pet.species,
                    "task_count": len(pet.get_tasks()),
                }
                for pet in self.session.owner_system.get_pets()
            ],
            "weekly_schedule": {},
        }

        for day in days:
            daily_plan = self.session.scheduler.get_daily_plan(day)
            schedule_data["weekly_schedule"][day] = [
                {
                    "time": task.scheduled_time,
                    "title": task.title,
                    "pet": task.pet.name if task.pet else "unknown",
                    "duration_minutes": task.duration_minutes,
                    "priority": task.priority,
                    "frequency": task.frequency,
                }
                for task in daily_plan
            ]

        # Write to file
        with open(filename, "w") as f:
            json.dump(schedule_data, f, indent=2)

        print(f"\n✅ Schedule exported to {filename}")
        return filename

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _prompt_user(self, question: str, default: Optional[str] = None) -> str:
        """Prompt user for input."""
        prompt = question
        if default:
            prompt += f" [{default}]"
        prompt += ": "

        response = input(prompt).strip()
        return response if response else (default or "")

    def _validate_time_window(self, time_window: str) -> bool:
        """Validate time window format (HH:MM-HH:MM)."""
        try:
            parts = time_window.split("-")
            if len(parts) != 2:
                return False
            for part in parts:
                datetime.strptime(part.strip(), "%H:%M")
            return True
        except ValueError:
            return False

    def _calculate_total_minutes(self, windows: List[Tuple[str, str]]) -> int:
        """Calculate total available minutes from time windows."""
        total = 0
        for start, end in windows:
            start_time = datetime.strptime(start.strip(), "%H:%M")
            end_time = datetime.strptime(end.strip(), "%H:%M")
            delta = end_time - start_time
            total += int(delta.total_seconds() / 60)
        return total

    def _determine_training_stage(
        self, species: str, age: int, health_status: str
    ) -> str:
        """Determine training stage based on species, age, and health."""
        if health_status == "senior" or age > 10:
            return "senior"
        elif age < 2:
            return "puppy"
        else:
            return "adult"

    def _get_task_templates(self, pet_profile: PetProfile) -> List[Dict]:
        """Get base task templates for a pet."""
        species = pet_profile.species.lower()
        training_stage = pet_profile.training_stage

        if species in TASK_TEMPLATES:
            if training_stage in TASK_TEMPLATES[species]:
                return TASK_TEMPLATES[species][training_stage]
            else:
                return TASK_TEMPLATES[species].get(
                    "adult", TASK_TEMPLATES[species][list(TASK_TEMPLATES[species].keys())[0]]
                )
        else:
            return TASK_TEMPLATES["other"]["default"]

    def _adjust_for_energy_level(
        self, templates: List[Dict], energy_level: str
    ) -> List[Dict]:
        """Adjust task durations and frequencies based on energy level."""
        adjusted = []
        for template in templates:
            adjusted_template = template.copy()

            if energy_level == "high":
                if "walk" in template["title"].lower() or "play" in template["title"].lower():
                    adjusted_template["duration_minutes"] = int(
                        template["duration_minutes"] * 1.3
                    )
            elif energy_level == "low":
                if "walk" in template["title"].lower() or "play" in template["title"].lower():
                    adjusted_template["duration_minutes"] = int(
                        template["duration_minutes"] * 0.7
                    )

            adjusted.append(adjusted_template)

        return adjusted

    def _adjust_for_special_needs(
        self, templates: List[Dict], special_needs: List[str]
    ) -> List[Dict]:
        """Add tasks based on special needs."""
        adjusted = templates.copy()

        if "medication" in special_needs:
            adjusted.append({
                "title": "Medication administration",
                "duration_minutes": 10,
                "priority": "high",
                "frequency": "daily",
            })

        if "training" in special_needs:
            adjusted.append({
                "title": "Behavior training",
                "duration_minutes": 20,
                "priority": "medium",
                "frequency": "daily",
            })

        if "anxiety" in special_needs:
            adjusted.append({
                "title": "Calming routine",
                "duration_minutes": 15,
                "priority": "high",
                "frequency": "daily",
            })

        return adjusted

    # ========================================================================
    # CONVERSATION MODE (CHAT INTERFACE)
    # ========================================================================

    def start_conversation(self) -> None:
        """Start an interactive chat with the user."""
        print("\n" + "="*70)
        print("🤖 PAWPAL+ AI AGENT - INTERACTIVE MODE")
        print("="*70)
        print("Type 'help' for available commands, 'quit' to exit\n")

        self.conversation_mode = True

        while self.conversation_mode:
            user_input = input("You: ").strip().lower()

            if not user_input:
                continue

            response = self._handle_conversation_input(user_input)
            print(f"Agent: {response}\n")

    def _handle_conversation_input(self, user_input: str) -> str:
        """Handle user input in conversation mode."""
        if user_input == "quit":
            self.conversation_mode = False
            return "Goodbye! Your schedule has been saved."

        elif user_input == "help":
            return (
                "Available commands:\n"
                "  'profile' - Show owner profile\n"
                "  'pets' - Show all pet profiles\n"
                "  'tasks' - Show generated tasks\n"
                "  'schedule [day]' - Show schedule for a day (default: Monday)\n"
                "  'export' - Export schedule to JSON\n"
                "  'help' - Show this help message\n"
                "  'quit' - Exit the chat"
            )

        elif user_input == "profile":
            if not self.session.owner_profile:
                return "No owner profile created yet."
            return self.session.owner_profile.summary()

        elif user_input == "pets":
            if not self.session.pet_profiles:
                return "No pet profiles created yet."
            summaries = "\n\n".join([p.summary() for p in self.session.pet_profiles])
            return summaries

        elif user_input == "tasks":
            if not self.session.generated_tasks:
                return "No tasks generated yet."
            task_list = "\n".join(
                [
                    f"  • {t.title} ({t.priority}, {t.duration_minutes}min, {t.frequency})"
                    for t in self.session.generated_tasks
                ]
            )
            return f"Generated {len(self.session.generated_tasks)} tasks:\n{task_list}"

        elif user_input.startswith("schedule"):
            if not self.session.scheduler:
                return "Schedule not yet generated."
            day = "Monday"
            parts = user_input.split()
            if len(parts) > 1:
                day = parts[1].capitalize()
            daily_plan = self.session.scheduler.get_daily_plan(day)
            if not daily_plan:
                return f"No tasks scheduled for {day}"
            schedule_str = "\n".join(
                [
                    f"  {t.scheduled_time} | {t.title:25} | {t.duration_minutes:3}min | "
                    f"{t.priority:6} | {t.pet.name if t.pet else 'unknown'}"
                    for t in daily_plan
                ]
            )
            return f"Schedule for {day}:\n{schedule_str}"

        elif user_input == "export":
            if not self.session.scheduler:
                return "Schedule not yet generated."
            self.export_schedule_to_json()
            return "Schedule exported to pawpal_schedule.json"

        else:
            return (
                "I didn't understand that command. Type 'help' for available commands, "
                "or ask me questions about the schedule."
            )


# ============================================================================
# WORKFLOW ORCHESTRATOR
# ============================================================================

def run_phase1_workflow() -> PawPalAgent:
    """Run the complete Phase 1 agentic workflow."""
    agent = PawPalAgent()

    # Stage 1: Gather owner profile
    agent.gather_owner_profile()

    # Stage 1B: Gather pet profiles
    agent.gather_pet_profiles()

    # Stage 2: Generate tasks
    agent.generate_tasks()

    # Stage 3: Optimize schedule
    agent.optimize_schedule()

    # Stage 4: Display and export
    agent.display_schedule("Monday")
    agent.export_schedule_to_json()

    # Start conversation mode
    print("\nWould you like to interact with the schedule? (yes/no)")
    response = input("> ").strip().lower()
    if response == "yes":
        agent.start_conversation()

    return agent


if __name__ == "__main__":
    agent = run_phase1_workflow()
