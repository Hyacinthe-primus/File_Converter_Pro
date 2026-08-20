# -*- mode: python ; coding: utf-8 -*-
# pyright: reportUndefinedVariable=false

block_cipher = None

a = Analysis(
    ['../src/quick_check.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PyQt5', 'PyQt6', 'PySide2', 'PySide6',

        'torch', 'torchvision', 'tensorflow',
        'numpy', 'pandas', 'scipy', 'sklearn',
        'matplotlib', 'PIL', 'cv2', 'easyocr',

        'requests', 'urllib3', 'http', 'email',
        'ftplib', 'imaplib', 'smtplib', 'poplib',

        'cryptography', 'ssl', '_ssl',

        'xml', 'xmlrpc', 'pydoc', 'doctest',
        'unittest', 'distutils', 'setuptools',
        'multiprocessing', 'concurrent',
        'asyncio', 'zipimport',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    target_arch='x86_64',
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Quick Check',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[
        'vcruntime140.dll',
        'python3.dll',
        'python313.dll',
    ],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon='../src/Assets/icon.ico',
)
