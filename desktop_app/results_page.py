"""
Results viewer page: browse runs, view trajectories, screenshots, export reports.
"""

import csv
import json
import os
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from worker import project_root


def _eval_runs_dir():
    return project_root() / "evaluation" / "runs"


def _repair_runs_dir():
    return project_root() / "evaluation" / "repair" / "runs"


def _list_runs():
    runs = []
    seen = set()
    # Eval runs
    runs_dir = _eval_runs_dir()
    if runs_dir.exists():
        for trajs_root in runs_dir.rglob("trajectories"):
            if not trajs_root.is_dir():
                continue
            run_dir = trajs_root.parent
            try:
                run_id = run_dir.relative_to(runs_dir).as_posix()
            except ValueError:
                continue
            if run_id not in seen:
                seen.add(run_id)
                runs.append((f"[评估] {run_id}", run_dir))
    # Repair runs
    repair_dir = _repair_runs_dir()
    if repair_dir.exists():
        for rd in sorted(repair_dir.iterdir()):
            if rd.is_dir():
                run_id = rd.name
                if run_id not in seen:
                    seen.add(run_id)
                    runs.append((f"[修复] {run_id}", rd))
    return sorted(runs, key=lambda x: x[0], reverse=True)


def _load_run_results(run_dir):
    results = []
    trajs = run_dir / "trajectories"
    if not trajs.exists():
        return results
    for td in sorted(trajs.iterdir()):
        if not td.is_dir():
            continue
        tf = td / "trajectory.json"
        if tf.exists():
            try:
                data = json.loads(tf.read_text(encoding="utf-8"))
                data["_traj_dir"] = str(td)
                results.append(data)
            except Exception:
                pass
    return results


def _load_report(run_dir):
    for name in ["report.json", "REPORT.md"]:
        f = run_dir / name
        if f.exists():
            try:
                if name.endswith(".json"):
                    return json.loads(f.read_text(encoding="utf-8"))
                else:
                    return {"_markdown": f.read_text(encoding="utf-8")}
            except Exception:
                pass
    return None


class ResultsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_results = []
        self._current_run_dir = None
        self._init_ui()
        self._refresh_runs()

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(30, 20, 30, 20)

        title = QLabel("评估结果")
        title.setObjectName("pageTitle")
        outer.addWidget(title)

        subtitle = QLabel("查看历史评估运行的结果，包括轨迹、截图和评分报告。支持导出 CSV/JSON。")
        subtitle.setObjectName("pageSubtitle")
        outer.addWidget(subtitle)

        # ── Run selector + buttons ──
        run_row = QHBoxLayout()
        run_row.addWidget(QLabel("选择运行:"))
        self.cb_run = QComboBox()
        self.cb_run.setMinimumWidth(350)
        self.cb_run.currentTextChanged.connect(self._on_run_selected)
        run_row.addWidget(self.cb_run, 1)

        btn_refresh = QPushButton("刷新")
        btn_refresh.setObjectName("btnSecondary")
        btn_refresh.clicked.connect(self._refresh_runs)
        run_row.addWidget(btn_refresh)

        self.btn_export_csv = QPushButton("导出 CSV")
        self.btn_export_csv.clicked.connect(self._export_csv)
        run_row.addWidget(self.btn_export_csv)

        self.btn_export_json = QPushButton("导出 JSON")
        self.btn_export_json.clicked.connect(self._export_json)
        run_row.addWidget(self.btn_export_json)

        outer.addLayout(run_row)

        # ── Summary card ──
        self.lbl_summary = QLabel("")
        self.lbl_summary.setWordWrap(True)
        self.lbl_summary.setStyleSheet(
            "background:#ffffff;border:1px solid #dfe6e9;border-radius:8px;"
            "padding:12px;font-size:14px;"
        )
        self.lbl_summary.setVisible(False)
        outer.addWidget(self.lbl_summary)

        # ── Splitter: table + detail ──
        splitter = QSplitter(Qt.Horizontal)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["任务 ID", "应用", "模型", "得分", "步数", "状态"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 6):
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.currentCellChanged.connect(self._on_select)
        splitter.addWidget(self.table)

        self.detail = QTextBrowser()
        self.detail.setOpenExternalLinks(True)
        self.detail.setPlaceholderText("点击左侧结果查看详情...")
        splitter.addWidget(self.detail)

        splitter.setSizes([500, 400])
        outer.addWidget(splitter, 1)

    def _refresh_runs(self):
        self.cb_run.clear()
        self._runs_map = {}
        runs = _list_runs()
        if not runs:
            self.cb_run.addItem("暂无评估记录")
            self.table.setRowCount(0)
            self.detail.clear()
            self.lbl_summary.setVisible(False)
            return
        for run_id, run_dir in runs:
            self.cb_run.addItem(run_id)
            self._runs_map[run_id] = run_dir

    def _on_run_selected(self, run_id):
        if not run_id or run_id == "暂无评估记录":
            self.table.setRowCount(0)
            self.detail.clear()
            self.lbl_summary.setVisible(False)
            return

        run_dir = self._runs_map.get(run_id)
        if not run_dir or not run_dir.exists():
            return

        self._current_run_dir = run_dir
        self._current_results = _load_run_results(run_dir)
        self._populate_table()

        report = _load_report(run_dir)
        total = len(self._current_results)
        if report and "_markdown" not in report:
            passed = report.get("passed", 0)
            avg = report.get("average_score", 0)
            model = report.get("model", "N/A")
            self.lbl_summary.setText(
                f"<b>模型:</b> {model}  |  "
                f"<b>总任务:</b> {total}  |  "
                f"<b>通过:</b> {passed}  |  "
                f"<b>平均分:</b> {avg:.2f}"
            )
        else:
            scores = [r.get("score", r.get("reward", 0)) or 0 for r in self._current_results]
            avg = sum(float(s) for s in scores) / max(len(scores), 1)
            passed = sum(1 for s in scores if float(s) >= 1.0)
            self.lbl_summary.setText(
                f"<b>总任务:</b> {total}  |  "
                f"<b>通过:</b> {passed}  |  "
                f"<b>平均分:</b> {avg:.2f}"
            )
        self.lbl_summary.setVisible(True)

    def _populate_table(self):
        results = self._current_results
        self.table.setRowCount(len(results))
        for i, r in enumerate(results):
            self.table.setItem(i, 0, QTableWidgetItem(r.get("task_id", "")))
            self.table.setItem(i, 1, QTableWidgetItem(r.get("app", "")))
            self.table.setItem(i, 2, QTableWidgetItem(r.get("model", "")))
            score = r.get("score", r.get("reward", ""))
            item_s = QTableWidgetItem(str(score) if score != "" else "N/A")
            item_s.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 3, item_s)
            steps = r.get("num_steps", r.get("iterations", ""))
            item_st = QTableWidgetItem(str(steps) if steps != "" else "N/A")
            item_st.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 4, item_st)
            status = r.get("status", "")
            if not status:
                s = r.get("score", r.get("reward", None))
                if s is not None:
                    try:
                        status = "通过" if float(s) >= 1.0 else "未通过"
                    except (ValueError, TypeError):
                        status = ""
            self.table.setItem(i, 5, QTableWidgetItem(status))

    def _on_select(self, row, col, prev_row, prev_col):
        if row < 0 or row >= len(self._current_results):
            self.detail.clear()
            return
        r = self._current_results[row]
        traj_dir = r.get("_traj_dir", "")
        html = f"<h2 style='color:#0984e3;'>{r.get('task_id', 'N/A')}</h2>"
        html += "<table>"
        for label, key in [("应用", "app"), ("模型", "model"), ("得分", "score"),
                           ("步数", "num_steps"), ("时间戳", "timestamp")]:
            val = r.get(key, r.get({"得分": "reward", "步数": "iterations"}.get(label, ""), "N/A"))
            html += f"<tr><td style='padding-right:16px;color:#636e72;'><b>{label}</b></td><td>{val}</td></tr>"
        html += "</table>"

        task_desc = r.get("task", r.get("task_description", ""))
        if task_desc:
            html += f"<h3>任务描述</h3><p style='background:#f5f6fa;padding:12px;border-radius:6px;'>{task_desc}</p>"

        verif = r.get("verification_details", r.get("verification", []))
        if verif and isinstance(verif, list):
            html += "<h3>验证结果</h3>"
            for i, v in enumerate(verif):
                passed = v.get("passed", False)
                color = "#00b894" if passed else "#d63031"
                st = "通过" if passed else "未通过"
                html += f"<div style='background:#f5f6fa;padding:8px;border-radius:6px;margin-bottom:4px;'>"
                html += f"<span style='color:{color};font-weight:bold;'>[{st}]</span> "
                html += f"{v.get('description', v.get('command', f'检查 {i+1}'))}</div>"

        if traj_dir:
            traj_path = Path(traj_dir)
            screenshots = sorted(traj_path.glob("*.png")) + sorted(traj_path.glob("*.jpg"))
            if screenshots:
                html += "<h3>截图</h3>"
                for ss in screenshots[:8]:
                    html += f"<p><b>{ss.name}</b></p><img src='file://{ss}' width='600'/><br/>"

        self.detail.setHtml(html)

    def _export_csv(self):
        if not self._current_results:
            QMessageBox.information(self, "提示", "没有数据可导出。")
            return
        path, _ = QFileDialog.getSaveFileName(self, "导出 CSV", "evaluation_results.csv", "CSV (*.csv)")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["任务ID", "应用", "模型", "得分", "步数", "状态", "时间戳"])
            for r in self._current_results:
                score = r.get("score", r.get("reward", ""))
                steps = r.get("num_steps", r.get("iterations", ""))
                status = r.get("status", "")
                writer.writerow([
                    r.get("task_id", ""),
                    r.get("app", ""),
                    r.get("model", ""),
                    score, steps, status,
                    r.get("timestamp", ""),
                ])
        QMessageBox.information(self, "导出成功", f"已导出到: {path}")

    def _export_json(self):
        if not self._current_results:
            QMessageBox.information(self, "提示", "没有数据可导出。")
            return
        path, _ = QFileDialog.getSaveFileName(self, "导出 JSON", "evaluation_results.json", "JSON (*.json)")
        if not path:
            return
        export = []
        for r in self._current_results:
            export.append({k: v for k, v in r.items() if not k.startswith("_")})
        with open(path, "w", encoding="utf-8") as f:
            json.dump(export, f, indent=2, ensure_ascii=False)
        QMessageBox.information(self, "导出成功", f"已导出到: {path}")
