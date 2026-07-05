"""
OpenComputer Desktop — WebUI backend (Flask).
Single-file backend serving the SPA and all API routes.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

from flask import Flask, jsonify, render_template, request, Response

# ── Paths ──
APP_DIR = Path(__file__).resolve().parent
DESKTOP_DIR = APP_DIR.parent
PROJECT_ROOT = DESKTOP_DIR.parent

app = Flask(
    __name__,
    template_folder=str(APP_DIR / "templates"),
    static_folder=str(APP_DIR / "static"),
)
app.config["SECRET_KEY"] = "opencomputer-desktop"

# ── Process manager ──
_processes = {}
_process_lock = threading.Lock()
_log_buffers = {}


def _project_root():
    return PROJECT_ROOT


def _run_background(proc_id, cmd, cwd=None):
    """Run a command in the background, stream output to log buffer."""
    cwd = cwd or str(_project_root())
    with _process_lock:
        _log_buffers[proc_id] = []
        _processes[proc_id] = {"status": "running", "code": None}

    def _worker():
        try:
            proc = subprocess.Popen(
                cmd, cwd=cwd,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
            )
            with _process_lock:
                _processes[proc_id]["popen"] = proc

            for line in proc.stdout:
                with _process_lock:
                    _log_buffers[proc_id].append(line.rstrip("\n"))
            proc.wait()
            with _process_lock:
                _processes[proc_id]["status"] = "done"
                _processes[proc_id]["code"] = proc.returncode
        except Exception as e:
            with _process_lock:
                _log_buffers[proc_id].append(f"[ERROR] {e}")
                _processes[proc_id]["status"] = "error"
                _processes[proc_id]["code"] = 1

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return proc_id


# ── Utility helpers ──

def _list_apps():
    tasks_dir = _project_root() / "task_generator" / "tasks"
    apps = set()
    if tasks_dir.exists():
        for td in tasks_dir.iterdir():
            if td.is_dir() and (td / "task.json").exists():
                try:
                    data = json.loads((td / "task.json").read_text("utf-8"))
                    a = data.get("app")
                    if a:
                        apps.add(a)
                except Exception:
                    pass
    return sorted(apps)


def _list_tasks_for_app(app_name):
    tasks_dir = _project_root() / "task_generator" / "tasks"
    tasks = []
    if not tasks_dir.exists():
        return tasks
    for td in sorted(tasks_dir.iterdir()):
        if td.is_dir() and (td / "task.json").exists():
            try:
                data = json.loads((td / "task.json").read_text("utf-8"))
                if data.get("app") == app_name:
                    tasks.append({"id": data.get("id", td.name), "task": data.get("task", "")})
            except Exception:
                pass
    return tasks


def _count_tasks():
    tasks_dir = _project_root() / "task_generator" / "tasks"
    count, apps = 0, set()
    if tasks_dir.exists():
        for td in tasks_dir.iterdir():
            if td.is_dir() and (td / "task.json").exists():
                count += 1
                try:
                    data = json.loads((td / "task.json").read_text("utf-8"))
                    a = data.get("app")
                    if a:
                        apps.add(a)
                except Exception:
                    pass
    return count, len(apps)


def _count_verifiers():
    v_dir = _project_root() / "verifiers"
    if not v_dir.exists():
        return 0
    return sum(1 for d in v_dir.iterdir() if d.is_dir() and (d / f"{d.name}.py").exists())


def _count_runs():
    runs_dir = _project_root() / "evaluation" / "runs"
    if not runs_dir.exists():
        return 0
    return sum(1 for d in runs_dir.rglob("trajectories") if d.is_dir())


def _check_env():
    env_path = _project_root() / ".env"
    if env_path.exists():
        content = env_path.read_text()
        for key in ["E2B_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]:
            for line in content.splitlines():
                if line.strip().startswith(key + "="):
                    val = line.split("=", 1)[1].strip()
                    if val and not val.startswith("#"):
                        return True, "已配置"
    return False, "未配置密钥"


def _list_verifier_apps():
    v_dir = _project_root() / "verifiers"
    apps = []
    if v_dir.exists():
        for d in sorted(v_dir.iterdir()):
            if d.is_dir() and (d / f"{d.name}.py").exists():
                apps.append(d.name)
    return apps


def _list_eval_runs():
    runs_dir = _project_root() / "evaluation" / "runs"
    runs = []
    if not runs_dir.exists():
        return runs
    for d in sorted(runs_dir.iterdir(), reverse=True):
        if d.is_dir():
            runs.append(d.name)
    return runs


def _list_smoke_runs(app_name=None):
    runs_dir = _project_root() / "smoke" / "runs"
    runs = []
    if not runs_dir.exists():
        return runs
    for d in sorted(runs_dir.iterdir(), reverse=True):
        if d.is_dir():
            if app_name and not d.name.startswith(app_name):
                continue
            runs.append({"name": d.name, "has_report": (d / "REPORT.md").exists()})
    return runs


# ── Routes ──

@app.route("/")
def index():
    return render_template("index.html")


# ── API: Dashboard ──

@app.route("/api/dashboard")
def api_dashboard():
    task_count, app_count = _count_tasks()
    run_count = _count_runs()
    v_count = _count_verifiers()
    env_ok, env_msg = _check_env()
    return jsonify({
        "tasks": task_count,
        "apps": app_count,
        "verifiers": v_count,
        "runs": run_count,
        "env_ok": env_ok,
        "env_msg": env_msg,
    })


# ── API: Setup ──

@app.route("/api/setup/status")
def api_setup_status():
    checks = {}
    # Python deps
    try:
        import e2b, anthropic, openai  # noqa
        checks["deps"] = True
    except ImportError:
        checks["deps"] = False
    # .env
    checks["env"] = (_project_root() / ".env").exists()
    # Docker
    checks["docker"] = bool(shutil.which("docker"))
    # AWS CLI
    checks["aws_cli"] = bool(shutil.which("aws"))
    return jsonify(checks)


@app.route("/api/setup/install-deps", methods=["POST"])
def api_install_deps():
    pid = "setup_deps"
    cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
    _run_background(pid, cmd)
    return jsonify({"proc_id": pid})


@app.route("/api/setup/create-env", methods=["POST"])
def api_create_env():
    root = _project_root()
    src = root / ".env.example"
    dst = root / ".env"
    if dst.exists():
        return jsonify({"ok": True, "msg": ".env 已存在"})
    if src.exists():
        shutil.copy(src, dst)
        return jsonify({"ok": True, "msg": "已创建 .env"})
    return jsonify({"ok": False, "msg": ".env.example 不存在"})


@app.route("/api/setup/run-step", methods=["POST"])
def api_setup_run_step():
    data = request.json or {}
    step = data.get("step")
    cmds = {
        "e2b": [sys.executable, "computer_env/provision/e2b/build_all_apps_template.py"],
        "docker": ["bash", "computer_env/provision/docker/build_image.sh"],
        "aws": [sys.executable, "computer_env/provision/aws/setup_prereqs.py"],
        "aws_workers": [sys.executable, "computer_env/provision/aws/deploy_workers.py"],
        "tencent": [sys.executable, "computer_env/provision/tencentcloud/setup_prereqs.py"],
        "tencent_workers": [sys.executable, "computer_env/provision/tencentcloud/deploy_workers.py"],
    }
    cmd = cmds.get(step)
    if not cmd:
        return jsonify({"error": "unknown step"}), 400
    pid = f"setup_{step}"
    _run_background(pid, cmd)
    return jsonify({"proc_id": pid})


@app.route("/api/setup/verify", methods=["POST"])
def api_setup_verify():
    checks = []
    all_ok = True

    checks.append(f"Python 版本: {platform.python_version()}")
    packages = [
        ("e2b", "E2B SDK"), ("e2b_desktop", "E2B Desktop"),
        ("anthropic", "Anthropic"), ("openai", "OpenAI"),
        ("httpx", "HTTPX"), ("PIL", "Pillow"),
        ("dotenv", "python-dotenv"),
    ]
    for mod, name in packages:
        try:
            __import__(mod)
            checks.append(f"  ✓ {name}")
        except ImportError:
            checks.append(f"  ✗ {name}")
            all_ok = False

    root = _project_root()
    env_path = root / ".env"
    if env_path.exists():
        checks.append("\n.env 文件: 存在")
    else:
        checks.append("\n.env 文件: 不存在")
        all_ok = False

    if shutil.which("docker"):
        checks.append("Docker: 已安装")
    else:
        checks.append("Docker: 未安装")

    tasks_dir = root / "task_generator" / "tasks"
    task_count = sum(1 for td in tasks_dir.iterdir()
                     if td.is_dir() and (td / "task.json").exists()) if tasks_dir.exists() else 0
    checks.append(f"\n已有任务数: {task_count}")
    checks.append(f"已有验证器数: {_count_verifiers()}")

    return jsonify({"checks": checks, "all_ok": all_ok})


# ── API: Settings ──

@app.route("/api/settings/load")
def api_settings_load():
    env_path = _project_root() / ".env"
    settings = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                settings[k.strip()] = v.strip()
    return jsonify(settings)


@app.route("/api/settings/save", methods=["POST"])
def api_settings_save():
    data = request.json or {}
    env_path = _project_root() / ".env"
    lines = []
    for k, v in data.items():
        lines.append(f"{k}={v}")
    env_path.write_text("\n".join(lines) + "\n")
    return jsonify({"ok": True})


# ── API: Verifiers ──

@app.route("/api/verifiers/list")
def api_verifiers_list():
    return jsonify(_list_verifier_apps())


@app.route("/api/verifiers/detail/<app_name>")
def api_verifier_detail(app_name):
    v_dir = _project_root() / "verifiers" / app_name
    result = {}
    readme = v_dir / "README.md"
    if readme.exists():
        result["readme"] = readme.read_text("utf-8", errors="replace")
    code = v_dir / f"{app_name}.py"
    if code.exists():
        result["code"] = code.read_text("utf-8", errors="replace")
    test_md = v_dir / "Test.md"
    if test_md.exists():
        result["test_md"] = test_md.read_text("utf-8", errors="replace")
    return jsonify(result)


@app.route("/api/verifiers/run-test", methods=["POST"])
def api_verifier_run_test():
    data = request.json or {}
    app_name = data.get("app")
    if not app_name:
        return jsonify({"error": "missing app"}), 400
    pid = f"verifier_test_{app_name}"
    cmd = [sys.executable, f"verifiers/{app_name}/test_{app_name}.py"]
    _run_background(pid, cmd)
    return jsonify({"proc_id": pid})


# ── API: Smoke ──

@app.route("/api/smoke/run", methods=["POST"])
def api_smoke_run():
    data = request.json or {}
    app_name = data.get("app")
    cmd = [sys.executable, "smoke/smoke_loop.py", "--app", app_name]
    if data.get("max_tasks"):
        cmd.extend(["--max-tasks", str(data["max_tasks"])])
    if data.get("generate_only"):
        cmd.append("--generate-only")
    if data.get("run_only"):
        cmd.append("--run-only")
    pid = f"smoke_{app_name}_{int(time.time())}"
    _run_background(pid, cmd)
    return jsonify({"proc_id": pid})


@app.route("/api/smoke/report/<app_name>")
def api_smoke_report(app_name):
    runs = _list_smoke_runs(app_name)
    if not runs or not runs[0]["has_report"]:
        return jsonify({"report": None})
    report_path = _project_root() / "smoke" / "runs" / runs[0]["name"] / "REPORT.md"
    return jsonify({"report": report_path.read_text("utf-8", errors="replace")})


# ── API: Task Generation ──

@app.route("/api/taskgen/stages/<app_name>")
def api_taskgen_stages(app_name):
    tasks_dir = _project_root() / "task_generator" / "tasks"
    items = []
    if tasks_dir.exists():
        for td in sorted(tasks_dir.iterdir()):
            if td.is_dir() and (td / "task.json").exists():
                try:
                    data = json.loads((td / "task.json").read_text("utf-8"))
                    if data.get("app") == app_name:
                        items.append({
                            "id": data.get("id", td.name),
                            "task": data.get("task", ""),
                            "complexity": data.get("metadata", {}).get("complexity"),
                            "difficulty": data.get("metadata", {}).get("estimated_difficulty"),
                        })
                except Exception:
                    pass
    lessons_path = _project_root() / "task_generator" / "LESSONS.md"
    lessons = ""
    if lessons_path.exists():
        lessons = lessons_path.read_text("utf-8", errors="replace")
    return jsonify({"tasks": items, "lessons": lessons})


# ── API: Tasks Browser ──

@app.route("/api/tasks")
def api_tasks():
    app_filter = request.args.get("app", "")
    search = request.args.get("search", "").lower()
    tasks_dir = _project_root() / "task_generator" / "tasks"
    results = []
    if not tasks_dir.exists():
        return jsonify(results)
    for td in sorted(tasks_dir.iterdir()):
        if not td.is_dir():
            continue
        tf = td / "task.json"
        if not tf.exists():
            continue
        try:
            data = json.loads(tf.read_text("utf-8"))
            if app_filter and data.get("app") != app_filter:
                continue
            tid = data.get("id", td.name)
            if search and search not in tid.lower() and search not in data.get("task", "").lower():
                continue
            results.append({
                "id": tid,
                "app": data.get("app", ""),
                "difficulty": data.get("metadata", {}).get("estimated_difficulty"),
                "complexity": data.get("metadata", {}).get("complexity"),
                "task": data.get("task", ""),
                "verification": data.get("verification", []),
            })
        except Exception:
            pass
    return jsonify(results)


# ── API: Evaluation ──

MODELS = [
    "deepseek-chat", "deepseek-coder", "deepseek-reasoner",
    "kimi-k2.6", "kimi-k2.5",
    "claude-sonnet-4-6", "claude-sonnet-4-5", "claude-sonnet-4",
    "claude-opus-4", "gpt-5.4", "gpt-5", "chatgpt",
    "gemini-3-flash", "qwen3-vl", "qwen3.5-35b-a3b",
    "evocua-s1", "mano", "opencua", "dart", "gui-owl-1.5", "holo-3.1",
]


@app.route("/api/eval/config")
def api_eval_config():
    return jsonify({"apps": _list_apps(), "models": MODELS})


@app.route("/api/eval/run", methods=["POST"])
def api_eval_run():
    data = request.json or {}
    cmd = [sys.executable, "evaluation/run_eval.py"]
    app_name = data.get("app")
    if app_name and app_name != "全部应用":
        cmd.extend(["--app", app_name])
        task = data.get("task")
        if task and task != "全部任务":
            cmd.extend(["--task", task])
    cmd.extend(["--model", data.get("model", "kimi-k2.6")])
    cmd.extend(["--env-backend", data.get("backend", "e2b")])
    cmd.extend(["--max-iterations", str(data.get("max_iter", 100))])
    cmd.extend(["--sandbox-timeout", str(data.get("timeout", 3600))])
    cmd.extend(["--parallel", str(data.get("parallel", 1))])
    if data.get("keep_alive"):
        cmd.append("--keep-alive")
    pid = f"eval_{int(time.time())}"
    _run_background(pid, cmd)
    return jsonify({"proc_id": pid})


# ── API: Rerun ──

@app.route("/api/rerun/runs")
def api_rerun_runs():
    return jsonify(_list_eval_runs())


@app.route("/api/rerun/run", methods=["POST"])
def api_rerun_run():
    data = request.json or {}
    cmd = [sys.executable, "evaluation/run_eval.py"]
    if data.get("resume"):
        cmd.extend(["--resume", data["resume"]])
    cmd.extend(["--model", data.get("model", "kimi-k2.6")])
    cmd.extend(["--max-iterations", str(data.get("max_iter", 100))])
    pid = f"rerun_{int(time.time())}"
    _run_background(pid, cmd)
    return jsonify({"proc_id": pid})


# ── API: Results ──

@app.route("/api/results/runs")
def api_results_runs():
    return jsonify(_list_eval_runs())


@app.route("/api/results/detail/<run_id>")
def api_results_detail(run_id):
    run_dir = _project_root() / "evaluation" / "runs" / run_id
    if not run_dir.exists():
        return jsonify([])
    results = []
    trajs = run_dir / "trajectories"
    if trajs.exists():
        for tf in sorted(trajs.iterdir()):
            if tf.suffix == ".json":
                try:
                    data = json.loads(tf.read_text("utf-8"))
                    results.append({
                        "id": tf.stem,
                        "app": data.get("app", ""),
                        "model": data.get("model", ""),
                        "score": data.get("score"),
                        "steps": data.get("steps"),
                        "status": data.get("status", ""),
                    })
                except Exception:
                    pass
    return jsonify(results)


# ── API: Repair ──

@app.route("/api/repair/run", methods=["POST"])
def api_repair_run():
    data = request.json or {}
    app_name = data.get("app")
    task = data.get("task")
    cmd = [sys.executable, "evaluation/repair/repair_loop.py",
           "--app", app_name, "--task", task,
           "--max-rounds", str(data.get("max_rounds", 3))]
    pid = f"repair_{task}_{int(time.time())}"
    _run_background(pid, cmd)
    return jsonify({"proc_id": pid})


@app.route("/api/repair/history")
def api_repair_history():
    runs_dir = _project_root() / "evaluation" / "repair" / "runs"
    runs = []
    if runs_dir and runs_dir.exists():
        for d in sorted(runs_dir.iterdir(), reverse=True):
            if d.is_dir():
                solved = d / "SOLVED.md"
                runs.append({
                    "name": d.name,
                    "has_solved": solved.exists(),
                    "solved": solved.read_text("utf-8", errors="replace") if solved.exists() else None,
                })
    return jsonify(runs)


# ── API: Sandbox ──

@app.route("/api/sandbox/launch", methods=["POST"])
def api_sandbox_launch():
    data = request.json or {}
    cmd = [sys.executable, "computer_env/launch_sandbox.py"]
    if data.get("app"):
        cmd.extend(["--app", data["app"]])
    cmd.extend(["--backend", data.get("backend", "e2b")])
    cmd.extend(["--timeout", str(data.get("timeout", 3600))])
    pid = f"sandbox_{int(time.time())}"
    _run_background(pid, cmd)
    return jsonify({"proc_id": pid})


# ── API: Cleanup ──

@app.route("/api/cleanup/run", methods=["POST"])
def api_cleanup_run():
    data = request.json or {}
    action = data.get("action")
    if action == "docker_list":
        cmd = ["docker", "ps", "-a", "--format", "{{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Names}}"]
    elif action == "docker_clean":
        force = data.get("force", False)
        if force:
            cmd = ["docker", "rm", "-f", "$(docker ps -aq)"]
        else:
            cmd = ["docker", "container", "prune", "-f"]
    elif action == "e2b_list":
        cmd = [sys.executable, "-c",
               "import e2b; sandboxes = e2b.Sandbox.list(); "
               "[print(f'{s.sandbox_id}\\t{s.template_id}') for s in sandboxes]"]
    elif action == "e2b_clean":
        cmd = [sys.executable, "-c",
               "import e2b; sandboxes = e2b.Sandbox.list(); "
               "[s.kill() for s in sandboxes]; print(f'Cleaned {len(sandboxes)} sandboxes')"]
    else:
        return jsonify({"error": "unknown action"}), 400
    pid = f"cleanup_{action}_{int(time.time())}"
    _run_background(pid, cmd)
    return jsonify({"proc_id": pid})


# ── API: Process log streaming ──

@app.route("/api/process/<proc_id>/logs")
def api_process_logs(proc_id):
    offset = int(request.args.get("offset", 0))
    with _process_lock:
        buf = _log_buffers.get(proc_id, [])
        status_info = _processes.get(proc_id, {"status": "unknown", "code": None})
    new_lines = buf[offset:]
    return jsonify({
        "lines": new_lines,
        "offset": offset + len(new_lines),
        "status": status_info["status"],
        "code": status_info.get("code"),
    })


@app.route("/api/process/<proc_id>/stop", methods=["POST"])
def api_process_stop(proc_id):
    with _process_lock:
        info = _processes.get(proc_id)
        if info and "popen" in info:
            try:
                info["popen"].terminate()
            except Exception:
                pass
    return jsonify({"ok": True})


# ── Main ──

def main():
    port = int(os.environ.get("OC_PORT", 18080))
    host = os.environ.get("OC_HOST", "127.0.0.1")

    # Try pywebview for native desktop window; fallback to browser
    use_webview = True
    try:
        import webview
    except ImportError:
        use_webview = False

    if use_webview:
        # Start Flask in background thread
        def _run_flask():
            app.run(host=host, port=port, debug=False, use_reloader=False)

        flask_thread = threading.Thread(target=_run_flask, daemon=True)
        flask_thread.start()
        time.sleep(0.8)

        print(f"\n  OpenComputer Desktop 已启动 (原生窗口模式)\n")
        webview.create_window(
            "OpenComputer Desktop",
            f"http://{host}:{port}",
            width=1280,
            height=860,
            min_size=(900, 600),
            resizable=True,
        )
        webview.start()
    else:
        # Fallback: open in browser
        def _open_browser():
            time.sleep(1.5)
            webbrowser.open(f"http://{host}:{port}")

        threading.Thread(target=_open_browser, daemon=True).start()
        print(f"\n  OpenComputer Desktop 已启动: http://{host}:{port}\n")
        app.run(host=host, port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
