
import os
import sys

def delete_files_with_prefix(root_directory, prefix):
    """
    删除指定目录及其子目录中所有以特定前缀开头的文件
    """
    deleted_count = 0

    # 递归遍历目录
    for root, dirs, files in os.walk(root_directory):
        for file in files:
            if file.startswith(prefix):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    print(f"已删除: {file_path}")
                    deleted_count += 1
                except Exception as e:
                    print(f"删除失败 {file_path}: {e}")

    print(f"总共删除了 {deleted_count} 个文件")
    return deleted_count

if __name__ == "__main__":
    # 默认路径为当前目录
    directory = "."
    prefix = ".-"

    # 如果提供了命令行参数，则使用参数
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    if len(sys.argv) > 2:
        prefix = sys.argv[2]

    print(f"正在搜索目录 '{directory}' 中以 '{prefix}' 开头的文件...")
    delete_files_with_prefix(directory, prefix)
