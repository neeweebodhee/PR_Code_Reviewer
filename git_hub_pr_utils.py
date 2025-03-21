import requests
import os
import re
from dotenv import load_dotenv

# Load API token from .env file
load_dotenv()
GIT_API = os.getenv("GIT_API")

GRAPHQL_URL = "https://api.github.com/graphql"
REST_API_BASE = "https://api.github.com/repos"

def get_open_pr_numbers(repo_owner, repo_name):
    """Fetches all open PR numbers using GitHub GraphQL API."""
    query = f"""
    {{
        repository(owner: "{repo_owner}", name: "{repo_name}") {{
            pullRequests(first: 100, states: OPEN, orderBy: {{field: CREATED_AT, direction: DESC}}) {{
                edges {{
                    node {{
                        number
                        title
                    }}
                }}
            }}
        }}
    }}
    """
    
    headers = {
        "Authorization": f"Bearer {GIT_API}",
        "Accept": "application/vnd.github.v3+json"
    }

    response = requests.post(GRAPHQL_URL, json={"query": query}, headers=headers)

    # Print full API response for debugging
    response_json = response.json()
    print("GraphQL API Response:", response_json)

    if response.status_code == 200:
        if "errors" in response_json:
            print("❌ GraphQL API Errors:", response_json["errors"])
            return []
        
        if "data" in response_json and response_json["data"] and "repository" in response_json["data"]:
            return [(pr["node"]["number"], pr["node"]["title"]) for pr in response_json["data"]["repository"]["pullRequests"]["edges"]]
        else:
            print("❌ Repository or PR data not found in GraphQL response.")
            return []
    
    print(f"❌ API request failed: {response.status_code} - {response.text}")
    return []



def get_pr_diff(repo_owner, repo_name, pr_number):
    """Fetches the diff of a PR using the GitHub REST API."""
    url = f"{REST_API_BASE}/{repo_owner}/{repo_name}/pulls/{pr_number}"
    
    headers = {
        "Authorization": f"Bearer {GIT_API}",
        "Accept": "application/vnd.github.v3.diff"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.text
    return None

def extract_function_changes(diff_text):
    """Extracts function changes from the PR diff."""
    changes = []
    current_file = None
    file_changes = []
    
    function_pattern = re.compile(r'^\+?\s*(def\s+\w+\(.*\):)')

    for line in diff_text.split("\n"):
        if line.startswith("diff --git"):
            if current_file:
                changes.append({"file": current_file, "changes": file_changes})
            file_changes = []
            match = re.search(r'b/(.*)', line)
            current_file = match.group(1) if match else "Unknown file"
        elif function_pattern.match(line):
            change_type = "added" if line.startswith("+") else "removed"
            file_changes.append({"type": change_type, "line": line.strip()})
        elif line.startswith("+") and not line.startswith("+++") and not function_pattern.match(line):
            file_changes.append({"type": "added", "line": line[1:].strip()})
        elif line.startswith("-") and not line.startswith("---") and not function_pattern.match(line):
            file_changes.append({"type": "removed", "line": line[1:].strip()})

    if current_file:
        changes.append({"file": current_file, "changes": file_changes})

    return changes