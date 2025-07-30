"""
Deploy Hugo site to Vercel using Vercel CLI.
This script ensures you're in the correct Hugo root directory and runs
`vercel --prod` to perform a production deployment.

Note: Git is optional for Vercel CLI deployment, but recommended for version control.

Assumptions:
- Hugo site is located in ./site/
- Vercel CLI is already installed and authenticated

To customize the deployment (project name, root dir), update the `vercel_args` list.
"""

import subprocess
import os
from pathlib import Path

def deploy_to_vercel():
    project_dir = Path("site")
    if not project_dir.exists():
        print("❌ ERROR: site/ directory not found. Expected Hugo site at ./site/")
        return

    os.chdir(project_dir)

    # You can add options like --confirm or --token if needed
    vercel_args = ["vercel", "--prod"]

    try:
        print(f"📦 Deploying Hugo site at {project_dir.resolve()} to Vercel...")
        result = subprocess.run(vercel_args, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Vercel deployment complete.")
            print(result.stdout)
        else:
            print("❌ Deployment failed:")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Error during deployment: {e}")

if __name__ == "__main__":
    deploy_to_vercel()