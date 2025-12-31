# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for PF2 Translation Tools.
Run: pyinstaller build.spec
"""

import sys
from pathlib import Path

block_cipher = None

# Exclude only confirmed unnecessary large libraries
# Keep exclusion list minimal to ensure all dependencies work
EXCLUDES = [
    'matplotlib',
    'scipy',
    'numpy.random._examples',
    'PIL',
    'tkinter.test',
    'test',
    'tests',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include nltk_data if it exists
        ('nltk_data', 'nltk_data'),
    ],
    hiddenimports=[
        'customtkinter',
        'pandas',
        'openpyxl',
        'nltk',
        'chardet',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
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
    name='PF2翻译工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Enable UPX compression
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one
)
