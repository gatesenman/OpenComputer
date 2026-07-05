"""
Dashboard / home page: project overview, pipeline flow guide, status cards.
"""

import json
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from worker import project_root


def _count_tasks():
    tasks_dir = project_root() / "task_generator" / "tasks"
    count = 0
    apps = set()
    if tasks_dir.exists():
        for td in tasks_dir.iterdir():
            if td.is_dir() and (td / "task.json").exists():
                count += 1
                try:
                    data = json.loads((td / "task.json").read_text(encoding="utf-8"))
                    app = data.get("app")
                    if app:
                        apps.add(app)
                except Exception:
                    pass
    return count, len(apps)


def _count_runs():
    runs_dir = project_root() / "evaluation" / "runs"
    count = 0
    if runs_dir.exists():
        for trajs_root in runs_dir.rglob("trajectories"):
            if trajs_root.is_dir():
                count += 1
    return count


def _count_verifiers():
    v_dir = project_root() / "verifiers"
    count = 0
    if v_dir.exists():
        for d in v_dir.iterdir():
            if d.is_dir() and (d / f"{d.name}.py").exists():
                count += 1
    return count


def _check_env():
    env_path = project_root() / ".env"
    if not env_path.exists():
        return False, "未配置"
    content = env_path.read_text()
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("#") or not line:
            continue
        if "API_KEY" in line and "=" in line:
            v = line.split("=", 1)[1].strip()
            if v:
                return True, "已配置"
    return False, "未配置密钥"


