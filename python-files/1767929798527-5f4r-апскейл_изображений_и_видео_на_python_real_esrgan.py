# requirements:
# pip install realesrgan opencv-python pillow numpy torch torchvision
# ffmpeg должен быть установлен в системе

import os
import cv2
import subprocess
from PIL import Image
import numpy as np
from realesrgan import RealESRGAN
import torch

DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

# ---------- IMAGE UPSCALE ----------

def upscale_image(input_path, output_path, scale=4):
    model = RealESRGAN(DEVICE, scale=scale)
    model.load_weights(f'RealESRGAN_x{scale}.pth')

    image = Image.open(input_path).convert('RGB')
    sr_image = model.predict(image)
    sr_image.save(output_path)


# ---------- VIDEO UPSCALE ----------

def extract_frames(video_path, frames_dir):
    os.makedirs(frames_dir, exist_ok=True)
    subprocess.run([
        'ffmpeg', '-i', video_path, f'{frames_dir}/frame_%06d.png'
    ], check=True)


def assemble_video(frames_dir, output_video, fps):
    subprocess.run([
        'ffmpeg', '-framerate', str(fps),
        '-i', f'{frames_dir}/frame_%06d.png',
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
        output_video
    ], check=True)


def upscale_video(input_video, output_video, scale=4, fps=30):
    frames_dir = 'frames'
    upscaled_dir = 'frames_upscaled'

    extract_frames(input_video, frames_dir)
    os.makedirs(upscaled_dir, exist_ok=True)

    model = RealESRGAN(DEVICE, scale=scale)
    model.load_weights(f'RealESRGAN_x{scale}.pth')

    for frame in sorted(os.listdir(frames_dir)):
        img = Image.open(os.path.join(frames_dir, frame)).convert('RGB')
        sr = model.predict(img)
        sr.save(os.path.join(upscaled_dir, frame))

    assemble_video(upscaled_dir, output_video, fps)


# ---------- EXAMPLE ----------
if __name__ == '__main__':
    # Изображение
    upscale_image('input.jpg', 'output_upscaled.png', scale=4)

    # Видео
    upscale_video('input.mp4', 'output_upscaled.mp4', scale=4, fps=30)
