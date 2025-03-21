import git
import os


def clone_repository(repo_url, local_path, branch="main"):
    """Clones the repository to a local path."""
    if os.path.exists(local_path):
        print("Repository already exists, pulling latest changes...")
        repo = git.Repo(local_path)
        repo.remotes.origin.pull()
    else:
        print(f"Cloning repository from {repo_url} (Branch: {branch})...")
        # Ensure branch is passed correctly
        git.Repo.clone_from(repo_url, local_path, branch=branch)


def get_latest_commit(repo_path: str, branch: str = "main"):
    """Fetch the latest commit from the given branch."""
    repo = git.Repo(repo_path)
    repo.git.checkout(branch)
    latest_commit = repo.head.commit
    print(
        f"🔹 Latest commit: {latest_commit.hexsha} by {latest_commit.author.name} at {latest_commit.committed_datetime}")
    return latest_commit


def list_files_in_directory(repo_path: str, subdirectory: str = None):
    """List all files in a repository or a specific subdirectory."""
    target_path = os.path.join(
        repo_path, subdirectory) if subdirectory else repo_path
    if not os.path.exists(target_path):
        print(" Error: Subdirectory does not exist!")
        return []

    files = []
    for root, _, filenames in os.walk(target_path):
        for filename in filenames:
            files.append(os.path.join(root, filename))

    print(
        f" Found {len(files)} files in {'subdirectory: ' + subdirectory if subdirectory else 'entire repo'}")
    return files


def list_subdirectories(local_path):
    """Lists subdirectories inside the cloned repository."""
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"Path '{local_path}' does not exist.")

    return [d for d in os.listdir(local_path) if os.path.isdir(os.path.join(local_path, d))]


def get_branches(repo_path):
    """Returns a list of all branches in the repo"""
    repo = git.Repo(repo_path)
    return [branch.name for branch in repo.branches]


def checkout_branch(repo_path, branch_name):
    """Checks out the given branch in the repo"""
    repo = git.Repo(repo_path)
    repo.git.checkout(branch_name)
