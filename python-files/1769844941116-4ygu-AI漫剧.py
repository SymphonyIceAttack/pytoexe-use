"""
AI动画生成软件 - 从文本到动画的完整解决方案
模块: 编剧、角色设计师、分镜师、视频制作、音效总监
"""

import os
import json
import sys
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import threading
from queue import Queue

# GUI框架 - 使用PyQt5
try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    QT_AVAILABLE = True
except ImportError:
    print("正在安装PyQt5...")
    os.system(f"{sys.executable} -m pip install PyQt5")
    QT_AVAILABLE = False
    # 重新尝试导入
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *

# 其他依赖
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cv2
from gtts import gTTS
import pygame
import markdown

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Character:
    """角色数据类"""
    name: str
    description: str
    age: Optional[int] = None
    gender: Optional[str] = None
    personality: List[str] = field(default_factory=list)
    appearance: Dict = field(default_factory=dict)
    image_path: Optional[str] = None

@dataclass
class Scene:
    """场景数据类"""
    id: int
    title: str
    description: str
    characters: List[str]
    location: str
    time: str
    duration: float  # 场景时长（秒）
    shot_type: str = "medium"  # 镜头类型
    emotion: str = "neutral"   # 场景情感

@dataclass
class StoryScript:
    """剧本数据类"""
    title: str
    author: str
    chapters: List[Dict]
    characters: List[Character]
    scenes: List[Scene]
    total_duration: float = 0.0


