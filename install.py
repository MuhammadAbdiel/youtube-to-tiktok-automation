#!/usr/bin/env python3
"""
Installation script for YouTube to TikTok Automation
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def main():
    print("🚀 Installing YouTube to TikTok Automation Dependencies")
    print("=" * 60)
    
    # Update pip first
    if not run_command(f"{sys.executable} -m pip install --upgrade pip", "Updating pip"):
        print("Warning: Failed to update pip, continuing anyway...")
    
    # Install/upgrade pytube to latest
    if not run_command(f"{sys.executable} -m pip install --upgrade pytube", "Installing/upgrading pytube"):
        print("❌ Failed to install pytube")
        return False
    
    # Install requirements
    if not run_command(f"{sys.executable} -m pip install -r requirements.txt", "Installing requirements"):
        print("❌ Failed to install requirements")
        return False
    
    # Install additional packages that might help with YouTube downloads
    additional_packages = [
        "certifi",  # For SSL certificate verification
        "urllib3",  # For HTTP requests
    ]
    
    for package in additional_packages:
        run_command(f"{sys.executable} -m pip install --upgrade {package}", f"Installing {package}")
    
    print("\n" + "=" * 60)
    print("✅ Installation completed!")
    print("\nNext steps:")
    print("1. Create a .env file with your API keys and credentials")
    print("2. Run: python main.py")
    print("\nIf you still get download errors, try:")
    print("- pip install --upgrade pytube yt-dlp")

if __name__ == "__main__":
    main() 