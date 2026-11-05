import streamlit as st
import pandas as pd
import threading
import time
import asyncio
from profiles import get_chrome_profiles, get_chrome_user_data_dir
from automation import run_automation
from db import init_db, insert_email, get_all_emails, set_profile_task, get_profile_task, get_due_tasks, update_last_run
from mcp_client import append_to_google_sheet

# Initialize Database on startup
init_db()

# --- Background Scheduler ---
def run_scheduler():
    user_data_dir = get_chrome_user_data_dir()
    while True:
        due_tasks = get_due_tasks()
        for profile_dir, task_url in due_tasks:
            try:
                # Update last_run first so it doesn't run continuously if it gets stuck
                update_last_run(profile_dir) 
                
                result = run_automation(user_data_dir, profile_dir, task_url)
                if result['status'] == 'success' and result['type'] == 'gmail':
                    insert_email(
                        profile_dir,
                        result['sender'],
                        result['subject'],
                        result['snippet']
                    )
                    # Use asyncio since we are in a background thread and mcp_client uses asyncio
                    # But append_to_google_sheet handles its own asyncio.run.
                    append_to_google_sheet(
                        result['sender'],
                        result['subject'],
                        result['snippet']
                    )
            except Exception as e:
                print(f"Background automation failed for {profile_dir}: {e}")
                
        time.sleep(30) # Check every 30 seconds

# Start the daemon thread if it's not already running
if 'scheduler_started' not in st.session_state:
    st.session_state.scheduler_started = True
    t = threading.Thread(target=run_scheduler, daemon=True)
    t.start()
# -----------------------------

st.set_page_config(page_title="BAuto - Browser Automation", page_icon="🤖", layout="wide")

st.title("🤖 BAuto: Browser Automation & Email Sync")
st.markdown("Automate Gmail data extraction and sync to Google Sheets seamlessly.")

# Layout
col1, col2 = st.columns([1, 2])

with col1:
    st.header("Settings")
    # Fetch profiles
    with st.spinner("Scanning for browser profiles..."):
        profiles, base_dir = get_chrome_profiles()
    
    if not profiles:
        st.warning(f"No profiles found in {base_dir}. Ensure Chrome is installed.")
        profile_options = {"Default": "Default"}
    else:
        profile_options = profiles

    selected_profile_name = st.selectbox(
        "Select Browser Profile",
        options=list(profile_options.keys()),
        format_func=lambda x: profile_options[x]
    )
    
    task_info = get_profile_task(selected_profile_name)
    
    task_url = st.text_input(
        "Task Website URL",
        value=task_info["url"],
        help="URL to open (e.g. https://mail.google.com/mail/u/0/#inbox or any custom website)"
    )
    
    timer_minutes = st.number_input(
        "Timer (minutes)",
        min_value=0,
        value=task_info["timer"],
        help="How often to run this task in the background. 0 means disabled."
    )
    
    if st.button("💾 Save Task"):
        set_profile_task(selected_profile_name, task_url, timer_minutes)
        st.success(f"Task updated for profile: {profile_options[selected_profile_name]}")

    st.markdown("---")
    st.subheader("Run Automation")
    st.markdown("Click below to launch the browser and execute the task.")
    
    if st.button("🚀 Start Automation", type="primary"):
        st.info("Automation started. Please wait...")
        
        # Load the saved task URL to ensure we run what's in the DB
        task_info = get_profile_task(selected_profile_name)
        run_url = task_info["url"]
        
        # Update last run so the scheduler doesn't run it immediately if timer is active
        update_last_run(selected_profile_name)
        
        with st.spinner(f"Launching browser to open: {run_url}..."):
            result = run_automation(base_dir, selected_profile_name, run_url)
        
        if result['status'] == 'success':
            if result['type'] == 'gmail':
                st.success("Email fetched successfully!")
                
                # 1. Log to DB
                insert_email(
                    selected_profile_name,
                    result['sender'],
                    result['subject'],
                    result['snippet']
                )
                
                # 2. Sync via MCP
                with st.spinner("Syncing to Google Sheets via MCP..."):
                    mcp_res = append_to_google_sheet(
                        result['sender'],
                        result['subject'],
                        result['snippet']
                    )
                st.success(f"MCP Sync: {mcp_res}")
                
                # Rerun to update history
                st.rerun()
            else:
                st.success(f"Successfully opened {result['url']}")
                if result.get('note'):
                    st.info(result['note'])
        elif result['status'] == 'not_logged_in':
             st.warning("Gmail is not logged in. Opened Gmail login page instead.")
        else:
            err_msg = result.get('message', 'Unknown error')
            st.error(f"Automation failed: {err_msg}. Please check the logs.")

with col2:
    st.header("Automation History")
    
    history_data = get_all_emails()
    
    if not history_data:
        st.info("No automation history yet. Run an automation to see results here.")
    else:
        # Columns: id, profile_dir, sender, subject, snippet, timestamp
        df = pd.DataFrame(history_data, columns=["ID", "Profile", "Sender", "Subject", "Snippet", "Timestamp"])
        
        # Display as a dataframe
        st.dataframe(
            df.drop(columns=["ID"]),
            use_container_width=True,
            hide_index=True
        )
