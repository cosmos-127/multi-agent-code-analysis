from backend.handlers.zip_handler import zipper
from backend.handlers.subdir_handler import list_subdirectories
from backend.handlers.repo_handler import clone_repository, get_branches, checkout_branch
import atexit
import os
import requests
import sys
import streamlit as st
import shutil  # To remove the cloned repo directory
import stat  # To modify file permissions

st.set_page_config(page_title="Multi-Agent Code Analysis", page_icon="🔍")

# Initialize session state before calling any function
if "alerts" not in st.session_state:
    st.session_state.alerts = {"repo": [],
                               "branch": [], "subdirs": [], "analysis": []}

# Load CSS
with open("frontend/style.css", "r") as css_file:
    st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)

# Session state initialization
if "current_step" not in st.session_state:
    st.session_state.current_step = 1
if "branches" not in st.session_state:
    st.session_state.branches = []
if "selected_branch" not in st.session_state:
    st.session_state.selected_branch = "main"
if "subdirs" not in st.session_state:
    st.session_state.subdirs = []
if "selected_subdirs" not in st.session_state:
    st.session_state.selected_subdirs = set()
if "repo_cloned" not in st.session_state:
    st.session_state.repo_cloned = False
if "branch_selected" not in st.session_state:
    st.session_state.branch_selected = False
if "subdirs_fetched" not in st.session_state:
    st.session_state.subdirs_fetched = False
if "zip_ready" not in st.session_state:
    st.session_state.zip_ready = False
if "repo_path" not in st.session_state:
    st.session_state.repo_path = "./repo_clone"

local_path = st.session_state.repo_path


def add_alert(section, message, alert_type="success"):
    """Adds an alert to session state."""
    if "alerts" not in st.session_state:
        st.session_state.alerts = {"repo": [],
                                   "branch": [], "subdirs": [], "analysis": []}
    st.session_state.alerts[section].append((message, alert_type))


def display_alerts(section):
    """Displays and clears alerts for a section."""

    if "alerts" not in st.session_state:
        st.session_state.alerts = {"repo": [],
                                   "branch": [], "subdirs": [], "analysis": []}

    # Get alerts for the given section
    alerts_to_show = st.session_state.alerts.get(section, [])

    # Clear alerts after displaying
    st.session_state.alerts[section] = []

    # Display the alerts
    for msg, msg_type in alerts_to_show:
        if msg_type == "success":
            st.success(msg)
        elif msg_type == "error":
            st.error(msg)
        elif msg_type == "warning":
            st.warning(msg)


def make_writable(path):
    """Ensure all files and directories are writable before deletion"""
    for root, dirs, files in os.walk(path):
        for dir in dirs:
            os.chmod(os.path.join(root, dir), stat.S_IWRITE)
        for file in files:
            os.chmod(os.path.join(root, file), stat.S_IWRITE)


def cleanup_repo():
    """Delete the cloned repository directory after session ends"""
    repo_path = st.session_state.get("repo_path", "")

    if os.path.exists(repo_path):
        try:
            print(f"DEBUG: Deleting repo at {repo_path}")  # Debugging line
            make_writable(repo_path)  # Ensure write permissions
            shutil.rmtree(repo_path)  # Delete the entire repo folder
            print(f"✅ Cleanup completed: {repo_path} deleted.")
        except Exception as e:
            print(f"❌ Error during repo cleanup: {e}")


# Register the cleanup function to be called when the session ends
st.session_state.on_session_end = cleanup_repo

st.title("🔍 Multi-Agent Code Analysis")
st.markdown("#### Analyze your repository using AI-powered agents.")

# Step 1️⃣: Clone Repository
st.subheader("📥 Step 1: Enter Repository URL")
repo_url = st.text_input(
    "🔗 Repository URL", "https://github.com/cosmos-127/portfolio_v1.git")

if st.button("📥 Clone Repository"):
    if os.path.exists(local_path):
        cleanup_repo()

    message = clone_repository(repo_url, local_path)
    add_alert("repo", message, "success" if "successfully" in message else "error")

    display_alerts("repo")  # Show alerts immediately

    if "successfully" in message:
        st.session_state.branches = get_branches(local_path)
        st.session_state.repo_cloned = True
        st.session_state.current_step = 2


