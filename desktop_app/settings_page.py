"""
Settings page: comprehensive configuration for all .env variables.
Covers API keys, backend selection, Docker/E2B/AWS/TencentCloud, Smoke pipeline,
evaluation defaults, Azure, S3, database, and advanced options.
"""

import os
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


def _project_root():
    return Path(__file__).resolve().parent.parent


def _env_path():
    return _project_root() / ".env"


def _load_env_dict():
    env = {}
    p = _env_path()
    if not p.exists():
        example = _project_root() / ".env.example"
        if example.exists():
            import shutil
            shutil.copy(example, p)
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def _save_env_dict(env_dict):
    p = _env_path()
    lines = []
    existing_keys = set()

    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                k = stripped.split("=", 1)[0].strip()
                if k in env_dict:
                    val = env_dict[k]
                    lines.append(f"{k}={val}")
                    existing_keys.add(k)
                else:
                    lines.append(line)
            else:
                lines.append(line)

    for k, v in env_dict.items():
        if k not in existing_keys:
            lines.append(f"{k}={v}")

    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _make_password_field(placeholder="", tooltip="", width=400):
    le = QLineEdit()
    le.setEchoMode(QLineEdit.Password)
    le.setPlaceholderText(placeholder)
    le.setToolTip(tooltip)
    le.setMinimumWidth(width)
    return le


def _make_text_field(placeholder="", tooltip="", width=400):
    le = QLineEdit()
    le.setPlaceholderText(placeholder)
    le.setToolTip(tooltip)
    le.setMinimumWidth(width)
    return le


def _make_spin(min_val, max_val, default, suffix="", tooltip=""):
    sp = QSpinBox()
    sp.setRange(min_val, max_val)
    sp.setValue(default)
    if suffix:
        sp.setSuffix(suffix)
    if tooltip:
        sp.setToolTip(tooltip)
    return sp


MODELS = [
    "kimi-k2.6", "kimi-k2.5",
    "claude-sonnet-4-6", "claude-sonnet-4-5", "claude-sonnet-4",
    "claude-opus-4", "claude-opus-4-1", "claude-opus-4-5", "claude-opus-4-6",
    "claude-3-7-sonnet",
    "gpt-5.4", "gpt-5", "chatgpt", "computer-use-preview",
    "gemini-3-flash", "gemini-3-flash-preview", "gemini-2.5-computer-use",
    "qwen3-vl", "qwen2.5-vl-72b",
    "qwen3.5-35b-a3b", "qwen3.5-27b", "qwen3.5-9b", "qwen3.5-4b",
    "evocua-s1", "evocua-s2",
    "mano", "opencua", "dart",
    "gui-owl-1.5", "holo-3.1",
    "azure-chatgpt", "azure-gpt-5.4", "azure-computer-use-preview",
    "azure-gpt-5.3-chat",
]


