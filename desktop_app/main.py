#!/usr/bin/env python3
"""
OpenComputer Desktop Application

A beginner-friendly desktop GUI for the OpenComputer framework.
Allows configuring API keys, running evaluations, browsing tasks,
and viewing results — all from a graphical interface.

Usage:
    python desktop_app/main.py
"""

import os
import sys

# Ensure the desktop_app directory is on sys.path for local imports
APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

# Also ensure the project root is on sys.path
PROJECT_ROOT = os.path.dirname(APP_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

from styles import MAIN_STYLE
from main_window import MainWindow


def main():
    # High-DPI support
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("OpenComputer")
    app.setOrganizationName("OpenComputer")

    # Set app icon
    icon_path = os.path.join(APP_DIR, "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Apply stylesheet
    app.setStyleSheet(MAIN_STYLE)

    # Set default font
    font = QFont()
    font.setFamily("Microsoft YaHei")
    fallbacks = ["Noto Sans CJK SC", "PingFang SC", "Segoe UI", "Helvetica Neue", "Arial"]
    font.setStyleHint(QFont.SansSerif)
    font.setPointSize(10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
