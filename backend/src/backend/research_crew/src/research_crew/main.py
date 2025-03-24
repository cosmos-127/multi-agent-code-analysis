#!/usr/bin/env python
import sys
import warnings

from datetime import datetime
from research_crew.crew import ResearchCrew
import json
import os

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

from backend.report_gen_engines.language_engine import analyze_folder

def run():
    """
    Run the crew.
    """
    # Ensure the file exists before trying to load it
    if os.path.exists(ANALYSIS_RESULT_FILE):
        with open(ANALYSIS_RESULT_FILE, "r", encoding="utf-8") as file:
            analysis_data = json.load(file)
            print("Successfully loaded analysis data!")
    else:
        print(f"Error: {ANALYSIS_RESULT_FILE} not found")

    inputs = {
        'topic': 'Git repository Summary',
        'git_scraped_data': analysis_data,
        'current_date': str(datetime.now())
    }

    try:
        ResearchCrew().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = { 
        "topic": "AI LLMs"
    }
    try:
        ResearchCrew().crew().train(n_iterations=int(
            sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        ResearchCrew().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }
    try:
        ResearchCrew().crew().test(n_iterations=int(
            sys.argv[1]), openai_model_name=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")
