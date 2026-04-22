# -*- coding: utf-8 -*-
#
# Short Video Deconstruction Software (精简卡点版 - 剪映级字幕样式重构版)
# Dependencies: numpy, librosa
# External Binaries: ffmpeg.exe, ffprobe.exe
#

import os
import sys
import traceback
import re
import shutil
import numpy as np

# ==================== 全局防崩溃机制 ====================
def write_crash_log():
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "崩溃日志_crash_log.txt")
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("=== 致命错误日志 ===\n")
        f.write(traceback.format_exc())
    print(f"\n[崩溃] 错误日志已导出至: {log_file}")

# 自动获取系统常用中文字体库
def get_system_fonts():
    font_dir = 'C:/Windows/Fonts'
    fonts = {"默认(系统黑体)": ""}
    standard_fonts = {
        "微软雅黑": "msyh.ttc",
        "黑体": "simhei.ttf",
        "宋体": "simsun.ttc",
        "楷体": "simkai.ttf",
        "幼圆": "SIMYOU.TTF",
        "方正粗黑": "FZTBH.TTF"
    }
    # 查找默认字体
    for p in ['simhei.ttf', 'msyh.ttc', 'simsun.ttc']:
        full_p = os.path.join(font_dir, p)
        if os.path.exists(full_p): 
            fonts["默认(系统黑体)"] = full_p
            break
            
    # 查找可选字体
    for name, file in standard_fonts.items():
        full_p = os.path.join(font_dir, file)
        if os.path.exists(full_p):
            fonts[name] = full_p
    return fonts

SYS_FONTS = get_system_fonts()

