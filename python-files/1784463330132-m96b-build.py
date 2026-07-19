"""
PyInstaller 打包脚本
使用方法：
    python build.py
或直接运行：
    pyinstaller desktop_pet.spec
"""
import os
import sys
import subprocess


def build():
    """执行打包"""
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('resources/images', 'resources/images'),
        ('resources/music', 'resources/music'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='桌面宠物',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 不显示控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='桌面宠物',
)
"""
    
    # 写入spec文件
    spec_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'desktop_pet.spec')
    with open(spec_path, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("正在打包，请稍候...")
    print("Spec文件已生成：", spec_path)
    
    # 执行pyinstaller
    result = subprocess.run(
        [sys.executable, '-m', 'PyInstaller', spec_path, '--clean'],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    if result.returncode == 0:
        print("\n✅ 打包完成！")
        print("输出目录：dist/桌面宠物/")
        print("运行：dist/桌面宠物/桌面宠物.exe")
    else:
        print("\n❌ 打包失败，请检查错误信息")


if __name__ == "__main__":
    build()
