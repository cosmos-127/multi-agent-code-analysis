import sys
import os
import streamlit as st
from backend.git_handler import clone_repository, list_subdirectories, get_branches, checkout_branch

# Set Page Configuration
st.set_page_config(page_title="Multi-Agent Code Analysis", page_icon="🔍")

# Custom CSS for Centered Layout
st.markdown("""
    <style>
        .block-container {
            max-width: 750px;  /* Adjust width */
            padding-top: 20px;
        }
        .stButton {
            display: flex;
            justify-content: center;
        }
        .stButton button {
            width: 100%; /* Full width */
        }
        .stCheckbox span, .stSelectbox label, .stTextInput label {
            font-size: 16px;
        }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("🔍 Multi-Agent Code Analysis")
st.markdown("#### Analyze your repository using AI-powered agents.")

# Initialize session state variables
if "branches" not in st.session_state:
    st.session_state.branches = []
if "selected_branch" not in st.session_state:
    st.session_state.selected_branch = "main"
if "analyze_all" not in st.session_state:
    st.session_state.analyze_all = False
if "subdirs" not in st.session_state:
    st.session_state.subdirs = []
if "selected_subdirs" not in st.session_state:
    st.session_state.selected_subdirs = set()
if "repo_cloned" not in st.session_state:
    st.session_state.repo_cloned = False
if "branch_selected" not in st.session_state:
    st.session_state.branch_selected = False

# Step 1️⃣: Repository Input Section
st.divider()
st.subheader("Step 1️⃣: 📥 Enter Repository URL")

repo_url = st.text_input(
    "🔗 Repository URL", "https://github.com/aaryansingh704/crowdfunding-project-for-students.git")
local_path = "./repo_clone"

if st.button("📥 Clone Repository"):
    if repo_url:
        clone_repository(repo_url, local_path, "main")
        st.session_state.branches = get_branches(
            local_path)  # Fetch all branches
        st.session_state.repo_cloned = True
        st.success("✅ Repository cloned successfully!")
    else:
        st.error("❌ Please enter a valid repository URL.")

# Step 2️⃣: Branch Selection (Expands After Clone)
if st.session_state.repo_cloned and st.session_state.branches:
    st.divider()
    st.subheader("Step 2️⃣: 🌿 Select a Branch")

    with st.form("branch_form"):
        selected_branch = st.selectbox(
            "Choose a branch",
            st.session_state.branches,
            index=st.session_state.branches.index(
                st.session_state.selected_branch)
            if st.session_state.selected_branch in st.session_state.branches else 0
        )

        branch_submitted = st.form_submit_button("✅ Confirm Branch")

    if branch_submitted:
        if selected_branch != st.session_state.selected_branch:
            st.session_state.selected_branch = selected_branch
            checkout_branch(local_path, selected_branch)
            st.session_state.subdirs = []  # Reset subdirectories

        st.session_state.branch_selected = True
        st.success(f"✅ Branch `{st.session_state.selected_branch}` selected!")

# Step 3️⃣: Fetch & Select Subdirectories (Expands After Branch Selection)
if st.session_state.branch_selected:
    st.divider()
    st.subheader("Step 3️⃣: 📂 Select Files for Analysis")

    if st.button("📂 Fetch Subdirectories"):
        if os.path.exists(local_path):
            try:
                subdirs = list_subdirectories(local_path)
                st.session_state.subdirs = subdirs  # Update session state
                st.success(
                    f"✅ Subdirectories fetched for branch `{st.session_state.selected_branch}`!")
            except Exception as e:
                st.error(f"⚠️ Error fetching subdirectories: {e}")
        else:
            st.error("❌ Repository not found! Clone the repo first.")

    # Subdirectory Selection Form
    with st.form("subdir_form"):
        st.markdown("### 📁 Choose Subdirectories")

        analyze_all = st.checkbox(
            "Analyze all files", value=st.session_state.analyze_all)

        if analyze_all:
            selected_subdirs = set(st.session_state.subdirs)
        else:
            selected_subdirs = st.multiselect(
                "Select Subdirectories",
                options=st.session_state.subdirs,
                default=list(st.session_state.selected_subdirs),
            )

        subdir_submitted = st.form_submit_button("✅ Apply Selection")

    if subdir_submitted:
        st.session_state.selected_subdirs = set(selected_subdirs)
        st.session_state.analyze_all = analyze_all
        st.success("Selections updated!")

# 🚀 Final Step: Start Analysis (Only Appears After Selecting Subdirectories)
if st.session_state.selected_subdirs:
    st.divider()
    st.subheader("🚀 Step 4️⃣: Start Analysis")

    if st.button("🚀 Start Analysis"):
        st.success(
            f"🔍 Analyzing: {', '.join(st.session_state.selected_subdirs)}")
        st.write(
            f"🔄 Analysis in progress on `{st.session_state.selected_branch}`...")
