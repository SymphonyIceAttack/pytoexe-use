import DaVinciResolveScript as dvr_script
import os
import sys
import time
import csv
import tkinter as tk
from tkinter import filedialog

# 初始化 Resolve API
resolve = dvr_script.scriptapp("Resolve")
pm = resolve.GetProjectManager()
project = pm.GetCurrentProject()
timeline = project.GetCurrentTimeline()

if not timeline:
    print("❌ 当前没有打开的时间线。")
    sys.exit()

timeline_name = timeline.GetName()

# 弹窗选择导出路径
root = tk.Tk()
root.withdraw()
output_dir = filedialog.askdirectory(title="请选择导出静帧的保存路径")
if not output_dir:
    print("❌ 未选择保存路径，脚本退出。")
    sys.exit()

# 准备 CSV 文件
csv_path = os.path.join(output_dir, "still_info.csv")
csv_header = ["Timecode", "Frame", "SourceFileName", "SourceFilePath", "StillFileName", "MarkerName", "Timeline"]

with open(csv_path, mode='w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(csv_header)

    markers = timeline.GetMarkers()
    if not markers:
        print("❌ 当前时间线没有任何标记点。")
        sys.exit()

    media_pool = project.GetMediaPool()
    current_clips = timeline.GetItemListInTrack("video", 1)

    def get_clip_at_frame(frame):
        for clip in current_clips:
            if clip.GetStart() <= frame < (clip.GetStart() + clip.GetDuration()):
                return clip
        return None

    for marker_frame_str, marker in markers.items():
        marker_frame = int(marker_frame_str)

        clip = get_clip_at_frame(marker_frame)
        if not clip:
            print(f"⚠️ 找不到帧 {marker_frame} 的片段，跳过。")
            continue

        media = clip.GetMediaPoolItem()
        if not media:
            print(f"⚠️ 无媒体文件，跳过帧 {marker_frame}。")
            continue

        # 获取文件名和路径
        clip_name = os.path.splitext(media.GetName())[0]
        source_path = media.GetClipProperty("File Path") or "N/A"
        timecode = timeline.GetTimecodeForFrame(marker_frame)
        marker_name = marker.get("name", "")

        # 生成静帧文件名
        still_filename = f"{clip_name}_{marker_frame}.jpg"
        export_path = os.path.join(output_dir, still_filename)

        # 定位时间线并导出静帧
        timeline.SetCurrentTimecode(timecode)
        time.sleep(0.5)  # 给 Resolve 一点缓冲时间

        success = timeline.ExportCurrentFrameAsStill(export_path)
        if success:
            print(f"✅ 已导出: {export_path}")
            # 写入 CSV 信息
            writer.writerow([timecode, marker_frame, clip_name, source_path, still_filename, marker_name, timeline_name])
        else:
            print(f"❌ 导出失败: {export_path}")