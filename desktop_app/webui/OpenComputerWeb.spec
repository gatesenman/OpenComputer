# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for OpenComputer Desktop WebUI edition.
Bundles Flask + templates + static into a single .exe.
"""
import os
import importlib

webui_dir = os.path.dirname(os.path.abspath(SPEC))
desktop_dir = os.path.dirname(webui_dir)
project_root = os.path.dirname(desktop_dir)

# Find webview package path for hooks and data
try:
    import webview as _wv
    _wv_dir = os.path.dirname(_wv.__file__)
    _wv_hooks = os.path.join(_wv_dir, '__pyinstaller')
    _wv_lib = os.path.join(_wv_dir, 'lib')
    _wv_js = os.path.join(_wv_dir, 'js')
except ImportError:
    _wv_hooks = ''
    _wv_lib = ''
    _wv_js = ''

a = Analysis(
    [os.path.join(webui_dir, 'app.py')],
    pathex=[webui_dir],
    binaries=[],
    datas=[
        (os.path.join(webui_dir, 'templates'), 'templates'),
        (os.path.join(webui_dir, 'static'), 'static'),
    ] + ([(_wv_lib, 'webview/lib')] if os.path.isdir(_wv_lib) else [])
      + ([(_wv_js, 'webview/js')] if os.path.isdir(_wv_js) else []),
    hiddenimports=['flask', 'jinja2', 'markupsafe', 'werkzeug',
                   'webview', 'webview.platforms', 'webview.platforms.edgechromium',
                   'webview.platforms.mshtml', 'webview.platforms.winforms',
                   'clr_loader', 'pythonnet', 'bottle', 'proxy_tools'],
    hookspath=[_wv_hooks] if os.path.isdir(_wv_hooks) else [],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'tkinter', 'matplotlib', 'numpy', 'scipy', 'pandas'],
    noarchive=False,
)

pyz = PYZ(a.pure)

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
