# -*- mode: python ; coding: utf-8 -*-
import os

import uiautomation
from PyInstaller.utils.hooks import collect_all

uia_bin = os.path.join(os.path.dirname(uiautomation.__file__), "bin")

# Recolectar TODO lo relacionado con reportlab y sus códigos de barras (Soluciona error del PDF)
datas_rl, binaries_rl, hiddenimports_rl = collect_all('reportlab')
datas_xhtml2pdf, binaries_xhtml2pdf, hiddenimports_xhtml2pdf = collect_all('xhtml2pdf')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries_rl + binaries_xhtml2pdf,
    datas=[
        ('app/assets', 'app/assets'),
        ('app/templates/informe_rastreador.html', 'app/templates'),
        (os.path.join(uia_bin, 'UIAutomationClient_VC140_X64.dll'), '.'),
        (os.path.join(uia_bin, 'UIAutomationClient_VC140_X86.dll'), '.'),
    ] + datas_rl + datas_xhtml2pdf,
    hiddenimports=[
        # Para el rastreador de URLs (UIAutomation)
        'uiautomation',
        'comtypes',
        'comtypes.client',
        'comtypes.gen',
        'win32gui',
        'win32api',
        'win32con',
        'win32process',
        'win32crypt',
        'psutil',
        'requests',
        'reportlab',
        # PySide6
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtNetwork',
        # --- NUEVOS: Paneles de Administración y Rastreador ---
        'app.ui.dialogs.panel_admin_rastreador',
        'app.ui.dialogs.rastreador_auto',
        'app.ui.dialogs.cambiar_password',
    ] + hiddenimports_rl + hiddenimports_xhtml2pdf,
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