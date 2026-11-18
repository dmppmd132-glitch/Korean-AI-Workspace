# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

project = Path(SPECPATH).parent
src = project / 'src'

hiddenimports = collect_submodules('korean_ai_workspace')

a = Analysis(
    [str(src / 'korean_ai_workspace' / 'app.py')],
    pathex=[str(src)],
    binaries=[], datas=[], hiddenimports=hiddenimports,
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='KoreanAI', debug=False, bootloader_ignore_signals=False, strip=False, upx=True, console=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=True, name='KoreanAI')
