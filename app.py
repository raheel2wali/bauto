import streamlit as st
import pandas as pd
from profiles import get_chrome_profiles
from automation import fetch_latest_email
from db import init_db, insert_email, get_all_emails
from mcp_client import append_to_google_sheet

# Initialize Database on startup
init_db()

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

    st.markdown("---")
    st.subheader("Run Automation")
    st.markdown("Click below to launch the browser and extract the latest email.")
    
    if st.button("🚀 Start Automation", type="primary"):
        st.info("Automation started. Please wait...")
        
        with st.spinner("Launching browser & fetching email..."):
            email_data = fetch_latest_email(base_dir, selected_profile_name)
        
        if email_data:
            st.success("Email fetched successfully!")
            
            # 1. Log to DB
            insert_email(
                selected_profile_name,
                email_data['sender'],
                email_data['subject'],
                email_data['snippet']
            )
            
            # 2. Sync via MCP
            with st.spinner("Syncing to Google Sheets via MCP..."):
                mcp_res = append_to_google_sheet(
                    email_data['sender'],
                    email_data['subject'],
                    email_data['snippet']
                )
            st.success(f"MCP Sync: {mcp_res}")
            
            # Rerun to update history
            st.rerun()
        else:
            st.error("Failed to fetch email. Please check the logs.")

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