class ScreenwriterAI:
    """编剧AI模块：分析小说，提取剧情和角色"""
    
    def __init__(self):
        self.name = "编剧AI"
        logger.info(f"{self.name} 模块初始化")
        
    def analyze_story(self, text: str) -> StoryScript:
        """分析小说文本，提取结构"""
        logger.info(f"{self.name}: 开始分析故事文本")
        
        # 提取标题和作者（简化版）
        lines = text.split('\n')
        title = lines[0].strip() if lines else "未命名故事"
        author = "未知作者"
        
        # 提取章节（简化逻辑）
        chapters = []
        current_chapter = None
        
        for i, line in enumerate(text.split('\n')):
            if "第" in line and "章" in line:
                if current_chapter:
                    chapters.append(current_chapter)
                current_chapter = {
                    "title": line.strip(),
                    "content": "",
                    "start_line": i
                }
            elif current_chapter:
                current_chapter["content"] += line + "\n"
        
        if current_chapter:
            chapters.append(current_chapter)
        
        # 提取角色（简单规则匹配）
        characters = self._extract_characters(text)
        
        # 创建场景
        scenes = self._create_scenes(text, characters)
        
        # 计算总时长
        total_duration = sum(scene.duration for scene in scenes)
        
        script = StoryScript(
            title=title,
            author=author,
            chapters=chapters,
            characters=characters,
            scenes=scenes,
            total_duration=total_duration
        )
        
        logger.info(f"{self.name}: 故事分析完成，共{len(characters)}个角色，{len(scenes)}个场景")
        return script
    
    def _extract_characters(self, text: str) -> List[Character]:
        """提取角色信息（简化版）"""
        characters = []
        
        # 常见中文姓氏
        chinese_surnames = ["李", "王", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴"]
        
        lines = text.split('\n')
        for line in lines:
            if len(line.strip()) < 20:  # 较短的行可能是对话
                # 寻找"说"、"道"等对话标记前的名字
                for surname in chinese_surnames:
                    if surname in line and ("说" in line or "道" in line):
                        # 提取名字（简化逻辑）
                        start = line.find(surname)
                        name = line[start:start+2] if start != -1 else surname + "某"
                        if name not in [c.name for c in characters]:
                            character = Character(
                                name=name,
                                description=f"故事中的角色{name}",
                                personality=["勇敢", "善良"] if len(characters) % 2 == 0 else ["聪明", "机智"]
                            )
                            characters.append(character)
        
        # 如果没有找到角色，创建默认角色
        if not characters:
            characters = [
                Character(name="小明", description="故事主角", personality=["勇敢", "善良"]),
                Character(name="小红", description="故事女主角", personality=["聪明", "美丽"])
            ]
        
        return characters[:5]  # 限制最多5个角色
    
    def _create_scenes(self, text: str, characters: List[Character]) -> List[Scene]:
        """创建场景分拆"""
        scenes = []
        
        # 将文本按段落分割
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        shot_types = ["close-up", "medium", "wide", "extreme-wide"]
        emotions = ["happy", "sad", "angry", "neutral", "surprised"]
        locations = ["室内", "室外", "城市", "森林", "海边", "山上"]
        times = ["白天", "夜晚", "早晨", "黄昏"]
        
        for i, para in enumerate(paragraphs[:10]):  # 最多10个场景
            if len(para) > 50:  # 只处理较长的段落
                scene = Scene(
                    id=i+1,
                    title=f"场景{i+1}",
                    description=para[:100] + "..." if len(para) > 100 else para,
                    characters=[c.name for c in characters[:2]],  # 每个场景最多2个角色
                    location=locations[i % len(locations)],
                    time=times[i % len(times)],
                    duration=5.0,  # 每个场景5秒
                    shot_type=shot_types[i % len(shot_types)],
                    emotion=emotions[i % len(emotions)]
                )
                scenes.append(scene)
        
        return scenes


class CharacterDesignerAI:
    """角色设计师AI模块：生成角色形象"""
    
    def __init__(self, output_dir="characters"):
        self.name = "角色设计师AI"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        logger.info(f"{self.name} 模块初始化")
        
        # 角色颜色方案
        self.color_schemes = [
            {"primary": (255, 100, 100), "secondary": (100, 100, 255)},  # 红蓝
            {"primary": (100, 255, 100), "secondary": (255, 100, 255)},  # 绿紫
            {"primary": (255, 255, 100), "secondary": (100, 255, 255)},  # 黄青
            {"primary": (255, 150, 50), "secondary": (50, 150, 255)},    # 橙蓝
            {"primary": (200, 100, 255), "secondary": (100, 255, 200)},  # 紫绿
        ]
    
    def design_character(self, character: Character, style: str = "anime") -> str:
        """为角色设计形象并生成图像"""
        logger.info(f"{self.name}: 为角色'{character.name}'设计形象")
        
        # 生成角色描述
        character.appearance = self._generate_appearance(character, style)
        
        # 创建角色图像
        image_path = self._create_character_image(character)
        character.image_path = str(image_path)
        
        return character.image_path
    
    def _generate_appearance(self, character: Character, style: str) -> Dict:
        """生成角色外观描述"""
        appearances = {
            "anime": {
                "hair_color": ["黑色", "金色", "棕色", "银色", "蓝色"],
                "eye_color": ["黑色", "蓝色", "绿色", "红色", "紫色"],
                "clothing": ["校服", "战斗服", "礼服", "休闲装", "魔法袍"]
            },
            "realistic": {
                "hair_color": ["黑色", "棕色", "金色", "红色", "灰色"],
                "eye_color": ["棕色", "蓝色", "绿色", "黑色", "灰色"],
                "clothing": ["西装", "裙子", "T恤", "外套", "制服"]
            }
        }
        
        style_data = appearances.get(style, appearances["anime"])
        seed = hash(character.name) % 100
        
        return {
            "hair_color": style_data["hair_color"][seed % len(style_data["hair_color"])],
            "eye_color": style_data["eye_color"][seed % len(style_data["eye_color"])],
            "clothing": style_data["clothing"][seed % len(style_data["clothing"])],
            "style": style
        }
    
    def _create_character_image(self, character: Character) -> Path:
        """创建角色图像（使用PIL生成简单图像）"""
        # 使用角色名字的哈希值选择颜色方案
        color_idx = hash(character.name) % len(self.color_schemes)
        colors = self.color_schemes[color_idx]
        
        # 创建图像
        img_size = (400, 600)
        image = Image.new('RGB', img_size, color=(240, 240, 240))
        draw = ImageDraw.Draw(image)
        
        # 绘制背景
        draw.rectangle([0, 0, img_size[0], img_size[1]], fill=(240, 240, 240))
        
        # 绘制角色轮廓（简化的人形）
        # 头部
        head_center = (img_size[0]//2, 150)
        head_radius = 60
        draw.ellipse(
            [head_center[0]-head_radius, head_center[1]-head_radius,
             head_center[0]+head_radius, head_center[1]+head_radius],
            fill=colors["primary"]
        )
        
        # 身体
        body_top = head_center[1] + head_radius
        body_bottom = body_top + 200
        draw.rectangle(
            [head_center[0]-40, body_top,
             head_center[0]+40, body_bottom],
            fill=colors["secondary"]
        )
        
        # 腿
        leg_width = 20
        draw.rectangle(
            [head_center[0]-30, body_bottom,
             head_center[0]-10, body_bottom+150],
            fill=colors["primary"]
        )
        draw.rectangle(
            [head_center[0]+10, body_bottom,
             head_center[0]+30, body_bottom+150],
            fill=colors["primary"]
        )
        
        # 手臂
        arm_length = 80
        draw.rectangle(
            [head_center[0]-40, body_top+20,
             head_center[0]-80, body_top+20+arm_length],
            fill=colors["primary"]
        )
        draw.rectangle(
            [head_center[0]+40, body_top+20,
             head_center[0]+80, body_top+20+arm_length],
            fill=colors["primary"]
        )
        
        # 添加名字
        try:
            font = ImageFont.truetype("arial.ttf", 30)
        except:
            font = ImageFont.load_default()
        
        # 绘制名字
        text_bbox = draw.textbbox((0, 0), character.name, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_position = (img_size[0]//2 - text_width//2, body_bottom + 160)
        draw.text(text_position, character.name, fill=(0, 0, 0), font=font)
        
        # 保存图像
        image_path = self.output_dir / f"{character.name}.png"
        image.save(image_path)
        
        logger.info(f"{self.name}: 角色'{character.name}'图像已保存到 {image_path}")
        return image_path


class StoryboardArtistAI:
    """分镜师AI模块：生成分镜脚本和预览"""
    
    def __init__(self, output_dir="storyboards"):
        self.name = "分镜师AI"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        logger.info(f"{self.name} 模块初始化")
    
    def create_storyboard(self, scene: Scene, characters: List[Character]) -> Dict:
        """为场景创建分镜"""
        logger.info(f"{self.name}: 为场景'{scene.title}'创建分镜")
        
        # 创建分镜描述
        storyboard = {
            "scene_id": scene.id,
            "title": scene.title,
            "description": scene.description,
            "shot_type": scene.shot_type,
            "emotion": scene.emotion,
            "duration": scene.duration,
            "characters": scene.characters,
            "camera_angles": self._generate_camera_angles(scene),
            "transitions": self._generate_transitions(scene),
            "visual_notes": self._generate_visual_notes(scene),
            "preview_image": None
        }
        
        # 生成分镜预览图像
        preview_path = self._create_storyboard_preview(scene, characters, storyboard)
        storyboard["preview_image"] = str(preview_path)
        
        return storyboard
    
    def _generate_camera_angles(self, scene: Scene) -> List[str]:
        """生成摄像机角度"""
        angles = []
        base_angles = {
            "close-up": ["特写镜头", "面部表情"],
            "medium": ["中景镜头", "腰部以上"],
            "wide": ["全景镜头", "全身镜头"],
            "extreme-wide": ["远景镜头", "环境展示"]
        }
        
        main_angle = base_angles.get(scene.shot_type, ["中景镜头"])
        angles.extend(main_angle)
        
        # 添加情感相关的角度
        if scene.emotion in ["happy", "sad"]:
            angles.append("低角度镜头" if scene.emotion == "happy" else "高角度镜头")
        
        return angles
    
    def _generate_transitions(self, scene: Scene) -> List[str]:
        """生成转场效果"""
        transitions = ["切镜头"]
        
        if scene.emotion == "happy":
            transitions.append("淡入")
        elif scene.emotion == "sad":
            transitions.append("淡出")
        elif scene.emotion == "surprised":
            transitions.append("快速变焦")
        
        return transitions
    
    def _generate_visual_notes(self, scene: Scene) -> List[str]:
        """生成视觉备注"""
        notes = []
        
        # 根据情感添加备注
        emotion_notes = {
            "happy": ["明亮色调", "高饱和度", "温暖光效"],
            "sad": ["冷色调", "低饱和度", "柔和光效"],
            "angry": ["高对比度", "红色调", "动态模糊"],
            "surprised": ["快速变焦", "高亮度", "定格效果"]
        }
        
        notes.extend(emotion_notes.get(scene.emotion, ["自然光效", "标准色调"]))
        notes.append(f"地点: {scene.location}")
        notes.append(f"时间: {scene.time}")
        
        return notes
    
    def _create_storyboard_preview(self, scene: Scene, characters: List[Character], storyboard: Dict) -> Path:
        """创建分镜预览图像"""
        # 创建画布
        img_size = (800, 600)
        image = Image.new('RGB', img_size, color=(255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        # 绘制标题
        try:
            title_font = ImageFont.truetype("arial.ttf", 24)
            text_font = ImageFont.truetype("arial.ttf", 16)
        except:
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
        
        # 标题
        title = f"分镜: {scene.title}"
        draw.text((20, 20), title, fill=(0, 0, 0), font=title_font)
        
        # 场景描述
        desc_y = 60
        description_lines = self._wrap_text(scene.description, 70)
        for line in description_lines[:3]:  # 最多3行
            draw.text((20, desc_y), line, fill=(100, 100, 100), font=text_font)
            desc_y += 25
        
        # 分镜信息
        info_y = desc_y + 20
        infos = [
            f"镜头类型: {scene.shot_type}",
            f"情感: {scene.emotion}",
            f"时长: {scene.duration}秒",
            f"地点: {scene.location}",
            f"时间: {scene.time}"
        ]
        
        for info in infos:
            draw.text((20, info_y), info, fill=(50, 50, 50), font=text_font)
            info_y += 25
        
        # 绘制简单的分镜示意图
        storyboard_box = (400, 60, 750, 400)
        draw.rectangle(storyboard_box, outline=(200, 200, 200), width=2)
        
        # 在示意图中绘制简单的场景
        draw.text((420, 80), f"[{scene.shot_type}]", fill=(0, 100, 200), font=text_font)
        
        # 绘制角色位置标记
        for i, char_name in enumerate(scene.characters[:3]):
            x = 450 + (i * 100)
            y = 200
            draw.ellipse([x-20, y-20, x+20, y+20], fill=(100, 150, 200))
            draw.text((x-15, y-10), char_name[:2], fill=(255, 255, 255), font=text_font)
        
        # 保存图像
        preview_path = self.output_dir / f"storyboard_scene_{scene.id}.png"
        image.save(preview_path)
        
        logger.info(f"{self.name}: 分镜预览已保存到 {preview_path}")
        return preview_path
    
    def _wrap_text(self, text: str, max_width: int) -> List[str]:
        """文本换行"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            if len(' '.join(current_line + [word])) <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines


class VideoProducerAI:
    """视频制作AI模块：合成视频"""
    
    def __init__(self, output_dir="videos"):
        self.name = "视频制作AI"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        logger.info(f"{self.name} 模块初始化")
    
    def create_video(self, storyboard: Dict, output_name: str = "output") -> str:
        """根据分镜创建视频"""
        logger.info(f"{self.name}: 开始创建视频")
        
        # 视频参数
        fps = 24
        frame_size = (1280, 720)
        
        # 创建视频写入器
        video_path = self.output_dir / f"{output_name}.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(str(video_path), fourcc, fps, frame_size)
        
        try:
            # 为每个场景创建帧
            scene_id = storyboard.get("scene_id", 1)
            duration = storyboard.get("duration", 5.0)
            frames_per_scene = int(duration * fps)
            
            for frame_idx in range(frames_per_scene):
                # 创建帧
                frame = self._create_frame(storyboard, frame_idx, frames_per_scene, frame_size)
                video_writer.write(frame)
            
            logger.info(f"{self.name}: 视频已保存到 {video_path}")
            return str(video_path)
            
        finally:
            video_writer.release()
    
    def _create_frame(self, storyboard: Dict, frame_idx: int, total_frames: int, size: Tuple[int, int]) -> np.ndarray:
        """创建单个视频帧"""
        # 创建画布
        frame = np.ones((size[1], size[0], 3), dtype=np.uint8) * 255
        
        # 添加场景信息
        cv2.putText(frame, f"场景 {storyboard['scene_id']}", (50, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        # 添加描述
        desc = storyboard['description'][:100] + "..."
        y_offset = 100
        for i in range(0, len(desc), 40):
            line = desc[i:i+40]
            cv2.putText(frame, line, (50, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 1)
            y_offset += 30
        
        # 添加分镜信息
        info_y = 300
        infos = [
            f"镜头: {storyboard['shot_type']}",
            f"情感: {storyboard['emotion']}",
            f"帧: {frame_idx+1}/{total_frames}"
        ]
        
        for info in infos:
            cv2.putText(frame, info, (50, info_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 50, 50), 1)
            info_y += 40
        
        # 添加进度条
        progress = (frame_idx + 1) / total_frames
        bar_width = 600
        bar_height = 20
        bar_x = 50
        bar_y = 500
        
        # 背景条
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (200, 200, 200), -1)
        # 进度条
        progress_width = int(bar_width * progress)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + progress_width, bar_y + bar_height), (0, 150, 255), -1)
        
        # 进度文本
        progress_text = f"{progress:.1%}"
        text_size = cv2.getTextSize(progress_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        text_x = bar_x + bar_width + 10
        text_y = bar_y + bar_height // 2 + text_size[1] // 2
        cv2.putText(frame, progress_text, (text_x, text_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        
        return frame


class SoundDirectorAI:
    """音效总监AI模块：添加音频"""
    
    def __init__(self, output_dir="audio"):
        self.name = "音效总监AI"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        logger.info(f"{self.name} 模块初始化")
        
        # 初始化pygame音频
        pygame.mixer.init()
    
    def add_audio_to_video(self, video_path: str, scene: Scene, output_path: str = None) -> str:
        """为视频添加音频"""
        logger.info(f"{self.name}: 为视频添加音频")
        
        if output_path is None:
            output_path = self.output_dir / f"with_audio_{Path(video_path).stem}.mp4"
        
        # 生成旁白
        narration_path = self._generate_narration(scene)
        
        # 生成音效
        sound_effects = self._generate_sound_effects(scene)
        
        # 合并音频（简化版，实际需要使用ffmpeg）
        logger.info(f"{self.name}: 音频生成完成")
        
        # 返回原始视频路径（实际项目中会合并音频）
        return video_path
    
    def _generate_narration(self, scene: Scene) -> str:
        """生成旁白音频"""
        # 使用gTTS生成语音（需要网络连接）
        try:
            tts = gTTS(text=scene.description[:100], lang='zh-cn')
            audio_path = self.output_dir / f"narration_scene_{scene.id}.mp3"
            tts.save(str(audio_path))
            return str(audio_path)
        except Exception as e:
            logger.warning(f"{self.name}: 无法生成语音: {e}")
            return ""
    
    def _generate_sound_effects(self, scene: Scene) -> List[str]:
        """生成音效列表"""
        effects = []
        
        # 根据场景类型添加音效
        if "室内" in scene.location:
            effects.append("室内环境音")
        elif "室外" in scene.location or "森林" in scene.location:
            effects.append("鸟叫声")
            effects.append("风声")
        elif "海边" in scene.location:
            effects.append("海浪声")
        
        # 根据情感添加音效
        if scene.emotion == "happy":
            effects.append("欢快音乐")
        elif scene.emotion == "sad":
            effects.append("悲伤音乐")
        elif scene.emotion == "angry":
            effects.append("紧张音乐")
        elif scene.emotion == "surprised":
            effects.append("惊讶音效")
        
        return effects


class AnimationStudioGUI(QMainWindow):
    """动画工作室主界面"""
    
    def __init__(self):
        super().__init__()
        self.story_text = ""
        self.current_script = None
        self.ai_modules = {}
        self.progress_queue = Queue()
        
        self.init_ui()
        self.init_ai_modules()
        self.show()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("AI动画工作室")
        self.setGeometry(100, 100, 1200, 800)
        
        # 设置主窗口中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 标题
        title_label = QLabel("🎬 AI动画生成工作室")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; padding: 20px;")
        main_layout.addWidget(title_label)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 导入选项卡
        self.setup_import_tab()
        
        # 分析选项卡
        self.setup_analysis_tab()
        
        # 角色设计选项卡
        self.setup_character_tab()
        
        # 分镜选项卡
        self.setup_storyboard_tab()
        
        # 视频生成选项卡
        self.setup_video_tab()
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
    
    def setup_import_tab(self):
        """设置导入选项卡"""
        import_tab = QWidget()
        layout = QVBoxLayout(import_tab)
        
        # 文本导入区域
        import_group = QGroupBox("导入小说或文章")
        import_layout = QVBoxLayout(import_group)
        
        # 文本编辑器
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("在此粘贴或输入小说文本...")
        self.text_edit.setMinimumHeight(400)
        import_layout.addWidget(self.text_edit)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 导入按钮
        import_btn = QPushButton("📂 导入文件")
        import_btn.clicked.connect(self.import_file)
        button_layout.addWidget(import_btn)
        
        # 示例按钮
        example_btn = QPushButton("📖 加载示例")
        example_btn.clicked.connect(self.load_example)
        button_layout.addWidget(example_btn)
        
        # 清空按钮
        clear_btn = QPushButton("🗑️ 清空")
        clear_btn.clicked.connect(self.clear_text)
        button_layout.addWidget(clear_btn)
        
        import_layout.addLayout(button_layout)
        layout.addWidget(import_group)
        
        # 信息显示
        info_group = QGroupBox("故事信息")
        info_layout = QVBoxLayout(info_group)
        
        self.story_info_text = QTextEdit()
        self.story_info_text.setReadOnly(True)
        self.story_info_text.setMaximumHeight(150)
        info_layout.addWidget(self.story_info_text)
        
        layout.addWidget(info_group)
        self.tab_widget.addTab(import_tab, "📄 导入")
    
    def setup_analysis_tab(self):
        """设置分析选项卡"""
        analysis_tab = QWidget()
        layout = QVBoxLayout(analysis_tab)
        
        # 分析按钮
        analyze_btn = QPushButton("🔍 开始分析故事")
        analyze_btn.clicked.connect(self.analyze_story)
        layout.addWidget(analyze_btn)
        
        # 结果显示区域
        result_group = QGroupBox("分析结果")
        result_layout = QVBoxLayout(result_group)
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        result_layout.addWidget(self.result_text)
        
        layout.addWidget(result_group)
        self.tab_widget.addTab(analysis_tab, "🔍 分析")
    
    def setup_character_tab(self):
        """设置角色设计选项卡"""
        character_tab = QWidget()
        layout = QVBoxLayout(character_tab)
        
        # 角色设计按钮
        design_btn = QPushButton("🎨 设计角色形象")
        design_btn.clicked.connect(self.design_characters)
        layout.addWidget(design_btn)
        
        # 角色显示区域
        self.character_scroll = QScrollArea()
        self.character_widget = QWidget()
        self.character_layout = QVBoxLayout(self.character_widget)
        self.character_scroll.setWidget(self.character_widget)
        self.character_scroll.setWidgetResizable(True)
        layout.addWidget(self.character_scroll)
        
        self.tab_widget.addTab(character_tab, "👤 角色")
    
    def setup_storyboard_tab(self):
        """设置分镜选项卡"""
        storyboard_tab = QWidget()
        layout = QVBoxLayout(storyboard_tab)
        
        # 分镜生成按钮
        storyboard_btn = QPushButton("🎬 生成分镜")
        storyboard_btn.clicked.connect(self.generate_storyboards)
        layout.addWidget(storyboard_btn)
        
        # 分镜显示区域
        self.storyboard_scroll = QScrollArea()
        self.storyboard_widget = QWidget()
        self.storyboard_layout = QVBoxLayout(self.storyboard_widget)
        self.storyboard_scroll.setWidget(self.storyboard_widget)
        self.storyboard_scroll.setWidgetResizable(True)
        layout.addWidget(self.storyboard_scroll)
        
        self.tab_widget.addTab(storyboard_tab, "🎬 分镜")
    
    def setup_video_tab(self):
        """设置视频生成选项卡"""
        video_tab = QWidget()
        layout = QVBoxLayout(video_tab)
        
        # 视频生成按钮
        video_btn = QPushButton("🎥 生成动画视频")
        video_btn.clicked.connect(self.generate_video)
        layout.addWidget(video_btn)
        
        # 视频预览区域
        self.video_label = QLabel("视频预览区域")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("border: 2px dashed #ccc; padding: 20px;")
        layout.addWidget(self.video_label)
        
        # 播放控制
        control_layout = QHBoxLayout()
        
        play_btn = QPushButton("▶️ 播放")
        play_btn.clicked.connect(self.play_video)
        control_layout.addWidget(play_btn)
        
        export_btn = QPushButton("💾 导出视频")
        export_btn.clicked.connect(self.export_video)
        control_layout.addWidget(export_btn)
        
        layout.addLayout(control_layout)
        
        self.tab_widget.addTab(video_tab, "🎥 视频")
    
    def init_ai_modules(self):
        """初始化AI模块"""
        self.ai_modules["screenwriter"] = ScreenwriterAI()
        self.ai_modules["character_designer"] = CharacterDesignerAI()
        self.ai_modules["storyboard_artist"] = StoryboardArtistAI()
        self.ai_modules["video_producer"] = VideoProducerAI()
        self.ai_modules["sound_director"] = SoundDirectorAI()
    
    def import_file(self):
        """导入文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "", "文本文件 (*.txt *.md);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.story_text = f.read()
                    self.text_edit.setText(self.story_text)
                    self.update_story_info()
                    self.status_bar.showMessage(f"已导入文件: {Path(file_path).name}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法读取文件: {str(e)}")
    
    def load_example(self):
        """加载示例故事"""
        example_text = """第一章：相遇

在一个阳光明媚的早晨，小明走在去学校的路上。他是一位普通的高中生，有着黑色的短发和明亮的眼睛。

突然，他听到一个声音：“救命啊！”

小明转过头，看到一个女孩正被几个不良少年围住。那个女孩有着金色的长发，穿着白色的连衣裙。

“住手！”小明大喊一声，冲了过去。

不良少年们看到有人来，骂骂咧咧地走了。女孩感激地看着小明：“谢谢你救了我。我叫小红。”

“我是小明。你没事吧？”

“我没事。你真的很勇敢。”

从那天起，小明和小红成为了好朋友。他们一起上学，一起回家，分享彼此的梦想和烦恼。"""
        
        self.story_text = example_text
        self.text_edit.setText(example_text)
        self.update_story_info()
        self.status_bar.showMessage("已加载示例故事")
    
    def clear_text(self):
        """清空文本"""
        self.story_text = ""
        self.text_edit.clear()
        self.story_info_text.clear()
        self.status_bar.showMessage("已清空文本")
    
    def update_story_info(self):
        """更新故事信息"""
        if self.story_text:
            lines = self.story_text.split('\n')
            title = lines[0].strip() if lines else "未命名"
            word_count = len(self.story_text)
            
            info = f"标题: {title}\n"
            info += f"字数: {word_count} 字\n"
            info += f"段落数: {len([p for p in self.story_text.split('\n\n') if p.strip()])}\n"
            
            self.story_info_text.setText(info)
    
    def analyze_story(self):
        """分析故事"""
        if not self.story_text.strip():
            QMessageBox.warning(self, "警告", "请先导入或输入故事文本")
            return
        
        self.status_bar.showMessage("正在分析故事...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        
        # 在新线程中执行分析
        thread = threading.Thread(target=self._analyze_story_thread)
        thread.start()
    
    def _analyze_story_thread(self):
        """分析故事线程"""
        try:
            screenwriter = self.ai_modules["screenwriter"]
            self.current_script = screenwriter.analyze_story(self.story_text)
            
            # 更新UI（需要在主线程中执行）
            QMetaObject.invokeMethod(self, "_update_analysis_results", Qt.QueuedConnection)
            
        except Exception as e:
            QMetaObject.invokeMethod(self, "_analysis_error", Qt.QueuedConnection, Q_ARG(str, str(e)))
    
    def _update_analysis_results(self):
        """更新分析结果"""
        if self.current_script:
            result_text = f"故事标题: {self.current_script.title}\n\n"
            result_text += f"角色列表 ({len(self.current_script.characters)}个):\n"
            
            for i, char in enumerate(self.current_script.characters, 1):
                result_text += f"{i}. {char.name}: {char.description}\n"
            
            result_text += f"\n场景列表 ({len(self.current_script.scenes)}个):\n"
            for i, scene in enumerate(self.current_script.scenes[:5], 1):  # 只显示前5个
                result_text += f"{i}. {scene.title}: {scene.description[:50]}...\n"
            
            self.result_text.setText(result_text)
            self.progress_bar.setVisible(False)
            self.status_bar.showMessage("故事分析完成")
    
    def _analysis_error(self, error_msg):
        """分析错误处理"""
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "分析错误", f"分析过程中出现错误: {error_msg}")
        self.status_bar.showMessage("分析失败")
    
    def design_characters(self):
        """设计角色形象"""
        if not self.current_script or not self.current_script.characters:
            QMessageBox.warning(self, "警告", "请先分析故事")
            return
        
        self.status_bar.showMessage("正在设计角色形象...")
        
        # 清空现有角色显示
        for i in reversed(range(self.character_layout.count())): 
            widget = self.character_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # 设计每个角色
        designer = self.ai_modules["character_designer"]
        
        for character in self.current_script.characters:
            # 设计角色
            image_path = designer.design_character(character)
            
            # 创建角色显示卡片
            char_card = QGroupBox(character.name)
            card_layout = QHBoxLayout(char_card)
            
            # 显示角色图片
            if image_path and Path(image_path).exists():
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(200, 300, Qt.KeepAspectRatio)
                    image_label = QLabel()
                    image_label.setPixmap(pixmap)
                    card_layout.addWidget(image_label)
            
            # 角色信息
            info_text = f"描述: {character.description}\n"
            if character.personality:
                info_text += f"性格: {', '.join(character.personality)}\n"
            if character.appearance:
                info_text += f"外观: {', '.join([f'{k}: {v}' for k, v in character.appearance.items()])}"
            
            info_label = QLabel(info_text)
            info_label.setWordWrap(True)
            card_layout.addWidget(info_label)
            
            self.character_layout.addWidget(char_card)
        
        self.status_bar.showMessage("角色设计完成")
    
    def generate_storyboards(self):
        """生成分镜"""
        if not self.current_script or not self.current_script.scenes:
            QMessageBox.warning(self, "警告", "请先分析故事")
            return
        
        self.status_bar.showMessage("正在生成分镜...")
        
        # 清空现有分镜显示
        for i in reversed(range(self.storyboard_layout.count())): 
            widget = self.storyboard_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # 生成分镜
        artist = self.ai_modules["storyboard_artist"]
        
        for scene in self.current_script.scenes[:3]:  # 只生成前3个场景的分镜
            storyboard = artist.create_storyboard(scene, self.current_script.characters)
            
            # 创建分镜显示卡片
            board_card = QGroupBox(f"分镜 {scene.id}: {scene.title}")
            card_layout = QVBoxLayout(board_card)
            
            # 显示分镜预览
            if storyboard["preview_image"] and Path(storyboard["preview_image"]).exists():
                pixmap = QPixmap(storyboard["preview_image"])
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(600, 400, Qt.KeepAspectRatio)
                    image_label = QLabel()
                    image_label.setPixmap(pixmap)
                    card_layout.addWidget(image_label)
            
            # 分镜信息
            info_text = f"描述: {scene.description[:100]}...\n"
            info_text += f"镜头类型: {scene.shot_type}\n"
            info_text += f"情感: {scene.emotion}\n"
            info_text += f"时长: {scene.duration}秒\n"
            info_text += f"角色: {', '.join(scene.characters)}\n"
            info_text += f"摄像机角度: {', '.join(storyboard['camera_angles'])}"
            
            info_label = QLabel(info_text)
            info_label.setWordWrap(True)
            card_layout.addWidget(info_label)
            
            self.storyboard_layout.addWidget(board_card)
        
        self.status_bar.showMessage("分镜生成完成")
    
    def generate_video(self):
        """生成视频"""
        if not self.current_script or not self.current_script.scenes:
            QMessageBox.warning(self, "警告", "请先分析故事并生成分镜")
            return
        
        self.status_bar.showMessage("正在生成视频...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        
        # 在新线程中生成视频
        thread = threading.Thread(target=self._generate_video_thread)
        thread.start()
    
    def _generate_video_thread(self):
        """生成视频线程"""
        try:
            producer = self.ai_modules["video_producer"]
            sound_director = self.ai_modules["sound_director"]
            
            total_scenes = min(3, len(self.current_script.scenes))  # 只处理前3个场景
            video_paths = []
            
            for i in range(total_scenes):
                # 更新进度
                progress = int((i + 1) / total_scenes * 100)
                QMetaObject.invokeMethod(self.progress_bar, "setValue", Qt.QueuedConnection, Q_ARG(int, progress))
                
                # 为每个场景生成分镜
                artist = self.ai_modules["storyboard_artist"]
                scene = self.current_script.scenes[i]
                storyboard = artist.create_storyboard(scene, self.current_script.characters)
                
                # 生成视频
                scene_video = producer.create_video(storyboard, f"scene_{i+1}")
                
                # 添加音频
                final_video = sound_director.add_audio_to_video(scene_video, scene)
                video_paths.append(final_video)
            
            # 合并所有场景视频（简化版，实际需要合并）
            if video_paths:
                self.final_video_path = video_paths[0]
                QMetaObject.invokeMethod(self, "_video_generation_complete", Qt.QueuedConnection)
            else:
                QMetaObject.invokeMethod(self, "_video_generation_error", Qt.QueuedConnection, 
                                       Q_ARG(str, "未生成视频"))
                
        except Exception as e:
            QMetaObject.invokeMethod(self, "_video_generation_error", Qt.QueuedConnection, 
                                   Q_ARG(str, str(e)))
    
    def _video_generation_complete(self):
        """视频生成完成"""
        self.progress_bar.setVisible(False)
        
        # 显示视频预览
        if hasattr(self, 'final_video_path') and Path(self.final_video_path).exists():
            self.video_label.setText(f"视频已生成: {Path(self.final_video_path).name}")
            
            # 可以在这里添加视频预览功能
            # 例如，使用OpenCV读取第一帧显示
            
        self.status_bar.showMessage("视频生成完成")
        QMessageBox.information(self, "成功", "动画视频生成完成！")
    
    def _video_generation_error(self, error_msg):
        """视频生成错误"""
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "生成错误", f"视频生成失败: {error_msg}")
        self.status_bar.showMessage("视频生成失败")
    
    def play_video(self):
        """播放视频"""
        if hasattr(self, 'final_video_path') and Path(self.final_video_path).exists():
            try:
                # 使用系统默认播放器打开视频
                if sys.platform == 'win32':
                    os.startfile(self.final_video_path)
                elif sys.platform == 'darwin':  # macOS
                    os.system(f'open "{self.final_video_path}"')
                else:  # Linux
                    os.system(f'xdg-open "{self.final_video_path}"')
            except Exception as e:
                QMessageBox.warning(self, "播放错误", f"无法播放视频: {str(e)}")
        else:
            QMessageBox.warning(self, "警告", "请先生成视频")
    
    def export_video(self):
        """导出视频"""
        if hasattr(self, 'final_video_path') and Path(self.final_video_path).exists():
            save_path, _ = QFileDialog.getSaveFileName(
                self, "保存视频", "", "MP4文件 (*.mp4);;所有文件 (*.*)"
            )
            
            if save_path:
                try:
                    import shutil
                    shutil.copy2(self.final_video_path, save_path)
                    self.status_bar.showMessage(f"视频已保存到: {save_path}")
                    QMessageBox.information(self, "成功", "视频导出成功！")
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
        else:
            QMessageBox.warning(self, "警告", "请先生成视频")


def create_installer():
    """创建安装包脚本"""
    installer_script = """# setup.py - 安装脚本
from setuptools import setup, find_packages
import sys

APP = ['animation_studio.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'packages': ['PyQt5', 'PIL', 'opencv-python', 'gtts', 'pygame', 'numpy'],
    'includes': ['PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets'],
}

setup(
    name='AIAnimationStudio',
    version='1.0.0',
    author='AI Studio',
    description='AI动画生成软件',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    install_requires=[
        'PyQt5>=5.15.0',
        'Pillow>=8.0.0',
        'opencv-python>=4.5.0',
        'gtts>=2.2.0',
        'pygame>=2.0.0',
        'numpy>=1.19.0',
        'markdown>=3.3.0'
    ],
)

# 使用方法:
# 安装依赖: pip install -r requirements.txt
# 打包为Mac应用: python setup.py py2app
# 打包为Windows exe: 使用PyInstaller
# pyinstaller --onefile --windowed --add-data "*.py;." animation_studio.py
"""

    with open("setup.py", "w", encoding="utf-8") as f:
        f.write(installer_script)
    
    requirements = """PyQt5>=5.15.0
Pillow>=8.0.0
opencv-python>=4.5.0
gtts>=2.2.0
pygame>=2.0.0
numpy>=1.19.0
markdown>=3.3.0"""
    
    with open("requirements.txt", "w", encoding="utf-8") as f:
        f.write(requirements)
    
    print("安装脚本已创建: setup.py")
    print("依赖文件已创建: requirements.txt")


def main():
    """主函数"""
    # 检查并安装缺失的依赖
    missing_packages = []
    
    required_packages = [
        ('PyQt5', 'PyQt5'),
        ('PIL', 'Pillow'),
        ('cv2', 'opencv-python'),
        ('gtts', 'gTTS'),
        ('pygame', 'pygame'),
        ('numpy', 'numpy'),
        ('markdown', 'markdown')
    ]
    
    print("检查依赖包...")
    for import_name, package_name in required_packages:
        try:
            __import__(import_name)
            print(f"✓ {package_name} 已安装")
        except ImportError:
            print(f"✗ {package_name} 未安装")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\n正在安装缺失的包: {', '.join(missing_packages)}")
        import subprocess
        for package in missing_packages:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print("所有依赖已安装完成！")
    
    # 创建输出目录
    for directory in ["characters", "storyboards", "videos", "audio"]:
        Path(directory).mkdir(exist_ok=True)
    
    # 启动应用程序
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 设置现代样式
    
    # 创建并显示主窗口
    window = AnimationStudioGUI()
    
    # 创建安装脚本
    create_installer()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()