# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

# Recolectar TODO lo relacionado con reportlab y sus códigos de barras (Soluciona error del PDF)
datas_rl, binaries_rl, hiddenimports_rl = collect_all('reportlab')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries_rl,
    datas=[('app/assets', 'app/assets')] + datas_rl,
    hiddenimports=[
        # Para el rastreador de URLs (UIAutomation)
        'uiautomation',
        'comtypes',
        'comtypes.client',
        'win32gui',
        'win32api',
        'win32con',
        'win32process',
        'psutil',
        'requests',
        # PySide6
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtNetwork',
    ] + hiddenimports_rl,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ControlAsistencia',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app/assets/favicon.ico',   
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ControlAsistencia',
)