class _StatCard(QFrame):
    def __init__(self, title, value, color="#0984e3", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumHeight(100)
        self.setMinimumWidth(160)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(6)
        lbl_val = QLabel(str(value))
        lbl_val.setAlignment(Qt.AlignCenter)
        lbl_val.setStyleSheet(f"font-size:34px;font-weight:bold;color:{color};")
        layout.addWidget(lbl_val)
        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet("font-size:12px;color:#6b7b8d;letter-spacing:0.5px;text-transform:uppercase;")
        layout.addWidget(lbl_title)


class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(30, 20, 30, 20)

        title = QLabel("OpenComputer 桌面端")
        title.setObjectName("pageTitle")
        outer.addWidget(title)

        subtitle = QLabel("可验证的软件世界 — 面向计算机使用代理的合成环境框架")
        subtitle.setObjectName("pageSubtitle")
        outer.addWidget(subtitle)

        # Stat cards
        cards = QHBoxLayout()
        cards.setSpacing(12)
        task_count, app_count = _count_tasks()
        run_count = _count_runs()
        v_count = _count_verifiers()
        env_ok, env_msg = _check_env()

        cards.addWidget(_StatCard("评估任务", task_count, "#0984e3"))
        cards.addWidget(_StatCard("应用数量", app_count, "#6c5ce7"))
        cards.addWidget(_StatCard("验证器", v_count, "#00b894"))
        cards.addWidget(_StatCard("评估运行", run_count, "#fdcb6e"))
        cards.addWidget(_StatCard("环境配置", env_msg, "#00b894" if env_ok else "#d63031"))
        outer.addLayout(cards)

        # Guide
        guide = QTextBrowser()
        guide.setOpenExternalLinks(True)
        guide.setStyleSheet(
            "QTextBrowser{background:#ffffff;color:#2d3a4a;"
            "border:1px solid rgba(0,0,0,0.06);border-radius:12px;padding:24px;"
            "font-family:'Microsoft YaHei','Noto Sans CJK SC',sans-serif;font-size:14px;}"
        )
        guide.setHtml("""
        <h2 style="color:#00b894;margin-top:0;font-size:20px;letter-spacing:-0.3px;">
        端到端使用流程</h2>
        <p style="color:#6b7b8d;margin-bottom:16px;">
        按照左侧导航栏从上到下的顺序，即可走完整个评估流程。每个步骤独立可操作。</p>

        <table style="width:100%;border-collapse:separate;border-spacing:0 4px;">
        <tr style="background:#f6f8fc;border-radius:8px;">
            <td style="padding:12px 16px;font-weight:bold;color:#00b894;width:32px;
                       border-radius:8px 0 0 8px;font-size:16px;">1</td>
            <td style="padding:12px 16px;border-radius:0 8px 8px 0;">
                <b style="color:#1a2332;">环境安装</b>
                <span style="color:#6b7b8d;"> — 安装依赖、创建配置、构建沙盒、云部署（可选）</span></td>
        </tr>
        <tr style="background:#ffffff;">
            <td style="padding:12px 16px;font-weight:bold;color:#00b894;font-size:16px;">2</td>
            <td style="padding:12px 16px;">
                <b style="color:#1a2332;">设置</b>
                <span style="color:#6b7b8d;"> — API 密钥、运行后端、Docker、评估参数、AWS/腾讯云配置</span></td>
        </tr>
        <tr style="background:#f6f8fc;">
            <td style="padding:12px 16px;font-weight:bold;color:#00b894;border-radius:8px 0 0 8px;font-size:16px;">3</td>
            <td style="padding:12px 16px;border-radius:0 8px 8px 0;">
                <b style="color:#1a2332;">验证器管理</b>
                <span style="color:#6b7b8d;"> — 查看 33 个应用的验证器代码、文档和测试</span></td>
        </tr>
        <tr style="background:#ffffff;">
            <td style="padding:12px 16px;font-weight:bold;color:#00b894;font-size:16px;">4</td>
            <td style="padding:12px 16px;">
                <b style="color:#1a2332;">Smoke 测试</b>
                <span style="color:#6b7b8d;"> — 在真实沙盒中验证验证器端点正常工作</span></td>
        </tr>
        <tr style="background:#f6f8fc;">
            <td style="padding:12px 16px;font-weight:bold;color:#00b894;border-radius:8px 0 0 8px;font-size:16px;">5</td>
            <td style="padding:12px 16px;border-radius:0 8px 8px 0;">
                <b style="color:#1a2332;">任务生成</b>
                <span style="color:#6b7b8d;"> — 查看流水线产物（提案 → 评估 → 最终任务）</span></td>
        </tr>
        <tr style="background:#ffffff;">
            <td style="padding:12px 16px;font-weight:bold;color:#00b894;font-size:16px;">6</td>
            <td style="padding:12px 16px;">
                <b style="color:#1a2332;">任务浏览</b>
                <span style="color:#6b7b8d;"> — 搜索/筛选 900+ 评估任务，查看详情</span></td>
        </tr>
        <tr style="background:#f6f8fc;">
            <td style="padding:12px 16px;font-weight:bold;color:#00b894;border-radius:8px 0 0 8px;font-size:16px;">7</td>
            <td style="padding:12px 16px;border-radius:0 8px 8px 0;">
                <b style="color:#1a2332;">运行评估</b>
                <span style="color:#6b7b8d;"> — 选择应用 / AI 模型 / 参数，一键启动评估</span></td>
        </tr>
        <tr style="background:#ffffff;">
            <td style="padding:12px 16px;font-weight:bold;color:#00b894;font-size:16px;">8</td>
            <td style="padding:12px 16px;">
                <b style="color:#1a2332;">重新评估</b>
                <span style="color:#6b7b8d;"> — 用不同模型重跑已有运行，对比模型表现</span></td>
        </tr>
        <tr style="background:#f6f8fc;">
            <td style="padding:12px 16px;font-weight:bold;color:#00b894;border-radius:8px 0 0 8px;font-size:16px;">9</td>
            <td style="padding:12px 16px;border-radius:0 8px 8px 0;">
                <b style="color:#1a2332;">评估结果</b>
                <span style="color:#6b7b8d;"> — 查看得分 / 轨迹 / 截图，导出 CSV/JSON</span></td>
        </tr>
        <tr style="background:#ffffff;">
            <td style="padding:12px 16px;font-weight:bold;color:#00b894;font-size:16px;">10-12</td>
            <td style="padding:12px 16px;">
                <b style="color:#1a2332;">修复循环 · 交互沙盒 · 资源清理</b>
                <span style="color:#6b7b8d;"> — 可选的调试和维护工具</span></td>
        </tr>
        </table>

        <hr style="border:none;border-top:1px solid #e8ecf2;margin:20px 0;">

        <table style="width:100%;border-collapse:collapse;">
        <tr>
            <td style="vertical-align:top;width:50%;padding-right:16px;">
                <h3 style="color:#1a2332;font-size:15px;margin-bottom:8px;">支持的应用（33个）</h3>
                <p style="color:#6b7b8d;line-height:1.7;font-size:13px;">
                <span style="color:#00b894;font-weight:bold;">浏览器</span> Chrome · Firefox · Brave<br/>
                <span style="color:#00b894;font-weight:bold;">办公</span> LibreOffice 全套 · gedit · galculator · Obsidian · Zotero<br/>
                <span style="color:#00b894;font-weight:bold;">图形</span> GIMP · Inkscape · Krita · darktable · draw.io<br/>
                <span style="color:#00b894;font-weight:bold;">3D</span> FreeCAD · CloudCompare · RenderDoc<br/>
                <span style="color:#00b894;font-weight:bold;">媒体</span> VLC · OBS · Kdenlive · Audacity · Shotcut · MuseScore<br/>
                <span style="color:#00b894;font-weight:bold;">开发</span> VS Code · Eclipse · Godot 4<br/>
                <span style="color:#00b894;font-weight:bold;">其他</span> Zoom · PCManFM · Thunderbird
                </p>
            </td>
            <td style="vertical-align:top;width:50%;padding-left:16px;border-left:1px solid #e8ecf2;">
                <h3 style="color:#1a2332;font-size:15px;margin-bottom:8px;">支持的 AI 模型（30+）</h3>
                <p style="color:#6b7b8d;line-height:1.7;font-size:13px;">
                <span style="color:#0984e3;font-weight:bold;">Claude</span> sonnet-4-6 · opus-4<br/>
                <span style="color:#0984e3;font-weight:bold;">GPT</span> 5.4 · 5 · chatgpt<br/>
                <span style="color:#0984e3;font-weight:bold;">Gemini</span> 3-flash<br/>
                <span style="color:#0984e3;font-weight:bold;">Kimi</span> k2.6 · k2.5<br/>
                <span style="color:#0984e3;font-weight:bold;">Qwen</span> 3-vl · 3.5<br/>
                <span style="color:#0984e3;font-weight:bold;">More</span> EvoCUA · Mano · OpenCUA · Dart · GUI-Owl · Holo-3.1
                </p>
            </td>
        </tr>
        </table>

        <hr style="border:none;border-top:1px solid #e8ecf2;margin:16px 0 12px 0;">
        <p style="color:#a0aab4;font-size:12px;">
        <a href="https://echo0715.github.io/OpenComputer" style="color:#0984e3;text-decoration:none;">项目主页</a> &nbsp;·&nbsp;
        <a href="https://arxiv.org/pdf/2605.19769" style="color:#0984e3;text-decoration:none;">论文</a> &nbsp;·&nbsp;
        Apache 2.0 许可证
        </p>
        """)
        outer.addWidget(guide, 1)
