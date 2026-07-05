"""
Verifier management page: list all verifiers, view code/docs, run tests.
"""

import json
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from worker import CmdWorker, project_root
import sys


def _list_verifiers():
    v_dir = project_root() / "verifiers"
    result = []
    if not v_dir.exists():
        return result
    for d in sorted(v_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        py_file = d / f"{d.name}.py"
        readme = d / "README.md"
        test_file = d / f"test_{d.name}.py"
        test_md = d / "Test.md"
        if py_file.exists():
            result.append({
                "name": d.name,
                "dir": str(d),
                "has_py": py_file.exists(),
                "has_readme": readme.exists(),
                "has_test": test_file.exists(),
                "has_test_md": test_md.exists(),
            })
    return result


class VerifierPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._verifiers = []
        self._init_ui()
        self._refresh()

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(30, 20, 30, 20)

        title = QLabel("验证器管理")
        title.setObjectName("pageTitle")
        outer.addWidget(title)

        subtitle = QLabel("查看、测试所有应用验证器。验证器用于判定 AI 代理是否正确完成了任务。")
        subtitle.setObjectName("pageSubtitle")
        outer.addWidget(subtitle)

        splitter = QSplitter(Qt.Horizontal)

        # Left: verifier list
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)

        lbl_list = QLabel("验证器列表")
        lbl_list.setStyleSheet("font-weight:bold;font-size:14px;")
        left_layout.addWidget(lbl_list)

        self.vlist = QListWidget()
        self.vlist.currentRowChanged.connect(self._on_select)
        left_layout.addWidget(self.vlist)

        # Test button
        btn_row = QHBoxLayout()
        self.btn_test = QPushButton("运行测试")
        self.btn_test.setObjectName("btnSuccess")
        self.btn_test.clicked.connect(self._run_test)
        btn_row.addWidget(self.btn_test)

        self.btn_stop = QPushButton("停止")
        self.btn_stop.setObjectName("btnDanger")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop_test)
        btn_row.addWidget(self.btn_stop)

        left_layout.addLayout(btn_row)

        splitter.addWidget(left)

        # Right: tabs for code / readme / test log
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()

        self.tab_readme = QTextBrowser()
        self.tab_readme.setOpenExternalLinks(True)
        self.tabs.addTab(self.tab_readme, "文档 (README)")

        self.tab_code = QPlainTextEdit()
        self.tab_code.setReadOnly(True)
        self.tabs.addTab(self.tab_code, "验证器代码")

        self.tab_testmd = QTextBrowser()
        self.tabs.addTab(self.tab_testmd, "测试计划 (Test.md)")

        self.tab_testlog = QPlainTextEdit()
        self.tab_testlog.setReadOnly(True)
        self.tab_testlog.setPlaceholderText("点击「运行测试」查看测试输出...")
        self.tabs.addTab(self.tab_testlog, "测试输出")

        right_layout.addWidget(self.tabs)

        # Progress
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        right_layout.addWidget(self.progress)

        splitter.addWidget(right)
        splitter.setSizes([250, 700])
        outer.addWidget(splitter, 1)

    def _refresh(self):
        self._verifiers = _list_verifiers()
        self.vlist.clear()
        for v in self._verifiers:
            status_parts = []
            if v["has_readme"]:
                status_parts.append("文档")
            if v["has_test"]:
                status_parts.append("测试")
            status = " | ".join(status_parts) if status_parts else ""
            item = QListWidgetItem(f"{v['name']}  ({status})")
            self.vlist.addItem(item)

    def _on_select(self, row):
        if row < 0 or row >= len(self._verifiers):
            return
        v = self._verifiers[row]
        d = Path(v["dir"])

        # README
        readme_path = d / "README.md"
        if readme_path.exists():
            content = readme_path.read_text(encoding="utf-8", errors="replace")
            self.tab_readme.setMarkdown(content)
        else:
            self.tab_readme.setPlainText("(无 README.md)")

        # Code
        py_path = d / f"{v['name']}.py"
        if py_path.exists():
            content = py_path.read_text(encoding="utf-8", errors="replace")
            self.tab_code.setPlainText(content)
        else:
            self.tab_code.setPlainText("(无验证器代码)")

        # Test.md
        testmd_path = d / "Test.md"
        if testmd_path.exists():
            content = testmd_path.read_text(encoding="utf-8", errors="replace")
            self.tab_testmd.setMarkdown(content)
        else:
            self.tab_testmd.setPlainText("(无 Test.md)")

        self.tab_testlog.clear()

    def _run_test(self):
        row = self.vlist.currentRow()
        if row < 0 or row >= len(self._verifiers):
            return
        v = self._verifiers[row]
        test_file = Path(v["dir"]) / f"test_{v['name']}.py"
        if not test_file.exists():
            self.tab_testlog.setPlainText(f"[ERROR] 测试文件不存在: {test_file}")
            self.tabs.setCurrentWidget(self.tab_testlog)
            return

        self.tabs.setCurrentWidget(self.tab_testlog)
        self.tab_testlog.clear()
        self.tab_testlog.appendPlainText(f">>> 运行 {test_file.name} ...\n")
        self.progress.setVisible(True)
        self.btn_test.setEnabled(False)
        self.btn_stop.setEnabled(True)

        cmd = [sys.executable, str(test_file)]
        self._worker = CmdWorker(cmd)
        self._worker.log.connect(lambda t: (
            self.tab_testlog.appendPlainText(t),
            self.tab_testlog.verticalScrollBar().setValue(
                self.tab_testlog.verticalScrollBar().maximum()
            ),
        ))
        self._worker.finished.connect(self._on_test_done)
        self._worker.start()

    def _stop_test(self):
        if self._worker:
            self._worker.cancel()

    def _on_test_done(self, code):
        self.progress.setVisible(False)
        self.btn_test.setEnabled(True)
        self.btn_stop.setEnabled(False)
        status = "通过" if code == 0 else f"失败 (退出码 {code})"
        self.tab_testlog.appendPlainText(f"\n--- 测试{status} ---")
        self._worker = None
