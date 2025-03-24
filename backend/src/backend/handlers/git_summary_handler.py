# Defines the API endpoint for triggering the Git summary agent.

from fastapi import APIRouter
from backend.agents.git_summary_agent import GitSummaryAgent

router = APIRouter()

@router.post("/analyze_git")
async def analyze_git(data: dict):
    # Create an instance of GitSummaryAgent
    agent = GitSummaryAgent(
        name="GitSummaryAgent",
        llm="your_model_here",  # Specify the language model you're using
        role="Analyze and provide insights about Git repository data",
        goal="To provide a detailed summary of the repository.",
        backstory="This agent gathers and summarizes the details of a Git repository."
    )
    
    # Analyze the provided Git data
    summary = agent.analyze(data)
    
    return summary
