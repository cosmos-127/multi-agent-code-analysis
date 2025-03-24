from datetime import datetime
import logging
import time
from collections import Counter
import os
import subprocess
import json


# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set logging level
    format="%(asctime)s - %(levelname)s - %(message)s",  # Log format
    handlers=[
        logging.StreamHandler()  # Print logs to the console
    ]
)


def format_date(raw_date):
    """Convert raw Git commit date to a readable format."""
    try:
        parsed_date = datetime.strptime(raw_date, "%a %b %d %H:%M:%S %Y %z")
        return parsed_date.strftime("%B %d, %Y")  # Example: "March 23, 2025"
    except ValueError:
        return raw_date


def run_git_command(directory, command):
    """Run a Git command and return output."""
    try:
        return subprocess.check_output(command, cwd=directory, text=True, encoding="utf-8", errors="ignore").strip()
    except FileNotFoundError:
        return ""  # Handle missing Git
    except subprocess.CalledProcessError:
        return None  # Handle Git errors


def get_repository_metadata(directory):
    """Fetch basic repository metadata."""
    metadata = {}

    # Get default branch
    metadata["default_branch"] = run_git_command(
        directory, ["git", "symbolic-ref", "--short", "HEAD"])

    # Get repository size (parse 'size-pack' value)
    repo_size_output = run_git_command(
        directory, ["git", "count-objects", "-vH"])
    size_pack_line = next((line for line in repo_size_output.split(
        "\n") if "size-pack" in line), "size-pack: 0")
    metadata["repository_size"] = size_pack_line.split(":")[-1].strip()

    # Get number of releases (tags)
    tags_output = run_git_command(directory, ["git", "tag"])
    metadata["number_of_releases"] = len(
        tags_output.split("\n")) if tags_output else 0

    return metadata


def get_commit_analysis(directory):
    """Efficiently analyze commit history and developer activity."""
    commit_info = {}

    # Single command to get last commit date, total commits, and contributor details
    last_commit_date = run_git_command(
        directory, ["git", "log", "-1", "--format=%cd"])

    commit_count = int(run_git_command(
        directory, ["git", "rev-list", "--count", "HEAD"]))

    # Get contributors efficiently
    contributor_data = run_git_command(directory, ["git", "shortlog", "-sn"])
    contributors = contributor_data.split("\n") if contributor_data else []
    most_active_contributor = contributors[0].split(
        "\t", 1)[-1].strip() if contributors else "N/A"

    commit_info.update({
        "last_commit_date": format_date(last_commit_date),
        "commit_count": commit_count,
        "total_contributors": len(contributors),
        "most_active_contributor": most_active_contributor
    })

    # Optimize commit dates retrieval for longest inactive period
    commit_dates_output = run_git_command(directory, [
                                          "git", "log", "--pretty=format:%cd", "--date=iso", "--since='2 years ago'"])
    commit_dates = [
        datetime.fromisoformat(date.strip().replace(" ", "T"))
        for date in commit_dates_output.split("\n") if date.strip()
    ]

    if len(commit_dates) > 1:
        max_gap = max(
            (commit_dates[i] - commit_dates[i + 1]).days for i in range(len(commit_dates) - 1)
        )
    else:
        max_gap = 0

    commit_info["longest_inactive_period_for_repository"] = f'{max_gap} Days'

    # Optimize computing average lines changed per commit
    numstat_output = run_git_command(
        directory, ["git", "log", "--numstat", "--since='1 year ago'"])
    total_changes = sum(
        int(parts[0]) + int(parts[1]
                            ) if parts[0].isdigit() and parts[1].isdigit() else 0
        for line in numstat_output.split("\n")
        if (parts := line.split()) and len(parts) >= 2
    )

    return commit_info


def get_branch_info(directory):
    """Fetch the total number of branches (local and remote)."""
    branches = run_git_command(directory, ["git", "branch", "-a"])
    return {"branch_count": len([b for b in branches.split("\n") if b.strip()])}


def get_recent_commit_messages(directory, num_commits=5):
    """Fetch recent commit messages."""
    commits = run_git_command(
        directory, ["git", "log", f"-{num_commits}", '--pretty=format:%h - %s'])
    return {"recent_commits": commits.split("\n") if commits else []}


