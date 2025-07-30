# Claude Code Prompt: Deploy Hugo Site to Vercel (Production)

import subprocess
import os
from pathlib import Path

def deploy_to_vercel():
    site_dir = Path.cwd() / "site"
    if not site_dir.exists():
        print("[ERROR] `site/` directory does not exist. Cannot deploy.")
        return

    os.chdir(site_dir)
    print(f"Changed working directory to: {site_dir}")

    print("Running `vercel --prod` to deploy the Hugo site to production...")
    result = subprocess.run(["vercel", "--prod"], text=True)

    if result.returncode == 0:
        print("Site successfully deployed to Vercel in production mode.")
    else:
        print("Deployment failed. Check the logs above for errors.")

if __name__ == "__main__":
    deploy_to_vercel()