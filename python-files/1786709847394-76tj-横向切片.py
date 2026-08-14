import os
from PIL import Image
from tkinter import Tk, filedialog, messagebox

# =========================
# 用户可修改的参数
# =========================
SLICE_HEIGHT = 1500   # 每一片的固定高度（像素）
OVERLAP = 0          # 上下相邻切片的重叠像素
# =========================


def slice_image_by_height(image_path, slice_height, overlap=0):
    img = Image.open(image_path).convert("RGB")
    width, height = img.size

    output_dir = os.path.join(os.path.dirname(image_path), "详情页")
    os.makedirs(output_dir, exist_ok=True)

    basename = os.path.splitext(os.path.basename(image_path))[0]

    i = 0
    top = 0
    while top < height:
        # 当前切片的顶部和底部坐标
        slice_top = max(0, top - overlap)
        slice_bottom = min(height, top + slice_height + overlap)

        cropped = img.crop((0, slice_top, width, slice_bottom))
        save_path = os.path.join(output_dir, f"{basename}_slice_{i:04d}.jpg")
        cropped.save(save_path, "JPEG", quality=95)

        i += 1
        top += slice_height  # 下移一个切片高度

    return output_dir, i


if __name__ == "__main__":
    Tk().withdraw()

    image_paths = filedialog.askopenfilenames(
        title="选择图片（可多选）",
        filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.webp")]
    )

    if not image_paths:
        print("❌ 未选择图片")
    else:
        total = 0
        for img_path in image_paths:
            out_dir, count = slice_image_by_height(
                image_path=img_path,
                slice_height=SLICE_HEIGHT,
                overlap=OVERLAP
            )
            total += count
            print(f"✅ 处理完成: {os.path.basename(img_path)} → {count} 张切片")

        print(f"\n🎉 共处理 {len(image_paths)} 张图片，生成 {total} 张 JPG 切片")

        messagebox.showinfo(
            "完成",
            f"已成功处理 {len(image_paths)} 张图片\n"
            f"共生成 {total} 张 JPG 切片\n\n"
            f"保存路径示例：\n{out_dir}"
        )