def get_repository_age(directory):
    """Get the date of the first commit and calculate the repo age."""
    first_commit_date_str = run_git_command(
        directory, ["git", "log", "--reverse", "--format=%cd", "--date=iso"]).split("\n")[0]

    if not first_commit_date_str:
        return {"repo_age": "Unknown"}

    # Convert to datetime object
    first_commit_date = datetime.strptime(
        first_commit_date_str, "%Y-%m-%d %H:%M:%S %z")

    # Calculate age
    now = datetime.now(first_commit_date.tzinfo)
    age_in_days = (now - first_commit_date).days
    years = age_in_days // 365
    months = (age_in_days % 365) // 30

    return {
        "repo_first_commit": first_commit_date_str,
        "repo_age": f"{years} years, {months} months old"
    }


def get_largest_file(directory):
    """Find the largest file in the repo."""
    largest_file = run_git_command(directory, ["git", "ls-files", "-z"])
    if largest_file:
        file_sizes = {file: os.path.getsize(os.path.join(
            directory, file)) for file in largest_file.split("\x00") if file}
        largest = max(file_sizes, key=file_sizes.get, default="N/A")
        return {"largest_file": largest, "size_bytes": file_sizes.get(largest, 0)}
    return {"largest_file_in_repository": "N/A", "size_bytes": 0}


def get_repository_activity(directory):
    """Fetch last contributors and most modified directories."""
    activity = {}

    # Get last 5 unique contributors
    contributors_output = run_git_command(
        directory, ["git", "log", "--format=%an", "-5"])
    activity["last_5_contributors"] = list(
        set(contributors_output.split("\n"))) if contributors_output else []

    # Get modified files and extract directory names
    modified_files_output = run_git_command(
        directory, ["git", "log", "--name-only", "--pretty=format:"])
    modified_files = [f.strip()
                      for f in modified_files_output.split("\n") if f.strip()]

    if modified_files:
        # Convert file paths to directories
        modified_dirs = [os.path.dirname(
            f) for f in modified_files if os.path.dirname(f)]
        # Get the top 3 most modified directories
        top_dirs = [dir_name for dir_name,
                    _ in Counter(modified_dirs).most_common(5)]
    else:
        top_dirs = []

    activity["top_5_modified_directories"] = top_dirs

    return activity


def format_size(bytes_size):
    """Convert bytes to human-readable format (KB, MB, GB, etc.)."""
    suffixes = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while bytes_size >= 1024 and i < len(suffixes) - 1:
        bytes_size /= 1024.0
        i += 1
    return f"{bytes_size:.2f} {suffixes[i]}"


def get_file_directory_insights(directory):
    """Analyze file structures and extensions without using Unix commands."""
    file_list_output = run_git_command(directory, ["git", "ls-files"])

    if not file_list_output:
        return {"average_file_size": "0 B", "most_frequent_extension": "N/A"}

    file_list = file_list_output.split("\n")

    # Count file extensions
    ext_count = Counter(os.path.splitext(f)[1] if os.path.splitext(f)[
                        1] else "No Extension" for f in file_list)
    most_frequent_ext = ext_count.most_common(1)[0][0] if ext_count else "N/A"

    # Get file sizes manually
    file_sizes = []
    for file in file_list:
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path):
            file_sizes.append(os.path.getsize(file_path))

    avg_file_size = sum(file_sizes) / len(file_sizes) if file_sizes else 0
    formatted_avg_size = format_size(avg_file_size)

    return {
        "average_file_size": formatted_avg_size,
        "most_frequent_extension": most_frequent_ext
    }


def get_git_info(directory):
    """Main function to collect all repository insights."""
    git_info = {}
    # Basic repo details (size, name, default branch)
    git_info.update(get_repository_metadata(directory))
    # Establish repo's historical timeline
    git_info.update(get_repository_age(directory))
    git_info.update(get_branch_info(directory))  # Analyze branches
    git_info.update(get_recent_commit_messages(
        directory))  # Recent commit activity
    # Contributor and commit trends
    git_info.update(get_commit_analysis(directory))
    # Activity trends & periods of inactivity
    git_info.update(get_repository_activity(directory))
    # Identify the largest files in the repo
    git_info.update(get_largest_file(directory))
    # File type distributions & directory structures
    git_info.update(get_file_directory_insights(directory))

    return git_info


if __name__ == "__main__":
    folder_path = input("Enter the folder path to analyze: ").strip()

    if os.path.isdir(folder_path):
        logging.info(f"Starting analysis for: {folder_path}")

        start_time = time.time()
        git_info = get_git_info(folder_path)
        end_time = time.time()

        logging.info(
            f"Analysis completed in {end_time - start_time:.2f} seconds")

        # Pretty-print the output without escaping Unicode characters
        print(json.dumps(git_info, indent=4, ensure_ascii=False))

    else:
        logging.error(
            "Invalid directory path. Please enter a valid folder path.")
