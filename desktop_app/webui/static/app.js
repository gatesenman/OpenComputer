/* OpenComputer Desktop — Frontend SPA logic */

// ── Navigation ──
document.querySelectorAll('.nav-item').forEach(el => {
  el.addEventListener('click', e => {
    e.preventDefault();
    const page = el.dataset.page;
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    el.classList.add('active');
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById('page-' + page).classList.add('active');
    if (pageInit[page]) pageInit[page]();
  });
});

const pageInit = {};
let _initDone = {};

function initOnce(page, fn) {
  pageInit[page] = () => { if (!_initDone[page]) { _initDone[page] = true; fn(); } };
}

// ── Utility ──
function $(sel) { return document.querySelector(sel); }
function $$(sel) { return document.querySelectorAll(sel); }

async function api(path, opts) {
  const r = await fetch('/api/' + path, opts);
  return r.json();
}

async function apiPost(path, data) {
  return api(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data || {}),
  });
}

function logAppend(boxId, text) {
  const box = document.getElementById(boxId);
  if (!box) return;
  box.textContent += text + '\n';
  box.scrollTop = box.scrollHeight;
}

function logClear(boxId) {
  const box = document.getElementById(boxId);
  if (box) box.textContent = '';
}

// ── Process log polling ──
const _pollers = {};
function pollProcess(procId, logBoxId, onDone) {
  let offset = 0;
  if (_pollers[logBoxId]) clearInterval(_pollers[logBoxId]);
  _pollers[logBoxId] = setInterval(async () => {
    const data = await api(`process/${procId}/logs?offset=${offset}`);
    if (data.lines && data.lines.length) {
      data.lines.forEach(l => logAppend(logBoxId, l));
      offset = data.offset;
    }
    if (data.status !== 'running') {
      clearInterval(_pollers[logBoxId]);
      delete _pollers[logBoxId];
      logAppend(logBoxId, `\n--- 结束 (退出码: ${data.code}) ---`);
      if (onDone) onDone(data.code);
    }
  }, 800);
}

function stopProcess(procId) {
  apiPost(`process/${procId}/stop`);
}

// ══════════════════════════════════════════
// Dashboard
// ══════════════════════════════════════════
(async () => {
  const d = await api('dashboard');
  const colors = { tasks: '#0984e3', apps: '#6c5ce7', verifiers: '#00b894', runs: '#fdcb6e' };
  const labels = { tasks: '评估任务', apps: '应用数量', verifiers: '验证器', runs: '评估运行' };
  let html = '';
  for (const k of ['tasks', 'apps', 'verifiers', 'runs']) {
    html += `<div class="stat-card"><div class="stat-val" style="color:${colors[k]}">${d[k]}</div><div class="stat-label">${labels[k]}</div></div>`;
  }
  const envColor = d.env_ok ? '#00b894' : '#e74c3c';
  html += `<div class="stat-card"><div class="stat-val" style="color:${envColor};font-size:22px">${d.env_msg}</div><div class="stat-label">环境配置</div></div>`;
  $('#stat-cards').innerHTML = html;
})();

// ══════════════════════════════════════════
// Setup
// ══════════════════════════════════════════
const SETUP_STEPS = [
  { n: 1, title: '安装 Python 依赖', desc: '安装 requirements.txt 中的所有依赖', btn: '一键安装', action: 'install-deps' },
  { n: 2, title: '创建配置文件 (.env)', desc: '从 .env.example 复制创建 .env 文件', btn: '创建 .env', action: 'create-env' },
  { n: 3, title: '构建 E2B 沙盒模板', desc: '构建包含 33 个应用的 E2B 沙盒模板', btn: '构建模板', action: 'e2b' },
  { n: 4, title: '构建本地 Docker 镜像', desc: '构建本地 Docker 桌面镜像（选择 Docker 后端时使用）', btn: '构建镜像', action: 'docker' },
  { n: 5, title: 'AWS 云部署（可选）', desc: '创建 ECR 仓库、IAM 角色、S3 存储桶等', btn: 'AWS 部署', action: 'aws' },
  { n: 6, title: 'AWS 启动 Worker（可选）', desc: '启动远程 Docker Worker 实例', btn: '启动 Worker', action: 'aws_workers' },
  { n: 7, title: '腾讯云部署（可选）', desc: '创建 CVM、TCR、COS 等基础设施', btn: '腾讯云部署', action: 'tencent' },
  { n: 8, title: '腾讯云启动 Worker（可选）', desc: '启动远程 Docker Worker 实例', btn: '启动 Worker', action: 'tencent_workers' },
  { n: 9, title: '环境验证', desc: '全面检查 Python、依赖包、配置、Docker', btn: '检查环境', action: 'verify' },
];

