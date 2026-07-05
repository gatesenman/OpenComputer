#!/usr/bin/env python3
"""
OpenComputer Desktop — WebUI Launcher
Double-click or run: python launch_webui.py
"""
import os
import sys
import subprocess

APP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "desktop_app", "webui")

def ensure_deps():
    try:
        import flask  # noqa
    except ImportError:
        print("正在安装 Flask...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "-q"])

if __name__ == "__main__":
    ensure_deps()
    sys.path.insert(0, APP_DIR)
    from app import main
    main()
