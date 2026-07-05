"""
Reusable background worker for running shell commands with real-time log output.
"""

import os
import subprocess
import sys
from pathlib import Path

from PyQt5.QtCore import QThread, pyqtSignal


def project_root():
    return Path(__file__).resolve().parent.parent


class CmdWorker(QThread):
    """Run a shell command in a background thread, emitting log lines."""
    log = pyqtSignal(str)
    finished = pyqtSignal(int)

    def __init__(self, cmd, cwd=None, env_extra=None):
        super().__init__()
        self.cmd = cmd
        self.cwd = cwd or str(project_root())
        self.env_extra = env_extra or {}
        self._process = None
        self._cancelled = False

    def run(self):
        env = {**os.environ, **self.env_extra}
        try:
            self._process = subprocess.Popen(
                self.cmd,
                cwd=self.cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env,
            )
            for line in self._process.stdout:
                if self._cancelled:
                    break
                self.log.emit(line.rstrip("\n"))
            self._process.wait()
            self.finished.emit(self._process.returncode or 0)
        except Exception as e:
            self.log.emit(f"[ERROR] {e}")
            self.finished.emit(1)

    def cancel(self):
        self._cancelled = True
        if self._process and self._process.poll() is None:
            self._process.terminate()
