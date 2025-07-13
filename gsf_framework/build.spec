# build.spec

analysis = Analysis(
    ['gsf\\service.py'],
    pathex=['.'],
    binaries=[],
    datas=[('gsf\\assets', 'gsf\\assets')] + pyside6_datas,
    hiddenimports=['win32timezone', 'pystray._win32', 'PySide6.QtSvg'], # 添加其他可能需要的PySide6模块
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher
)

pyz = PYZ(analysis.pure, analysis.zipped_data, cipher=block_cipher)

service_exe = EXE(
    pyz,
    analysis.scripts,
    name='GSFService',
    console=True,
    icon='gsf\\assets\\icon.ico'
)

coll = COLLECT(
    service_exe,
    analysis.binaries,
    analysis.zipfiles,
    analysis.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GSF_Distribution'
)