try:
    import random
    import subprocess
    import tempfile
    import threading
    import concurrent.futures
    from datetime import datetime, timedelta
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, scrolledtext

    # --- 依赖项检查与导入 ---
    missing_packages = []
    try:
        import librosa
    except ImportError:
        missing_packages.append("librosa")

    if missing_packages:
        error_msg = f"关键Python库缺失, 程序无法运行:\n\n" + "\n".join(missing_packages) + \
                    f"\n\n请在命令行中运行以下命令来安装它们:\n" \
                    f"pip install librosa numpy"
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("依赖缺失", error_msg)
        sys.exit(1)

    # ==================== 寻址与底层函数 ====================
    def get_executable_path(exe_name):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        exe_path = os.path.join(base_path, exe_name)
        if sys.platform == "win32" and not exe_path.endswith('.exe'):
             exe_path += '.exe'
        return exe_path

    FFMPEG_CMD_path = get_executable_path('ffmpeg')
    FFPROBE_CMD_path = get_executable_path('ffprobe')

    _ffmpeg_dir = os.path.dirname(FFMPEG_CMD_path)
    if _ffmpeg_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = _ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

    def check_dependencies():
        deps = {
            "FFMPEG (视频处理核心)": FFMPEG_CMD_path,
            "FFPROBE (视频分析核心)": FFPROBE_CMD_path,
        }
        missing = []
        for name, path in deps.items():
            try:
                if not os.path.exists(path):
                    raise FileNotFoundError(f"未找到文件")
                startupinfo = None
                if sys.platform == "win32":
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                subprocess.run([path, '-version'], capture_output=True, check=True, startupinfo=startupinfo)
            except Exception as e:
                missing.append(name)
        return missing

    def run_subprocess_hidden(cmd, **kwargs):
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            kwargs['startupinfo'] = startupinfo
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        return subprocess.run(cmd, **kwargs)

    def get_video_files(folder_path, extensions):
        return [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(extensions)]

    def get_media_duration(media_path):
        if not media_path or not os.path.exists(media_path): return 0.0
        cmd = [FFPROBE_CMD_path, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', media_path]
        try: return float(run_subprocess_hidden(cmd, capture_output=True, text=True, encoding='utf-8').stdout.strip())
        except: return 0.0

    def get_media_framerate(media_path):
        cmd = [FFPROBE_CMD_path, '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate', '-of', 'default=noprint_wrappers=1:nokey=1', media_path]
        try:
            output = run_subprocess_hidden(cmd, capture_output=True, text=True, encoding='utf-8').stdout.strip()
            num, den = map(int, output.split('/'))
            return num / den
        except: return 0.0

    _black_intervals_cache = {}
    def get_black_intervals(video_path):
        if video_path in _black_intervals_cache: return _black_intervals_cache[video_path]
        try:
            cmd = [FFMPEG_CMD_path, '-i', video_path, '-vf', "blackdetect=d=1:pix_th=0.02", '-an', '-f', 'null', '-']
            output = run_subprocess_hidden(cmd, capture_output=True, text=True, encoding='utf-8', stderr=subprocess.PIPE).stderr
            intervals = []
            for l in output.split('\n'):
                if 'black_start' in l:
                    try: intervals.append((float(re.search(r'black_start:(\d+\.?\d*)', l).group(1)), float(re.search(r'black_end:(\d+\.?\d*)', l).group(1))))
                    except: pass
            _black_intervals_cache[video_path] = intervals
            return intervals
        except: 
            _black_intervals_cache[video_path] = []
            return []

    # ==================== 字幕解析 ====================
    def srt_time_to_seconds(time_str):
        try:
            h, m, s_ms = time_str.split(':')
            s, ms = s_ms.split(',')
            return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
        except: return 0.0

    def parse_srt_file(file_path, log_callback):
        log_callback(f"📖 解析 SRT 字幕文件: {os.path.basename(file_path)}")
        subtitles = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            blocks = content.strip().split('\n\n')
            for block in blocks:
                lines = block.split('\n')
                if len(lines) >= 3:
                    time_line = lines[1]
                    match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', time_line)
                    if match:
                        start_time = srt_time_to_seconds(match.group(1))
                        end_time = srt_time_to_seconds(match.group(2))
                        text = ' '.join(lines[2:]).strip()
                        if text:
                            subtitles.append({'start': start_time, 'end': end_time, 'text': text})
            log_callback(f"  ✅ SRT 解析完成，共 {len(subtitles)} 句。")
            return subtitles
        except Exception as e:
            log_callback(f"  ❌ SRT 文件解析失败: {e}")
            return []

    def parse_txt_file(file_path, total_duration, log_callback):
        log_callback(f"📝 解析 TXT 文本文件: {os.path.basename(file_path)}")
        subtitles = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            texts = [t.strip() for t in content.replace('，', ',').split(',') if t.strip()]
            if not texts:
                log_callback("  ⚠️ TXT 文件为空或无内容。")
                return []
            time_per_text = total_duration / len(texts)
            for i, text in enumerate(texts):
                start_time = i * time_per_text
                end_time = min((i + 1) * time_per_text, total_duration)
                subtitles.append({'start': start_time, 'end': end_time, 'text': text})
            log_callback(f"  ✅ TXT 解析完成并均分时间轴，共 {len(subtitles)} 句。")
            return subtitles
        except Exception as e:
            log_callback(f"  ❌ TXT 文件解析失败: {e}")
            return []

    # ==================== 多素材智能卡点混剪引擎 ====================
    def get_audio_beats_rhythmic(bgm_path, min_clip_len, log_callback):
        log_callback("🎵 分析音频物理鼓点 (Rhythmic)...")
        try:
            import librosa
            y, sr = librosa.load(bgm_path, sr=22050)
            _, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
            beat_times = librosa.frames_to_time(beat_frames, sr=sr)
            intervals = np.diff(beat_times, prepend=0)
            duration = librosa.get_duration(y=y, sr=sr)
            if duration > beat_times[-1]: intervals = np.append(intervals, duration - beat_times[-1])
            merged, cur = [], 0
            for i in intervals:
                cur += i
                if cur >= min_clip_len: 
                    merged.append(cur)
                    cur = 0
            if cur > 0:
                if merged: merged[-1] += cur
                else: merged.append(cur)
            log_callback(f"🎵 分析完成！鼓点片段数: {len(merged)}")
            return merged
        except Exception as e:
            log_callback(f"❌ 鼓点分析失败: {e}")
            return None

    def get_audio_beats_precise(bgm_path, min_clip_duration, log_callback):
        log_callback("💥 精准分析音频瞬态起搏点 (Precise Onset)...")
        try:
            import librosa
            y, sr = librosa.load(bgm_path)
            onset_times = librosa.onset.onset_detect(y=y, sr=sr, units='time', backtrack=True)
            if len(onset_times) == 0: return None
            p_times = [0.0]
            for t in onset_times:
                if t - p_times[-1] >= min_clip_duration: p_times.append(t)
            duration = librosa.get_duration(y=y, sr=sr)
            if duration - p_times[-1] < min_clip_duration and len(p_times) > 1: p_times[-1] = duration
            else: p_times.append(duration)
            log_callback(f"💥 分析完成！捕获 {len(p_times) - 1} 个精准镜头。")
            return p_times
        except Exception as e: 
            log_callback(f"❌ 精准踩点分析失败: {e}")
            return None

    def create_clip_list(video_files, temp_dir, config, log_callback, target_duration=None, max_duration=0):
        tasks = []
        shuffled_videos = video_files.copy()
        random.shuffle(shuffled_videos)
        
        beat_intervals = config.get('beat_intervals')
        beat_timestamps = config.get('beat_timestamps')
        use_beats = config.get('sync_beats') and (bool(beat_intervals) or bool(beat_timestamps))
        limit_duration = target_duration or (max_duration if max_duration > 0 else None)
        cycle_videos = (limit_duration is not None) or use_beats
        
        try: target_w, target_h = map(int, config['target_resolution'].split('x'))
        except: target_w, target_h = 2560, 1440
        target_fps = int(config['target_fps'])

        if config.get('avoid_black_screen'): 
            log_callback("⬛ 预扫描素材黑场...")
            for v in shuffled_videos: get_black_intervals(v)
            log_callback("⬛ 黑场扫描完毕！")

        vid_idx, beat_idx, loop_counter = 0, 0, 0
        total_videos = len(shuffled_videos)
        current_total_duration = 0.0
        consecutive_fails = 0

        while True:
            if consecutive_fails > max(50, total_videos * 5):
                log_callback("⚠ 素材因过短或黑场过多，片段收集提前结束。")
                break

            if use_beats:
                if beat_timestamps and beat_idx >= len(beat_timestamps) - 1: break
                elif beat_intervals and beat_idx >= len(beat_intervals): break
            else:
                if limit_duration and current_total_duration >= limit_duration: break
                if not cycle_videos and loop_counter >= total_videos: break

            if vid_idx >= total_videos:
                if cycle_videos: 
                    vid_idx = 0
                    random.shuffle(shuffled_videos)
                else: break

            video_file = shuffled_videos[vid_idx]
            vid_idx += 1
            loop_counter += 1

            duration = get_media_duration(video_file)
            if duration <= 1.5: 
                consecutive_fails += 1
                continue
            
            # --- 时长计算模块 ---
            if use_beats and beat_timestamps: target_clip_dur = beat_timestamps[beat_idx+1] - beat_timestamps[beat_idx]
            elif use_beats and beat_intervals: target_clip_dur = beat_intervals[beat_idx]
            else: target_clip_dur = config['clip_duration']
            
            # 【关键修改】如果开启转场，需要预留出相撞重叠的额外时间，保证拼接后不损失整体时长
            transition_pad = config.get('transition_duration', 0.2) if config.get('enable_transitions', False) else 0.0
            extract_target_dur = target_clip_dur + transition_pad
            
            speed_factor = round(random.uniform(0.95, 1.05), 3) if config['dedup_speed'] else 1.0
            actual_input_duration = extract_target_dur * speed_factor
            
            if duration < actual_input_duration: 
                actual_input_duration = duration
                extract_target_dur = actual_input_duration / speed_factor
                # 反向更新此片段对主轴时长的有效贡献
                target_clip_dur = max(0.1, extract_target_dur - transition_pad)
            
            start_time = -1
            for _ in range(15):
                s = random.uniform(0, duration - actual_input_duration)
                if config.get('avoid_black_screen'):
                    has_black = False
                    for bs, be in get_black_intervals(video_file):
                        if max(s, bs) < min(s + actual_input_duration, be):
                            has_black = True
                            break
                    if not has_black: 
                        start_time = s
                        break
                else:
                    start_time = s
                    break
            
            if start_time == -1: 
                consecutive_fails += 1
                continue

            consecutive_fails = 0

            # --- 滤镜组建 ---
            base_filters = []
            if config.get('avoid_subs'): base_filters.append("crop=iw:ih*0.88:0:0")
            if config['dedup_zoom']: 
                zoom = round(random.uniform(0.95, 0.98), 3)
                base_filters.append(f"crop=iw*{zoom}:ih*{zoom}")
            
            if config['dedup_color']: 
                b = round(random.uniform(-0.03, 0.03), 3)
                c = round(random.uniform(0.97, 1.03), 3)
                s_val = round(random.uniform(0.97, 1.05), 3)
                base_filters.append(f"eq=brightness={b}:contrast={c}:saturation={s_val}")
                
            if config['dedup_flip'] and random.random() < 0.5: base_filters.append("hflip")
            
            post_filters = []
            if config.get('interpolate_120'):
                source_fps = get_media_framerate(video_file)
                if 0 < source_fps < 119:
                    log_callback(f"🚀 AI平滑补帧: {os.path.basename(video_file)} -> 120fps")
                    post_filters.append("framerate=fps=120:interp_start=0:interp_end=255:scene=100")
                else: 
                    post_filters.append(f"fps={target_fps}")
            else: 
                post_filters.append(f"fps={target_fps}")

            if config['dedup_speed'] and speed_factor != 1.0: post_filters.append(f"setpts={1/speed_factor:.4f}*PTS")
            if config.get('film_grain'): post_filters.append("noise=alls=10:allf=t+u")
            if config.get('vignette_effect'): post_filters.append("vignette=angle=PI/5")
            if config.get('sharpen_edge'): post_filters.append("unsharp=5:5:1.0:5:5:0.0")
            post_filters.append("format=yuv420p")

            is_complex = False
            full_vf_str = ""

            if config.get('pip_mode'):
                main_w = int(target_w * 0.9)
                fc = []
                base_str = ",".join(base_filters)
                
                if base_str: fc.append(f"[0:v]{base_str}[base_out];[base_out]split[v_main][v_bg]")
                else: fc.append("[0:v]split[v_main][v_bg]")
                
                fc.append(f"[v_main]scale={main_w}:-2[main]")
                fc.append(f"[v_bg]scale={target_w}:{target_h},gblur=sigma=20[bg]")
                fc.append(f"[bg][main]overlay=(W-w)/2:(H-h)/2[pip_out]")
                
                post_str = ",".join(post_filters)
                if post_str: fc.append(f"[pip_out]{post_str}[final]")
                else: fc.append("[pip_out]copy[final]")
                
                full_vf_str = ";".join(fc)
                is_complex = True
            else:
                framing = []
                if config.get('force_fullscreen', False): 
                    framing.extend([f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase", f"crop={target_w}:{target_h}"])
                else: 
                    framing.extend([f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease", f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:black"])
                
                all_filters = base_filters + framing + post_filters
                full_vf_str = ",".join(all_filters)
                is_complex = False

            # 注意这里提取的时长使用的是预留加长后的 actual_input_duration
            tasks.append({'index': len(tasks), 'file': video_file, 'start': start_time, 'duration': actual_input_duration, 'vf': full_vf_str, 'is_complex': is_complex})
            
            current_total_duration += target_clip_dur
            if use_beats: beat_idx += 1

        clip_files = [None] * len(tasks)
        
        if config.get('interpolate_120'): max_workers = min(os.cpu_count() or 2, 2)
        else: max_workers = min(os.cpu_count() or 4, 8)
        
        def process_task(task):
            clip_file = os.path.join(temp_dir, f"clip_{task['index']:04d}.ts")
            if task['is_complex']:
                cmd = [FFMPEG_CMD_path, '-hwaccel', 'auto', '-ss', str(task['start']), '-t', str(task['duration']), '-i', task['file'], '-an', '-filter_complex', task['vf'], '-map', '[final]', '-c:v', config['video_codec'], '-preset', 'faster', '-crf', str(config['video_crf']), '-y', clip_file]
            else:
                cmd = [FFMPEG_CMD_path, '-hwaccel', 'auto', '-ss', str(task['start']), '-t', str(task['duration']), '-i', task['file'], '-an', '-vf', task['vf'], '-c:v', config['video_codec'], '-preset', 'faster', '-crf', str(config['video_crf']), '-y', clip_file]
            
            try: run_subprocess_hidden(cmd, capture_output=True, check=True)
            except subprocess.CalledProcessError as e:
                err_msg = e.stderr.decode('utf-8', 'ignore') if e.stderr else str(e)
                raise RuntimeError(f"FFMPEG 内部报错信息为:\n{err_msg}")
            
            return task['index'], clip_file
        
        log_callback(f"  🚀 多线程并发提取 {len(tasks)} 个片段...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures_map = {executor.submit(process_task, task): task for task in tasks}
            for future in concurrent.futures.as_completed(futures_map):
                try:
                    idx, clip_file = future.result()
                    clip_files[idx] = clip_file
                except Exception as exc:
                    log_callback(f'\n❌ 片段 {futures_map[future]["index"]} 生成失败:\n{exc}')
        
        return [c for c in clip_files if c]

    def merge_clips(clip_files, output_file, config, log_callback):
        if not clip_files: return None
        if len(clip_files) == 1:
            shutil.copy(clip_files[0], output_file)
            return output_file
        
        use_transitions = config.get('enable_transitions', False)
        transition_duration = config.get('transition_duration', 0.2)
        
        if not use_transitions:
            log_callback("🔗 执行无缝拼接...")
            concat_list_path = os.path.join(os.path.dirname(output_file), "concat_list.txt")
            with open(concat_list_path, 'w', encoding='utf-8') as f:
                for clip in clip_files:
                    f.write(f"file '{os.path.basename(clip)}'\n")
            
            cmd = [FFMPEG_CMD_path, '-f', 'concat', '-safe', '0', '-i', concat_list_path, '-c', 'copy', '-y', output_file]
            run_subprocess_hidden(cmd, cwd=os.path.dirname(clip_files[0]), capture_output=True, check=True)
            return output_file
        else:
            log_callback(f"🌊 执行无损时长丝滑转场 (过渡: {transition_duration}s)...")
            cmd = [FFMPEG_CMD_path]
            for clip in clip_files: cmd.extend(['-i', clip])
            
            filter_complex = []
            last_stream = "[0:v]"
            current_offset = 0.0
            
            for i in range(1, len(clip_files)):
                output_stream = f"[v{i}]" if i < len(clip_files) - 1 else "[vout]"
                prev_dur = get_media_duration(clip_files[i-1])
                # 由于提取时已经为转场预留了时间，这里的相减刚好让下一个素材严丝合缝对在主卡点上！
                current_offset += prev_dur - transition_duration
                
                filter_complex.append(f"{last_stream}[{i}:v]xfade=transition=fade:duration={transition_duration}:offset={current_offset:.3f}{output_stream}")
                last_stream = output_stream
                
            cmd.extend(['-filter_complex', ";".join(filter_complex), '-map', '[vout]', '-c:v', config['video_codec'], '-preset', config['video_preset'], '-crf', str(config['video_crf']), '-y', output_file])
            run_subprocess_hidden(cmd, capture_output=True, check=True)
            return output_file

    def apply_final_render_with_text(merged_video, bgm_file, output_file, config, log_callback, temp_dir):
        log_callback("\n⚙️ 开始渲染最终成品...")
        total_duration = get_media_duration(merged_video)
        bgm_duration = get_media_duration(bgm_file) if (bgm_file and os.path.exists(bgm_file)) else 0
        target_dur = min(total_duration, bgm_duration) if (config['match_bgm'] and bgm_duration > 0) else total_duration
        
        cmd = [FFMPEG_CMD_path, '-i', merged_video]
        if bgm_duration > 0: cmd.extend(['-i', bgm_file])
        
        global_vf = []
        try: target_w, target_h = map(int, config['target_resolution'].split('x'))
        except: target_w, target_h = 2560, 1440
        
        if config['enable_letterbox']: 
            p_top = config['letterbox_top']
            p_bottom = config['letterbox_bottom']
            ch = target_h - p_top - p_bottom
            global_vf.extend([f"scale={target_w}:-1", f"crop={target_w}:{ch if ch>0 else target_h//2}", f"pad={target_w}:{target_h}:0:{p_top}:black"])
            
        if config.get('lut_enable') and config.get('lut_path') and os.path.exists(config['lut_path']): 
            safe_lut = config['lut_path'].replace('\\', '/').replace(':', '\\:')
            global_vf.append(f"lut3d=file='{safe_lut}'")

        def add_subtitle_filters(subtitle_list, cfg, temp_dir, track_name):
            filters = []
            if not subtitle_list: return filters
            log_callback(f"✒️ 挂载 {track_name} 字幕...")
            
            font_path = SYS_FONTS.get(cfg.get('font', '默认(系统黑体)'), '')
            if not font_path or not os.path.exists(font_path):
                log_callback(f"  ⚠️ {track_name} 找不到字体文件，跳过渲染。")
                return filters
            
            sf = font_path.replace('\\', '/').replace(':', '\\:')
            ts = int(cfg.get('size', 75))
            
            # 颜色解析
            color_map = {
                "纯白": "white", "亮黄": "#FFD700", "荧光绿": "#00FF00", 
                "大红": "red", "纯黑": "black", "粉红": "#FF69B4", "天蓝": "#00BFFF"
            }
            base_color = color_map.get(cfg.get('color', '纯白'), 'white')
            
            # 样式引擎构建 (剪映级预设)
            style_type = cfg.get('style', '基础无样式')
            style_params = f"fontcolor={base_color}:"
            
            if style_type == "经典描边 (经典)":
                style_params += "borderw=4:bordercolor=black:"
            elif style_type == "柔和阴影 (流行)":
                style_params += "shadowx=3:shadowy=3:shadowcolor=black@0.7:"
            elif style_type == "半透黑底 (科普)":
                style_params += "box=1:boxcolor=black@0.5:boxborderw=10:"
            elif style_type == "综艺花字 (浮夸)":
                # 强行覆盖基础色为白色，外层黑边+粗阴影模仿多层发光效果
                style_params = "fontcolor=white:borderw=3:bordercolor=black:shadowx=5:shadowy=5:shadowcolor=#FFD700:"

            # 排版引擎构建
            pos_type = cfg.get('position', '底部对齐')
            offset = int(cfg.get('offset', 150))
            line_spacing = int(ts * 0.25)

            for i, sub_data in enumerate(subtitle_list):
                if sub_data['start'] >= target_dur: continue
                lines = [line.strip() for line in sub_data['text'].replace('\\n', '|').split('|') if line.strip()]
                total_lines = len(lines)

                for j, line_text in enumerate(lines):
                    temp_text_path = os.path.join(temp_dir, f"sub_{track_name}_{i}_{j}.txt")
                    with open(temp_text_path, 'w', encoding='utf-8-sig') as f: f.write(line_text)
                    
                    safe_tp = temp_text_path.replace('\\', '/').replace(':', '\\:')
                    
                    # 动态 Y 坐标计算
                    if pos_type == "顶部对齐":
                        base_y = f"{offset} + {j * (ts + line_spacing)}"
                    elif pos_type == "居中对齐":
                        base_y = f"(h-{total_lines*ts})/2 + {j * (ts + line_spacing)}"
                    else: # 底部对齐
                        base_y = f"h-text_h-{offset} - {(total_lines - 1 - j) * (ts + line_spacing)}"
                    
                    drawtext_filter = f"drawtext=fontfile='{sf}':textfile='{safe_tp}':fontsize={ts}:{style_params}x=(w-text_w)/2:y={base_y}:enable='between(t,{sub_data['start']},{min(sub_data['end'], target_dur)})'"
                    filters.append(drawtext_filter)
            return filters
        
        if config.get('sub1_enable') and config.get('subtitles1'):
            global_vf.extend(add_subtitle_filters(config['subtitles1'], config['sub1_cfg'], temp_dir, "主字幕轨"))
        if config.get('sub2_enable') and config.get('subtitles2'):
            global_vf.extend(add_subtitle_filters(config['subtitles2'], config['sub2_cfg'], temp_dir, "副字幕轨"))
                    
        global_vf.append("format=yuv420p")
        video_filter_str = ",".join(global_vf)
        
        if bgm_duration > 0:
            fade_start = max(0.0, target_dur - min(2.0, target_dur))
            afs = f",afade=t=out:st={fade_start}:d={min(2.0, target_dur)}" if config['enable_fadeout'] else ""
            af = f"[1:a]atrim=0:{target_dur}{afs}[aout]"
            cmd.extend(['-filter_complex', f"[0:v]{video_filter_str}[vout];{af}", '-map', '[vout]', '-map', '[aout]'])
        else: 
            cmd.extend(['-vf', video_filter_str, '-map', '0:v'])
            
        cmd.extend(['-c:v', config['video_codec'], '-preset', config['video_preset'], '-crf', str(config['video_crf']), '-t', str(target_dur), '-y', output_file])
        if bgm_duration > 0: cmd.extend(['-c:a', config['audio_codec']])
        
        run_subprocess_hidden(cmd, capture_output=True, check=True)
        return output_file

    def process_videos_tab1(config, log_callback, progress_callback):
        try:
            timestamp = datetime.now().strftime('%y%m%d_%H%M%S')
            output_path = os.path.join(config['output_folder'], f"{config['output_basename']}_{timestamp}.mp4")
            
            video_files = get_video_files(config['folder_path'], config['video_extensions'])
            if not video_files: 
                log_callback("❌ 指定素材池为空！")
                return False
                
            with tempfile.TemporaryDirectory() as temp_dir:
                progress_callback(30)
                
                target_duration = get_media_duration(config['bgm_path']) if config['match_bgm'] and os.path.exists(config['bgm_path']) else None
                if not target_duration and (config.get('sub1_enable') or config.get('sub2_enable')):
                    log_callback("⚠️ 警告: 未设置BGM或未勾选'对齐BGM'，将以第一个素材时长作为字幕均分基准。")
                    target_duration = get_media_duration(video_files[0])

                if config.get('interpolate_120'): config['target_fps'] = '120'
                config['beat_intervals'], config['beat_timestamps'] = None, None
                config['subtitles1'], config['subtitles2'] = [], []
                
                if os.path.exists(config['bgm_path']):
                    if config['sync_beats']:
                        if config.get('beat_sync_mode') == '精准踩点 (Precise Onset)': 
                            config['beat_timestamps'] = get_audio_beats_precise(config['bgm_path'], config['beat_min_duration'], log_callback)
                        else: 
                            config['beat_intervals'] = get_audio_beats_rhythmic(config['bgm_path'], config['beat_min_duration'], log_callback)
                
                if config.get('sub1_enable') and config.get('sub1_cfg', {}).get('path'):
                    sub1_path = config['sub1_cfg']['path']
                    if sub1_path.lower().endswith('.srt'): config['subtitles1'] = parse_srt_file(sub1_path, log_callback)
                    elif sub1_path.lower().endswith('.txt'): config['subtitles1'] = parse_txt_file(sub1_path, target_duration, log_callback)

                if config.get('sub2_enable') and config.get('sub2_cfg', {}).get('path'):
                    sub2_path = config['sub2_cfg']['path']
                    if sub2_path.lower().endswith('.srt'): config['subtitles2'] = parse_srt_file(sub2_path, log_callback)
                    elif sub2_path.lower().endswith('.txt'): config['subtitles2'] = parse_txt_file(sub2_path, target_duration, log_callback)
                
                clip_files = create_clip_list(video_files, temp_dir, config, log_callback, target_duration, config['max_duration'])
                if not clip_files: 
                    log_callback("❌ 未能成功提取任何有效视频片段！")
                    return False
                progress_callback(70)
                
                merged_video = os.path.join(temp_dir, "merged.mp4")
                merge_clips(clip_files, merged_video, config, log_callback)
                progress_callback(85)
                
                apply_final_render_with_text(merged_video, config['bgm_path'], output_path, config, log_callback, temp_dir)
                progress_callback(100)
                log_callback(f"\n✅ 成功了！作品已保存在:\n{output_path}")
                return True
                
        except Exception as e: 
            log_callback(f"\n❌ 渲染引擎爆炸: {e}\n{traceback.format_exc()}")
            return False

    # ==================== 界面构建 ====================
    class VideoProcessorGUI:
        def __init__(self):
            self.root = tk.Tk()
            self.root.title("短视频霸主级解构软件 (无损时长版 - 剪映级字幕特调)")
            self.root.geometry("1100x900")
            self.root.minsize(950, 800)
            self.t1_cfg = {'clip_duration': 2.5, 'beat_min_duration': 0.5, 'video_preset': "fast", 'video_crf': 20, 'target_res': "2560x1440", 'target_fps': "60"}
            
            # 基础预设选项字典
            self.UI_FONTS = list(SYS_FONTS.keys())
            self.UI_COLORS = ["纯白", "亮黄", "荧光绿", "大红", "纯黑", "粉红", "天蓝"]
            self.UI_STYLES = ["基础无样式", "经典描边 (经典)", "柔和阴影 (流行)", "半透黑底 (科普)", "综艺花字 (浮夸)"]
            self.UI_POSITIONS = ["底部对齐", "居中对齐", "顶部对齐"]
            
            self.setup_ui()
        
        def setup_ui(self):
            missing_deps = check_dependencies()
            if missing_deps:
                tk.Label(self.root, text=f"⛔ 核心组件 {', '.join(missing_deps)} 丢失！请放在同目录。", bg="#FFE4E1", fg="#B22222", font=("微软雅黑", 12, "bold"), pady=10).pack(fill=tk.X)

            self.main_panel = ttk.Frame(self.root)
            self.main_panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            self.build_main_ui()
            
            cf = ttk.Frame(self.root)
            cf.pack(fill=tk.X, padx=10, pady=5)
            self.generate_btn = tk.Button(cf, text="🚀 开始批量执行智能混剪指令！", command=self.start_processing, font=("微软雅黑", 14, "bold"), bg="#DC143C", fg="white", pady=8)
            self.generate_btn.pack(fill=tk.X)
            
            self.progress_var = tk.IntVar()
            ttk.Progressbar(self.root, variable=self.progress_var, maximum=100).pack(fill=tk.X, padx=10, pady=5)
            
            lf = ttk.LabelFrame(self.root, text="执行流日志", padding="5")
            lf.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))
            self.log_text = scrolledtext.ScrolledText(lf, width=80, height=8, wrap=tk.WORD, state="disabled", font=("宋体", 10))
            self.log_text.pack(fill=tk.BOTH, expand=True)
            self.log_text.tag_config("green", foreground="green")
            self.log_text.tag_config("red", foreground="red")

        # --- 辅助 UI 搭建的方法 ---
        def build_subtitle_ui(self, parent, title, is_main=True):
            frame = ttk.LabelFrame(parent, text=title, padding=8)
            frame.columnconfigure(1, weight=1)
            
            # --- 变量集 ---
            vars_dict = {
                'enable': tk.BooleanVar(value=False),
                'path': tk.StringVar(),
                'font': tk.StringVar(value="默认(系统黑体)"),
                'style': tk.StringVar(value="经典描边 (经典)" if is_main else "柔和阴影 (流行)"),
                'color': tk.StringVar(value="亮黄" if is_main else "纯白"),
                'size': tk.StringVar(value="80" if is_main else "60"),
                'position': tk.StringVar(value="底部对齐" if is_main else "顶部对齐"),
                'offset': tk.StringVar(value="180" if is_main else "100")
            }
            
            # 第一排：加载文件
            chk = ttk.Checkbutton(frame, text="✅ 启用", variable=vars_dict['enable'], command=self.update_t1_sub_states)
            chk.grid(row=0, column=0, sticky=tk.W)
            
            ent_path = ttk.Entry(frame, textvariable=vars_dict['path'])
            ent_path.grid(row=0, column=1, padx=5, sticky=tk.EW)
            btn_path = ttk.Button(frame, text="选择TXT/SRT字幕", command=lambda: vars_dict['path'].set(filedialog.askopenfilename(filetypes=[("字幕文件", "*.txt *.srt")])))
            btn_path.grid(row=0, column=2, sticky=tk.E)
            
            # 第二排：核心样式选单 (剪映风格)
            opt_f1 = ttk.Frame(frame)
            opt_f1.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(8,4))
            
            ttk.Label(opt_f1, text="字体模板:").pack(side=tk.LEFT)
            cb_font = ttk.Combobox(opt_f1, textvariable=vars_dict['font'], values=self.UI_FONTS, state="readonly", width=15)
            cb_font.pack(side=tk.LEFT, padx=(5,15))
            
            ttk.Label(opt_f1, text="视觉样式:").pack(side=tk.LEFT)
            cb_style = ttk.Combobox(opt_f1, textvariable=vars_dict['style'], values=self.UI_STYLES, state="readonly", width=18)
            cb_style.pack(side=tk.LEFT, padx=(5,15))
            
            ttk.Label(opt_f1, text="文字颜色:").pack(side=tk.LEFT)
            cb_color = ttk.Combobox(opt_f1, textvariable=vars_dict['color'], values=self.UI_COLORS, state="readonly", width=10)
            cb_color.pack(side=tk.LEFT, padx=(5,0))
            
            # 第三排：排版控制
            opt_f2 = ttk.Frame(frame)
            opt_f2.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=4)
            
            ttk.Label(opt_f2, text="字体大小:").pack(side=tk.LEFT)
            sp_size = ttk.Spinbox(opt_f2, from_=10, to=300, width=5, textvariable=vars_dict['size'])
            sp_size.pack(side=tk.LEFT, padx=(5,15))
            
            ttk.Label(opt_f2, text="排版位置:").pack(side=tk.LEFT)
            cb_pos = ttk.Combobox(opt_f2, textvariable=vars_dict['position'], values=self.UI_POSITIONS, state="readonly", width=12)
            cb_pos.pack(side=tk.LEFT, padx=(5,15))
            
            ttk.Label(opt_f2, text="边缘偏移量(px):").pack(side=tk.LEFT)
            sp_off = ttk.Spinbox(opt_f2, from_=0, to=2000, width=6, textvariable=vars_dict['offset'])
            sp_off.pack(side=tk.LEFT, padx=(5,0))
            
            # 记录组件以便联动禁用
            vars_dict['widgets'] = [ent_path, btn_path, cb_font, cb_style, cb_color, sp_size, cb_pos, sp_off]
            
            return frame, vars_dict

        def build_main_ui(self):
            self.t1_canvas = tk.Canvas(self.main_panel)
            scroll = ttk.Scrollbar(self.main_panel, command=self.t1_canvas.yview)
            self.f1 = ttk.Frame(self.t1_canvas, padding=10)
            
            self.t1_window_id = self.t1_canvas.create_window((0, 0), window=self.f1, anchor="nw")
            self.t1_canvas.configure(yscrollcommand=scroll.set)
            scroll.pack(side="right", fill="y")
            self.t1_canvas.pack(side="left", fill="both", expand=True)
            
            self.f1.bind("<Configure>", lambda e: self.t1_canvas.configure(scrollregion=self.t1_canvas.bbox("all")))
            self.t1_canvas.bind("<Configure>", lambda e: self.t1_canvas.itemconfig(self.t1_window_id, width=e.width))
            
            cf = ttk.LabelFrame(self.f1, text="1. 源目录输入", padding=10)
            cf.pack(fill=tk.X, pady=5)
            cf.columnconfigure(1, weight=1)
            self.t1_folder_var = tk.StringVar(value=os.getcwd())
            self.t1_bgm_var = tk.StringVar(value="")
            
            ttk.Label(cf, text="素材池:").grid(row=0, column=0, sticky=tk.W)
            ttk.Entry(cf, textvariable=self.t1_folder_var).grid(row=0, column=1, sticky="ew", padx=5)
            ttk.Button(cf, text="浏览", command=lambda: self.t1_folder_var.set(filedialog.askdirectory())).grid(row=0, column=2)
            ttk.Label(cf, text="背景音乐:").grid(row=1, column=0, sticky=tk.W)
            ttk.Entry(cf, textvariable=self.t1_bgm_var).grid(row=1, column=1, sticky="ew", padx=5)
            ttk.Button(cf, text="浏览", command=lambda: self.t1_bgm_var.set(filedialog.askopenfilename(filetypes=[("媒体文件", "*.mp3 *.wav *.aac *.mp4 *.mov")]))).grid(row=1, column=2)
            
            sf = ttk.Frame(cf)
            sf.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=5)
            self.t1_match_bgm = tk.BooleanVar(value=True)
            ttk.Checkbutton(sf, text="对齐BGM长度", variable=self.t1_match_bgm).pack(side=tk.LEFT, padx=5)
            self.t1_sync_beats = tk.BooleanVar(value=True)
            ttk.Checkbutton(sf, text="AI卡点", variable=self.t1_sync_beats).pack(side=tk.LEFT, padx=(5,0))
            self.t1_beat_mode = tk.StringVar(value="精准踩点 (Precise Onset)")
            ttk.Combobox(sf, textvariable=self.t1_beat_mode, values=["精准踩点 (Precise Onset)", "智能鼓点 (Rhythmic)"], state="readonly", width=22, font=("微软雅黑", 9)).pack(side=tk.LEFT, padx=(2,10))
            self.t1_fade = tk.BooleanVar(value=True)
            ttk.Checkbutton(sf, text="片尾音频消散", variable=self.t1_fade).pack(side=tk.LEFT, padx=5)
            
            # --- 全新 剪映风格字幕中心 ---
            text_frame = ttk.LabelFrame(self.f1, text="2. 👑 智能预设双轨字幕系统 (剪映级控制台)", padding=10)
            text_frame.pack(fill=tk.X, pady=5)

            self.f_sub1, self.sub1_vars = self.build_subtitle_ui(text_frame, "主字幕轨 (解说/歌词)", is_main=True)
            self.f_sub1.pack(fill=tk.X, pady=(0, 5))
            
            self.f_sub2, self.sub2_vars = self.build_subtitle_ui(text_frame, "副字幕轨 (标题/备注)", is_main=False)
            self.f_sub2.pack(fill=tk.X, pady=(5, 0))
            
            self.update_t1_sub_states()
            
            # ---------------------------
            
            df = ttk.LabelFrame(self.f1, text="3. 基础去重与画面处理", padding=10)
            df.pack(fill=tk.X, pady=5)
            
            mf = ttk.Frame(df)
            mf.pack(fill=tk.X, pady=5)
            self.t1_zoom = tk.BooleanVar(value=True)
            ttk.Checkbutton(mf, text="微距放大", variable=self.t1_zoom).pack(side=tk.LEFT, padx=(0,15))
            self.t1_speed = tk.BooleanVar(value=True)
            ttk.Checkbutton(mf, text="光流变速", variable=self.t1_speed).pack(side=tk.LEFT, padx=15)
            self.t1_color = tk.BooleanVar(value=True)
            ttk.Checkbutton(mf, text="色彩偏移", variable=self.t1_color).pack(side=tk.LEFT, padx=15)
            self.t1_flip = tk.BooleanVar(value=True)
            ttk.Checkbutton(mf, text="镜像翻转", variable=self.t1_flip).pack(side=tk.LEFT, padx=15)
            
            mf2 = ttk.Frame(df)
            mf2.pack(fill=tk.X, pady=(0, 5))
            self.t1_force_fullscreen = tk.BooleanVar(value=False)
            ttk.Checkbutton(mf2, text="✅ 强制拉伸全屏", variable=self.t1_force_fullscreen).pack(side=tk.LEFT, padx=(0,5))
            
            mf3 = ttk.Frame(df)
            mf3.pack(fill=tk.X, pady=(5,5))
            self.t1_transitions = tk.BooleanVar(value=True)
            ttk.Checkbutton(mf3, text="🌊 片段间无损转场", variable=self.t1_transitions).pack(side=tk.LEFT, padx=(0,5))
            self.t1_transition_dur = tk.DoubleVar(value=0.2)
            ttk.Spinbox(mf3, from_=0.1, to=1.0, increment=0.1, textvariable=self.t1_transition_dur, width=4).pack(side=tk.LEFT)
            tk.Label(mf3, text="s").pack(side=tk.LEFT, padx=(0,15))
            
            self.t1_avoid_subs = tk.BooleanVar(value=False)
            ttk.Checkbutton(mf3, text="✂️ 规避原素材字幕区", variable=self.t1_avoid_subs).pack(side=tk.LEFT, padx=5)
            self.t1_avoid_black = tk.BooleanVar(value=True)
            ttk.Checkbutton(mf3, text="⬛ 规避黑屏", variable=self.t1_avoid_black).pack(side=tk.LEFT, padx=5)
            
            trend_f = ttk.LabelFrame(self.f1, text="4. 潮流视觉强化 (高级去重)", padding=10)
            trend_f.pack(fill=tk.X, pady=5)
            
            self.t1_interpolate_120 = tk.BooleanVar(value=False)
            ttk.Checkbutton(trend_f, text="🚀 AI强力补帧至120FPS (耗时)", variable=self.t1_interpolate_120).pack(anchor=tk.W)
            self.t1_pip_mode = tk.BooleanVar(value=False)
            ttk.Checkbutton(trend_f, text="视频画中画 (电影感模糊背景)", variable=self.t1_pip_mode).pack(anchor=tk.W)
            self.t1_film_grain = tk.BooleanVar(value=False)
            ttk.Checkbutton(trend_f, text="叠加电影颗粒 (胶片质感)", variable=self.t1_film_grain).pack(anchor=tk.W)
            self.t1_vignette_effect = tk.BooleanVar(value=False)
            ttk.Checkbutton(trend_f, text="增加暗角 (突出主体)", variable=self.t1_vignette_effect).pack(anchor=tk.W)
            self.t1_sharpen_edge = tk.BooleanVar(value=False)
            ttk.Checkbutton(trend_f, text="边缘锐化 (提升清晰度)", variable=self.t1_sharpen_edge).pack(anchor=tk.W)
            
            mf_lut = ttk.Frame(self.f1)
            mf_lut.pack(fill=tk.X, pady=5)
            self.t1_lut_enable = tk.BooleanVar(value=False)
            ttk.Checkbutton(mf_lut, text="🎨 全局LUT电影调色(.cube)", variable=self.t1_lut_enable, command=self.update_lut_state).pack(side=tk.LEFT)
            self.t1_lut_path = tk.StringVar(value="")
            self.t1_lut_entry = ttk.Entry(mf_lut, textvariable=self.t1_lut_path, width=38)
            self.t1_lut_entry.pack(side=tk.LEFT, padx=5)
            self.t1_lut_btn = ttk.Button(mf_lut, text="选择LUT", command=lambda: self.t1_lut_path.set(filedialog.askopenfilename(filetypes=[("LUT", "*.cube *.3dl")])))
            self.t1_lut_btn.pack(side=tk.LEFT)
            self.update_lut_state()
            
            outf = ttk.LabelFrame(self.f1, text="5. 导出设置", padding=10)
            outf.pack(fill=tk.X, pady=5)
            outf.columnconfigure(1, weight=1)
            
            ttk.Label(outf, text="保存到:").grid(row=0, column=0, sticky=tk.W)
            self.t1_out_var = tk.StringVar(value=os.getcwd())
            ttk.Entry(outf, textvariable=self.t1_out_var).grid(row=0, column=1, sticky="ew", padx=5)
            ttk.Button(outf, text="浏览", command=lambda: self.t1_out_var.set(filedialog.askdirectory())).grid(row=0, column=2)
            
            out_row1 = ttk.Frame(outf)
            out_row1.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=5)
            self.t1_letterbox = tk.BooleanVar(value=True)
            ttk.Checkbutton(out_row1, text="保留上下电影黑边", variable=self.t1_letterbox).pack(side=tk.LEFT, padx=(0, 20))
            ttk.Label(out_row1, text="批量生成数量:").pack(side=tk.LEFT)
            self.t1_output_count = tk.IntVar(value=1)
            ttk.Spinbox(out_row1, from_=1, to=999, textvariable=self.t1_output_count, width=5).pack(side=tk.LEFT, padx=5)

        def update_t1_sub_states(self):
            state1 = tk.NORMAL if self.sub1_vars['enable'].get() else tk.DISABLED
            for w in self.sub1_vars['widgets']: 
                try: w.config(state=state1)
                except: pass
            
            state2 = tk.NORMAL if self.sub2_vars['enable'].get() else tk.DISABLED
            for w in self.sub2_vars['widgets']: 
                try: w.config(state=state2)
                except: pass

        def update_lut_state(self): 
            state = tk.NORMAL if self.t1_lut_enable.get() else tk.DISABLED
            self.t1_lut_entry.config(state=state)
            self.t1_lut_btn.config(state=state)

        def log_message(self, m, overwrite=False): self.root.after(0, self._log, m, overwrite)
        def _log(self, m, overwrite): 
            self.log_text.config(state="normal")
            if overwrite:
                self.log_text.delete("end-2l", "end-1l")
            self.log_text.insert(tk.END, m + "\n", "green" if "✅" in m else ("red" if "❌" in m else None))
            self.log_text.see(tk.END)
            self.log_text.config(state="disabled")
            
        def update_progress(self, v): 
            self.root.after(0, lambda: self.progress_var.set(v))

        def start_processing(self):
            self.generate_btn.config(state=tk.DISABLED, bg="gray", text="矩阵重铸启动...")
            self.progress_var.set(0)
            self.log_text.config(state="normal")
            self.log_text.delete(1.0, tk.END)
            self.log_text.config(state="disabled")
            
            # --- 采集字幕变量并打包 ---
            s1_cfg = {k: v.get() for k, v in self.sub1_vars.items() if k != 'widgets'}
            s2_cfg = {k: v.get() for k, v in self.sub2_vars.items() if k != 'widgets'}
            
            config = {
                'folder_path': self.t1_folder_var.get(), 'output_folder': self.t1_out_var.get(), 'bgm_path': self.t1_bgm_var.get(),
                'beat_min_duration': self.t1_cfg['beat_min_duration'], 'match_bgm': self.t1_match_bgm.get(),
                'sync_beats': self.t1_sync_beats.get(), 'beat_sync_mode': self.t1_beat_mode.get(), 'enable_fadeout': self.t1_fade.get(),
                
                'sub1_enable': s1_cfg['enable'], 'sub1_cfg': s1_cfg,
                'sub2_enable': s2_cfg['enable'], 'sub2_cfg': s2_cfg,
                
                'dedup_zoom': self.t1_zoom.get(), 'dedup_speed': self.t1_speed.get(), 'dedup_color': self.t1_color.get(), 'dedup_flip': self.t1_flip.get(),
                'force_fullscreen': self.t1_force_fullscreen.get(), 'enable_transitions': self.t1_transitions.get(), 'transition_duration': self.t1_transition_dur.get(),
                'avoid_subs': self.t1_avoid_subs.get(), 'avoid_black_screen': self.t1_avoid_black.get(),
                'interpolate_120': self.t1_interpolate_120.get(), 'pip_mode': self.t1_pip_mode.get(), 'film_grain': self.t1_film_grain.get(),
                'vignette_effect': self.t1_vignette_effect.get(), 'sharpen_edge': self.t1_sharpen_edge.get(),
                'lut_enable': self.t1_lut_enable.get(), 'lut_path': self.t1_lut_path.get(), 'enable_letterbox': self.t1_letterbox.get(),
                'letterbox_top': 130, 'letterbox_bottom': 130, 'output_basename': "MagicCut", 'output_count': self.t1_output_count.get(),
                'video_codec': "libx264", 'audio_codec': "aac", 'video_preset': 'faster', 'video_crf': 20,
                'target_resolution': self.t1_cfg['target_res'], 'target_fps': self.t1_cfg['target_fps'],
                'video_extensions': (".mp4", ".avi", ".mov", ".mkv"), 'max_duration': 0.0, 'clip_duration': self.t1_cfg['clip_duration'],
            }
            if not os.path.isdir(config['folder_path']): 
                messagebox.showerror("出错", "请指定有效的素材目录！")
                self.reset_btn()
                return
            thread = threading.Thread(target=self.run_t1_thread, args=(config,))
            thread.daemon = True
            thread.start()

        def reset_btn(self): 
            self.root.after(0, lambda: self.generate_btn.config(state=tk.NORMAL, bg="#DC143C", text="🚀 开始批量执行智能混剪指令！"))
            
        def run_t1_thread(self, config):
            try:
                total, success = config.get('output_count', 1), 0
                for i in range(total):
                    if total > 1: self.log_message(f"\n{'='*40}\n🔄 矩阵裂变: 第 {i+1}/{total} 个\n{'='*40}")
                    if process_videos_tab1(config.copy(), self.log_message, self.update_progress): success += 1
                if success > 0: messagebox.showinfo("大功告成", f"✅ 成功裂变出 {success} 个作品！")
            finally: 
                self.reset_btn()

    if __name__ == "__main__":
        missing_bins = check_dependencies()
        if missing_bins:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("核心组件缺失", f"必需的外部程序缺失:\n\n" + "\n".join(missing_bins) + \
                                f"\n\n请确保 ffmpeg.exe 和 ffprobe.exe 文件与本程序放在同一个文件夹。")
            sys.exit(1)

        app = VideoProcessorGUI()
        app.root.mainloop()

except Exception as e:
    write_crash_log()