class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._fields = {}
        self._init_ui()
        self._load()

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(30, 20, 30, 20)

        title = QLabel("设置")
        title.setObjectName("pageTitle")
        outer.addWidget(title)

        subtitle = QLabel("配置所有运行参数。修改后点击底部「保存」按钮写入 .env 文件。")
        subtitle.setObjectName("pageSubtitle")
        outer.addWidget(subtitle)

        # Tab widget for organized settings
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #dfe6e9; border-radius: 8px; padding: 8px; background: #fff; }
            QTabBar::tab { padding: 8px 18px; font-size: 13px; }
            QTabBar::tab:selected { background: #0984e3; color: #fff; border-radius: 6px 6px 0 0; }
            QTabBar::tab:!selected { background: #f5f6fa; color: #2d3436; }
        """)

        tabs.addTab(self._build_api_tab(), "API 密钥")
        tabs.addTab(self._build_backend_tab(), "运行后端")
        tabs.addTab(self._build_docker_tab(), "Docker 配置")
        tabs.addTab(self._build_eval_tab(), "评估参数")
        tabs.addTab(self._build_smoke_tab(), "Smoke 测试")
        tabs.addTab(self._build_aws_tab(), "AWS 云")
        tabs.addTab(self._build_tencent_tab(), "腾讯云")
        tabs.addTab(self._build_advanced_tab(), "高级设置")

        outer.addWidget(tabs, 1)

        # ── Buttons ──
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_reset = QPushButton("重置")
        btn_reset.setObjectName("btnSecondary")
        btn_reset.setToolTip("放弃修改，重新加载")
        btn_reset.clicked.connect(self._load)
        btn_row.addWidget(btn_reset)

        btn_save = QPushButton("保存设置")
        btn_save.setObjectName("btnSuccess")
        btn_save.setToolTip("保存所有设置到 .env 文件")
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_save)

        outer.addLayout(btn_row)

    # ── Tab builders ──

    def _build_api_tab(self):
        w = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)

        grp = QGroupBox("模型 API 密钥")
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(12)

        api_keys = [
            ("E2B_API_KEY", "E2B 密钥", "E2B 沙盒服务 API 密钥 (https://e2b.dev)"),
            ("OPENAI_API_KEY", "OpenAI 密钥", "GPT 系列模型 + LLM 评判"),
            ("ANTHROPIC_API_KEY", "Anthropic 密钥", "Claude 系列模型"),
            ("KIMI_API_KEY", "Kimi 密钥", "Kimi 系列模型（月之暗面）"),
            ("google_ai_studio_api_key", "Google AI 密钥", "Gemini 系列模型"),
            ("DASHSCOPE_API_KEY", "DashScope 密钥", "Qwen 系列模型（阿里云百炼）"),
        ]

        for key, label, tooltip in api_keys:
            le = _make_password_field("点击输入密钥...", tooltip)
            form.addRow(QLabel(label + ":"), le)
            self._fields[key] = le

        grp.setLayout(form)
        layout.addWidget(grp)

        # Azure keys
        grp_az = QGroupBox("Azure OpenAI（可选）")
        form_az = QFormLayout()
        form_az.setLabelAlignment(Qt.AlignRight)
        form_az.setSpacing(12)

        le_azk = _make_password_field("Azure API 密钥", "Azure OpenAI 资源密钥")
        form_az.addRow(QLabel("Azure 密钥:"), le_azk)
        self._fields["azure_api_key"] = le_azk

        le_azep = _make_text_field("https://YOUR-RESOURCE.cognitiveservices.azure.com/", "Azure 部署端点 URL")
        form_az.addRow(QLabel("Azure 端点:"), le_azep)
        self._fields["AZURE_OPENAI_ENDPOINT"] = le_azep

        grp_az.setLayout(form_az)
        layout.addWidget(grp_az)

        # AWS S3 keys (for env file storage)
        grp_s3 = QGroupBox("AWS S3 存储（可选，用于环境文件存储）")
        form_s3 = QFormLayout()
        form_s3.setLabelAlignment(Qt.AlignRight)
        form_s3.setSpacing(12)

        le_s3ak = _make_password_field("AWS Access Key", "")
        form_s3.addRow(QLabel("Access Key:"), le_s3ak)
        self._fields["aws_access_key"] = le_s3ak

        le_s3sk = _make_password_field("AWS Secret Key", "")
        form_s3.addRow(QLabel("Secret Key:"), le_s3sk)
        self._fields["aws_secret_key"] = le_s3sk

        le_s3r = _make_text_field("us-east-1", "AWS S3 区域")
        form_s3.addRow(QLabel("区域:"), le_s3r)
        self._fields["aws_region"] = le_s3r

        grp_s3.setLayout(form_s3)
        layout.addWidget(grp_s3)

        layout.addStretch()
        scroll.setWidget(container)
        vl = QVBoxLayout(w)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.addWidget(scroll)
        return w

    def _build_backend_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(12)

        grp = QGroupBox("沙盒运行后端")
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(12)

        cb = QComboBox()
        cb.addItems(["e2b", "docker", "remote_docker"])
        cb.setToolTip("选择运行沙盒的后端类型")
        form.addRow(QLabel("后端类型:"), cb)
        self._fields["ENV_BACKEND"] = cb

        grp.setLayout(form)
        layout.addWidget(grp)

        # E2B settings
        grp_e2b = QGroupBox("E2B 后端配置")
        form_e2b = QFormLayout()
        form_e2b.setLabelAlignment(Qt.AlignRight)
        form_e2b.setSpacing(12)

        le_tpl = _make_text_field("desktop-all-apps", "E2B 沙盒模板 ID")
        form_e2b.addRow(QLabel("E2B 模板:"), le_tpl)
        self._fields["E2B_ENV_TEMPLATE"] = le_tpl

        le_domain = _make_text_field("默认留空", "自部署 E2B 时使用")
        form_e2b.addRow(QLabel("E2B 域名:"), le_domain)
        self._fields["E2B_DOMAIN"] = le_domain

        grp_e2b.setLayout(form_e2b)
        layout.addWidget(grp_e2b)

        # Remote Docker
        grp_rd = QGroupBox("Remote Docker 配置（云端 Docker 后端）")
        form_rd = QFormLayout()
        form_rd.setLabelAlignment(Qt.AlignRight)
        form_rd.setSpacing(12)

        le_pool = _make_text_field(
            "~/.config/gui-synth-env/tencentcloud/worker_pool.json",
            "Worker 池文件路径"
        )
        form_rd.addRow(QLabel("Worker 池文件:"), le_pool)
        self._fields["REMOTE_DOCKER_POOL_FILE"] = le_pool

        le_img = _make_text_field(
            "gui-synth-env-desktop:latest",
            "Docker 镜像名称（由 setup_prereqs.py 打印的 URI）"
        )
        form_rd.addRow(QLabel("Docker 镜像:"), le_img)
        self._fields["DOCKER_ENV_IMAGE"] = le_img

        le_rdtoken = _make_password_field("随机字符串", "远程 Docker API 认证令牌")
        form_rd.addRow(QLabel("API Token:"), le_rdtoken)
        self._fields["REMOTE_DOCKER_API_TOKEN"] = le_rdtoken

        grp_rd.setLayout(form_rd)
        layout.addWidget(grp_rd)

        layout.addStretch()
        return w

    def _build_docker_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(12)

        grp = QGroupBox("本地 Docker 后端参数")
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(12)

        le_img = _make_text_field("gui-synth-env-desktop:latest", "本地 Docker 镜像名")
        form.addRow(QLabel("Docker 镜像:"), le_img)
        self._fields["DOCKER_IMAGE"] = le_img

        le_plat = _make_text_field("linux/amd64", "Docker 平台架构")
        form.addRow(QLabel("平台:"), le_plat)
        self._fields["DOCKER_PLATFORM"] = le_plat

        le_shm = _make_text_field("2g", "共享内存大小（如 1g, 2g, 4g）")
        form.addRow(QLabel("SHM 大小:"), le_shm)
        self._fields["DOCKER_SHM_SIZE"] = le_shm

        le_mem = _make_text_field("留空不限制", "内存限制（如 4g, 8g）")
        form.addRow(QLabel("内存限制:"), le_mem)
        self._fields["DOCKER_MEMORY"] = le_mem

        le_cpu = _make_text_field("留空不限制", "CPU 限制（如 2, 4）")
        form.addRow(QLabel("CPU 限制:"), le_cpu)
        self._fields["DOCKER_CPUS"] = le_cpu

        sp_rdy = _make_spin(10, 600, 120, " 秒", "等待桌面就绪的超时时间")
        form.addRow(QLabel("就绪超时:"), sp_rdy)
        self._fields["DOCKER_READY_TIMEOUT"] = sp_rdy

        grp.setLayout(form)
        layout.addWidget(grp)

        hint = QLabel(
            "提示：选择 docker 后端时，需先构建 Docker 镜像（在「环境安装」页面操作），"
            "或手动运行 computer_env/provision/docker/build_image.sh。"
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#636e72;font-size:12px;padding:8px;")
        layout.addWidget(hint)

        layout.addStretch()
        return w

    def _build_eval_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(12)

        grp = QGroupBox("评估默认参数")
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(12)

        cb_model = QComboBox()
        cb_model.setEditable(True)
        cb_model.addItems(MODELS)
        cb_model.setToolTip("默认评估模型")
        form.addRow(QLabel("默认模型:"), cb_model)
        self._fields["EVAL_MODEL"] = cb_model

        sp_iter = _make_spin(1, 500, 100, "", "每个任务的最大代理步数")
        form.addRow(QLabel("最大步数:"), sp_iter)
        self._fields["EVAL_MAX_ITERATIONS"] = sp_iter

        sp_timeout = _make_spin(60, 7200, 3600, " 秒", "沙盒运行超时时间")
        form.addRow(QLabel("沙盒超时:"), sp_timeout)
        self._fields["EVAL_SANDBOX_TIMEOUT"] = sp_timeout

        cb_judge = QComboBox()
        cb_judge.setEditable(True)
        cb_judge.addItems(["gpt-5.4", "gpt-5", "claude-sonnet-4-6", "claude-sonnet-4-5", "kimi-k2.6"])
        cb_judge.setToolTip("LLM 评判模型（用于自动评分）")
        form.addRow(QLabel("评判模型:"), cb_judge)
        self._fields["JUDGE_MODEL"] = cb_judge

        grp.setLayout(form)
        layout.addWidget(grp)

        # Database (optional)
        grp_db = QGroupBox("数据库（可选，用于结果持久化）")
        form_db = QFormLayout()
        form_db.setLabelAlignment(Qt.AlignRight)
        form_db.setSpacing(12)

        le_pg = _make_text_field("postgresql://user:pass@host:5432/dbname", "PostgreSQL 连接字符串")
        form_db.addRow(QLabel("连接字符串:"), le_pg)
        self._fields["POSTGRES_CONNECTION_STRING"] = le_pg

        grp_db.setLayout(form_db)
        layout.addWidget(grp_db)

        layout.addStretch()
        return w

    def _build_smoke_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(12)

        grp = QGroupBox("Smoke 测试流水线参数")
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(12)

        cb_sb = QComboBox()
        cb_sb.addItems(["claude", "codex"])
        cb_sb.setToolTip("Smoke 测试使用的后端")
        form.addRow(QLabel("Smoke 后端:"), cb_sb)
        self._fields["SMOKE_BACKEND"] = cb_sb

        cb_sm = QComboBox()
        cb_sm.setEditable(True)
        cb_sm.addItems(["kimi-k2.6", "kimi-k2.5", "claude-sonnet-4-6", "gpt-5.4"])
        cb_sm.setToolTip("执行 Smoke 任务的 GUI 代理模型")
        form.addRow(QLabel("Smoke 模型:"), cb_sm)
        self._fields["SMOKE_MODEL"] = cb_sm

        sp_si = _make_spin(10, 500, 100, "", "每个 Smoke 任务最大代理步数")
        form.addRow(QLabel("最大步数:"), sp_si)
        self._fields["SMOKE_MAX_ITERATIONS"] = sp_si

        sp_sr = _make_spin(1, 10, 3, "", "评判→比较→修复 最大轮数")
        form.addRow(QLabel("最大修复轮数:"), sp_sr)
        self._fields["SMOKE_MAX_ROUNDS"] = sp_sr

        sp_st = _make_spin(60, 7200, 3600, " 秒", "Smoke 沙盒超时")
        form.addRow(QLabel("沙盒超时:"), sp_st)
        self._fields["SMOKE_SANDBOX_TIMEOUT"] = sp_st

        sp_smt = _make_spin(1, 100, 20, "", "每应用最大 Smoke 任务数")
        form.addRow(QLabel("最大任务数:"), sp_smt)
        self._fields["SMOKE_MAX_TASKS"] = sp_smt

        grp.setLayout(form)
        layout.addWidget(grp)

        hint = QLabel(
            "提示：这些参数也可以在「Smoke 测试」页面运行时通过命令行参数覆盖。"
            "此处配置的是默认值，写入 .env 文件后全局生效。"
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#636e72;font-size:12px;padding:8px;")
        layout.addWidget(hint)

        layout.addStretch()
        return w

    def _build_aws_tab(self):
        w = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)

        grp = QGroupBox("AWS Remote Docker 部署配置")
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(12)

        fields = [
            ("AWS_PROFILE", "AWS Profile", "AWS SSO profile 名称", ""),
            ("AWS_REGION", "区域", "AWS 部署区域", "us-east-1"),
            ("AWS_NAME_PREFIX", "名称前缀", "资源命名前缀", "opencomputer-dev"),
            ("AWS_CONTROLLER_CIDR", "控制器 CIDR", "允许入站的 IP/CIDR（通常填你的公网 IP/32）", ""),
        ]
        for key, label, tooltip, placeholder in fields:
            le = _make_text_field(placeholder, tooltip)
            form.addRow(QLabel(label + ":"), le)
            self._fields[key] = le

        grp.setLayout(form)
        layout.addWidget(grp)

        grp2 = QGroupBox("AWS Worker 配置")
        form2 = QFormLayout()
        form2.setLabelAlignment(Qt.AlignRight)
        form2.setSpacing(12)

        le_it = _make_text_field("m6i.2xlarge", "EC2 实例类型")
        form2.addRow(QLabel("实例类型:"), le_it)
        self._fields["AWS_WORKER_INSTANCE_TYPE"] = le_it

        sp_wc = _make_spin(1, 50, 1, "", "Worker 实例数量")
        form2.addRow(QLabel("Worker 数:"), sp_wc)
        self._fields["AWS_WORKER_COUNT"] = sp_wc

        sp_cpw = _make_spin(1, 20, 6, "", "每个 Worker 运行容器数")
        form2.addRow(QLabel("容器/Worker:"), sp_cpw)
        self._fields["AWS_CONTAINERS_PER_WORKER"] = sp_cpw

        grp2.setLayout(form2)
        layout.addWidget(grp2)

        grp3 = QGroupBox("AWS 可选覆盖")
        form3 = QFormLayout()
        form3.setLabelAlignment(Qt.AlignRight)
        form3.setSpacing(12)

        opt_fields = [
            ("AWS_S3_BUCKET", "S3 存储桶", "留空自动生成", ""),
            ("AWS_VPC_ID", "VPC ID", "留空使用默认 VPC", "vpc-xxxxxxxx"),
            ("AWS_SUBNET_ID", "子网 ID", "留空使用默认子网", "subnet-xxxxxxxx"),
            ("AWS_ECR_REPOSITORY", "ECR 仓库", "留空自动派生", ""),
            ("AWS_INSTANCE_PROFILE_NAME", "实例 Profile", "留空自动派生", ""),
            ("AWS_DEBUG_ACCESS", "调试访问", "SSM 或留空", "SSM"),
        ]
        for key, label, tooltip, placeholder in opt_fields:
            le = _make_text_field(placeholder, tooltip)
            form3.addRow(QLabel(label + ":"), le)
            self._fields[key] = le

        sp_vol = _make_spin(20, 500, 64, " GB", "根卷大小")
        form3.addRow(QLabel("根卷大小:"), sp_vol)
        self._fields["AWS_WORKER_ROOT_VOLUME_SIZE_GB"] = sp_vol

        grp3.setLayout(form3)
        layout.addWidget(grp3)

        hint = QLabel(
            "提示：AWS 部署需要先运行 setup_prereqs.py 脚本创建基础设施。"
            "请在「环境安装」页面点击「AWS 部署」按钮。"
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#636e72;font-size:12px;padding:8px;")
        layout.addWidget(hint)

        layout.addStretch()
        scroll.setWidget(container)
        vl = QVBoxLayout(w)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.addWidget(scroll)
        return w

    def _build_tencent_tab(self):
        w = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)

        grp = QGroupBox("腾讯云认证")
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(12)

        le_sid = _make_password_field("腾讯云 SecretId", "")
        form.addRow(QLabel("SecretId:"), le_sid)
        self._fields["TENCENTCLOUD_SECRET_ID"] = le_sid

        le_skey = _make_password_field("腾讯云 SecretKey", "")
        form.addRow(QLabel("SecretKey:"), le_skey)
        self._fields["TENCENTCLOUD_SECRET_KEY"] = le_skey

        le_token = _make_password_field("临时令牌（可选）", "STS 临时凭证")
        form.addRow(QLabel("Session Token:"), le_token)
        self._fields["TENCENTCLOUD_SESSION_TOKEN"] = le_token

        grp.setLayout(form)
        layout.addWidget(grp)

        grp2 = QGroupBox("腾讯云部署配置")
        form2 = QFormLayout()
        form2.setLabelAlignment(Qt.AlignRight)
        form2.setSpacing(12)

        tc_fields = [
            ("TENCENTCLOUD_REGION", "地域", "ap-guangzhou"),
            ("TENCENTCLOUD_NAME_PREFIX", "名称前缀", "opencomputer-dev"),
            ("TENCENTCLOUD_CONTROLLER_CIDR", "控制器 CIDR", "你的公网 IP/32"),
            ("TENCENTCLOUD_CVM_ZONE", "可用区", "ap-guangzhou-6"),
            ("TENCENTCLOUD_CVM_IMAGE_ID", "镜像 ID", "img-487zeit5"),
            ("TENCENTCLOUD_CVM_INSTANCE_TYPE", "实例类型", "S5.LARGE8"),
            ("TENCENTCLOUD_VPC_ID", "VPC ID", "vpc-xxxxxxxx"),
            ("TENCENTCLOUD_SUBNET_ID", "子网 ID", "subnet-xxxxxxxx"),
            ("TENCENTCLOUD_ACCOUNT_UIN", "账号 UIN", "100012345678"),
        ]
        for key, label, placeholder in tc_fields:
            le = _make_text_field(placeholder, "")
            form2.addRow(QLabel(label + ":"), le)
            self._fields[key] = le

        sp_twc = _make_spin(1, 50, 1, "", "Worker 数")
        form2.addRow(QLabel("Worker 数:"), sp_twc)
        self._fields["TENCENTCLOUD_WORKER_COUNT"] = sp_twc

        sp_tcpw = _make_spin(1, 20, 6, "", "每 Worker 容器数")
        form2.addRow(QLabel("容器/Worker:"), sp_tcpw)
        self._fields["TENCENTCLOUD_CONTAINERS_PER_WORKER"] = sp_tcpw

        grp2.setLayout(form2)
        layout.addWidget(grp2)

        grp3 = QGroupBox("腾讯云 TCR 镜像仓库")
        form3 = QFormLayout()
        form3.setLabelAlignment(Qt.AlignRight)
        form3.setSpacing(12)

        tcr_fields = [
            ("TENCENTCLOUD_TCR_PERSONAL_SERVER", "TCR 服务器", "ccr.ccs.tencentyun.com"),
            ("TENCENTCLOUD_TCR_PERSONAL_NAMESPACE", "TCR 命名空间", ""),
            ("TENCENTCLOUD_TCR_PERSONAL_REPOSITORY", "TCR 仓库名", "desktop"),
        ]
        for key, label, placeholder in tcr_fields:
            le = _make_text_field(placeholder, "")
            form3.addRow(QLabel(label + ":"), le)
            self._fields[key] = le

        le_tcrpw = _make_password_field("TCR 密码", "")
        form3.addRow(QLabel("TCR 密码:"), le_tcrpw)
        self._fields["TENCENTCLOUD_TCR_PERSONAL_PASSWORD"] = le_tcrpw

        grp3.setLayout(form3)
        layout.addWidget(grp3)

        layout.addStretch()
        scroll.setWidget(container)
        vl = QVBoxLayout(w)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.addWidget(scroll)
        return w

    def _build_advanced_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(12)

        grp = QGroupBox("自定义 API 端点")
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(12)

        le_base = _make_text_field("http://127.0.0.1:8001/v1", "自定义 OpenAI 兼容 API 端点（本地 vLLM / 代理）")
        form.addRow(QLabel("自定义 API 地址:"), le_base)
        self._fields["OPENAI_BASE_URL"] = le_base

        grp.setLayout(form)
        layout.addWidget(grp)

        grp2 = QGroupBox("代理设置（可选）")
        form2 = QFormLayout()
        form2.setLabelAlignment(Qt.AlignRight)
        form2.setSpacing(12)

        le_hp = _make_text_field("http://proxy:port", "HTTP 代理")
        form2.addRow(QLabel("HTTP 代理:"), le_hp)
        self._fields["HTTP_PROXY"] = le_hp

        le_hsp = _make_text_field("http://proxy:port", "HTTPS 代理")
        form2.addRow(QLabel("HTTPS 代理:"), le_hsp)
        self._fields["HTTPS_PROXY"] = le_hsp

        le_np = _make_text_field("localhost,127.0.0.1", "不代理的地址列表")
        form2.addRow(QLabel("No Proxy:"), le_np)
        self._fields["NO_PROXY"] = le_np

        grp2.setLayout(form2)
        layout.addWidget(grp2)

        grp3 = QGroupBox("其他高级选项")
        form3 = QFormLayout()
        form3.setLabelAlignment(Qt.AlignRight)
        form3.setSpacing(12)

        le_bp = _make_text_field("留空自动派生", "AWS S3 引导路径前缀")
        form3.addRow(QLabel("Bootstrap 前缀:"), le_bp)
        self._fields["AWS_BOOTSTRAP_PREFIX"] = le_bp

        grp3.setLayout(form3)
        layout.addWidget(grp3)

        hint = QLabel(
            "提示：代理设置在网络受限环境下使用。自定义 API 端点用于本地部署模型"
            "（如 vLLM、LocalAI 等 OpenAI 兼容服务）。"
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#636e72;font-size:12px;padding:8px;")
        layout.addWidget(hint)

        layout.addStretch()
        return w

    # ── Load / Save ──

    def _load(self):
        env = _load_env_dict()
        for key, widget in self._fields.items():
            val = env.get(key, "")
            if isinstance(widget, QLineEdit):
                widget.setText(val)
            elif isinstance(widget, QComboBox):
                idx = widget.findText(val)
                if idx >= 0:
                    widget.setCurrentIndex(idx)
                elif val:
                    widget.setCurrentText(val)
            elif isinstance(widget, QSpinBox):
                try:
                    widget.setValue(int(val))
                except (ValueError, TypeError):
                    pass

    def _save(self):
        env = _load_env_dict()
        for key, widget in self._fields.items():
            if isinstance(widget, QLineEdit):
                v = widget.text().strip()
            elif isinstance(widget, QComboBox):
                v = widget.currentText().strip()
            elif isinstance(widget, QSpinBox):
                v = str(widget.value())
            else:
                continue
            if v:
                env[key] = v
            elif key in env:
                del env[key]

        _save_env_dict(env)
        QMessageBox.information(self, "保存成功", "设置已保存到 .env 文件。\n部分设置需要重启应用才能生效。")
