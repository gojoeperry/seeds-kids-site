# Claude Code Prompt: Hugo + Vercel Deployment Audit Script

# Goal: Check for Hugo installation, run Hugo build, validate that the `public/` folder contains deployable output (especially `index.html`),
# and print warnings for anything that might cause 404 errors after deploying to Vercel.

import os
import subprocess
from pathlib import Path

def check_hugo_installed():
    try:
        result = subprocess.run(["hugo", "version"], capture_output=True, text=True, check=True)
        print(f"Hugo is installed: {result.stdout.strip()}")
    except subprocess.CalledProcessError:
        print("[ERROR] Hugo is not installed or not found in PATH.")
        return False
    return True

def run_hugo_build():
    print("Running `hugo` build...")
    result = subprocess.run(["hugo"], capture_output=True, text=True)
    if result.returncode != 0:
        print("[ERROR] Hugo build failed:")
        print(result.stderr)
        return False
    print("Hugo build completed.")
    return True

def validate_output():
    public_path = Path("public")
    if not public_path.exists() or not public_path.is_dir():
        print("[ERROR] No `public/` folder found. Hugo may not have generated output correctly.")
        return False

    index_file = public_path / "index.html"
    if not index_file.exists():
        print("[ERROR] No `index.html` file found in the `public/` directory.")
        print("This may cause a 404 error on Vercel.")
        return False

    print("`public/index.html` exists.")
    print("Static site is ready for Vercel deployment.")
    return True

def check_vercel_json():
    vercel_file = Path("vercel.json")
    if not vercel_file.exists():
        print("[WARNING] No `vercel.json` file found. Vercel may not know the correct output folder.")
    else:
        print("Found `vercel.json`. Make sure it sets `distDir` to `public`.")

def audit_for_vercel_deploy():
    print("=== Running Hugo + Vercel Pre-Deployment Audit ===")
    if not check_hugo_installed():
        return
    if not run_hugo_build():
        return
    validate_output()
    check_vercel_json()

if __name__ == "__main__":
    audit_for_vercel_deploy()