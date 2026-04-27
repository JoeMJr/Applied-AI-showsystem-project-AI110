import streamlit as st
import pawpal_system as pawpal
from ai_agent_logic import PawPalAgent, OwnerProfile, PetProfile
from datetime import datetime
import json

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if "owner" not in st.session_state:
    st.session_state.owner = pawpal.Owner(name="Jordan")

if "agent" not in st.session_state:
    st.session_state.agent = None

if "app_mode" not in st.session_state:
    st.session_state.app_mode = "home"  # home, quick, detailed, chat, manual

if "agent_session" not in st.session_state:
    st.session_state.agent_session = None


def is_valid_time(time_str: str) -> bool:
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

st.title("🐾 PawPal+ - Intelligent Pet Care Scheduling")

# ============================================================================
# HOME PAGE / MODE SELECTION
# ============================================================================

def show_home_page():
    """Display the home page with mode selection."""
    st.markdown("## Welcome to PawPal+\nYour intelligent pet care planning assistant.")

    # If a schedule already exists, surface a shortcut banner
    if st.session_state.agent is not None:
        owner_name = st.session_state.agent.session.owner_profile.name
        task_count = len(st.session_state.agent.session.generated_tasks)
        st.success(
            f"✅ **Active schedule found** for {owner_name} — {task_count} tasks generated. "
            "Jump straight back in!"
        )
        if st.button("📅 View My AI Schedule →", use_container_width=True, type="primary"):
            st.session_state.app_mode = "schedule_view"
            st.rerun()
        st.divider()

    st.markdown("#### How would you like to get started?")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div style="background:#ebf8ff;border-radius:12px;padding:16px;border:1px solid #90cdf4;min-height:160px;">
            <h3 style="margin:0 0 6px;">⚡ Quick Schedule</h3>
            <p style="font-size:0.85rem;color:#2c5282;margin:0;"><strong>~5 minutes</strong><br>
            Answer 3 questions and get an AI-optimised schedule instantly. Perfect for first-timers.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("")
        if st.button("Start Quick Scheduling", key="quick_btn", use_container_width=True, type="primary"):
            st.session_state.app_mode = "quick"
            st.rerun()

    with col2:
        st.markdown(
            """
            <div style="background:#f0fff4;border-radius:12px;padding:16px;border:1px solid #9ae6b4;min-height:160px;">
            <h3 style="margin:0 0 6px;">📋 Detailed Setup</h3>
            <p style="font-size:0.85rem;color:#22543d;margin:0;"><strong>~15 minutes</strong><br>
            Full owner + pet interview for a deeply customised, priority-weighted weekly schedule.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("")
        if st.button("Start Detailed Setup", key="detailed_btn", use_container_width=True):
            st.session_state.app_mode = "detailed"
            st.rerun()

    with col3:
        st.markdown(
            """
            <div style="background:#fffff0;border-radius:12px;padding:16px;border:1px solid #f6e05e;min-height:160px;">
            <h3 style="margin:0 0 6px;">✏️ Manual Entry</h3>
            <p style="font-size:0.85rem;color:#744210;margin:0;"><strong>Custom</strong><br>
            Create tasks yourself and build a schedule manually. Full control, no AI assistance.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("")
        if st.button("Manual Mode", key="manual_btn", use_container_width=True):
            st.session_state.app_mode = "manual"
            st.rerun()

    st.divider()

    with st.expander("ℹ️ About PawPal+"):
        st.markdown("""
        **PawPal+** is an AI-powered pet care planning assistant that helps busy pet owners:

        - 🧠 Generate smart task recommendations based on your pet's profile
        - ⏰ Optimize schedules around your availability
        - 🎯 Prioritize tasks based on pet health and owner capacity
        - 📊 Export schedules for easy reference
        - 💬 Chat with your schedule for updates and questions
        """)


# ============================================================================
# FLOW A: QUICK SCHEDULING (5 MIN)
# ============================================================================

def show_quick_scheduling():
    """Quick scheduling flow with 3 questions."""
    st.header("⚡ Quick Schedule Generation")
    st.markdown("Answer 3 quick questions to generate your pet care schedule.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Question 1: Your Pet")
        pet_name = st.text_input("Pet name:", value="Buddy", key="quick_pet_name")
        pet_species = st.selectbox(
            "Pet species:",
            ["dog", "cat", "rabbit", "bird", "other"],
            key="quick_species"
        )
        pet_age = st.number_input("Age (years):", min_value=0, max_value=30, value=3, key="quick_age")
        
        st.subheader("Question 2: Your Availability")
        available_time = st.slider(
            "How many minutes daily can you spend on pet care?",
            min_value=30,
            max_value=360,
            value=120,
            step=15,
            key="quick_time"
        )
        
        st.subheader("Question 3: Special Needs")
        special_needs_options = st.multiselect(
            "Any special needs? (select all that apply)",
            ["None", "Medication", "Training needed", "Anxiety issues", "Other"],
            default=["None"],
            key="quick_needs"
        )
        special_needs = [item for item in special_needs_options if item != "None"]
        
        if st.button("Generate Quick Schedule", use_container_width=True, type="primary"):
            with st.spinner("Generating your schedule..."):
                # Create agent session with quick defaults
                agent = PawPalAgent()
                
                # Create owner profile with default values
                owner_profile = OwnerProfile(
                    name="Pet Owner",
                    work_schedule="9-5",
                    available_time_windows=[("06:00", "07:00"), ("12:00", "13:00"), ("17:00", "19:00")],
                    total_daily_minutes=available_time,
                    lifestyle_constraints="Standard work schedule",
                    tech_comfort="beginner"
                )
                agent.session.owner_profile = owner_profile
                
                # Create pet profile
                pet_profile = PetProfile(
                    name=pet_name,
                    species=pet_species.lower(),
                    age=pet_age,
                    energy_level="medium",
                    health_status="healthy",
                    special_needs=special_needs,
                    training_stage="adult" if pet_age >= 2 else "puppy"
                )
                agent.session.pet_profiles = [pet_profile]
                
                # Generate tasks
                agent.generate_tasks()
                
                # Optimize schedule
                agent.optimize_schedule()
                
                # Save to session
                st.session_state.agent = agent
                st.session_state.app_mode = "schedule_view"
                st.success("✅ Schedule generated successfully!")
                st.rerun()
    
    with col2:
        st.markdown("### 📱 Preview")
        st.info("""
        Your quick schedule will include:
        - Feeding times
        - Exercise/play
        - Grooming
        - Health checks
        - Training (if needed)
        """)
    
    col_back, _ = st.columns([1, 3])
    with col_back:
        if st.button("← Back to Home"):
            st.session_state.app_mode = "home"
            st.rerun()


# ============================================================================
# FLOW B: DETAILED SCHEDULING (15 MIN)
# ============================================================================

def show_detailed_scheduling():
    """Detailed scheduling flow with full interview."""
    st.header("📋 Complete Pet Care Profile Setup")
    st.markdown("Let's build a comprehensive, personalized schedule for your pet(s).")
    
    # Use tabs for organization
    tab1, tab2, tab3 = st.tabs(["Step 1: Owner Profile", "Step 2: Pet Profiles", "Step 3: Review & Generate"])
    
    # Step 1: Owner Profile
    with tab1:
        st.subheader("👤 About You")
        
        owner_name = st.text_input(
            "Your name:",
            value="Jordan",
            key="detailed_owner_name"
        )
        
        work_schedule = st.selectbox(
            "Work schedule:",
            ["9-5", "7-3", "3-11", "variable", "remote", "freelance", "retired"],
            key="detailed_work_schedule"
        )
        
        st.markdown("#### ⏰ Daily Available Time Windows")
        st.caption("When can you dedicate time to pet care? (e.g., 6-7am, 12-1pm, 5-7pm)")
        
        num_windows = st.number_input(
            "How many time windows?",
            min_value=1,
            max_value=5,
            value=3,
            key="detailed_num_windows"
        )
        
        time_windows = []
        for i in range(num_windows):
            cols = st.columns(2)
            with cols[0]:
                start = st.time_input(f"Start time {i+1}:", value=datetime.strptime("06:00", "%H:%M").time(), key=f"detailed_start_{i}")
            with cols[1]:
                end = st.time_input(f"End time {i+1}:", value=datetime.strptime("07:00", "%H:%M").time(), key=f"detailed_end_{i}")
            time_windows.append((start.strftime("%H:%M"), end.strftime("%H:%M")))
        
        lifestyle = st.text_area(
            "Lifestyle constraints:",
            placeholder="e.g., 1hr commute, family responsibilities, shift work",
            key="detailed_lifestyle"
        )
        
        tech_comfort = st.radio(
            "Tech comfort level:",
            ["Beginner", "Intermediate", "Advanced"],
            key="detailed_tech"
        )
        
        st.info("✅ Owner profile ready. Move to Step 2 to add your pets.")
    
    # Step 2: Pet Profiles
    with tab2:
        st.subheader("🐾 Your Pets")
        
        num_pets = st.number_input(
            "How many pets?",
            min_value=1,
            max_value=5,
            value=1,
            key="detailed_num_pets"
        )
        
        pet_profiles_list = []
        for pet_idx in range(num_pets):
            st.markdown(f"#### Pet #{pet_idx + 1}")
            
            cols = st.columns(3)
            with cols[0]:
                pet_name = st.text_input(
                    "Name:",
                    key=f"detailed_pet_name_{pet_idx}"
                )
            with cols[1]:
                pet_species = st.selectbox(
                    "Species:",
                    ["dog", "cat", "rabbit", "bird", "other"],
                    key=f"detailed_pet_species_{pet_idx}"
                )
            with cols[2]:
                pet_age = st.number_input(
                    "Age (years):",
                    min_value=0,
                    max_value=30,
                    value=3,
                    key=f"detailed_pet_age_{pet_idx}"
                )
            
            energy = st.select_slider(
                "Energy level:",
                options=["Low", "Medium", "High"],
                value="Medium",
                key=f"detailed_energy_{pet_idx}"
            )
            
            health = st.selectbox(
                "Health status:",
                ["Healthy", "Senior", "Has conditions"],
                key=f"detailed_health_{pet_idx}"
            )
            
            special_needs_input = st.multiselect(
                "Special needs:",
                ["None", "Medication", "Training", "Anxiety", "Allergies", "Other"],
                default=["None"],
                key=f"detailed_needs_{pet_idx}"
            )
            special_needs_list = [s for s in special_needs_input if s != "None"]
            
            pet_profile = PetProfile(
                name=pet_name,
                species=pet_species.lower(),
                age=pet_age,
                energy_level=energy.lower(),
                health_status=health.lower().replace(" ", "_"),
                special_needs=special_needs_list,
                training_stage="senior" if pet_age > 10 or health.lower() == "senior" else ("puppy" if pet_age < 2 else "adult")
            )
            pet_profiles_list.append(pet_profile)
            
            if pet_idx < num_pets - 1:
                st.divider()
        
        st.session_state.pet_profiles_temp = pet_profiles_list
        st.info("✅ Pet profiles ready. Move to Step 3 to review and generate.")
    
    # Step 3: Review & Generate
    with tab3:
        st.subheader("🎯 Review & Generate Schedule")
        
        st.markdown(f"**Owner:** {owner_name}")
        st.markdown(f"**Work Schedule:** {work_schedule}")
        st.markdown(f"**Daily Time Windows:** {', '.join([f'{s}-{e}' for s, e in time_windows])}")
        
        if hasattr(st.session_state, 'pet_profiles_temp'):
            st.markdown("**Pets:**")
            for pet in st.session_state.pet_profiles_temp:
                st.markdown(f"- {pet.name} ({pet.species}, {pet.age} years, {pet.energy_level} energy)")
        
        if st.button("✨ Generate Comprehensive Schedule", use_container_width=True, type="primary"):
            with st.spinner("Creating your personalized schedule..."):
                agent = PawPalAgent()
                
                owner_profile = OwnerProfile(
                    name=owner_name,
                    work_schedule=work_schedule,
                    available_time_windows=time_windows,
                    total_daily_minutes=sum([
                        int((datetime.strptime(e, "%H:%M") - datetime.strptime(s, "%H:%M")).total_seconds() / 60)
                        for s, e in time_windows
                    ]),
                    lifestyle_constraints=lifestyle or "None",
                    tech_comfort=tech_comfort.lower()
                )
                agent.session.owner_profile = owner_profile
                agent.session.pet_profiles = st.session_state.pet_profiles_temp
                
                agent.generate_tasks()
                agent.optimize_schedule()
                
                st.session_state.agent = agent
                st.session_state.app_mode = "schedule_view"
                st.success("✅ Schedule generated successfully!")
                st.rerun()


# ============================================================================
# SCHEDULE VIEW & CHAT
# ============================================================================

PRIORITY_COLORS = {
    "high":   {"bg": "#fde8e8", "border": "#e53e3e", "badge": "#e53e3e", "label": "🔴 HIGH"},
    "medium": {"bg": "#fef3cd", "border": "#d69e2e", "badge": "#d69e2e", "label": "🟡 MEDIUM"},
    "low":    {"bg": "#e8f5e9", "border": "#38a169", "badge": "#38a169", "label": "🟢 LOW"},
}

DAY_ICONS = {
    "Monday": "🌅", "Tuesday": "🌤", "Wednesday": "☀️",
    "Thursday": "🌈", "Friday": "🎉", "Saturday": "🌴", "Sunday": "😴"
}


def _render_task_card(task):
    """Render a single task as a styled card."""
    priority = task.priority.lower() if task.priority else "medium"
    colors = PRIORITY_COLORS.get(priority, PRIORITY_COLORS["medium"])
    pet_name = task.pet.name if task.pet else "Unknown"
    badge_label = colors["label"]
    st.markdown(
        f"""
        <div style="
            background:{colors['bg']};
            border-left: 4px solid {colors['border']};
            border-radius: 8px;
            padding: 10px 14px;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 12px;
        ">
            <div style="font-size:1.4rem; min-width:36px; text-align:center;">🐾</div>
            <div style="flex:1;">
                <div style="font-weight:600; font-size:0.95rem;">{task.title}</div>
                <div style="font-size:0.8rem; color:#555; margin-top:2px;">
                    🕐 {task.scheduled_time or "—"} &nbsp;|&nbsp;
                    ⏱ {task.duration_minutes} min &nbsp;|&nbsp;
                    🐾 {pet_name}
                </div>
            </div>
            <div style="
                background:{colors['badge']};
                color:white;
                border-radius:12px;
                padding:2px 10px;
                font-size:0.72rem;
                font-weight:600;
                white-space:nowrap;
            ">{badge_label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_weekly_heatmap(agent):
    """Render a compact weekly overview showing task load per day."""
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    cols = st.columns(7)
    for i, day in enumerate(days):
        daily_plan = agent.session.scheduler.get_daily_plan(day)
        task_count = len(daily_plan)
        total_mins = sum(t.duration_minutes for t in daily_plan)
        available = agent.session.owner_profile.total_daily_minutes
        pct = min(total_mins / max(available, 1), 1.0)
        fill_color = "#48bb78" if pct < 0.7 else ("#d69e2e" if pct < 0.95 else "#e53e3e")
        icon = DAY_ICONS.get(day, "📅")
        with cols[i]:
            st.markdown(
                f"""
                <div style="text-align:center; padding:8px 4px;">
                    <div style="font-size:1.2rem;">{icon}</div>
                    <div style="font-weight:700; font-size:0.75rem; color:#444;">{day[:3].upper()}</div>
                    <div style="
                        background:{fill_color};
                        color:white;
                        border-radius:20px;
                        padding:3px 0;
                        margin:4px 0;
                        font-size:0.78rem;
                        font-weight:600;
                    ">{task_count} tasks</div>
                    <div style="font-size:0.7rem; color:#666;">{total_mins} min</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def show_schedule_view():
    """Display the AI-generated schedule with rich visual cards and chat."""
    if not st.session_state.agent:
        st.error("No schedule generated yet.")
        if st.button("← Back to Home"):
            st.session_state.app_mode = "home"
            st.rerun()
        return

    agent = st.session_state.agent

    # ── Header ──────────────────────────────────────────────────────────────
    st.header(f"🤖 AI-Generated Schedule — {agent.session.owner_profile.name}")

    # Summary metrics
    daily_tasks = [t for t in agent.session.generated_tasks if t.frequency == "daily"]
    daily_minutes_needed = sum(t.duration_minutes for t in daily_tasks)
    available_minutes = agent.session.owner_profile.total_daily_minutes
    pct_used = int(daily_minutes_needed / max(available_minutes, 1) * 100)
    capacity_status = "✅ Fits schedule" if pct_used <= 100 else "⚠️ Over capacity"

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👤 Owner", agent.session.owner_profile.name)
    col2.metric("🐾 Pets", len(agent.session.pet_profiles))
    col3.metric("📋 Tasks Generated", len(agent.session.generated_tasks))
    col4.metric("⏱ Daily Load", f"{daily_minutes_needed}/{available_minutes} min", capacity_status)

    if pct_used > 100:
        st.warning(
            f"⚠️ Your daily tasks require **{daily_minutes_needed} min** but you only have "
            f"**{available_minutes} min** available. Consider reducing task frequency or delegating grooming tasks."
        )

    st.divider()

    # ── Weekly Overview Heatmap ──────────────────────────────────────────────
    st.subheader("📆 Weekly Overview")
    _render_weekly_heatmap(agent)
    st.divider()

    # ── Day View (Task Cards) ────────────────────────────────────────────────
    st.subheader("📋 Daily Schedule")

    DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    selected_day = st.segmented_control(
        "Select day:",
        options=DAYS,
        default="Monday",
        key="schedule_day_view",
    ) if hasattr(st, "segmented_control") else st.selectbox(
        "Select day:", DAYS, key="schedule_day_view"
    )

    daily_plan = agent.session.scheduler.get_daily_plan(selected_day)

    if daily_plan:
        day_icon = DAY_ICONS.get(selected_day, "📅")
        total_day_minutes = sum(t.duration_minutes for t in daily_plan)
        st.markdown(
            f"#### {day_icon} {selected_day} — {len(daily_plan)} tasks · {total_day_minutes} min total"
        )

        # Priority filter
        filter_col, sort_col = st.columns([2, 2])
        with filter_col:
            priority_filter = st.multiselect(
                "Filter by priority:",
                ["high", "medium", "low"],
                default=["high", "medium", "low"],
                key="priority_filter",
            )
        with sort_col:
            sort_by = st.radio(
                "Sort by:", ["Time", "Priority", "Duration"],
                horizontal=True, key="sort_by"
            )

        filtered = [t for t in daily_plan if t.priority.lower() in priority_filter]

        if sort_by == "Priority":
            order = {"high": 0, "medium": 1, "low": 2}
            filtered = sorted(filtered, key=lambda t: order.get(t.priority.lower(), 3))
        elif sort_by == "Duration":
            filtered = sorted(filtered, key=lambda t: t.duration_minutes, reverse=True)

        if filtered:
            for task in filtered:
                _render_task_card(task)
        else:
            st.info("No tasks match the selected filters.")

        # Capacity bar
        st.markdown(
            f"""
            <div style="margin-top:12px;">
                <div style="font-size:0.82rem; color:#555; margin-bottom:4px;">
                    Time used: {total_day_minutes} of {available_minutes} min available
                </div>
                <div style="background:#e2e8f0; border-radius:8px; height:10px; overflow:hidden;">
                    <div style="
                        width:{min(pct_used, 100)}%;
                        background:{'#48bb78' if pct_used <= 70 else ('#d69e2e' if pct_used <= 95 else '#e53e3e')};
                        height:100%;
                        border-radius:8px;
                        transition:width 0.4s;
                    "></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info(f"No tasks scheduled for {selected_day}.")

    st.divider()

    # ── All Tasks Breakdown ──────────────────────────────────────────────────
    with st.expander("🔍 View All Generated Tasks (across all days & frequencies)"):
        all_tasks = agent.session.generated_tasks
        if all_tasks:
            table_data = [
                {
                    "Task": t.title,
                    "Duration": f"{t.duration_minutes} min",
                    "Priority": t.priority.upper(),
                    "Frequency": t.frequency,
                }
                for t in all_tasks
            ]
            st.dataframe(table_data, use_container_width=True, hide_index=True)
        else:
            st.info("No tasks found.")

    # ── Per-Pet Summary ──────────────────────────────────────────────────────
    with st.expander("🐾 Per-Pet Schedule Summary"):
        for pet_profile in agent.session.pet_profiles:
            pet_tasks = [t for t in agent.session.generated_tasks if pet_profile.name in (t.description or "")]
            daily_pet = [t for t in pet_tasks if t.frequency == "daily"]
            st.markdown(
                f"**{pet_profile.name}** ({pet_profile.species}, {pet_profile.age}yr, "
                f"{pet_profile.energy_level} energy) — "
                f"**{len(pet_tasks)} tasks** · {sum(t.duration_minutes for t in daily_pet)} min/day"
            )

    st.divider()

    # ── Chat Interface ───────────────────────────────────────────────────────
    st.subheader("💬 Chat with Your Schedule")
    st.caption("Ask about specific days, time requirements, your pets, or export the schedule.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for exchange in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(exchange["user"])
        with st.chat_message("assistant"):
            st.markdown(exchange["agent"])

    user_query = st.chat_input("Ask something... e.g. 'Show me Friday' or 'How many minutes daily?'")
    if user_query:
        response = handle_schedule_query(agent, user_query)
        st.session_state.chat_history.append({"user": user_query, "agent": response})
        st.rerun()

    st.divider()

    # Export options
    st.subheader("📥 Export Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Export as JSON", use_container_width=True):
            filename = agent.export_schedule_to_json("pawpal_schedule.json")
            st.success(f"✅ Schedule exported to {filename}")
    
    with col2:
        if st.button("🔄 Generate New Schedule", use_container_width=True):
            st.session_state.app_mode = "home"
            st.rerun()


def handle_schedule_query(agent, query: str) -> str:
    """Handle natural language queries about the schedule."""
    query_lower = query.lower()
    
    if "monday" in query_lower or "tuesday" in query_lower or "wednesday" in query_lower or "thursday" in query_lower or "friday" in query_lower or "saturday" in query_lower or "sunday" in query_lower:
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
            if day.lower() in query_lower:
                daily_plan = agent.session.scheduler.get_daily_plan(day)
                if daily_plan:
                    tasks_str = "\n".join([f"• {t.scheduled_time}: {t.title} ({t.duration_minutes}min)" for t in daily_plan])
                    return f"**{day}'s Schedule:**\n{tasks_str}"
                else:
                    return f"No tasks scheduled for {day}."
    
    elif "how many" in query_lower and "minutes" in query_lower:
        total = agent.session.owner_profile.total_daily_minutes
        available = sum([
            int((datetime.strptime(e, "%H:%M") - datetime.strptime(s, "%H:%M")).total_seconds() / 60)
            for s, e in agent.session.owner_profile.available_time_windows
        ])
        return f"You have **{available} minutes** daily available for pet care. Current schedule uses **{sum([t.duration_minutes for t in agent.session.generated_tasks if t.frequency == 'daily'])} minutes/day**."
    
    elif "pets" in query_lower:
        pet_list = ", ".join([f"{p.name} ({p.species})" for p in agent.session.pet_profiles])
        return f"Your pets: {pet_list}"
    
    elif "export" in query_lower:
        agent.export_schedule_to_json()
        return "✅ Schedule exported to pawpal_schedule.json"
    
    elif "help" in query_lower or "what can" in query_lower:
        return """I can help with:
- View schedules for specific days (e.g., "Show me Monday")
- Answer questions about your schedule
- Export your schedule
- Tell you about your pets and tasks
- Calculate time requirements"""
    
    else:
        return "I'm here to help! Try asking about a specific day, your available time, your pets, or export options."


# ============================================================================
# MANUAL MODE (ORIGINAL)
# ============================================================================

def show_manual_mode():
    """Original manual task creation and scheduling mode."""
    st.header("✏️ Manual Pet Care Management")
    
    owner = st.session_state.owner
    owner_name = st.text_input("Owner name", value=owner.name, key="manual_owner_name")
    if owner_name != owner.name:
        owner.name = owner_name
    
    st.markdown("### Pets")
    
    new_pet_name = st.text_input("New pet name", value="Mochi", key="manual_pet_name")
    species = st.selectbox("Species", ["dog", "cat", "other"], key="manual_species")
    
    if st.button("Add pet", key="add_pet_btn"):
        pet_name_text = new_pet_name.strip() or "Unnamed pet"
        if owner.find_pet(pet_name_text):
            st.warning(f"A pet named '{pet_name_text}' already exists.")
        else:
            owner.add_pet(pawpal.Pet(name=pet_name_text, species=species))
            st.success(f"Added pet {pet_name_text} the {species}")
    
    pets = owner.get_pets()
    if pets:
        st.write("Current pets:")
        st.table([{"name": pet.name, "species": pet.species} for pet in pets])
    else:
        st.info("No pets yet. Add one above.")
    
    st.markdown("### Tasks")
    st.caption("Add tasks for your pets.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk", key="manual_task_title")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20, key="manual_duration")
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2, key="manual_priority")
    
    frequency = st.selectbox("Frequency", ["daily", "weekly", "once"], index=0, key="manual_frequency")
    selected_day = st.selectbox(
        "Scheduled day",
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        index=0,
        key="manual_day"
    )
    scheduled_time = st.text_input("Scheduled time", value="08:00", key="manual_time")
    
    pet_names = [pet.name for pet in owner.get_pets()]
    if pet_names:
        selected_pet = st.selectbox("Pet", pet_names, key="manual_pet")
        if st.button("Add task", key="add_task_btn"):
            title = task_title.strip() or "Untitled task"
            if not is_valid_time(scheduled_time):
                st.error("Please enter a valid scheduled time in HH:MM format.")
            else:
                pet = owner.find_pet(selected_pet)
                if pet is None:
                    st.error("Selected pet could not be found. Please refresh the app.")
                else:
                    new_task = pawpal.Task(
                        title=title,
                        description=f"{title} for {selected_pet}",
                        duration_minutes=int(duration),
                        priority=priority,
                        frequency=frequency,
                        pet=pet,
                    )
                    try:
                        owner.add_task(new_task, pet_name=selected_pet)
                    except ValueError as error:
                        st.error(str(error))
                    else:
                        scheduler = pawpal.Scheduler(owner)
                        conflict_warning = scheduler.schedule_task(new_task, selected_day, scheduled_time)
                        if conflict_warning:
                            st.warning(conflict_warning)
                        st.success(f"Added task '{title}' for {selected_pet} on {selected_day} at {scheduled_time}")
    else:
        st.warning("Add a pet before adding tasks.")
    
    all_tasks = owner.get_all_tasks()
    if all_tasks:
        st.write("Current tasks:")
        st.table([
            {
                "title": task.title,
                "pet": task.pet.name if task.pet else "",
                "day": task.scheduled_day or "",
                "time": task.scheduled_time or "",
                "priority": task.priority,
            }
            for task in all_tasks
        ])
    else:
        st.info("No tasks yet. Add one above.")
    
    st.divider()
    
    st.subheader("Build Schedule")
    schedule_day = st.selectbox(
        "Select day to view",
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        index=0,
        key="manual_schedule_day"
    )
    
    scheduler = pawpal.Scheduler(owner)
    if st.button("Generate schedule", key="gen_schedule_btn"):
        daily_tasks = scheduler.get_daily_plan(schedule_day)
        if daily_tasks:
            st.write(f"Today's Schedule for {schedule_day}:")
            for task in daily_tasks:
                st.write(
                    f"- {task.title} for {task.pet.name if task.pet else 'unknown pet'} "
                    f"at {task.scheduled_time} ({task.duration_minutes} min, priority={task.priority})"
                )
        else:
            st.info(f"No tasks scheduled for {schedule_day}.")


# ============================================================================
# MAIN APP ROUTING
# ============================================================================

def main():
    """Main app routing based on current mode."""
    if st.session_state.app_mode == "home":
        show_home_page()
    elif st.session_state.app_mode == "quick":
        show_quick_scheduling()
    elif st.session_state.app_mode == "detailed":
        show_detailed_scheduling()
    elif st.session_state.app_mode == "schedule_view":
        show_schedule_view()
    elif st.session_state.app_mode == "manual":
        show_manual_mode()


if __name__ == "__main__":
    main()
