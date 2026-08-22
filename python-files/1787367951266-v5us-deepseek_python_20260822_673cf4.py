import os
import sys
import pydicom

# 简化的隐私标签列表
PRIVACY_TAGS = [
    (0x0008, 0x0050), (0x0010, 0x0010), (0x0010, 0x0020),
    (0x0010, 0x0030), (0x0010, 0x0032), (0x0010, 0x0040),
    (0x0010, 0x1010), (0x0010, 0x21C0), (0x0008, 0x0080),
]

def main():
    print("=" * 60)
    print("🔒 DICOM Privacy Anonymizer")
    print("=" * 60)
    
    # 获取文件路径
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = input("\n📁 Enter DICOM file path: ").strip().strip('"')
    
    if not file_path or not os.path.exists(file_path):
        print("❌ File not found")
        input("\nPress Enter to exit...")
        return
    
    print(f"\n📖 Processing: {file_path}")
    
    try:
        # 读取文件
        ds = pydicom.dcmread(file_path, force=True)
        
        # 移除标签
        removed = 0
        for tag in PRIVACY_TAGS:
            if tag in ds:
                vr = ds[tag].VR
                if vr in ['US', 'SS', 'UL', 'SL', 'FL', 'FD']:
                    ds[tag].value = 0
                elif vr in ['DA', 'TM', 'DT']:
                    ds[tag].value = ''
                else:
                    ds[tag].value = 'NONE'
                removed += 1
                print(f"  ✅ Removed: {ds[tag].name}")
        
        # 保存文件
        output_file = file_path.replace('.dcm', '_anonymized.dcm')
        ds.save_as(output_file, write_like_original=True)
        
        print(f"\n✅ Done! Removed {removed} tags")
        print(f"📁 Saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()