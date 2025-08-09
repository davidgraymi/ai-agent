import argparse
from src.ai_agent import run_agent

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_name", type=str, help="GitHub repository name")
    parser.add_argument("issue_number", type=int, help="GitHub issue number")
    parser.add_argument("--max_iterations", type=int, default=10)
    args = parser.parse_args()

    run_agent(args.repo_name, args.issue_number, args.max_iterations)
