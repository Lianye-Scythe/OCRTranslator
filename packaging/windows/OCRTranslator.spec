# -*- mode: python ; coding: utf-8 -*-
from __future__ import annotations

import os
from pathlib import Path


spec_dir = Path(globals().get("SPECPATH", ".")).resolve()
project_root = spec_dir.parents[1]
version_file_value = os.environ.get("OCRT_VERSION_FILE")
version_file = Path(version_file_value) if version_file_value else project_root / "build" / "OCRTranslator.version-info.txt"
version_file = version_file.resolve()
if not version_file.exists():
    raise SystemExit(f"Missing Windows version resource file: {version_file}")

icon_file = (project_root / "app" / "assets" / "icons" / "app-icon.ico").resolve()
if not icon_file.exists():
    raise SystemExit(f"Missing application icon file: {icon_file}")


datas = [
    (str(project_root / "app" / "ui" / "styles"), "app/ui/styles"),
    (str(project_root / "app" / "locales"), "app/locales"),
    (str(project_root / "app" / "assets" / "icons"), "app/assets/icons"),
]

excludes = [
    "tkinter",
    "_tkinter",
    "pynput.keyboard._darwin",
    "pynput.mouse._darwin",
    "pynput._util.darwin",
    "pynput.keyboard._xorg",
    "pynput.mouse._xorg",
    "pynput._util.xorg",
    "pynput.keyboard._uinput",
    "pynput._util.uinput",
]


a = Analysis(
    [str(project_root / "launcher.pyw")],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="OCRTranslator",
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
    version=str(version_file),
    icon=str(icon_file),
)