initOnce('setup', async () => {
  const container = $('#setup-steps');
  const status = await api('setup/status');
  container.innerHTML = SETUP_STEPS.map(s => `
    <div class="setup-step" id="setup-step-${s.n}">
      <div class="step-badge">${s.n}</div>
      <div class="step-info"><h4>${s.title}</h4><p>${s.desc}</p></div>
      <span class="step-status" id="setup-status-${s.n}">待执行</span>
      <button class="btn primary" onclick="Setup.run('${s.action}', ${s.n})">${s.btn}</button>
    </div>
  `).join('');
  // Update status
  if (status.deps) Setup.setStatus(1, '已安装', 'ok');
  else Setup.setStatus(1, '未安装', 'err');
  if (status.env) Setup.setStatus(2, '已创建', 'ok');
  else Setup.setStatus(2, '未创建', 'err');
  if (status.docker) Setup.setStatus(4, 'Docker 可用', 'ok');
  for (const n of [3,5,6,7,8]) Setup.setStatus(n, '可选', '');
  Setup.setStatus(9, '待检查', '');
});

const Setup = {
  setStatus(n, text, type) {
    const el = $(`#setup-status-${n}`);
    if (!el) return;
    el.textContent = text;
    el.className = 'step-status ' + (type === 'ok' ? 'status-ok' : type === 'err' ? 'status-err' : type === 'warn' ? 'status-warn' : '');
  },
  async run(action, n) {
    logClear('setup-log');
    Setup.setStatus(n, '执行中...', 'warn');
    if (action === 'create-env') {
      const r = await apiPost('setup/create-env');
      logAppend('setup-log', r.msg);
      Setup.setStatus(n, r.ok ? '已创建' : '失败', r.ok ? 'ok' : 'err');
      return;
    }
    if (action === 'verify') {
      const r = await apiPost('setup/verify');
      r.checks.forEach(c => logAppend('setup-log', c));
      Setup.setStatus(n, r.all_ok ? '检查完成' : '部分缺失', r.all_ok ? 'ok' : 'warn');
      return;
    }
    if (action === 'install-deps') {
      const r = await apiPost('setup/install-deps');
      pollProcess(r.proc_id, 'setup-log', code => Setup.setStatus(n, code === 0 ? '已安装' : '失败', code === 0 ? 'ok' : 'err'));
      return;
    }
    const r = await apiPost('setup/run-step', { step: action });
    pollProcess(r.proc_id, 'setup-log', code => Setup.setStatus(n, code === 0 ? '已完成' : '失败', code === 0 ? 'ok' : 'err'));
  }
};

