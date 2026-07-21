import os
import sys
import subprocess

def check_ffprobe():
    """检查 ffprobe 是否可用，不可用则提示安装 FFmpeg 并退出。"""
    try:
        subprocess.run(
            ["ffprobe", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("错误：未找到 ffprobe，请安装 FFmpeg 并确保 ffprobe 在系统 PATH 中。")
        sys.exit(1)

def is_mp4_damaged(filepath, timeout=30):
    """
    使用 ffprobe 检测 MP4 文件是否损坏。
    返回 True 表示损坏，False 表示正常。
    此过程完全静默，不输出任何信息。
    """
    try:
        subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "stream=codec_type",
                "-of", "default=noprint_wrappers=1:nokey=1",
                filepath,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            check=True,
        )
        return False
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return True
    except Exception:
        return True

def print_progress_bar(iteration, total, length=50):
    """打印进度条"""
    percent = 100 * (iteration / float(total))
    filled_len = int(length * iteration // total)
    bar = '█' * filled_len + '-' * (length - filled_len)
    sys.stdout.write(f'\r检测进度: |{bar}| {percent:.1f}% {iteration}/{total}')
    sys.stdout.flush()

def delete_files(file_list):
    """删除列表中的文件，并打印结果。"""
    for path in file_list:
        try:
            os.remove(path)
            print(f"  已删除: {path}")
        except OSError as e:
            print(f"  删除失败: {path}，原因: {e}")

def main():
    # 脚本所在目录作为扫描根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 递归收集所有 .mp4 文件
    mp4_files = []
    for root, dirs, files in os.walk(script_dir):
        for file in files:
            if file.lower().endswith(".mp4"):
                mp4_files.append(os.path.join(root, file))

    if not mp4_files:
        print(f"在目录 '{script_dir}' 及其子目录中未找到任何 .mp4 文件。")
        sys.exit(0)

    # 检查 ffprobe 可用性
    check_ffprobe()

    total = len(mp4_files)
    print(f"找到 {total} 个 MP4 文件，开始检测...")
    damaged_files = []

    # 逐个检测并更新进度条
    for idx, filepath in enumerate(mp4_files, 1):
        if is_mp4_damaged(filepath):
            damaged_files.append(filepath)
        print_progress_bar(idx, total)

    # 完成进度条后换行
    sys.stdout.write('\n')
    sys.stdout.flush()

    # 结果汇总
    if not damaged_files:
        print("所有 MP4 文件均正常，无损坏文件。")
        sys.exit(0)

    print(f"共发现 {len(damaged_files)} 个损坏文件：")
    for path in damaged_files:
        rel = os.path.relpath(path, script_dir)
        print(f"  - {rel}")

    # 第一次确认删除
    choice1 = input("\n是否删除这些损坏文件？(y/n): ").strip().lower()
    if choice1 != 'y':
        print("已取消删除。")
        sys.exit(0)

    # 第二次确认
    choice2 = input("确定要永久删除这些文件吗？此操作不可恢复！(y/n): ").strip().lower()
    if choice2 != 'y':
        print("已取消删除。")
        sys.exit(0)

    # 执行删除
    delete_files(damaged_files)
    print("处理完毕。")

if __name__ == "__main__":
    main()