import os
import sys
import subprocess
import tempfile
from pathlib import Path
from PIL import Image
from tqdm import tqdm

def get_base_dir():
    return Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent

def find_ffmpeg():
    base = get_base_dir()
    local = base / "ffmpeg.exe" if sys.platform == "win32" else base / "ffmpeg"
    return str(local) if local.exists() else ("ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")

def log(msg): print(f"[LOG] {msg}")

def main():
    FFMPEG = find_ffmpeg()
    try:
        subprocess.run([FFMPEG, "-version"], capture_output=True, check=True)
    except Exception:
        sys.exit("[ERROR] 未检测到 ffmpeg。请将 ffmpeg 放在 EXE 同级目录或加入系统 PATH。")

    print("=== APNG 转换工具 ===")
    src = input("输入文件路径 (图片/GIF/视频): ").strip().strip('"')
    if not os.path.isfile(src):
        sys.exit("[ERROR] 文件不存在或路径无效。")

    base_dir = get_base_dir()
    dst_dir = input(f"输出文件夹 (默认: {base_dir}): ").strip()
    dst_dir = Path(dst_dir) if dst_dir else base_dir
    dst_dir.mkdir(parents=True, exist_ok=True)

    fps = input("输出帧率 FPS (默认: 15): ").strip()
    fps = float(fps) if fps else 15.0

    resize = input("缩放分辨率 宽x高 (留空保持原样): ").strip()
    vf_scale = f",scale={resize}" if resize else ""

    loop = input("循环次数 (0=无限, 默认: 0): ").strip()
    loop = int(loop) if loop else 0

    comp = input("压缩等级 1-9 (默认: 6): ").strip()
    comp = int(comp) if comp else 6

    print("\n--- 配置摘要 ---")
    print(f"源: {src}\n输出: {dst_dir}\nFPS: {fps} | 循环: {'∞' if loop==0 else loop}")
    print(f"尺寸: {resize or '原样'} | 压缩: {comp}")
    if input("确认执行? (y/n): ").strip().lower() != 'y':
        sys.exit("[INFO] 已取消。")

    out_path = dst_dir / f"{Path(src).stem}.apng"

    with tempfile.TemporaryDirectory(prefix="apng_") as tmp:
        tmp_dir = Path(tmp)
        log("提取帧中...")
        cmd = [FFMPEG, "-y", "-i", src, "-pix_fmt", "rgba", "-vf", f"fps={fps}{vf_scale}", str(tmp_dir / "f_%04d.png")]
        
        proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
        for line in proc.stderr:
            if any(k in line for k in ("frame=", "time=", "speed=")):
                print(f"\r[FFMPEG] {line.strip()}", end="", flush=True)
        proc.wait()
        if proc.returncode != 0: sys.exit("[ERROR] ffmpeg 提取失败。")

        frames = sorted(tmp_dir.glob("f_*.png"))
        if not frames: sys.exit("[ERROR] 未提取到帧。")

        log(f"\n共 {len(frames)} 帧，生成 APNG...")
        images = [Image.open(f).convert("RGBA") for f in tqdm(frames, desc="处理", unit="帧")]
        
        delay = max(1, int(1000 / fps))
        if len(images) == 1:
            images[0].save(str(out_path), optimize=True, compress_level=comp)
        else:
            images[0].save(str(out_path), save_all=True, append_images=images[1:],
                          duration=delay, loop=loop, optimize=True, compress_level=comp)
        
        log(f"✅ 完成: {out_path} ({out_path.stat().st_size/1024:.1f} KB)")

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: sys.exit("\n[INFO] 中断。")
    except Exception as e: sys.exit(f"\n[ERROR] {e}")