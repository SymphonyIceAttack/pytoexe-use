import os
from PIL import Image
from pillow_heif import register_heif_opener

# 註冊 HEIF 開啟器
register_heif_opener()

def convert_heic_to_jpg():
    # 取得目前程式所在的資料夾
    current_dir = os.getcwd()
    print(f"📂 當前路徑：{current_dir}")
    print("🚀 開始掃描 HEIC 檔案...")

    count = 0
    for filename in os.listdir(current_dir):
        if filename.lower().endswith(".heic"):
            # 開啟 HEIC
            image = Image.open(filename)
            # 取得檔名（不含副檔名）
            target_name = os.path.splitext(filename)[0] + ".jpg"
            
            # 轉存為 JPG
            image.save(target_name, "JPEG", quality=90)
            print(f"✅ 已轉換: {filename} -> {target_name}")
            count += 1

    if count == 0:
        print("💡 找不到任何 HEIC 檔案。")
    else:
        print(f"\n✨ 任務完成！共轉換 {count} 個檔案。")

if __name__ == "__main__":
    convert_heic_to_jpg()
    input("\n請按 Enter 結束視窗...")