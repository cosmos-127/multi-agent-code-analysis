import streamlit as st

def initialize_session():
    default_values = {
        "current_step": 1,
        "branches": [],
        "selected_branch": "main",
        "analyze_all": False,
        "subdirs": [],
        "selected_subdirs": set(),
        "repo_cloned": False,
        "branch_selected": False,
        "subdirs_fetched": False,
        "zip_ready": False,
        "alerts": {"repo": [], "branch": [], "subdirs": [], "analysis": []}
    }
    
    for key, value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = value
