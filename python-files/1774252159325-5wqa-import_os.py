import os
import re

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
    
    # Hỏi người dùng nhập tên file
    print("=" * 50)
    print("CHƯƠNG TRÌNH PHẲNG HÓA DỮ LIỆU GPON")
    print("=" * 50)
    print(f"📁 Thư mục hiện tại: {script_dir}\n")
    
    file_name = input("Nhập tên file input (ví dụ: abc): ").strip()
    
    # Nếu người dùng không nhập đuôi, tự động thêm .txt
    if not file_name.endswith('.txt'):
        file_name += '.txt'
    
    # Nối tên file với thư mục script
    input_file = os.path.join(script_dir, file_name)
    
    # Kiểm tra file có tồn tại không
    if not os.path.exists(input_file):
        print(f"❌ Lỗi: Không tìm thấy file {input_file}!")
        return
    
    # Tách tên file và extension
    file_name_only, file_ext = os.path.splitext(file_name)
    
    # Tạo tên file đầu ra: [tên_file]_output.[extension]
    output_file = os.path.join(script_dir, f"{file_name_only}_output{file_ext}")

    all_flattened = []
    
    print(f"\n⏳ Đang xử lý file: {input_file}")
    
    # Đọc file đầu vào
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            all_flattened.extend(flatten_gpon_line(line))

    # Ghi kết quả ra file đầu ra
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in all_flattened:
            f.write(item + '\n')

    print(f"\n✅ Xong! Đã xử lý {len(lines)} dòng gộp thành {len(all_flattened)} dòng chi tiết.")
    print(f"📄 Kết quả: {f'{file_name_only}_output{file_ext}'}")
    print("=" * 50)

# Thực thi chương trình
if __name__ == "__main__":
    process_files()