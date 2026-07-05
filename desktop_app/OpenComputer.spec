# -*- mode: python ; coding: utf-8 -*-

import os
block_cipher = None

desktop_dir = os.path.dirname(os.path.abspath(SPEC))

all_pages = [
    'dashboard_page.py', 'setup_page.py', 'settings_page.py',
    'verifier_page.py', 'smoke_page.py', 'taskgen_page.py',
    'tasks_page.py', 'eval_page.py', 'rerun_page.py',
    'results_page.py', 'repair_page.py', 'sandbox_page.py',
    'cleanup_page.py', 'main_window.py', 'worker.py', 'styles.py',
]

a = Analysis(
    [os.path.join(desktop_dir, 'main.py')],
    pathex=[desktop_dir],
    binaries=[],
    datas=[(os.path.join(desktop_dir, 'icon.png'), '.')],
    hiddenimports=[
        'PyQt5', 'PyQt5.QtCore', 'PyQt5.QtWidgets', 'PyQt5.QtGui',
        'dashboard_page', 'setup_page', 'settings_page',
        'verifier_page', 'smoke_page', 'taskgen_page',
        'tasks_page', 'eval_page', 'rerun_page',
        'results_page', 'repair_page', 'sandbox_page',
        'cleanup_page', 'main_window', 'worker', 'styles',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy', 'pandas'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='OpenComputer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(desktop_dir, 'icon.ico'),
)
