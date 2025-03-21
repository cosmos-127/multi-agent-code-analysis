import sys
import os

# Get the absolute path of the backend directory
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
# Add the backend directory to sys.path
sys.path.append(backend_path)
print(backend_path)

from git_handler import clone_repository, get_latest_commit, list_files_in_directory

REPO_URL = "https://github.com/aaryansingh704/crowdfunding-project-for-students.git"  # Change this
LOCAL_PATH = "./aryan_repo_clone"
BRANCH = "main"
SUBDIRECTORY = "client"  # Change to a specific folder inside the repo

# Clone the repo
repo = clone_repository(REPO_URL, LOCAL_PATH)

# Get latest commit
latest_commit = get_latest_commit(LOCAL_PATH, BRANCH)

# List files in subdirectory (or full repo)
files = list_files_in_directory(LOCAL_PATH, SUBDIRECTORY)

print("\nFiles to analyze:")
for f in files:
    print(f)
