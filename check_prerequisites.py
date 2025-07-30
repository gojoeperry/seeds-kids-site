#!/usr/bin/env python3
"""
Pre-Deployment Prerequisite Checker for Hugo + Vercel

This script checks all required tools, credentials, and project structure
before performing a full deployment audit or starting a Vercel build.
"""

import subprocess
import os
from pathlib import Path

def check_command_installed(command, version_flag="--version"):
    try:
        result = subprocess.run([command, version_flag], capture_output=True, text=True, check=True)
        return True, result.stdout.strip()
    except Exception as e:
        return False, str(e)

def check_vercel_auth():
    try:
        result = subprocess.run(["vercel", "whoami"], capture_output=True, text=True)
        if result.returncode == 0 and "email" in result.stdout.lower():
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip() if result.stderr else "Not authenticated"
    except Exception as e:
        return False, str(e)

def check_required_dirs():
    expected_paths = [
        Path("site/content"),
        Path("site/static"),
        Path("site/config.toml"),
    ]
    missing = []
    present = []
    
    for p in expected_paths:
        if p.exists():
            present.append(str(p))
        else:
            missing.append(str(p))
    
    return missing, present

def main():
    print("\nChecking prerequisites for Hugo + Vercel deployment...")
    print("=" * 60)
    
    # Check Hugo
    hugo_installed, hugo_info = check_command_installed("hugo")
    if hugo_installed:
        print(f"✓ Hugo is installed: {hugo_info.split()[0] if hugo_info else 'version unknown'}")
    else:
        print("✗ Hugo is not installed or not in PATH")
        print("  Install from: https://gohugo.io/getting-started/installing/")
    
    # Check Vercel CLI
    vercel_installed, vercel_info = check_command_installed("vercel")
    if vercel_installed:
        print(f"✓ Vercel CLI is installed: {vercel_info.split()[0] if vercel_info else 'version unknown'}")
    else:
        print("✗ Vercel CLI is not installed")
        print("  Install with: npm install -g vercel")
    
    # Check Vercel authentication (only if CLI is installed)
    if vercel_installed:
        auth_ok, auth_info = check_vercel_auth()
        if auth_ok:
            print(f"✓ Vercel is authenticated: {auth_info}")
        else:
            print("✗ Vercel is not authenticated")
            print("  Run: vercel login")
    
    # Check required directories and files
    missing, present = check_required_dirs()
    
    if not missing:
        print("✓ All required directories and config.toml are present")
        for p in present:
            print(f"  - {p}")
    else:
        print("✗ Missing required directories or config:")
        for m in missing:
            print(f"  - {m}")
        if present:
            print("  Present:")
            for p in present:
                print(f"  - {p}")
    
    # Summary
    print("\n" + "=" * 60)
    all_good = hugo_installed and vercel_installed and not missing
    if vercel_installed:
        auth_ok, _ = check_vercel_auth()
        all_good = all_good and auth_ok
    
    if all_good:
        print("✓ All prerequisites met! Ready for deployment.")
    else:
        print("✗ Some prerequisites are missing. Please resolve the issues above.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()