// ══════════════════════════════════════════
// Settings
// ══════════════════════════════════════════
const SETTINGS_TABS = {
  api: {
    title: '模型 API 密钥',
    fields: [
      { key: 'E2B_API_KEY', label: 'E2B 密钥', type: 'password' },
      { key: 'DEEPSEEK_API_KEY', label: 'DeepSeek 密钥', type: 'password' },
      { key: 'OPENAI_API_KEY', label: 'OpenAI 密钥', type: 'password' },
      { key: 'ANTHROPIC_API_KEY', label: 'Anthropic 密钥', type: 'password' },
      { key: 'KIMI_API_KEY', label: 'Kimi 密钥', type: 'password' },
      { key: 'google_ai_studio_api_key', label: 'Google AI 密钥', type: 'password' },
      { key: 'DASHSCOPE_API_KEY', label: 'DashScope 密钥', type: 'password' },
      { key: 'AZURE_API_KEY', label: 'Azure 密钥', type: 'password' },
      { key: 'AZURE_ENDPOINT', label: 'Azure 端点', type: 'text', placeholder: 'https://YOUR-RESOURCE.cognitiveservices.azure.com/' },
    ]
  },
  backend: {
    title: '运行后端配置',
    fields: [
      { key: 'ENV_BACKEND', label: '运行后端', type: 'select', options: ['e2b', 'docker', 'remote_docker'] },
      { key: 'REMOTE_DOCKER_HOST', label: 'Remote Docker Host', type: 'text' },
      { key: 'REMOTE_DOCKER_POOL_SIZE', label: 'Pool Size', type: 'number' },
    ]
  },
  docker: {
    title: '本地 Docker 后端参数',
    fields: [
      { key: 'DOCKER_IMAGE', label: 'Docker 镜像', type: 'text', placeholder: 'gui-synth-env-desktop:latest' },
      { key: 'DOCKER_PLATFORM', label: '平台', type: 'text', placeholder: 'linux/amd64' },
      { key: 'DOCKER_SHM_SIZE', label: 'SHM 大小', type: 'text', placeholder: '2g' },
      { key: 'DOCKER_MEMORY_LIMIT', label: '内存限制', type: 'text' },
      { key: 'DOCKER_CPU_LIMIT', label: 'CPU 限制', type: 'text' },
      { key: 'DOCKER_STARTUP_TIMEOUT', label: '就绪超时', type: 'number', placeholder: '120' },
    ]
  },
  eval_params: {
    title: '评估运行参数',
    fields: [
      { key: 'EVAL_MODEL', label: '默认模型', type: 'text', placeholder: 'kimi-k2.6' },
      { key: 'MAX_ITERATIONS', label: '最大步数', type: 'number', placeholder: '100' },
      { key: 'SANDBOX_TIMEOUT', label: '沙盒超时(秒)', type: 'number', placeholder: '3600' },
      { key: 'JUDGE_MODEL', label: '评判模型', type: 'text', placeholder: 'gpt-5.4' },
      { key: 'DATABASE_URL', label: '数据库 URL', type: 'text' },
    ]
  },
  smoke_cfg: {
    title: 'Smoke 测试参数',
    fields: [
      { key: 'SMOKE_MAX_TASKS', label: '最大任务数', type: 'number', placeholder: '20' },
      { key: 'SMOKE_MAX_ROUNDS', label: '最大修复轮数', type: 'number', placeholder: '3' },
    ]
  },
  aws: {
    title: 'AWS Remote Docker 部署配置',
    fields: [
      { key: 'AWS_PROFILE', label: 'AWS Profile', type: 'text' },
      { key: 'AWS_REGION', label: '区域', type: 'text', placeholder: 'us-east-1' },
      { key: 'AWS_NAME_PREFIX', label: '名称前缀', type: 'text' },
      { key: 'AWS_CONTROLLER_CIDR', label: '控制器 CIDR', type: 'text' },
      { key: 'AWS_WORKER_INSTANCE_TYPE', label: '实例类型', type: 'text', placeholder: 'm6i.2xlarge' },
      { key: 'AWS_NUM_WORKERS', label: 'Worker 数', type: 'number', placeholder: '1' },
      { key: 'AWS_CONTAINERS_PER_WORKER', label: '容器/Worker', type: 'number', placeholder: '6' },
      { key: 'AWS_S3_BUCKET', label: 'S3 存储桶', type: 'text' },
    ]
  },
  tencent: {
    title: '腾讯云部署配置',
    fields: [
      { key: 'TENCENT_SECRET_ID', label: 'SecretId', type: 'password' },
      { key: 'TENCENT_SECRET_KEY', label: 'SecretKey', type: 'password' },
      { key: 'TENCENT_REGION', label: '地域', type: 'text', placeholder: 'ap-guangzhou' },
      { key: 'TENCENT_NAME_PREFIX', label: '名称前缀', type: 'text', placeholder: 'opencomputer-dev' },
      { key: 'TENCENT_VPC_ID', label: 'VPC ID', type: 'text' },
      { key: 'TENCENT_SUBNET_ID', label: '子网 ID', type: 'text' },
      { key: 'TENCENT_NUM_WORKERS', label: 'Worker 数', type: 'number', placeholder: '1' },
    ]
  },
  advanced: {
    title: '高级设置',
    fields: [
      { key: 'HTTP_PROXY', label: 'HTTP 代理', type: 'text' },
      { key: 'HTTPS_PROXY', label: 'HTTPS 代理', type: 'text' },
      { key: 'CUSTOM_API_BASE', label: '自定义 API 端点', type: 'text' },
      { key: 'LOG_LEVEL', label: '日志级别', type: 'select', options: ['INFO', 'DEBUG', 'WARNING', 'ERROR'] },
    ]
  }
};

