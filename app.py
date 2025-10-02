# app.py
import streamlit as st
import pandas as pd
import json
import os
import calendar
import numpy as np 
from datetime import datetime, date, timedelta
import plotly.express as px
import time
import sys # <--- ADDED IMPORT

# ----------------------------
# Helpers: Fix PyInstaller Pathing
# ----------------------------
def resource_path(relative_path):
    """Get the absolute path to a resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        # This is where your added data files are extracted.
        base_path = sys._MEIPASS
    except Exception:
        # If not running in PyInstaller, use the normal path (current directory)
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# ----------------------------
# File paths (same folder as app.py)
# ----------------------------
# --- UPDATED TO USE THE HELPER FUNCTION ---
TASKS_FILE = resource_path("tasks.json")
REWARDS_FILE = resource_path("rewards.json")
LOG_FILE = resource_path("xp_log.csv")
# ----------------------------
# Helpers: load/save persistent data
# ----------------------------
def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_log(path):
    if os.path.exists(path):
        return pd.read_csv(path, parse_dates=["time"])
    return pd.DataFrame(columns=["time", "type", "name", "minutes", "xp"])

def save_log(df, path):
    df.to_csv(path, index=False)

# ----------------------------
# XP Formula Implementation (Task Earning)
# ----------------------------
def calculate_task_xp(base_xp, base_minutes, multiplier, actual_minutes):
    """
    Calculates XP using the formula:
    XP = ROUND( (base_xp/base_minutes * T) * (Multiplier) ^ ((T-Base_minutes)/Base_minutes), 0)
    T is actual_minutes
    """
    if actual_minutes < base_minutes:
        # If less than min time, we give proportional XP.
        xp_calc = (actual_minutes / base_minutes) * base_xp
        return round(xp_calc, 2) # Use float precision for partial completion
    
    # Base XP per minute
    base_xp_per_min = base_xp / base_minutes
    
    # Part 1: Proportional XP
    proportional_xp = base_xp_per_min * actual_minutes
    
    # Part 2: Multiplier
    # (T - Base_minutes) / Base_minutes
    exponent = (actual_minutes - base_minutes) / base_minutes
    
    # (Multiplier) ^ exponent
    multiplier_factor = multiplier ** exponent
    
    # Total XP
    total_xp = proportional_xp * multiplier_factor
    
    # The requirement is to round the final result to the nearest integer.
    return int(np.round(total_xp, 0))


# ----------------------------
# XP Formula Implementation (Reward Cost)
# ----------------------------
def calculate_reward_cost(base_xp_cost, base_minutes, multiplier, actual_minutes):
    """
    Calculates XP cost using the formula (same structure as task XP, but for cost):
    Cost = ROUND( (base_xp/base_minutes * T) * (Multiplier) ^ ((T-Base_minutes)/Base_minutes), 0)
    T is actual_minutes
    """
    if actual_minutes < base_minutes:
        # If less than min time, we use proportional cost.
        xp_calc = (actual_minutes / base_minutes) * base_xp_cost
        return round(xp_calc, 2) # Use float precision for partial completion
        
    # Base XP cost per minute
    base_xp_per_min = base_xp_cost / base_minutes
    
    # Part 1: Proportional XP
    proportional_xp = base_xp_per_min * actual_minutes
    
    # Part 2: Multiplier
    # (T - Base_minutes) / Base_minutes
    exponent = (actual_minutes - base_minutes) / base_minutes
    
    # (Multiplier) ^ exponent
    multiplier_factor = multiplier ** exponent
    
    # Total XP Cost
    total_xp = proportional_xp * multiplier_factor
    
    # Round the final result to the nearest integer.
    return int(np.round(total_xp, 0))


# ----------------------------
# Initialize persistent storages
# ----------------------------
if "tasks" not in st.session_state:
    st.session_state.tasks = load_json(TASKS_FILE)
if "rewards" not in st.session_state:
    st.session_state.rewards = load_json(REWARDS_FILE)
if "log_df" not in st.session_state:
    st.session_state.log_df = load_log(LOG_FILE)


# --- TIMER STATE INITIALIZATION ---
if 'timer_active' not in st.session_state:
    st.session_state.timer_active = False
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'session_type' not in st.session_state:
    st.session_state.session_type = None
if 'target_minutes' not in st.session_state:
    st.session_state.target_minutes = 0
if 'xp_value' not in st.session_state:
    st.session_state.xp_value = 0
if 'session_details' not in st.session_state:
    st.session_state.session_details = {}
# ----------------------------------


# compute current total XP from log
def compute_total_xp(df):
    if df.empty:
        return 0.0
    earned = df.loc[df["type"] == "Add", "xp"].sum()
    spent = df.loc[df["type"] == "Spend", "xp"].sum()
    return float(earned) - float(spent)


# --- TIMER HELPER ---
def play_ring_sound():
    """Injects an HTML audio tag to play a brief sound effect."""
    # Using a royalty-free, short sound clip (replace with your own if needed)
    # Note: Streamlit may cache this URL, use a different one if needed to force update.
    AUDIO_URL = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3" 
    
    st.markdown(
        f"""
        <audio autoplay="true">
            <source src="{AUDIO_URL}" type="audio/mp3">
        </audio>
        """,
        unsafe_allow_html=True,
    )
# --------------------


# ----------------------------
# UI: top tabs (chrome-like) - This sets up the tabs visually
# ----------------------------
st.set_page_config(page_title="XP Tracker", layout="wide")
tabs = st.tabs(["➕ Add XP", "💸 Spend XP", "📝 Task Manager", "🎯 Reward Manager", "📊 Statistics", "📅 Calendar", "⚙️ Reset Data"])
add_tab, spend_tab, task_tab, reward_tab, stats_tab, cal_tab, reset_tab = tabs
# -------------------------------------------------------------

# ----------------------------
# TAB: Task Manager (create/edit) 
# ----------------------------
with task_tab:
    st.header("📝 Task Manager — Create tasks that give XP")
    st.write("Define task rules: Base time (min duration), XP for that time, and the multiplier for extended work.")
    with st.form("task_form", clear_on_submit=True):
        new_name = st.text_input("Task name")
        col1, col2, col3 = st.columns(3)
        with col1:
            # This is the '10' from (T-10)/10
            base_minutes = st.number_input("Minimum, Duration/Reps/Quantity", min_value=1, value=10, step=1)
        with col2:
            # This determines the base XP per minute (Base XP / Base Minutes)
            base_xp = st.number_input("Base XP", min_value=0.1, value=5.0, step=0.1, format="%.2f")
        with col3:
            # This is the '1.2' from (1.2)^...
            multiplier = st.number_input("Multiplier", min_value=1.0, value=1.2, step=0.01, format="%.2f")

        submitted = st.form_submit_button("Add / Update Task")
        if submitted:
            if not new_name.strip():
                st.error("Enter valid task name.")
            else:
                st.session_state.tasks[new_name.strip()] = {
                    "base_minutes": int(base_minutes),
                    "base_xp": float(base_xp),
                    "multiplier": float(multiplier)
                }
                save_json(TASKS_FILE, st.session_state.tasks)
                st.success(f"Saved task: {new_name.strip()} — {base_minutes} min = {base_xp} XP, Multiplier: {multiplier}")

    if st.session_state.tasks:
        st.subheader("Existing tasks")
        for tname, meta in st.session_state.tasks.items():
            m = meta.get('multiplier', 1.0) 
            st.write(f"- **{tname}** | Base: {meta['base_minutes']} min = {meta['base_xp']} XP | **Multiplier: {m}**")
        st.write("---")
        to_delete = st.selectbox("Delete task (choose one)", options=[""] + list(st.session_state.tasks.keys()), key="task_to_delete")
        if to_delete:
            if st.button("Delete task"):
                st.session_state.tasks.pop(to_delete, None)
                save_json(TASKS_FILE, st.session_state.tasks)
                st.success(f"Deleted task '{to_delete}'")

# ----------------------------
# TAB: Reward Manager
# ----------------------------
with reward_tab:
    st.header("🎯 Reward Manager — Create rewards that cost XP")
    st.write("Create rewards with a base time, base XP cost, and a **Multiplier** for proportional/exponential cost growth.")
    with st.form("reward_form", clear_on_submit=True):
        new_rname = st.text_input("Reward name (e.g. Play Game)")
        rcol1, rcol2, rcol3 = st.columns(3) 
        with rcol1:
            r_base_minutes = st.number_input("Base Duration (min)", min_value=1, value=30, step=1, key="r_min")
        with rcol2:
            r_base_xp = st.number_input("Base XP Cost (for base duration)", min_value=0.1, value=10.0, step=0.1, format="%.2f", key="r_xp")
        with rcol3:
            r_multiplier = st.number_input("Cost Multiplier Base (e.g. 1.2)", min_value=1.0, value=1.2, step=0.01, format="%.2f", key="r_multiplier")

        rsubmitted = st.form_submit_button("Add / Update Reward")
        if rsubmitted:
            if not new_rname.strip():
                st.error("Enter valid reward name.")
            else:
                st.session_state.rewards[new_rname.strip()] = {
                    "base_minutes": int(r_base_minutes),
                    "base_xp": float(r_base_xp),
                    "multiplier": float(r_multiplier)
                }
                save_json(REWARDS_FILE, st.session_state.rewards)
                st.success(f"Saved reward: {new_rname.strip()} — {r_base_minutes} min = {r_base_xp} XP, Multiplier: {r_multiplier}")

    if st.session_state.rewards:
        st.subheader("Existing rewards")
        for rname, meta in st.session_state.rewards.items():
            m = meta.get('multiplier', 1.0)
            st.write(f"- *{rname}* | Base: {meta['base_minutes']} min = {meta['base_xp']} XP | **Multiplier: {m}** (cost)")
        st.write("---")
        r_to_delete = st.selectbox("Delete reward (choose one)", options=[""] + list(st.session_state.rewards.keys()), key="reward_to_delete")
        if r_to_delete:
            if st.button("Delete reward", key="delete_reward_btn"):
                st.session_state.rewards.pop(r_to_delete, None)
                save_json(REWARDS_FILE, st.session_state.rewards)
                st.success(f"Deleted reward '{r_to_delete}'")

# ----------------------------
# TAB: Add XP (log doing tasks) - UPDATED FOR TIMER
# ----------------------------
with add_tab:
    st.header("➕ Session: Earn XP (do a task)")
    st.write(f"Total XP: *{compute_total_xp(st.session_state.log_df):.0f}*") 

    if st.session_state.timer_active and st.session_state.session_type == "add":
        # --- TIMER IS RUNNING ---
        
        elapsed_seconds = (datetime.now() - st.session_state.start_time).total_seconds()
        target_seconds = st.session_state.target_minutes * 60
        
        remaining_seconds = max(0, target_seconds - elapsed_seconds)
        
        minutes_remaining = int(remaining_seconds // 60)
        seconds_remaining = int(remaining_seconds % 60)
        
        progress = elapsed_seconds / target_seconds if target_seconds > 0 else 1.0

        if remaining_seconds <= 0:
            # --- TIMER END: AWARD XP ---
            xp_to_log = st.session_state.xp_value
            details = st.session_state.session_details
            
            # Log the XP
            now = datetime.now()
            row = {"time": now, "type": "Add", "name": details['name'], "minutes": details['minutes'], "xp": xp_to_log}
            st.session_state.log_df = pd.concat([st.session_state.log_df, pd.DataFrame([row])], ignore_index=True)
            save_log(st.session_state.log_df, LOG_FILE)
            
            # Reset Timer State
            st.session_state.timer_active = False
            st.session_state.start_time = None
            st.session_state.session_type = None

            play_ring_sound()
            st.balloons()
            st.success(f"🎉 **SESSION COMPLETE!** Logged +{xp_to_log:.0f} XP for {details['name']} ({details['minutes']} min).")
            # Rerun to clear the timer display and show the success message clearly
            time.sleep(1)
            st.rerun()

        # Display progress bar and timer
        st.subheader(f"Session Active: {st.session_state.session_details['name']}")
        
        # Display the timer with a non-breaking space to keep it centered
        st.markdown(
            f"## <div style='text-align: center;'>{minutes_remaining:02d}:{seconds_remaining:02d}</div>", 
            unsafe_allow_html=True
        )
        
        st.progress(progress, text=f"Time remaining: {minutes_remaining} min {seconds_remaining} sec")

        # Rerun the script every 1 second to update the timer display
        time.sleep(1)
        st.rerun()
        
    else:
        # --- TIMER IS IDLE: START FORM ---
        xp_save_val = 0.0
        is_disabled_add = True 
        task_choice = None
        minutes = 1
        
        if not st.session_state.tasks:
            st.info("No tasks available. Go to *Task Manager* to create tasks.")
        else:
            is_disabled_add = False 
            task_choice = st.selectbox("Choose task", options=list(st.session_state.tasks.keys()), key="add_task_choice")
            base = st.session_state.tasks[task_choice]
            multiplier_val = base.get('multiplier', 1.0) 
            
            st.write(f"Rules: **Min Duration: {base['base_minutes']} min**, **Base XP: {base['base_xp']}**, **Multiplier: {multiplier_val}**")
            
            minutes = st.number_input("Target Minutes Performed", min_value=1, value=base["base_minutes"], step=1, key="add_minutes")
            
            xp_calc = calculate_task_xp(base_xp=base['base_xp'], base_minutes=base["base_minutes"], multiplier=multiplier_val, actual_minutes=int(minutes))
            
            if isinstance(xp_calc, int):
                st.info(f"You will earn: **{xp_calc} XP** for {minutes} min (Calculated using Multiplier)")
                xp_save_val = float(xp_calc)
            else:
                st.warning(f"Duration is less than min duration. You earn proportional XP: **{xp_calc:.2f} XP** for {minutes} min")
                xp_save_val = xp_calc

        if st.button("▶️ START XP Session", key="start_add_session_btn", disabled=is_disabled_add):
            # --- START TIMER LOGIC ---
            st.session_state.timer_active = True
            st.session_state.start_time = datetime.now()
            st.session_state.session_type = "add"
            st.session_state.target_minutes = int(minutes)
            st.session_state.xp_value = xp_save_val
            st.session_state.session_details = {'name': task_choice, 'minutes': int(minutes)}
            
            st.info(f"Starting session for **{task_choice}** for {minutes} minutes.")
            # Rerun to switch to the timer display immediately
            time.sleep(1) 
            st.rerun()

# ----------------------------
# TAB: Spend XP - UPDATED FOR TIMER
# ----------------------------
with spend_tab:
    st.header("💸 Session: Spend XP (use a reward)")
    st.write(f"Total XP: *{compute_total_xp(st.session_state.log_df):.0f}*")

    balance = compute_total_xp(st.session_state.log_df)

    if st.session_state.timer_active and st.session_state.session_type == "spend":
        # --- TIMER IS RUNNING (SAME AS ADD XP) ---
        
        elapsed_seconds = (datetime.now() - st.session_state.start_time).total_seconds()
        target_seconds = st.session_state.target_minutes * 60
        remaining_seconds = max(0, target_seconds - elapsed_seconds)
        
        minutes_remaining = int(remaining_seconds // 60)
        seconds_remaining = int(remaining_seconds % 60)
        
        progress = elapsed_seconds / target_seconds if target_seconds > 0 else 1.0

        if remaining_seconds <= 0:
            # --- TIMER END: SESSION ENDED (XP ALREADY SPENT) ---
            details = st.session_state.session_details
            
            # Reset Timer State
            st.session_state.timer_active = False
            st.session_state.start_time = None
            st.session_state.session_type = None

            play_ring_sound()
            st.info(f"**SESSION COMPLETE!** Your reward session for {details['name']} is over.")
            # Rerun to clear the timer display
            time.sleep(1)
            st.rerun()

        # Display progress bar and timer
        st.subheader(f"Session Active: {st.session_state.session_details['name']}")
        
        st.markdown(
            f"## <div style='text-align: center;'>{minutes_remaining:02d}:{seconds_remaining:02d}</div>", 
            unsafe_allow_html=True
        )
        st.progress(progress, text=f"Time remaining: {minutes_remaining} min {seconds_remaining} sec")

        # Rerun the script every 1 second to update the timer display
        time.sleep(1)
        st.rerun()
        
    else:
        # --- TIMER IS IDLE: START FORM ---
        xp_save_val = 0.0
        is_disabled_spend = True
        reward_choice = None
        rminutes = 1

        if not st.session_state.rewards:
            st.info("No rewards available. Go to *Reward Manager* to create rewards.")
        else:
            is_disabled_spend = False 
            reward_choice = st.selectbox("Choose reward", options=list(st.session_state.rewards.keys()), key="spend_reward_choice")
            rbase = st.session_state.rewards[reward_choice]
            
            r_multiplier_val = rbase.get('multiplier', 1.0)
            st.write(f"Rules: **Min Duration: {rbase['base_minutes']} min**, **Base XP Cost: {rbase['base_xp']}**, **Multiplier: {r_multiplier_val}**")

            rminutes = st.number_input("Target Minutes of reward", min_value=1, value=rbase["base_minutes"], step=1, key="spend_minutes")
            
            xp_cost = calculate_reward_cost(
                base_xp_cost=rbase['base_xp'],
                base_minutes=rbase["base_minutes"],
                multiplier=r_multiplier_val,
                actual_minutes=int(rminutes)
            )
            
            if isinstance(xp_cost, int):
                st.info(f"This will *cost: **{xp_cost} XP*** for {rminutes} min (Calculated using Multiplier)")
                xp_save_val = float(xp_cost)
            else:
                st.warning(f"Duration is less than min duration. Proportional cost: **{xp_cost:.2f} XP** for {rminutes} min")
                xp_save_val = xp_cost

            if xp_save_val > balance:
                st.error(f"Not enough XP! Current: {balance:.2f}, required: {xp_save_val:.2f}")
                is_disabled_spend = True
                
        if st.button("▶️ START XP Session", key="start_spend_session_btn", disabled=is_disabled_spend):
            # --- START TIMER & INSTANTLY LOG SPEND XP ---
            
            # 1. Log the Spend XP immediately
            now = datetime.now()
            row = {"time": now, "type": "Spend", "name": reward_choice, "minutes": int(rminutes), "xp": xp_save_val} 
            st.session_state.log_df = pd.concat([st.session_state.log_df, pd.DataFrame([row])], ignore_index=True)
            save_log(st.session_state.log_df, LOG_FILE)
            
            # 2. Start the Timer State
            st.session_state.timer_active = True
            st.session_state.start_time = datetime.now()
            st.session_state.session_type = "spend"
            st.session_state.target_minutes = int(rminutes)
            st.session_state.xp_value = xp_save_val # Storing for future reference, even though it's already logged
            st.session_state.session_details = {'name': reward_choice, 'minutes': int(rminutes)}
            
            st.success(f"Cost of -{xp_save_val:.0f} XP logged instantly! Enjoy your reward session.")
            # Rerun to switch to the timer display
            time.sleep(1) 
            st.rerun()

# ----------------------------
# TAB: Statistics (UNCHANGED)
# ----------------------------
with stats_tab:
    st.header("📊 Statistics")
    total = compute_total_xp(st.session_state.log_df)
    st.subheader(f"Total XP: {total:.0f}")

    if not st.session_state.log_df.empty:
        df = st.session_state.log_df.copy()
        df["time"] = pd.to_datetime(df["time"])
        df_sorted = df.sort_values("time")
        # cumulative total over time
        df_sorted["signed_xp"] = df_sorted.apply(lambda r: r["xp"] if r["type"] == "Add" else -r["xp"], axis=1)
        df_sorted["cumsum"] = df_sorted["signed_xp"].cumsum()
        
        # Line chart for cumulative XP
        fig = px.line(df_sorted, x="time", y="cumsum", labels={"cumsum": "Total XP", "time": "Time"})
        st.plotly_chart(fig, use_container_width=True)

        # Bar chart for XP breakdown by task
        earned_df = df_sorted[df_sorted['type'] == 'Add'].groupby('name')['xp'].sum().reset_index()
        if not earned_df.empty:
            fig_bar = px.bar(
                earned_df.sort_values('xp', ascending=False),
                x='name',
                y='xp',
                labels={'xp': 'Total Earned XP', 'name': 'Task'},
                title='XP Earned Breakdown by Task'
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
        # show recent activity
        st.subheader("Recent activity")
        st.dataframe(df_sorted.tail(50).loc[:, ["time", "type", "name", "minutes", "xp"]].iloc[::-1])
    else:
        st.info("No activity logged yet.")

# ----------------------------
# TAB: Calendar (FIXED CSS so only calendar buttons are hidden)
# ----------------------------
with cal_tab:
    st.header("📅 Calendar (click a day to open/close summary)")
    
    # --- Custom CSS for Calendar Styling ---
    st.markdown("""
    <style>
    /* 0. STREAMLIT COLUMN HEADER ALIGNMENT */
    .stHorizontalBlock {
        align-items: flex-start !important;
        margin-bottom: 5px; 
    }
    .stHorizontalBlock div[data-testid^="stMarkdownContainer"] {
        text-align: center;
    }

    /* 1. INVISIBLE BUTTON: Only calendar buttons (keys start with cal_) */
    button[data-testid="stButton"][id^="cal_"] {
        height: 80px; 
        width: 100%; 
        aspect-ratio: 1 / 1; 
        display: block;
        padding: 0; 
        margin: 0; 
        margin-top: -5px; 
        margin-left: 30px; 
        
        opacity: 0; /* hidden only for calendar */
        position: relative;
        z-index: 10; 
        border: none !important; 
        cursor: pointer;
    }

    /* Hover highlight for clickable calendar cells */
    .calendar-cell-content:hover {
        border: 2px solid var(--primary-color);
        background-color: rgba(0, 123, 255, 0.1);
    }

    /* 2. VISIBLE CONTENT: Styles the div content that the user actually sees */
    .calendar-cell-content {
        height: 70px;
        width: 70%;
        position: relative;
        top: -70px; 
        margin-bottom: -85px; 
        margin-left: 20px;
        
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        align-items: center;
        padding: 5px;
        line-height: 1.2;
        
        border: 1px solid var(--border-color); 
        border-radius: 4px;
        z-index: 5;
        background-color: var(--secondary-background); 
        transition: border 0.1s;
    }
    
    /* Highlight the actively selected day */
    .calendar-cell-content.selected-day {
        border: 3px solid var(--primary-color); 
        padding: 3px; 
    }

    .date-number { font-size: 1.2em; font-weight: 800; color: var(--text-color); margin-bottom: 2px; }
    .xp-totals { font-size: 0.75em; color: #808080; text-align: center; }
    .empty-space { height: 80px; }
    </style>
    """, unsafe_allow_html=True)
    
    # --- Step 1: Initialize State for Toggle ---
    if 'selected_calendar_date' not in st.session_state:
        st.session_state.selected_calendar_date = None 
    
    # --- Step 2: Display Summary First (If Selected) ---
    selected_date_str = st.session_state.selected_calendar_date

    if selected_date_str:
        selected_date_obj = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        
        with st.container(border=True):
            st.markdown(f"### Activity Summary for {selected_date_obj.strftime('%d %b %Y')}")
            
            df = st.session_state.log_df.copy()
            df["time"] = pd.to_datetime(df["time"])
            df["date"] = df["time"].dt.date 
            day_rows = df[df["date"] == selected_date_obj].sort_values("time") 
            total_e = day_rows[day_rows["type"]=="Add"]["xp"].sum()
            total_s = day_rows[day_rows["type"]=="Spend"]["xp"].sum()
            
            if not day_rows.empty:
                st.markdown('<div style="max-height: 300px; overflow-y: auto;">', unsafe_allow_html=True)
                for _, r in day_rows.iterrows():
                    tstr = r["time"].strftime("%I:%M %p")
                    sign = "+" if r["type"] == "Add" else "-"
                    st.write(f"&nbsp; • {tstr} — **{r['type']}**: {r['name']} ({r['minutes']} min) **{sign}{r['xp']:.2f} XP**")
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("---")
                st.markdown(f"**Total Earned:** {total_e:.0f} | **Total Spent:** {total_s:.2f}")
            else:
                st.write("No activity recorded on this day.")

            st.markdown(f'<p style="font-size: 0.85em; color: #aaa;">Click the **{selected_date_obj.day}** date box again to close this summary.</p>', unsafe_allow_html=True)

        st.markdown("---") 

    # --- Step 3: Calendar Grid Logic ---
    if not st.session_state.log_df.empty:
        df = st.session_state.log_df.copy()
        df["time"] = pd.to_datetime(df["time"])
        df["date"] = df["time"].dt.date 

        daily = df.groupby(["date", "type"])["xp"].sum().unstack(fill_value=0).reset_index()
        daily["Earned"] = daily.get("Add", 0)
        daily["Spent"] = daily.get("Spend", 0)

        min_date = df["date"].min().replace(day=1)
        max_dt = df["date"].max()
        max_date = (max_dt.replace(day=1) + pd.offsets.MonthEnd(0)).date()

        current = min_date
        while current <= max_date:
            st.subheader(current.strftime("%B %Y"))
            week_days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
            header_cols = st.columns(7)
            for i, wd in enumerate(week_days):
                header_cols[i].markdown(f"**{wd}**") 

            cal_obj = calendar.Calendar(firstweekday=6) 
            month_matrix = cal_obj.monthdatescalendar(current.year, current.month)

            for week in month_matrix:
                cols = st.columns(7)
                for i, day in enumerate(week):
                    with cols[i]:
                        if day.month != current.month:
                            st.markdown("<div class='empty-space'></div>", unsafe_allow_html=True)
                            continue

                        row = daily[daily["date"] == day]
                        earned = float(row["Earned"]) if not row.empty and "Earned" in row.columns else 0.0
                        spent = float(row["Spent"]) if not row.empty and "Spent" in row.columns else 0.0
                        
                        key = f"cal_{day}"
                        day_str = day.strftime('%Y-%m-%d') 

                        if st.button("", key=key): 
                            if st.session_state.selected_calendar_date == day_str:
                                st.session_state.selected_calendar_date = None
                            else:
                                st.session_state.selected_calendar_date = day_str
                            st.rerun() 

                        highlight_class = " selected-day" if st.session_state.selected_calendar_date == day_str else ""
                        visible_html = f"""
                        <div class="calendar-cell-content{highlight_class}">
                            <div class="date-number">{day.day}</div>
                            <div class="xp-totals">E: {earned:.0f}<br>S: {spent:.0f}</div>
                        </div>
                        """
                        st.markdown(visible_html, unsafe_allow_html=True)

            current = (current + pd.offsets.MonthBegin(1)).date()

# ----------------------------
# TAB: Reset Data (FIXED FOR RELIABLE CONFIRMATION)
# ----------------------------
with reset_tab:
    st.header("⚙️ Data Management")

    # --- Utility Functions (unchanged) ---
    def reset_all_data():
        """Deletes all data files and clears state."""
        for file in [TASKS_FILE, REWARDS_FILE, LOG_FILE]:
            if os.path.exists(file):
                os.remove(file)
        
        # Reset session state and re-create empty files
        st.session_state.tasks = {}
        st.session_state.rewards = {}
        st.session_state.log_df = pd.DataFrame(columns=["time", "type", "name", "minutes", "xp"])
        save_json(TASKS_FILE, st.session_state.tasks)
        save_json(REWARDS_FILE, st.session_state.rewards)
        save_log(st.session_state.log_df, LOG_FILE)
        st.success("✅ All data (Tasks, Rewards, XP Log) has been successfully reset!")
        time.sleep(2)
        st.rerun()

    def reset_xp_log():
        """Resets the XP log (and statistics) only."""
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
        
        # Reset session state log
        st.session_state.log_df = pd.DataFrame(columns=["time", "type", "name", "minutes", "xp"])
        save_log(st.session_state.log_df, LOG_FILE)
        st.success("✅ XP Log and all statistics have been reset (Tasks and Rewards remain).")
        time.sleep(2)
        st.rerun()

    def reset_tasks():
        """Resets only the tasks."""
        if os.path.exists(TASKS_FILE):
            os.remove(TASKS_FILE)
        
        st.session_state.tasks = {}
        save_json(TASKS_FILE, st.session_state.tasks)
        st.success("✅ All tasks have been deleted (XP and Rewards remain).")
        time.sleep(2)
        st.rerun()

    def reset_rewards():
        """Resets only the rewards."""
        if os.path.exists(REWARDS_FILE):
            os.remove(REWARDS_FILE)
        
        st.session_state.rewards = {}
        save_json(REWARDS_FILE, st.session_state.rewards)
        st.success("✅ All rewards have been deleted (XP and Tasks remain).")
        time.sleep(2)
        st.rerun()

    def undo_last_action():
        """Deletes the last entry from the XP log."""
        if st.session_state.log_df.empty:
            st.warning("⚠️ No actions to undo.")
            return

        # Get the row to be deleted (last row in the dataframe)
        last_row = st.session_state.log_df.iloc[-1]
        action = last_row["type"]
        name = last_row["name"]
        xp_value = last_row["xp"]

        # Drop the last row
        st.session_state.log_df = st.session_state.log_df.drop(st.session_state.log_df.index[-1]).reset_index(drop=True)
        save_log(st.session_state.log_df, LOG_FILE)

        st.success(f"↩️ UNDO successful! Deleted last registered action: **{action} {name}** ({xp_value:.2f} XP).")
        time.sleep(2)
        st.rerun()


    # ------------------ UNDO SECTION ------------------
    st.subheader("Undo Last Action")
    st.info("The Undo button deletes the very last item logged, whether it was adding XP or spending XP.")
    
    current_log_df = st.session_state.log_df
    last_action = "N/A"
    
    if not current_log_df.empty:
        last_row = current_log_df.iloc[-1]
        last_action = f"**{last_row['type']}** {last_row['name']} ({last_row['xp']:.2f} XP) at {pd.to_datetime(last_row['time']).strftime('%I:%M %p')}"

    st.markdown(f"**Last Logged Action:** {last_action}")
    if st.button("↩️ UNDO Last Action", type="secondary", key="undo_btn"):
        undo_last_action()

    st.markdown("---")
    
    # ------------------ GRANULAR RESET SECTION (FIXED) ------------------
    st.subheader("Granular Resets")
    st.warning("These actions are permanent. Use the checkbox to enable the button.")

    # Reset XP/Statistics
    confirm_xp = st.checkbox("Confirm deletion of XP Log and Statistics?", key="confirm_xp_state")
    if st.button("Reset XP Log and Statistics Only", help="Deletes all XP earnings and spendings, resetting your balance to 0. Keeps all Tasks and Rewards.", key="reset_xp_btn", disabled=not confirm_xp):
        reset_xp_log()

    # Reset Tasks
    confirm_tasks = st.checkbox("Confirm deletion of all Tasks?", key="confirm_tasks_state")
    if st.button("Reset Tasks Only", help="Deletes all your defined tasks. Keeps your XP balance and Rewards.", key="reset_tasks_btn", disabled=not confirm_tasks):
        reset_tasks()

    # Reset Rewards
    confirm_rewards = st.checkbox("Confirm deletion of all Rewards?", key="confirm_rewards_state")
    if st.button("Reset Rewards Only", help="Deletes all your defined rewards. Keeps your XP balance and Tasks.", key="reset_rewards_btn", disabled=not confirm_rewards):
        reset_rewards()
            
    st.markdown("---")

    # ------------------ FULL RESET SECTION (FIXED) ------------------
    st.subheader("Full Application Reset")
    st.error("🚨 **DANGER ZONE:** This deletes EVERYTHING (Tasks, Rewards, and XP Log).")

    confirm_all = st.checkbox("Final Confirmation: Reset EVERYTHING?", key="confirm_all_state")
    if st.button("🔥 Confirm and Reset ALL Data", type="primary", key="reset_all_btn", disabled=not confirm_all):
        reset_all_data()

# ---------------------------- END ----------------------------