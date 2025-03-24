import os
import xml.etree.ElementTree as ET
import json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import re
from datetime import datetime
from git_scrap_data_basic import get_git_info
import logging
import time
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()



# Get the absolute path of the project root (go one level up from 'backend')


# Get the absolute path of the project root
CURRENT_FILE_PATH = os.path.abspath(__file__)
BACKEND_DIR = os.path.dirname(CURRENT_FILE_PATH)  # Gets 'backend/report_gen_engines'
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, "..", ".."))  # Moves up two levels

# Construct absolute paths using PROJECT_ROOT
DIRECTORY = os.path.join(PROJECT_ROOT, os.getenv("DIRECTORY", "repo_clone"))
GIT_SCRAP_FILE = os.path.join(PROJECT_ROOT, os.getenv("GIT_SCRAP_FILE", "backend/output/analysis_result.json"))



# Mapping of file extensions to languages
LANGUAGE_EXTENSIONS = {
    "py": "Python", "js": "JavaScript", "java": "Java", "cpp": "C++",
    "c": "C", "cs": "C#", "rb": "Ruby", "php": "PHP", "ts": "TypeScript",
    "go": "Go", "rs": "Rust", "swift": "Swift", "kt": "Kotlin", "dart": "Dart",
    "html": "HTML", "css": "CSS", "sh": "Shell"
}

# Directories to ignore
IGNORED_DIRS = {"node_modules", "venv", "dist", ".git", "__pycache__", "tests"}

# Files to ignore
IGNORED_FILES = {"README.md", "README.txt", "LICENSE", "CONTRIBUTING.md"}

# File size limit (in MB) to skip large non-code files
FILE_SIZE_LIMIT_MB = 5


def detect_frameworks(DIRECTORY):
    frameworks = set()

    def parse_json_file(filepath, keys):
        """Parse JSON file and extract dependencies from given keys."""
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    data = json.load(f)
                    extracted = set()
                    for key in keys:
                        extracted.update(data.get(key, {}).keys())
                    return extracted
            except json.JSONDecodeError:
                pass
        return set()

    # Check for JavaScript dependencies
    frameworks.update(parse_json_file(os.path.join(
        DIRECTORY, "package.json"), ["dependencies", "devDependencies"]))

    # Check for PHP dependencies
    frameworks.update(parse_json_file(os.path.join(
        DIRECTORY, "composer.json"), ["require", "require-dev"]))

    # Check for Java Maven dependencies
    pom_xml = os.path.join(DIRECTORY, "pom.xml")
    if os.path.exists(pom_xml):
        try:
            tree = ET.parse(pom_xml)
            root = tree.getroot()
            # Handle Maven XML namespace
            ns = {'mvn': 'http://maven.apache.org/POM/4.0.0'}
            frameworks.update(dep.text for dep in root.findall(
                ".//mvn:dependency/mvn:artifactId", ns) if dep.text)
        except ET.ParseError:
            pass

    # Check for Python dependencies
    requirements_txt = os.path.join(DIRECTORY, "requirements.txt")
    if os.path.exists(requirements_txt):
        try:
            with open(requirements_txt, "r", encoding="utf-8") as f:
                frameworks.update([line.strip().split("==")[0]
                                  for line in f if line.strip()])
        except Exception:
            pass

    # Check for .NET projects
    if any(file.endswith(".csproj") for file in os.listdir(DIRECTORY)):
        frameworks.add(".NET")

    # Check for PHP frameworks
    if os.path.exists(os.path.join(DIRECTORY, "artisan")):
        frameworks.add("Laravel")
    if os.path.exists(os.path.join(DIRECTORY, "bin/console")):
        frameworks.add("Symfony")
    if os.path.exists(os.path.join(DIRECTORY, "index.php")):
        frameworks.add("PHP Web")

    # Check for JavaScript frameworks
    js_frameworks = {
        "angular.json": "Angular",
        "next.config.js": "Next.js",
        "gatsby-config.js": "Gatsby"
    }

    for file, framework in js_frameworks.items():
        if os.path.exists(os.path.join(DIRECTORY, file)):
            frameworks.add(framework)

    # Check for Vue.js and Svelte
    for file in os.listdir(DIRECTORY):
        if file.endswith(".vue"):
            frameworks.add("Vue.js")
        if file.endswith(".svelte"):
            frameworks.add("Svelte")

    # Detect Express.js
    if "express" in frameworks:
        frameworks.add("Express.js")

    # Detect React (Check for react-scripts)
    if "react-scripts" in frameworks:
        frameworks.add("React")

    return list(frameworks)


