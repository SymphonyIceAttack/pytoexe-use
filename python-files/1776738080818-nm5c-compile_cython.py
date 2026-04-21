"""
Cython 编译脚本 - 将 Python 文件编译为 .pyd 二进制文件
适用于 Maya 插件保护
"""
import os
import sys
import shutil
import glob
from distutils.core import setup
from Cython.Build import cythonize
from Cython.Compiler import Options

# Cython 编译选项
Options.annotate = True  # 生成注释 HTML 文件（可选）
Options.docstrings = False  # 移除文档字符串
Options.embed = False  # 不嵌入 Python 主函数

def get_python_version():
    """获取当前 Python 版本字符串"""
    return f"cp{sys.version_info.major}{sys.version_info.minor}"

def compile_to_pyd(py_files, build_dir="build_cython", output_dir="dist_pyd"):
    """
    将 Python 文件编译为 .pyd 文件
    
    Args:
        py_files: 要编译的 .py 文件列表
        build_dir: 临时构建目录
        output_dir: 输出目录
    """
    # 清理旧文件
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"开始编译 {len(py_files)} 个文件...")
    
    # 创建扩展模块列表
    ext_modules = []
    for py_file in py_files:
        if os.path.exists(py_file):
            ext_modules.append(py_file)
            print(f"  添加: {py_file}")
    
    if not ext_modules:
        print("错误: 没有找到要编译的文件!")
        return
    
    # 配置编译
    setup(
        ext_modules=cythonize(
            ext_modules,
            language_level="3",
            compiler_directives={
                'boundscheck': False,  # 关闭边界检查（提高性能）
                'wraparound': False,   # 关闭负索引支持
                'cdivision': True,     # 使用 C 语言除法规则
                'nonecheck': False,    # 关闭 None 检查
            }
        ),
        script_args=['build_ext', '--build-lib', build_dir]
    )
    
    # 复制编译后的 .pyd 文件到输出目录
    pyd_pattern = os.path.join(build_dir, "**", "*.pyd")
    pyd_files = glob.glob(pyd_pattern, recursive=True)
    
    for pyd_file in pyd_files:
        filename = os.path.basename(pyd_file)
        dest = os.path.join(output_dir, filename)
        shutil.copy2(pyd_file, dest)
        print(f"  输出: {dest}")
    
    print(f"\n编译完成! 输出目录: {os.path.abspath(output_dir)}")

def main():
    """主函数"""
    print("=" * 60)
    print("Cython 编译器 - Python 转 PYD")
    print("=" * 60)
    
    # 获取要编译的文件
    if len(sys.argv) > 1:
        files_to_compile = sys.argv[1:]
    else:
        # 默认编译当前目录下所有 .py 文件（排除本脚本）
        files_to_compile = [
            f for f in glob.glob("*.py") 
            if f != os.path.basename(__file__) and not f.startswith("test_")
        ]
    
    if not files_to_compile:
        print("用法: python compile_cython.py <file1.py> [file2.py ...]")
        print("或直接运行（编译当前目录所有 .py 文件）")
        return
    
    compile_to_pyd(files_to_compile)

if __name__ == "__main__":
    main()
