"""
Setup page: comprehensive environment initialization wizard.
Covers Python deps, .env creation, E2B/Docker/AWS/TencentCloud provisioning,
and full environment verification.
"""

import os
import platform
import shutil
import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from worker import CmdWorker, project_root


class _StepCard(QGroupBox):
    """A single setup step with status indicator, description, and action button(s)."""

    def __init__(self, number, title, desc, btn_text, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        layout = QHBoxLayout(self)

        badge = QLabel(str(number))
        badge.setFixedSize(36, 36)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(
            "background:#0984e3;color:#fff;border-radius:18px;"
            "font-size:16px;font-weight:bold;"
        )
        layout.addWidget(badge)

        text_col = QVBoxLayout()
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size:15px;font-weight:bold;color:#2d3436;")
        text_col.addWidget(lbl_title)
        lbl_desc = QLabel(desc)
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("font-size:13px;color:#636e72;")
        text_col.addWidget(lbl_desc)
        layout.addLayout(text_col, 1)

        self.lbl_status = QLabel("待执行")
        self.lbl_status.setStyleSheet("color:#636e72;font-weight:bold;padding:0 12px;")
        layout.addWidget(self.lbl_status)

        self.btn = QPushButton(btn_text)
        self.btn.setMinimumWidth(120)
        layout.addWidget(self.btn)

    def set_status(self, text, color):
        self.lbl_status.setText(text)
        self.lbl_status.setStyleSheet(f"color:{color};font-weight:bold;padding:0 12px;")


class SetupPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker = None
        self._init_ui()
        self._check_status()

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(30, 20, 30, 20)

        title = QLabel("环境安装与初始化")
        title.setObjectName("pageTitle")
        outer.addWidget(title)

        subtitle = QLabel(
            "按照步骤完成环境配置。每步可单独执行，绿色=已完成，红色=需处理。"
        )
        subtitle.setObjectName("pageSubtitle")
        outer.addWidget(subtitle)

        # Scrollable steps area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        steps_container = QWidget()
        steps_layout = QVBoxLayout(steps_container)
        steps_layout.setSpacing(8)

        # Step 1: Python deps
        self.step1 = _StepCard(
            1, "安装 Python 依赖",
            "安装 requirements.txt 中的所有依赖（e2b, anthropic, openai, pillow, httpx 等）",
            "一键安装",
        )
        self.step1.btn.clicked.connect(self._install_deps)
        steps_layout.addWidget(self.step1)

        # Step 2: Create .env
        self.step2 = _StepCard(
            2, "创建配置文件 (.env)",
            "从 .env.example 复制创建 .env 文件。之后请到「设置」页面填写 API 密钥。",
            "创建 .env",
        )
        self.step2.btn.clicked.connect(self._create_env)
        steps_layout.addWidget(self.step2)

        # Step 3: Build E2B template
        self.step3 = _StepCard(
            3, "构建 E2B 沙盒模板",
            "构建包含 33 个应用的 E2B 沙盒模板（需先在「设置」中配置 E2B_API_KEY）",
            "构建模板",
        )
        self.step3.btn.clicked.connect(self._build_e2b)
        steps_layout.addWidget(self.step3)

        # Step 4: Build Docker image
        self.step4 = _StepCard(
            4, "构建本地 Docker 镜像",
            "构建本地 Docker 桌面镜像（选择 Docker 后端时使用，需安装 Docker）",
            "构建镜像",
        )
        self.step4.btn.clicked.connect(self._build_docker)
        steps_layout.addWidget(self.step4)

        # Step 5: AWS provisioning
        self.step5 = _StepCard(
            5, "AWS 云部署（可选）",
            "运行 AWS setup_prereqs.py 创建 ECR 仓库、IAM 角色、S3 存储桶等基础设施",
            "AWS 部署",
        )
        self.step5.btn.clicked.connect(self._provision_aws)
        steps_layout.addWidget(self.step5)

        # Step 6: AWS deploy workers
        self.step6 = _StepCard(
            6, "AWS 启动 Worker（可选）",
            "在 AWS 上启动远程 Docker Worker 实例，用于大规模并行评估",
            "启动 Worker",
        )
        self.step6.btn.clicked.connect(self._deploy_aws_workers)
        steps_layout.addWidget(self.step6)

        # Step 7: TencentCloud provisioning
        self.step7 = _StepCard(
            7, "腾讯云部署（可选）",
            "运行腾讯云 setup_prereqs.py 创建 CVM、TCR、COS 等基础设施",
            "腾讯云部署",
        )
        self.step7.btn.clicked.connect(self._provision_tencent)
        steps_layout.addWidget(self.step7)

        # Step 8: TencentCloud deploy workers
        self.step8 = _StepCard(
            8, "腾讯云启动 Worker（可选）",
            "在腾讯云上启动远程 Docker Worker 实例",
            "启动 Worker",
        )
        self.step8.btn.clicked.connect(self._deploy_tencent_workers)
        steps_layout.addWidget(self.step8)

        # Step 9: Verify environment
        self.step9 = _StepCard(
            9, "环境验证",
            "全面检查 Python 版本、依赖包、.env 配置、Docker、已有任务和验证器",
            "检查环境",
        )
        self.step9.btn.clicked.connect(self._verify_env)
        steps_layout.addWidget(self.step9)

        steps_layout.addStretch()
        scroll.setWidget(steps_container)
        outer.addWidget(scroll, 1)

        # Progress
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        outer.addWidget(self.progress)

        # Log area
        self.log_area = QPlainTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(200)
        self.log_area.setPlaceholderText("操作日志...")
        outer.addWidget(self.log_area)

    def _check_status(self):
        root = project_root()

        # Check deps
        try:
            import e2b  # noqa
            import anthropic  # noqa
            import openai  # noqa
            self.step1.set_status("已安装", "#00b894")
        except ImportError:
            self.step1.set_status("未安装", "#d63031")

        # Check .env
        if (root / ".env").exists():
            self.step2.set_status("已创建", "#00b894")
        else:
            self.step2.set_status("未创建", "#d63031")

        # E2B / Docker / AWS / Tencent — hints
        self.step3.set_status("需配置", "#636e72")
        self.step4.set_status("可选", "#636e72")
        self.step5.set_status("可选", "#636e72")
        self.step6.set_status("可选", "#636e72")
        self.step7.set_status("可选", "#636e72")
        self.step8.set_status("可选", "#636e72")
        self.step9.set_status("待检查", "#636e72")

        # Check Docker
        if shutil.which("docker"):
            self.step4.set_status("Docker 可用", "#00b894")

    def _run_cmd(self, cmd, on_done=None):
        if self._worker and self._worker.isRunning():
            self.log_area.appendPlainText("[提示] 已有任务正在运行，请等待完成。")
            return
        self.log_area.clear()
        self.progress.setVisible(True)
        self._worker = CmdWorker(cmd)
        self._worker.log.connect(lambda t: (
            self.log_area.appendPlainText(t),
            self.log_area.verticalScrollBar().setValue(
                self.log_area.verticalScrollBar().maximum()
            ),
        ))

        def _on_finished(code):
            self.progress.setVisible(False)
            if on_done:
                on_done(code)

        self._worker.finished.connect(_on_finished)
        self._worker.start()

    def _install_deps(self):
        self.step1.set_status("安装中...", "#fdcb6e")
        cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
        self._run_cmd(cmd, lambda code: (
            self.step1.set_status(
                "已安装" if code == 0 else "安装失败",
                "#00b894" if code == 0 else "#d63031"
            ),
            self._check_status(),
        ))

    def _create_env(self):
        root = project_root()
        src = root / ".env.example"
        dst = root / ".env"
        if dst.exists():
            self.log_area.appendPlainText(".env 文件已存在，跳过创建。")
            self.step2.set_status("已创建", "#00b894")
            return
        if src.exists():
            shutil.copy(src, dst)
            self.log_area.appendPlainText("已从 .env.example 创建 .env 文件。")
            self.log_area.appendPlainText("请前往「设置」页面填写 API 密钥。")
            self.step2.set_status("已创建", "#00b894")
        else:
            self.log_area.appendPlainText("[ERROR] .env.example 不存在！")
            self.step2.set_status("失败", "#d63031")

    def _build_e2b(self):
        self.step3.set_status("构建中...", "#fdcb6e")
        cmd = [sys.executable, "computer_env/provision/e2b/build_all_apps_template.py"]
        self._run_cmd(cmd, lambda code: self.step3.set_status(
            "已构建" if code == 0 else "构建失败",
            "#00b894" if code == 0 else "#d63031"
        ))

    def _build_docker(self):
        self.step4.set_status("构建中...", "#fdcb6e")
        cmd = ["bash", "computer_env/provision/docker/build_image.sh"]
        self._run_cmd(cmd, lambda code: self.step4.set_status(
            "已构建" if code == 0 else "构建失败",
            "#00b894" if code == 0 else "#d63031"
        ))

    def _provision_aws(self):
        self.step5.set_status("部署中...", "#fdcb6e")
        cmd = [sys.executable, "computer_env/provision/aws/setup_prereqs.py"]
        self._run_cmd(cmd, lambda code: self.step5.set_status(
            "已部署" if code == 0 else "部署失败",
            "#00b894" if code == 0 else "#d63031"
        ))

    def _deploy_aws_workers(self):
        self.step6.set_status("启动中...", "#fdcb6e")
        cmd = [sys.executable, "computer_env/provision/aws/deploy_workers.py"]
        self._run_cmd(cmd, lambda code: self.step6.set_status(
            "已启动" if code == 0 else "启动失败",
            "#00b894" if code == 0 else "#d63031"
        ))

    def _provision_tencent(self):
        self.step7.set_status("部署中...", "#fdcb6e")
        cmd = [sys.executable, "computer_env/provision/tencentcloud/setup_prereqs.py"]
        self._run_cmd(cmd, lambda code: self.step7.set_status(
            "已部署" if code == 0 else "部署失败",
            "#00b894" if code == 0 else "#d63031"
        ))

    def _deploy_tencent_workers(self):
        self.step8.set_status("启动中...", "#fdcb6e")
        cmd = [sys.executable, "computer_env/provision/tencentcloud/deploy_workers.py"]
        self._run_cmd(cmd, lambda code: self.step8.set_status(
            "已启动" if code == 0 else "启动失败",
            "#00b894" if code == 0 else "#d63031"
        ))

    def _verify_env(self):
        self.step9.set_status("检查中...", "#fdcb6e")
        self.log_area.clear()

        checks = []
        all_ok = True

        # Python version
        py_ver = platform.python_version()
        checks.append(f"Python 版本: {py_ver}")

        # Key packages
        packages = [
            ("e2b", "E2B SDK"),
            ("e2b_desktop", "E2B Desktop SDK"),
            ("anthropic", "Anthropic SDK"),
            ("openai", "OpenAI SDK"),
            ("httpx", "HTTPX"),
            ("PIL", "Pillow"),
            ("dotenv", "python-dotenv"),
            ("google.genai", "Google GenAI SDK"),
        ]
        for mod, name in packages:
            try:
                __import__(mod)
                checks.append(f"  [OK] {name}")
            except ImportError:
                checks.append(f"  [MISSING] {name}")
                all_ok = False

        # .env file
        root = project_root()
        env_path = root / ".env"
        if env_path.exists():
            checks.append("\n.env 文件: 存在")
            content = env_path.read_text()
            key_names = [
                "E2B_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
                "KIMI_API_KEY", "google_ai_studio_api_key", "DASHSCOPE_API_KEY",
            ]
            for kn in key_names:
                found = False
                for line in content.splitlines():
                    if line.strip().startswith(kn + "="):
                        val = line.split("=", 1)[1].strip()
                        if val:
                            found = True
                checks.append(f"  {'[OK]' if found else '[未配置]'} {kn}")
        else:
            checks.append("\n.env 文件: 不存在")
            all_ok = False

        # Docker
        if shutil.which("docker"):
            checks.append("\nDocker: 已安装")
            import subprocess
            try:
                result = subprocess.run(
                    ["docker", "info"], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    checks.append("  Docker 守护进程: 运行中")
                else:
                    checks.append("  Docker 守护进程: 未运行")
            except Exception:
                checks.append("  Docker 守护进程: 检查失败")
        else:
            checks.append("\nDocker: 未安装（如使用 Docker 后端则需要）")

        # AWS CLI
        if shutil.which("aws"):
            checks.append("AWS CLI: 已安装")
        else:
            checks.append("AWS CLI: 未安装（如使用 AWS 后端则需要）")

        # Tasks count
        tasks_dir = root / "task_generator" / "tasks"
        task_count = 0
        app_set = set()
        if tasks_dir.exists():
            for td in tasks_dir.iterdir():
                if td.is_dir() and (td / "task.json").exists():
                    task_count += 1
                    import json
                    try:
                        data = json.loads((td / "task.json").read_text(encoding="utf-8"))
                        app = data.get("app")
                        if app:
                            app_set.add(app)
                    except Exception:
                        pass
        checks.append(f"\n已有任务数: {task_count}（覆盖 {len(app_set)} 个应用）")

        # Verifiers count
        v_dir = root / "verifiers"
        v_count = 0
        if v_dir.exists():
            v_count = sum(
                1 for d in v_dir.iterdir()
                if d.is_dir() and (d / f"{d.name}.py").exists()
            )
        checks.append(f"已有验证器数: {v_count}")

        # Eval runs
        runs_dir = root / "evaluation" / "runs"
        run_count = 0
        if runs_dir.exists():
            for trajs in runs_dir.rglob("trajectories"):
                if trajs.is_dir():
                    run_count += 1
        checks.append(f"已有评估运行: {run_count}")

        # Smoke runs
        smoke_dir = root / "smoke" / "runs"
        smoke_count = 0
        if smoke_dir.exists():
            smoke_count = sum(1 for d in smoke_dir.iterdir() if d.is_dir())
        checks.append(f"已有 Smoke 运行: {smoke_count}")

        # Remote Docker pool
        pool_path = Path(os.path.expanduser(
            "~/.config/gui-synth-env/tencentcloud/worker_pool.json"
        ))
        if pool_path.exists():
            checks.append(f"\nRemote Docker Pool: 存在 ({pool_path})")
        else:
            checks.append(f"\nRemote Docker Pool: 不存在")

        # Disk space
        try:
            import shutil as _s
            total, used, free = _s.disk_usage(str(root))
            checks.append(f"\n磁盘空间: 总计 {total // (1024**3)}GB, "
                         f"已用 {used // (1024**3)}GB, "
                         f"可用 {free // (1024**3)}GB")
        except Exception:
            pass

        for line in checks:
            self.log_area.appendPlainText(line)

        self.step9.set_status(
            "检查完成" if all_ok else "部分缺失",
            "#00b894" if all_ok else "#fdcb6e"
        )