let _settingsData = {};
let _activeSettingsTab = 'api';

const Settings = {
  async init() {
    _settingsData = await api('settings/load');
    Settings.renderTab(_activeSettingsTab);
    $$('#settings-tabs .tab').forEach(t => {
      t.addEventListener('click', () => {
        $$('#settings-tabs .tab').forEach(b => b.classList.remove('active'));
        t.classList.add('active');
        _activeSettingsTab = t.dataset.tab;
        Settings.renderTab(_activeSettingsTab);
      });
    });
  },
  renderTab(tabKey) {
    const tab = SETTINGS_TABS[tabKey];
    if (!tab) return;
    let html = `<h3 class="section-title teal">${tab.title}</h3><div class="form-grid" style="max-width:700px;margin-top:16px;">`;
    for (const f of tab.fields) {
      const val = _settingsData[f.key] || '';
      html += `<label>${f.label}:</label>`;
      if (f.type === 'select') {
        html += `<select data-key="${f.key}">${(f.options||[]).map(o => `<option ${val===o?'selected':''}>${o}</option>`).join('')}</select>`;
      } else {
        html += `<input type="${f.type || 'text'}" data-key="${f.key}" value="${val}" placeholder="${f.placeholder || ''}">`;
      }
    }
    html += '</div>';
    $('#settings-content').innerHTML = html;
  },
  async save() {
    $$('#settings-content [data-key]').forEach(el => {
      _settingsData[el.dataset.key] = el.value;
    });
    await apiPost('settings/save', _settingsData);
    alert('设置已保存到 .env 文件');
  },
  reset() {
    Settings.renderTab(_activeSettingsTab);
  }
};

initOnce('settings', () => Settings.init());

// ══════════════════════════════════════════
// Verifiers
// ══════════════════════════════════════════
let _verifierApps = [];
let _selectedVerifier = '';
let _verifierActiveTab = 'readme';
let _verifierDetail = {};
let _verifierProcId = null;

const Verifiers = {
  async init() {
    _verifierApps = await api('verifiers/list');
    const list = $('#verifier-list');
    list.innerHTML = _verifierApps.map(a =>
      `<div class="list-item" data-app="${a}" onclick="Verifiers.select('${a}')">${a}（文档 | 测试）</div>`
    ).join('');
    if (_verifierApps.length) Verifiers.select(_verifierApps[0]);
    $$('#verifier-tabs .tab').forEach(t => {
      t.addEventListener('click', () => {
        $$('#verifier-tabs .tab').forEach(b => b.classList.remove('active'));
        t.classList.add('active');
        _verifierActiveTab = t.dataset.vtab;
        Verifiers.renderDetail();
      });
    });
  },
  async select(appName) {
    _selectedVerifier = appName;
    $$('#verifier-list .list-item').forEach(el => el.classList.toggle('active', el.dataset.app === appName));
    _verifierDetail = await api(`verifiers/detail/${appName}`);
    Verifiers.renderDetail();
  },
  renderDetail() {
    const box = $('#verifier-content');
    const map = { readme: _verifierDetail.readme, code: _verifierDetail.code, testmd: _verifierDetail.test_md, output: '' };
    box.textContent = map[_verifierActiveTab] || '（无内容）';
  },
  async runTest() {
    if (!_selectedVerifier) return;
    _verifierActiveTab = 'output';
    $$('#verifier-tabs .tab').forEach(b => b.classList.toggle('active', b.dataset.vtab === 'output'));
    const box = $('#verifier-content');
    box.textContent = '运行测试中...\n';
    const r = await apiPost('verifiers/run-test', { app: _selectedVerifier });
    _verifierProcId = r.proc_id;
    let offset = 0;
    const iv = setInterval(async () => {
      const data = await api(`process/${r.proc_id}/logs?offset=${offset}`);
      if (data.lines && data.lines.length) {
        box.textContent += data.lines.join('\n') + '\n';
        offset = data.offset;
        box.scrollTop = box.scrollHeight;
      }
      if (data.status !== 'running') {
        clearInterval(iv);
        box.textContent += `\n--- 测试结束 (退出码: ${data.code}) ---\n`;
      }
    }, 800);
  }
};