# Step 2️⃣: Select Branch
if st.session_state.repo_cloned:
    st.subheader("🌿 Step 2: Select a Branch")

    selected_branch = st.selectbox(
        "Choose a branch", st.session_state.branches)

    if st.button("✅ Confirm Branch"):
        message = checkout_branch(local_path, selected_branch)
        add_alert("branch", message,
                  "success" if "Switched" in message else "error")

        st.session_state.selected_branch = selected_branch
        st.session_state.branch_selected = True
        st.session_state.current_step = 3

    display_alerts("branch")  # Call after the button logic
# Step 3️⃣: Choose Subdirectories
if st.session_state.branch_selected:
    st.subheader("📂 Step 3: Choose Subdirectories")

    if st.button("📂 Fetch Subdirectories"):
        subdirs = list_subdirectories(local_path)
        if isinstance(subdirs, list):
            st.session_state.subdirs = subdirs
            st.session_state.subdirs_fetched = True
            add_alert("subdirs", "✅ Subdirectories fetched!", "success")
        else:
            add_alert("subdirs", subdirs, "error")
        st.rerun()  # Ensure UI updates

    # Display alerts outside buttons so they persist
    display_alerts("subdirs")

    if st.session_state.subdirs_fetched:
        analyze_all = st.checkbox("Select all files", value=False)

        # Select all subdirectories if analyze_all is checked
        selected_subdirs = st.session_state.subdirs if analyze_all else st.multiselect(
            "Select Subdirectories", options=st.session_state.subdirs)

        if st.button("✅ Apply Selection", key="apply_selection_button"):
            # Make sure the selection is stored in session state
            st.session_state.selected_subdirs = set(selected_subdirs)

            # Ensure any old zip is removed before creating a new one
            output_zip = "selected_subdirs.zip"
            if os.path.exists(output_zip):
                os.remove(output_zip)

            # Create a new zip file with the selected directories
            zipper(local_path, st.session_state.selected_subdirs, output_zip)
            st.session_state.zip_ready = os.path.exists(output_zip)
            st.session_state.output_zip_path = output_zip  # Store zip path

            if st.session_state.zip_ready:
                add_alert(
                    "subdirs", "✅ Subdirectories zipped successfully!", "success")

            st.rerun()  # Ensure UI updates to reflect new zip file

    display_alerts("subdirs")  # Show alert before the download button

    # Check if the zip is ready and display the download button
    if st.session_state.zip_ready and os.path.exists(st.session_state.output_zip_path):
        st.subheader("📥 Download Selected Files")
        with open(st.session_state.output_zip_path, "rb") as zip_file:
            st.download_button(
                label="📥 Download Files",
                data=zip_file,
                file_name="selected_subdirectories.zip",
                mime="application/zip"
            )


# Step 4️⃣: Start Analysis
if st.session_state.zip_ready:
    st.subheader("🚀 Step 4: Start Analysis")

    project_description = st.text_area(
        "📝 Enter Project Description", "Describe the tech stack or architecture..."
    )

    # Ensure "Start Analysis" button remains visible
    if "analysis_started" not in st.session_state:
        st.session_state.analysis_started = False

    if not st.session_state.analysis_started:
        if st.button("🚀 Start Analysis", key="start_analysis_button"):
            if not project_description.strip():
                st.warning(
                    "⚠️ Please enter a project description before analyzing.")
            else:
                add_alert("analysis", "🔍 Analysis started!", "success")
                st.session_state.analysis_started = True
                st.rerun()  # Refresh UI to show progress message

    if st.session_state.analysis_started:
        with st.spinner("🔍 Analyzing tech stack..."):
            try:
                response = requests.get(
                    "http://localhost:8000/api/analyze-git-summary",
                    params={"query": project_description}
                )

                if response.status_code == 200:
                    st.success("✅ Analysis Complete!")
                    st.subheader("📊 Analysis Results")
                    st.json(response.json())  # Display formatted JSON response
                else:
                    st.error(
                        f"❌ Error {response.status_code}: {response.text}")

            except requests.exceptions.RequestException as e:
                st.error(f"❌ Failed to connect to backend: {e}")


atexit.register(cleanup_repo)
