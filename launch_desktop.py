#!/usr/bin/env python3
"""
Convenience launcher for the OpenComputer Desktop application.

Usage (from project root):
    python launch_desktop.py
"""

import os
import subprocess
import sys


def main():
    project_root = os.path.dirname(os.path.abspath(__file__))
    desktop_main = os.path.join(project_root, "desktop_app", "main.py")

    if not os.path.exists(desktop_main):
        print("[ERROR] desktop_app/main.py not found.")
        sys.exit(1)

    # Check PyQt5
    try:
        import PyQt5  # noqa: F401
    except ImportError:
        print("[INFO] PyQt5 not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyQt5>=5.15"])

    # Launch
    os.execv(sys.executable, [sys.executable, desktop_main])


if __name__ == "__main__":
    main()