initOnce('verifiers', () => Verifiers.init());

// ══════════════════════════════════════════
// Smoke
// ══════════════════════════════════════════
let _smokeProcId = null;

const Smoke = {
  async init() {
    const apps = await api('verifiers/list');
    const sel = $('#smoke-app');
    sel.innerHTML = apps.map(a => `<option>${a}</option>`).join('');
  },
  async start() {
    const app = $('#smoke-app').value;
    if (!app) return;
    logClear('smoke-log');
    const r = await apiPost('smoke/run', {
      app,
      max_tasks: parseInt($('#smoke-max-tasks').value),
      generate_only: $('#smoke-gen-only').checked,
      run_only: $('#smoke-run-only').checked,
    });
    _smokeProcId = r.proc_id;
    pollProcess(r.proc_id, 'smoke-log');
  },
  stop() { if (_smokeProcId) stopProcess(_smokeProcId); },
  async viewReport() {
    const app = $('#smoke-app').value;
    const r = await api(`smoke/report/${app}`);
    const box = $('#smoke-report');
    if (r.report) {
      box.style.display = 'block';
      box.textContent = r.report;
    } else {
      box.style.display = 'block';
      box.textContent = '暂无测试报告。';
    }
  }
};

initOnce('smoke', () => Smoke.init());

// ══════════════════════════════════════════
// Task Generation
// ══════════════════════════════════════════
const TaskGen = {
  async init() {
    const apps = await api('verifiers/list');
    const sel = $('#taskgen-app');
    sel.innerHTML = apps.map(a => `<option>${a}</option>`).join('');
    if (apps.length) TaskGen.load(apps[0]);
    sel.addEventListener('change', () => TaskGen.load(sel.value));
  },
  async load(app) {
    const d = await api(`taskgen/stages/${app}`);
    const tbody = $('#taskgen-table tbody');
    tbody.innerHTML = d.tasks.map(t =>
      `<tr><td>${t.id}</td><td>${t.difficulty||'-'}</td><td>${t.complexity||'-'}</td><td>${t.task}</td></tr>`
    ).join('') || '<tr><td colspan="4" class="placeholder-text">暂无任务数据</td></tr>';
  },
  refresh() { TaskGen.load($('#taskgen-app').value); },
  async viewLessons() {
    const d = await api(`taskgen/stages/${$('#taskgen-app').value}`);
    if (d.lessons) {
      const w = window.open('', '_blank');
      w.document.write(`<pre style="font-family:monospace;padding:20px;white-space:pre-wrap">${d.lessons}</pre>`);
    }
  }
};

initOnce('taskgen', () => TaskGen.init());

// ══════════════════════════════════════════
// Tasks Browser
// ══════════════════════════════════════════
let _allTasks = [];

const Tasks = {
  async init() {
    _allTasks = await api('tasks');
    const apps = [...new Set(_allTasks.map(t => t.app))].sort();
    const sel = $('#tasks-app-filter');
    sel.innerHTML = '<option value="">全部</option>' + apps.map(a => `<option>${a}</option>`).join('');
    sel.addEventListener('change', () => Tasks.filter());
    $('#tasks-search').addEventListener('input', () => Tasks.filter());
    Tasks.render(_allTasks);
  },
  filter() {
    const app = $('#tasks-app-filter').value;
    const search = $('#tasks-search').value.toLowerCase();
    const filtered = _allTasks.filter(t => {
      if (app && t.app !== app) return false;
      if (search && !t.id.toLowerCase().includes(search) && !t.task.toLowerCase().includes(search)) return false;
      return true;
    });
    Tasks.render(filtered);
  },
  render(tasks) {
    $('#tasks-count').textContent = `共 ${tasks.length} 个任务`;
    const tbody = $('#tasks-table tbody');
    tbody.innerHTML = tasks.map(t =>
      `<tr onclick="Tasks.showDetail('${t.id}')"><td>${t.id}</td><td>${t.app}</td><td>${t.difficulty||'-'}</td><td>${t.complexity||'-'}</td></tr>`
    ).join('');
  },
  showDetail(id) {
    const t = _allTasks.find(x => x.id === id);
    if (!t) return;
    $$('#tasks-table tbody tr').forEach(tr => tr.classList.toggle('selected', tr.cells[0].textContent === id));
    let html = `<h3 style="color:#00b894;margin-bottom:8px">${t.id}</h3>`;
    html += `<p><b>应用:</b> ${t.app} &nbsp; <b>难度:</b> ${t.difficulty||'-'} &nbsp; <b>复杂度:</b> ${t.complexity||'-'}</p>`;
    html += `<h4 style="margin-top:14px;margin-bottom:6px">任务描述</h4><p>${t.task}</p>`;
    if (t.verification && t.verification.length) {
      html += `<h4 style="margin-top:14px;margin-bottom:6px">验证命令</h4>`;
      t.verification.forEach(v => {
        html += `<div style="background:#f6f8fc;padding:8px 12px;border-radius:6px;margin-bottom:4px;font-size:12px;font-family:monospace">${v.command} → ${v.key}=${JSON.stringify(v.expected)}</div>`;
      });
    }
    $('#task-detail').innerHTML = html;
  }
};

