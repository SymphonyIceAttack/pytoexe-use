#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版批量将txt文件转换为MP3音频文件
支持设置音频码率为48K
"""

import pyttsx3
import os
import glob
import argparse
import tempfile
from pydub import AudioSegment

def txt_to_mp3_48k(txt_file, output_dir=None, rate=200, volume=1.0, voice_id=None):
    """
    将单个txt文件转换为48K码率的mp3

    Args:
        txt_file (str): 输入的txt文件路径
        output_dir (str): 输出目录，默认为None表示与txt文件同一目录
        rate (int): 语速，默认200
        volume (float): 音量，默认1.0
        voice_id (str): 语音ID，默认None使用系统默认
    """
    # 初始化tts引擎
    engine = pyttsx3.init()

    # 设置语音属性
    engine.setProperty('rate', rate)  # 语速
    engine.setProperty('volume', volume)  # 音量

    # 设置语音（如果指定）
    if voice_id:
        engine.setProperty('voice', voice_id)

    # 读取txt文件内容
    with open(txt_file, 'r', encoding='utf-8') as f:
        text = f.read()

    # 创建临时wav文件
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_wav:
        temp_wav_path = tmp_wav.name

    try:
        # 生成临时wav文件
        engine.save_to_file(text, temp_wav_path)
        engine.runAndWait()

        # 使用pydub加载wav并转换为48K mp3
        audio = AudioSegment.from_wav(temp_wav_path)

        # 确定输出文件路径
        if output_dir:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            base_name = os.path.splitext(os.path.basename(txt_file))[0]
            output_file = os.path.join(output_dir, f"{base_name}.mp3")
        else:
            base_name = os.path.splitext(txt_file)[0]
            output_file = f"{base_name}.mp3"

        # 导出为48K码率的MP3
        audio.export(output_file, format="mp3", bitrate="48k")

        print(f"已生成48K码率MP3: {output_file}")

    finally:
        # 清理临时文件
        if os.path.exists(temp_wav_path):
            os.unlink(temp_wav_path)

def batch_txt_to_mp3_48k(input_pattern, output_dir=None, rate=200, volume=1.0, voice_id=None):
    """
    批量将txt文件转换为48K码率的mp3

    Args:
        input_pattern (str): 输入文件匹配模式，如 "*.txt" 或 "files/*.txt"
        output_dir (str): 输出目录
        rate (int): 语速
        volume (float): 音量
        voice_id (str): 语音ID
    """
    # 查找所有匹配的txt文件
    txt_files = glob.glob(input_pattern)

    if not txt_files:
        print(f"未找到匹配的文件: {input_pattern}")
        return

    print(f"找到 {len(txt_files)} 个txt文件")

    # 逐个转换
    for i, txt_file in enumerate(txt_files, 1):
        print(f"[{i}/{len(txt_files)}] 正在转换: {txt_file}")
        try:
            txt_to_mp3_48k(txt_file, output_dir, rate, volume, voice_id)
        except Exception as e:
            print(f"转换失败: {txt_file} - {str(e)}")

def create_sample_txt_files():
    """创建示例txt文件用于测试"""
    sample_texts = [
        "欢迎使用TXT转MP3工具。这个工具可以将文本文件转换为音频文件。",
        "人工智能是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。",
        "Python是一种广泛使用的解释型、高级编程、通用型编程语言。Python支持多种编程范型，主要包括面向对象、命令式、函数式和 procedural。"
    ]

    for i, text in enumerate(sample_texts, 1):
        filename = f"sample_{i}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"已创建示例文件: {filename}")

def list_voices():
    """列出系统可用的语音"""
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    print("可用的语音:")
    for i, voice in enumerate(voices):
        print(f"{i}: {voice.name} ({voice.id}) - {voice.languages}")

def main():
    parser = argparse.ArgumentParser(description='批量将txt文件转换为48K码率MP3音频文件')
    parser.add_argument('input', nargs='?', default='*.txt', 
                        help='输入文件模式 (默认: *.txt)')
    parser.add_argument('-o', '--output', help='输出目录')
    parser.add_argument('-r', '--rate', type=int, default=200, 
                        help='语速 (默认: 200)')
    parser.add_argument('-v', '--volume', type=float, default=1.0, 
                        help='音量 0.0-1.0 (默认: 1.0)')
    parser.add_argument('--voice', help='语音ID')
    parser.add_argument('--list-voices', action='store_true', 
                        help='列出可用的语音')
    parser.add_argument('--create-samples', action='store_true',
                        help='创建示例txt文件')

    args = parser.parse_args()

    if args.list_voices:
        list_voices()
        return

    if args.create_samples:
        create_sample_txt_files()
        return

    batch_txt_to_mp3_48k(args.input, args.output, args.rate, args.volume, args.voice)

if __name__ == "__main__":
    main()
