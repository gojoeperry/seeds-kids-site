import requests
import os

def create_github_repo():
    token = os.getenv("GITHUB_TOKEN")  # Must be a personal access token with 'repo' scope
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }
    data = {
        "name": "seeds-kids-site",
        "description": "Static Hugo site for Seeds Kids Worship",
        "private": False
    }

    response = requests.post("https://api.github.com/user/repos", headers=headers, json=data)

    if response.status_code == 201:
        print("✅ GitHub repo 'seeds-kids-site' created successfully.")
    else:
        print(f"[ERROR] GitHub repo creation failed: {response.status_code}")
        print(response.json())

create_github_repo()