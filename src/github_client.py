import requests
from src.config import GITHUB_TOKEN, REPO_OWNER, REPO_NAME

BASE_URL = "https://api.github.com"

def get_issue_data(issue_number):
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
    issue = requests.get(f"{BASE_URL}/repos/{REPO_OWNER}/{REPO_NAME}/issues/{issue_number}", headers=headers).json()
    comments = requests.get(f"{BASE_URL}/repos/{REPO_OWNER}/{REPO_NAME}/issues/{issue_number}/comments", headers=headers).json()

    # simple tree snapshot (recursive)
    tree = requests.get(f"{BASE_URL}/repos/{REPO_OWNER}/{REPO_NAME}/git/trees/main?recursive=1", headers=headers).json()

    # GraphQL example for projects/epics (simplified — you can extend)
    graphql_url = "https://api.github.com/graphql"
    graphql_query = """
    query($owner:String!, $name:String!, $number:Int!) {
      repository(owner:$owner, name:$name) {
        issue(number:$number) {
          number
          title
          labels(first:10) { nodes { name } }
          milestone { title, number }
          projectCards(first:10) { nodes { project { name } } }
        }
      }
    }
    """
    gh_headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    resp = requests.post(graphql_url, json={"query": graphql_query, "variables":{"owner":REPO_OWNER,"name":REPO_NAME,"number": issue_number}}, headers=gh_headers)
    graphql_data = {}
    if resp.status_code == 200:
        graphql_data = resp.json().get("data", {})
    return {"issue": issue, "comments": comments, "tree": tree, "graphql": graphql_data}
