import os
import re
from tkinter import Tk, filedialog

def flatten_gpon_line(line):
    line = line.strip()
    if not line or "_" not in line:
        return []

    # Tách prefix (Ví dụ: gpon-onu_1/1/)
    parts_prefix = line.split('_')
    header = parts_prefix[0] + "_"
    path_parts = parts_prefix[1].split('/')
    base_path = header + "/".join(path_parts[:2]) + "/"
    
    # Lấy phần dữ liệu còn lại (4:3-4:3,5:2,13:3,...)
    content = "/".join(path_parts[2:])
    
    # Pattern: PORT:ONT_LIST:GEMPORT
    # Ví dụ: 4:3-4:3 (port 4, ont [3-4], gemport 3)
    #        5:2,13:3 (port 5, ont [2,13], gemport 3)
    port_patterns = re.findall(r'(\d+):([^:]+):\d+', content)
    
    results = []
    for port, ont_list in port_patterns:
        # ont_list có thể chứa dấu ',' phân tách các ONT
        # Ví dụ: "3-4" hoặc "2,13"
        for ont in ont_list.split(','):
            ont = ont.strip()
            if '-' in ont:  # Range như 3-4
                try:
                    start, end = map(int, ont.split('-'))
                    for i in range(start, end + 1):
                        results.append(f"{base_path}{port}:{i}")
                except:
                    continue
            elif ont:  # ONT đơn lẻ
                results.append(f"{base_path}{port}:{ont}")
    
    return results

def process_files():
    # Lấy thư mục chứa script .py này
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("=" * 50)
    print("CHƯƠNG TRÌNH PHẲNG HÓA DỮ LIỆU GPON")
    print("=" * 50)
    print(f"📁 Thư mục: {script_dir}\n")
    print("⏳ Đang mở cửa sổ chọn file...\n")
    
    # Tạo cửa sổ Tkinter ẩn
    root = Tk()
    root.withdraw()  # Ẩn cửa sổ chính
    root.attributes('-topmost', True)  # Đưa dialog lên trên cùng
    
    # Mở dialog browse file - cho phép chọn NHIỀU file
    input_files = filedialog.askopenfilenames(
        initialdir=script_dir,
        title="Chọn file(s) input",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )
    
    root.destroy()  # Đóng cửa sổ Tkinter
    
    # Nếu người dùng không chọn file, kết thúc
    if not input_files:
        print("❌ Không có file nào được chọn!")
        return
    
    print(f"✅ Đã chọn {len(input_files)} file\n")
    
    # Xử lý từng file
    for idx, input_file in enumerate(input_files, 1):
        # Kiểm tra file có tồn tại không
        if not os.path.exists(input_file):
            print(f"❌ [{idx}] Lỗi: Không tìm thấy file {input_file}!")
            continue
        
        # Tách tên file và extension
        file_dir = os.path.dirname(input_file)
        file_name = os.path.basename(input_file)
        file_name_only, file_ext = os.path.splitext(file_name)
        
        # Tạo tên file đầu ra: [tên_file]_output.[extension]
        output_file = os.path.join(file_dir, f"{file_name_only}_output{file_ext}")

        all_flattened = []
        
        print(f"⏳ [{idx}] Đang xử lý file: {file_name}")
        
        # Đọc file đầu vào
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                all_flattened.extend(flatten_gpon_line(line))

        # Ghi kết quả ra file đầu ra
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in all_flattened:
                f.write(item + '\n')

        print(f"✅ [{idx}] Xong! Xử lý {len(lines)} → {len(all_flattened)} dòng")
        print(f"    📄 Kết quả: {f'{file_name_only}_output{file_ext}\n'}")
    
    print("=" * 50)
    print("🎉 Hoàn thành xử lý tất cả file!")
    print("=" * 50)
    input("\n📌 Press any key to close...")

# Thực thi chương trình
if __name__ == "__main__":
    process_files()