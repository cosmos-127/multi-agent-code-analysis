import os
import git
import shutil
import stat


def make_writable(path):
    """Ensure the files are writable before deleting"""
    for root, dirs, files in os.walk(path):
        for dir in dirs:
            os.chmod(os.path.join(root, dir), stat.S_IWRITE)
        for file in files:
            os.chmod(os.path.join(root, file), stat.S_IWRITE)


def clone_repository(repo_url, repo_path):
    """Clones a repository and ensures all branches are fetched."""
    try:
        if os.path.exists(repo_path):
            make_writable(repo_path)  # Fix permission issues
            shutil.rmtree(repo_path)  # Remove existing repo

        repo = git.Repo.clone_from(repo_url, repo_path)
        repo.git.fetch("--all")  # Ensure all remote branches are fetched
        
        return f"✅ Repository cloned successfully: {repo_path}"
    except Exception as e:
        return f"❌ Error cloning repository: {e}"


def get_branches(repo_path):
    """Retrieve all branches (local + remote) in the repository."""
    try:
        repo = git.Repo(repo_path)
        repo.git.fetch("--all")  # Ensure all branches are updated
        # Get remote branches properly
        remote_branches = [
            ref.remote_head for ref in repo.remote().refs if ref.remote_head != "HEAD"
        ]
        
        return remote_branches
    except Exception as e:
        print(f"Error retrieving branches: {e}")
        return []


def checkout_branch(local_path, branch_name):
    """Switches the repository to a different branch."""
    try:
        repo = git.Repo(local_path)
        repo.git.checkout(branch_name)
        return f"Switched to branch {branch_name}"
    except Exception as e:
        return f"Error checking out branch: {e}"