initOnce('tasks', () => Tasks.init());

// ══════════════════════════════════════════
// Eval
// ══════════════════════════════════════════
let _evalProcId = null;

const Eval = {
  async init() {
    const cfg = await api('eval/config');
    const appSel = $('#eval-app');
    cfg.apps.forEach(a => appSel.add(new Option(a)));
    const modelSel = $('#eval-model');
    cfg.models.forEach(m => modelSel.add(new Option(m)));
    appSel.addEventListener('change', async () => {
      const app = appSel.value;
      const taskSel = $('#eval-task');
      taskSel.innerHTML = '<option>全部任务</option>';
      if (app && app !== '全部应用') {
        const tasks = await api(`tasks?app=${app}`);
        tasks.forEach(t => taskSel.add(new Option(t.id)));
      }
    });
  },
  async start() {
    logClear('eval-log');
    const r = await apiPost('eval/run', {
      app: $('#eval-app').value,
      task: $('#eval-task').value,
      model: $('#eval-model').value,
      backend: $('#eval-backend').value,
      max_iter: parseInt($('#eval-max-iter').value),
      timeout: parseInt($('#eval-timeout').value),
      parallel: parseInt($('#eval-parallel').value),
      keep_alive: $('#eval-keep-alive').checked,
    });
    _evalProcId = r.proc_id;
    pollProcess(r.proc_id, 'eval-log');
  },
  stop() { if (_evalProcId) stopProcess(_evalProcId); },
  clearLog() { logClear('eval-log'); }
};

initOnce('eval', () => Eval.init());

// ══════════════════════════════════════════
// Rerun
// ══════════════════════════════════════════
let _rerunProcId = null;

const Rerun = {
  async init() {
    const runs = await api('rerun/runs');
    const sel = $('#rerun-source');
    sel.innerHTML = runs.length ? runs.map(r => `<option>${r}</option>`).join('') : '<option>暂无评估记录</option>';
    const cfg = await api('eval/config');
    const modelSel = $('#rerun-model');
    cfg.models.forEach(m => modelSel.add(new Option(m)));
  },
  async start() {
    logClear('rerun-log');
    const r = await apiPost('rerun/run', {
      resume: $('#rerun-source').value,
      model: $('#rerun-model').value,
      max_iter: parseInt($('#rerun-max-iter').value),
    });
    _rerunProcId = r.proc_id;
    pollProcess(r.proc_id, 'rerun-log');
  },
  stop() { if (_rerunProcId) stopProcess(_rerunProcId); }
};

initOnce('rerun', () => Rerun.init());

// ══════════════════════════════════════════
// Results
// ══════════════════════════════════════════
let _resultsData = [];

