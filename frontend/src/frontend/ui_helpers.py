import streamlit as st

def set_page_config():
    st.set_page_config(page_title="Multi-Agent Code Analysis", page_icon="🔍")

def show_progress_tracker():
    step_labels = [
        "Step 1️⃣: Cloning Repository",
        "Step 2️⃣: Branch Selection",
        "Step 3️⃣: Choosing Subdirectories",
        "Step 4️⃣: Start Analysis"
    ]
    st.sidebar.markdown("## 🏗️ **Analysis Progress**")
    
    for idx, label in enumerate(step_labels, start=1):
        color = "#4CAF50" if idx < st.session_state.current_step else "#1E88E5" if idx == st.session_state.current_step else "gray"
        st.sidebar.markdown(
            f"<div style='color:{color}; font-weight:bold;'>{label}</div>", unsafe_allow_html=True
        )
