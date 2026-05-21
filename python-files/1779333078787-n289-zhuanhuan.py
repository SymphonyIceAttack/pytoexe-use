# -*- coding: utf-8 -*-
import os
import glob

# ====================== �����޸��κ����� ======================
# ��ȡ��ǰ exe/�ű� ���еĸ�Ŀ¼
current_dir = os.path.dirname(os.path.abspath(__file__))
# ��������ļ�������
output_folder = "m3u epgת��"
# ƴ������ļ�������·��
output_dir = os.path.join(current_dir, output_folder)
# ��������ļ��У��Ѵ����򲻱�����
os.makedirs(output_dir, exist_ok=True)
# =========================================================

def process_m3u(input_path: str, output_path: str):
    """��������m3u�ļ�������tvg-id"""
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            stripped = line.strip()
            # ƥ������ #EXTINF:-1,xxx ��ʽ
            if stripped.startswith("#EXTINF:-1,"):
                # ��ȡƵ������
                channel_name = stripped.split("#EXTINF:-1,")[1]
                # �����¸�ʽ
                new_line = f'#EXTINF:-1 tvg-id="{channel_name}",{channel_name}\n'
                new_lines.append(new_line)
            else:
                # ������ԭ������
                new_lines.append(line)

        # д�봦������ļ�
        with open(output_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        return True, ""
    except Exception as e:
        return False, str(e)

if __name__ == "__main__":
    # ���ҵ�ǰĿ¼������ .m3u �ļ������������ļ��У�
    m3u_file_list = glob.glob(os.path.join(current_dir, "*.m3u"))

    if not m3u_file_list:
        print("? δ�ڵ�ǰĿ¼�ҵ��κ� .m3u �ļ����뽫m3u�ļ�����exeͬһĿ¼�����ԣ�")
    else:
        success_count = 0
        fail_count = 0
        # ������������m3u�ļ�
        for file_path in m3u_file_list:
            file_name = os.path.basename(file_path)
            out_path = os.path.join(output_dir, file_name)
            
            success, msg = process_m3u(file_path, out_path)
            if success:
                print(f"? �����ɹ���{file_name}")
                success_count += 1
            else:
                print(f"? ����ʧ�ܣ�{file_name}��ԭ��{msg}")
                fail_count += 1

        print("-" * 50)
        print(f"? ������ɣ��ɹ� {success_count} �� | ʧ�� {fail_count} ��")
        print(f"? ��������ļ��ѱ�������{output_dir}")
        print("? ���Դϻ���EPG���� �� �������ļ�����")

    # ��ֹexe���к�ֱ������
    input("\n���س����˳�...")