def determine_project_architecture(DIRECTORY):
    has_docker, has_k8s, has_serverless, has_event_driven, has_layered, has_hexagonal = False, False, False, False, False, False
    service_dirs = []

    for root, dirs, files in os.walk(DIRECTORY):
        if "Dockerfile" in files or "docker-compose.yml" in files:
            has_docker = True
        if any(file.endswith(".yaml") and "k8s" in file for file in files):
            has_k8s = True
        if "services" in dirs:
            service_dirs.append(os.path.join(root, "services"))
        if any(file.endswith(".yml") and "serverless" in file for file in files):
            has_serverless = True
        if any(folder in dirs for folder in ["adapters", "ports"]):
            has_hexagonal = True
        if any(folder in dirs for folder in ["controller", "service", "repository"]):
            has_layered = True
        if any(dependency in files for dependency in ["kafka", "rabbitmq"]):
            has_event_driven = True

    if has_k8s or service_dirs:
        return "Microservices"
    if has_serverless:
        return "Serverless"
    if has_event_driven:
        return "Event-Driven"
    if has_hexagonal:
        return "Hexagonal"
    if has_layered:
        return "Layered"
    if has_docker:
        return "Modular"
    return "Monolithic"


def check_license_and_secrets(DIRECTORY):
    security_info = {"license": None, "potential_secrets": []}
    license_file = os.path.join(DIRECTORY, "LICENSE")

    # Detect common licenses from first few lines
    license_map = {
        "MIT License": "MIT",
        "Apache License": "Apache 2.0",
        "GNU General Public License": "GPL",
        "BSD License": "BSD",
        "Mozilla Public License": "MPL",
    }

    if os.path.exists(license_file):
        with open(license_file, "r", encoding="utf-8", errors="ignore") as f:
            first_lines = "\n".join(f.readlines()[:10])  # Read first 10 lines
            for key, license_type in license_map.items():
                if key in first_lines:
                    security_info["license"] = license_type
                    break  # Stop checking once a match is found

    # Enhanced secret detection patterns
    secret_patterns = re.compile(
        r"(API_KEY|SECRET_KEY|TOKEN|PASSWORD|ACCESS_KEY|PRIVATE_KEY)\s*=\s*[\'\"].+[\'\"]")

    for root, _, files in os.walk(DIRECTORY):
        for file in files:
            if file.endswith((".env", "config.json", "settings.py", "config.yaml")):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    security_info["potential_secrets"].extend(
                        secret_patterns.findall(f.read()))

    return security_info


def check_testing_and_docs(DIRECTORY):
    return {
        "has_readme": os.path.isfile(os.path.join(DIRECTORY, "README.md")),
        "has_docs": os.path.isdir(os.path.join(DIRECTORY, "docs")),
        "has_tests": any(os.path.isdir(os.path.join(DIRECTORY, test_dir)) for test_dir in ["tests", "test", "spec"])
    }


def analyze_folder(DIRECTORY, GIT_SCRAP_FILE):
    file_counts = defaultdict(int)
    total_files = 0
    total_folders = 0

    for root, dirs, files in os.walk(DIRECTORY):
        if any(ignored in root for ignored in IGNORED_DIRS):
            continue
        total_folders += len(dirs)
        for file in files:
            if file in IGNORED_FILES:
                continue
            ext = file.split(".")[-1]
            if ext in LANGUAGE_EXTENSIONS:
                file_counts[LANGUAGE_EXTENSIONS[ext]] += 1
                total_files += 1

    language_usage = {
        lang: f"{round((count / total_files) * 100, 2)} %"
        for lang, count in file_counts.items()
    } if total_files > 0 else {}

    frameworks = detect_frameworks(DIRECTORY)
    git_info = get_git_info(DIRECTORY)
    project_architecture = determine_project_architecture(DIRECTORY)
    security_info = check_license_and_secrets(DIRECTORY)
    documentation = check_testing_and_docs(DIRECTORY)

    analysis_data = {
        "project_architecture": project_architecture or "",
        "frameworks": frameworks or "",
        "total_files": total_files or "",
        "total_folders": total_folders or "",
        "language_usage": language_usage or "",
        "git_info": git_info or "",
        "security_info": security_info or "",
        "documentation": documentation or "",
    }

    # Save to JSON file
    if GIT_SCRAP_FILE:
        with open(GIT_SCRAP_FILE, "w", encoding="utf-8") as json_file:
            json.dump(analysis_data, json_file, indent=4)

        logging.info(f"Analysis saved to {GIT_SCRAP_FILE}")
    else:
        logging.error("No valid output file path provided.")

    return analysis_data


if __name__ == "__main__":
    if os.path.isdir(DIRECTORY):
        logging.info(f"Starting analysis for: {DIRECTORY}")

        start_time = time.time()
        analysis_result = analyze_folder(DIRECTORY, GIT_SCRAP_FILE)
        end_time = time.time()

        logging.info(
            f"Analysis completed in {end_time - start_time:.2f} seconds")

        # Pretty-print the output without escaping Unicode characters
        print(json.dumps(analysis_result, indent=4, ensure_ascii=False))

    else:
        logging.error(
            "Invalid directory path. Please enter a valid folder path.")
