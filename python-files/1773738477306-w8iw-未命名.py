import os
import glob
from fpdf import FPDF
from PIL import Image

# ===================== 配置参数（可根据需要修改） =====================
IMAGE_DIR = "./images"       # 存放图片的目录（相对路径，可改为绝对路径）
SUPPORTED_FORMATS = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')  # 支持的图片格式
OUTPUT_DIR = "./pdf_output"  # PDF输出目录
# =====================================================================

def main():
    # 1. 创建输出目录（不存在则自动创建）
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 2. 获取所有支持格式的图片路径（兼容大小写后缀，如JPG/jpg）
    image_paths = []
    for ext in SUPPORTED_FORMATS:
        image_paths.extend(glob.glob(os.path.join(IMAGE_DIR, f"*{ext}")))
        image_paths.extend(glob.glob(os.path.join(IMAGE_DIR, f"*{ext.upper()}")))
    
    # 去重（避免同一文件因后缀大小写被重复读取）
    image_paths = list(set(image_paths))
    
    # 3. 检查是否有图片
    if not image_paths:
        print(f"❌ 错误：在目录 {IMAGE_DIR} 中未找到任何图片文件！")
        return
    
    # 4. 按文件名倒序排序（仅基于文件名，不包含路径）
    image_paths.sort(key=lambda x: os.path.basename(x), reverse=True)
    print(f"✅ 共找到 {len(image_paths)} 张图片，已按文件名倒序排序")
    
    # 5. 两两分组（50张图片会分成25组）
    image_groups = [image_paths[i:i+2] for i in range(0, len(image_paths), 2)]
    
    # 6. 遍历分组生成PDF
    for group_idx, group in enumerate(image_groups, start=1):
        # 创建PDF对象（A4尺寸，单位mm）
        pdf = FPDF(unit="mm", format="A4")
        
        # 为每组中的每张图片添加PDF页面
        for img_path in group:
            try:
                # 打开图片并计算适配A4的尺寸（保持宽高比，居中显示）
                with Image.open(img_path) as img:
                    img_w_px, img_h_px = img.size
                    # 像素转mm（1px ≈ 0.264583mm）
                    img_w_mm = img_w_px * 0.264583
                    img_h_mm = img_h_px * 0.264583
                    
                    # 计算缩放比例（适配A4页面）
                    pdf_w, pdf_h = pdf.w, pdf.h  # A4：210mm × 297mm
                    scale = min(pdf_w / img_w_mm, pdf_h / img_h_mm)
                    new_w, new_h = img_w_mm * scale, img_h_mm * scale
                    
                    # 添加新页面并插入图片（居中）
                    pdf.add_page()
                    pdf.image(
                        img_path,
                        x=(pdf_w - new_w)/2,  # 水平居中
                        y=(pdf_h - new_h)/2,  # 垂直居中
                        w=new_w,
                        h=new_h
                    )
                print(f"  ├─ 已添加图片：{os.path.basename(img_path)}")
            except Exception as e:
                print(f"⚠️  处理图片 {os.path.basename(img_path)} 失败：{str(e)}")
                continue
        
        # 保存PDF文件（按分组顺序命名）
        pdf_filename = os.path.join(OUTPUT_DIR, f"output_{group_idx}.pdf")
        pdf.output(pdf_filename)
        print(f"  └─ 生成PDF：{pdf_filename}\n")
    
    print(f"🎉 全部完成！共生成 {len(image_groups)} 个PDF文件，存放于 {OUTPUT_DIR} 目录")

if __name__ == "__main__":
    main()