const Results = {
  async init() {
    const runs = await api('results/runs');
    const sel = $('#results-run');
    sel.innerHTML = runs.length ? runs.map(r => `<option>${r}</option>`).join('') : '<option>暂无评估记录</option>';
  },
  async load() {
    const run = $('#results-run').value;
    if (!run || run === '暂无评估记录') return;
    _resultsData = await api(`results/detail/${run}`);
    const tbody = $('#results-table tbody');
    tbody.innerHTML = _resultsData.map(r =>
      `<tr onclick="Results.showDetail('${r.id}')"><td>${r.id}</td><td>${r.app}</td><td>${r.model}</td><td>${r.score!=null?r.score:'-'}</td><td>${r.steps||'-'}</td><td>${r.status}</td></tr>`
    ).join('') || '<tr><td colspan="6" class="placeholder-text">暂无结果数据</td></tr>';
  },
  showDetail(id) {
    const r = _resultsData.find(x => x.id === id);
    if (!r) return;
    $('#result-detail').innerHTML = `<h3 style="color:#00b894">${r.id}</h3><pre style="font-size:12px;white-space:pre-wrap">${JSON.stringify(r, null, 2)}</pre>`;
  },
  exportCSV() {
    if (!_resultsData.length) return;
    let csv = 'ID,App,Model,Score,Steps,Status\n';
    _resultsData.forEach(r => csv += `${r.id},${r.app},${r.model},${r.score},${r.steps},${r.status}\n`);
    const blob = new Blob([csv], { type: 'text/csv' });
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'results.csv'; a.click();
  },
  exportJSON() {
    if (!_resultsData.length) return;
    const blob = new Blob([JSON.stringify(_resultsData, null, 2)], { type: 'application/json' });
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'results.json'; a.click();
  }
};

initOnce('results', () => Results.init());

// ══════════════════════════════════════════
// Repair
// ══════════════════════════════════════════
let _repairProcId = null;

const Repair = {
  async init() {
    const apps = await api('verifiers/list');
    const sel = $('#repair-app');
    sel.innerHTML = apps.map(a => `<option>${a}</option>`).join('');
    sel.addEventListener('change', () => Repair.loadTasks());
    if (apps.length) Repair.loadTasks();
    Repair.loadHistory();
  },
  async loadTasks() {
    const app = $('#repair-app').value;
    const tasks = await api(`tasks?app=${app}`);
    const sel = $('#repair-task');
    sel.innerHTML = tasks.map(t => `<option>${t.id}</option>`).join('');
  },
  async loadHistory() {
    const runs = await api('repair/history');
    const box = $('#repair-history');
    box.innerHTML = runs.length ? runs.map(r =>
      `<div class="list-item">${r.name} ${r.has_solved ? '✓' : ''}</div>`
    ).join('') : '<p class="placeholder-text" style="padding:12px">暂无修复记录</p>';
  },
  async start() {
    logClear('repair-log');
    const r = await apiPost('repair/run', {
      app: $('#repair-app').value,
      task: $('#repair-task').value,
      max_rounds: parseInt($('#repair-max-rounds').value),
    });
    _repairProcId = r.proc_id;
    pollProcess(r.proc_id, 'repair-log', () => Repair.loadHistory());
  },
  stop() { if (_repairProcId) stopProcess(_repairProcId); }
};

initOnce('repair', () => Repair.init());

// ══════════════════════════════════════════
// Sandbox
// ══════════════════════════════════════════
let _sandboxProcId = null;

const Sandbox = {
  async init() {
    const apps = await api('verifiers/list');
    const sel = $('#sandbox-app');
    sel.innerHTML = '<option value="">(不指定应用)</option>' + apps.map(a => `<option>${a}</option>`).join('');
  },
  async launch() {
    logClear('sandbox-log');
    const r = await apiPost('sandbox/launch', {
      app: $('#sandbox-app').value,
      backend: $('#sandbox-backend').value,
      timeout: parseInt($('#sandbox-timeout').value),
    });
    _sandboxProcId = r.proc_id;
    pollProcess(r.proc_id, 'sandbox-log');
  },
  stop() { if (_sandboxProcId) stopProcess(_sandboxProcId); }
};

initOnce('sandbox', () => Sandbox.init());

// ══════════════════════════════════════════
// Cleanup
// ══════════════════════════════════════════
const Cleanup = {
  async run(action) {
    logClear('cleanup-log');
    const r = await apiPost('cleanup/run', {
      action,
      force: action.includes('docker') ? $('#cleanup-docker-force').checked : $('#cleanup-e2b-force').checked,
    });
    pollProcess(r.proc_id, 'cleanup-log');
  }
};
