import time
import json
from langchain.agents import initialize_agent, Tool
from langchain_community.llms import OpenAI, Ollama
from src.config import LLM_PROVIDER, LLM_MODEL, DRY_RUN
from src.github_client import get_issue_data
from src.tools.file_tools import read_file, apply_file_patch, make_unified_diff
from src.tools.test_tools import run_tests
from src.state_manager import save_state, load_state

def get_llm():
    if LLM_PROVIDER == "ollama":
        return Ollama(model=LLM_MODEL)
    else:
        return OpenAI(model=LLM_MODEL)

def run_agent(repo_name, issue_number, max_iterations=10, base_branch="main", repo_root="."):
    # load previous state
    state = load_state()
    if state and state.get("issue_number") == issue_number and state.get("repo_name") == repo_name:
        history = state.get("history", [])
        iteration = state.get("last_iteration", 0)
    else:
        history = []
        iteration = 0

    issue_data = get_issue_data(repo_name, issue_number)
    llm = get_llm()

    # define tools exposed to the LLM
    tools = [
        Tool(name="read_file", func=lambda p: read_file(p), description="Read a file from the repo by path"),
        Tool(name="list_repo_tree", func=lambda: __list_tree(repo_root), description="List files in repo"),
        Tool(name="run_tests", func=lambda: run_tests(), description="Run tests and return results"),
        Tool(
            name="apply_patch",
            func=lambda path, new_content, summary: _apply_patch_helper(path, new_content, summary, repo_name, issue_number),
            description="Provide (path, new_content, commit_summary). Creates a branch, makes a patch, commits and opens a PR. Returns status and URLs."
        ),
        Tool(
            name="list_repo_tree",
            func=lambda: __list_tree(repo_root),
            description="List all tracked files in the repo, respecting .gitignore",
        ),
    ]

    agent = initialize_agent(
        tools, llm, agent="zero-shot-react-description", verbose=True
    )

    start_time = time.time()
    for i in range(iteration, iteration + max_iterations):
        # Build prompt with structured data (issue + repo tree summary)
        prompt = {
            "issue": {
                "number": issue_data.get("issue", {}).get("number"),
                "title": issue_data.get("issue", {}).get("title"),
                "body": issue_data.get("issue", {}).get("body"),
                "labels": [l["name"] for l in issue_data.get("issue", {}).get("labels", [])] if issue_data.get("issue") else [],
            },
            "comments": issue_data.get("comments", []),
            "history": history,
            "instructions": "You are an autonomous developer. Use provided tools to make safe, small changes. When you want to change files, call apply_patch(path, new_content, summary). Stop when the task is complete, by returning the text 'TASK_COMPLETE' in your final response."
        }

        # The agent.run expects text input: stringify JSON (structured inputs are better than one big blob)
        prompt_text = json.dumps(prompt, indent=2)
        result = agent.run(prompt_text)
        history.append({"iteration": i, "result": result})
        save_state(issue_number, history)

        # quick stop if agent says task complete
        if "TASK_COMPLETE" in result:
            save_state(issue_number, history)
            print("Agent reports task complete. Exiting loop.")
            break

        # safety: timeout by wall clock (example 30 minutes)
        if time.time() - start_time > 60 * 30:
            print("Timeout reached; saving state.")
            save_state(issue_number, history)
            break

    # final save
    save_state(issue_number, history)

# small helpers
def __list_tree(repo_root="."):
    import subprocess
    res = subprocess.run(["git", "ls-tree", "-r", "HEAD", "--name-only"], capture_output=True, text=True, cwd=repo_root)
    return res.stdout.strip().splitlines()

def _apply_patch_helper(path: str, new_content: str, summary: str, repo_name: str, issue_number: int):
    """
    Called by the agent via the Tool. We create a descriptive branch name using timestamp/issue/iteration.
    """
    import datetime, hashlib
    ts = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    h = hashlib.sha1((path + summary + ts).encode()).hexdigest()[:7]
    branch_name = f"agent/issue-{issue_number}/{h}"
    return apply_file_patch(path, new_content, repo_name, branch_name, summary, issue_number, dry_run=DRY_RUN)
