import os
import shutil
import re
from datetime import datetime
from pathlib import Path

def print_banner():
    """��ӡ�������"""
    print("\n" + "=" * 60)
    print("      JSON�ļ���������")
    print("=" * 60)

def print_menu():
    """��ӡ�˵�"""
    print("\n��ѡ��Ҫִ�еĲ�����")
    print("1. ת������JSON�ļ�")
    print("2. ȥ�ظ�JSON�ļ�")
    print("3. ��ת����ȥ�ظ�������������")
    print("4. �鿴��ǰ·������")
    print("5. �޸�·������")
    print("0. �˳�����")
    print("-" * 40)

def print_status(message, status_type="info"):
    """��ӡ״̬��Ϣ"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    if status_type == "info":
        prefix = f"[{timestamp}] INFO: "
        print(f"{prefix}{message}")
    elif status_type == "success":
        prefix = f"[{timestamp}] SUCCESS: "
        print(f"\033[92m{prefix}{message}\033[0m")
    elif status_type == "warning":
        prefix = f"[{timestamp}] WARNING: "
        print(f"\033[93m{prefix}{message}\033[0m")
    elif status_type == "error":
        prefix = f"[{timestamp}] ERROR: "
        print(f"\033[91m{prefix}{message}\033[0m")
    elif status_type == "title":
        print(f"\n\033[95m{message}\033[0m")
    elif status_type == "option":
        print(f"\033[96m{message}\033[0m")

def get_user_input(prompt, default=None):
    """��ȡ�û����룬֧��Ĭ��ֵ"""
    if default is not None:
        full_prompt = f"{prompt} (Ĭ��: {default}): "
    else:
        full_prompt = f"{prompt}: "
    
    user_input = input(full_prompt).strip()
    
    if user_input == "" and default is not None:
        return default
    return user_input

def extract_file_prefix(filename):
    """��ȡ�ļ���ǰ׺��ֻ������ĸ�ͺ��֣�"""
    # ȥ����չ��
    name_without_ext = Path(filename).stem
    
    # ʹ���������ʽƥ����ĸ�ͺ���
    # ���ַ�Χ: \u4e00-\u9fff
    # ��ĸ��Χ: a-zA-Z
    pattern = r'[\u4e00-\u9fffa-zA-Z]+'
    matches = re.findall(pattern, name_without_ext)
    
    if matches:
        # ���ص�һ��ƥ��Ĳ�����Ϊǰ׺
        return matches[0]
    return ""

class JSONFileManager:
    def __init__(self):
        # Ĭ��·������
        self.source_dir = Path("D:/Backup/Downloads")
        self.target_dir = Path("E:/youxix/databak")
        
        # �������ã�����У�
        self.load_config()
    
    def load_config(self):
        """�������ļ�����·��"""
        config_file = Path("json_manager_config.txt")
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines:
                        if line.startswith("source="):
                            self.source_dir = Path(line.strip()[7:])
                        elif line.startswith("target="):
                            self.target_dir = Path(line.strip()[7:])
                print_status("�Ѽ��������ļ�", "success")
            except Exception as e:
                print_status(f"���������ļ�ʧ��: {str(e)}", "warning")
    
    def save_config(self):
        """����·�����õ��ļ�"""
        try:
            config_file = Path("json_manager_config.txt")
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(f"source={self.source_dir}\n")
                f.write(f"target={self.target_dir}\n")
            print_status("�����ѱ���", "success")
        except Exception as e:
            print_status(f"��������ʧ��: {str(e)}", "error")
    
    def show_current_config(self):
        """��ʾ��ǰ����"""
        print_status("��ǰ·������:", "title")
        print(f"ԴĿ¼: \033[94m{self.source_dir}\033[0m")
        print(f"Ŀ��Ŀ¼: \033[94m{self.target_dir}\033[0m")
        
        # ���Ŀ¼�Ƿ����
        if not self.source_dir.exists():
            print_status("ԴĿ¼������", "warning")
        else:
            json_count = len(list(self.source_dir.glob("*.json")))
            print(f"ԴĿ¼JSON�ļ���: {json_count}")
        
        if not self.target_dir.exists():
            print_status("Ŀ��Ŀ¼������", "warning")
        else:
            json_count = len(list(self.target_dir.glob("*.json")))
            print(f"Ŀ��Ŀ¼JSON�ļ���: {json_count}")
    
    def modify_config(self):
        """�޸�·������"""
        print_status("�޸�·������", "title")
        
        current_source = str(self.source_dir)
        current_target = str(self.target_dir)
        
        new_source = get_user_input("������ԴĿ¼·��", current_source)
        new_target = get_user_input("������Ŀ��Ŀ¼·��", current_target)
        
        self.source_dir = Path(new_source)
        self.target_dir = Path(new_target)
        
        self.save_config()
        self.show_current_config()
    
    def transfer_json_files(self):
        """ת��JSON�ļ�"""
        print_status("��ʼת��JSON�ļ�...", "title")
        print_status(f"ԴĿ¼: {self.source_dir}")
        print_status(f"Ŀ��Ŀ¼: {self.target_dir}")
        
        # ���Ŀ¼�Ƿ����
        if not self.source_dir.exists():
            print_status(f"ԴĿ¼������: {self.source_dir}", "error")
            print_status("����ʹ��ѡ��5�޸�·������", "warning")
            return False
        
        # ����Ŀ��Ŀ¼����������ڣ�
        if not self.target_dir.exists():
            try:
                self.target_dir.mkdir(parents=True, exist_ok=True)
                print_status(f"�Ѵ���Ŀ��Ŀ¼: {self.target_dir}")
            except Exception as e:
                print_status(f"����Ŀ��Ŀ¼ʧ��: {str(e)}", "error")
                return False
        
        # ����JSON�ļ�
        json_files = list(self.source_dir.glob("*.json"))
        
        if not json_files:
            print_status("ԴĿ¼��û���ҵ�JSON�ļ�", "warning")
            return True
        
        print_status(f"�ҵ� {len(json_files)} ��JSON�ļ�")
        
        # ѯ���Ƿ����
        confirm = get_user_input(f"ȷ��Ҫת���� {len(json_files)} ���ļ���? (y/n)", "y")
        if confirm.lower() != 'y':
            print_status("������ȡ��", "warning")
            return False
        
        # �����ļ�
        transferred_count = 0
        for i, json_file in enumerate(json_files, 1):
            try:
                target_path = self.target_dir / json_file.name
                
                # ���Ŀ���ļ��Ѵ��ڣ��������
                counter = 1
                while target_path.exists():
                    name_parts = json_file.stem.rsplit('_', 1)
                    if len(name_parts) > 1 and name_parts[-1].isdigit():
                        base_name = name_parts[0]
                    else:
                        base_name = json_file.stem
                    
                    new_name = f"{base_name}_{counter}{json_file.suffix}"
                    target_path = self.target_dir / new_name
                    counter += 1
                
                shutil.copy2(json_file, target_path)
                print_status(f"[{i}/{len(json_files)}] �Ѹ���: {json_file.name}")
                transferred_count += 1
                
            except Exception as e:
                print_status(f"����ʧ�� {json_file.name}: {str(e)}", "error")
        
        print_status(f"ת����ɣ���ת�� {transferred_count}/{len(json_files)} ���ļ�", "success")
        return True
    
    def deduplicate_json_files(self):
        """ȥ�ظ�JSON�ļ�"""
        print_status("��ʼȥ�ظ�JSON�ļ�...", "title")
        print_status(f"Ŀ��Ŀ¼: {self.target_dir}")
        
        # ���Ŀ¼�Ƿ����
        if not self.target_dir.exists():
            print_status(f"Ŀ��Ŀ¼������: {self.target_dir}", "error")
            print_status("����ʹ��ѡ��5�޸�·������", "warning")
            return False
        
        # ����JSON�ļ�
        json_files = list(self.target_dir.glob("*.json"))
        
        if not json_files:
            print_status("Ŀ��Ŀ¼��û���ҵ�JSON�ļ�", "warning")
            return True
        
        print_status(f"�ҵ� {len(json_files)} ��JSON�ļ�")
        
        # ��ǰ׺����
        file_groups = {}
        
        for json_file in json_files:
            try:
                prefix = extract_file_prefix(json_file.name)
                create_time = json_file.stat().st_ctime
                create_datetime = datetime.fromtimestamp(create_time)
                
                file_info = {
                    'path': json_file,
                    'name': json_file.name,
                    'prefix': prefix,
                    'create_time': create_time,
                    'create_datetime': create_datetime
                }
                
                if prefix not in file_groups:
                    file_groups[prefix] = []
                
                file_groups[prefix].append(file_info)
                
            except Exception as e:
                print_status(f"�����ļ� {json_file.name} ʱ����: {str(e)}", "error")
        
        # �ҳ����ظ��ķ���
        duplicate_groups = {prefix: files for prefix, files in file_groups.items() 
                          if prefix and len(files) > 1}
        
        if not duplicate_groups:
            print_status("û���ҵ��ظ���JSON�ļ�", "success")
            return True
        
        print_status(f"���� {len(duplicate_groups)} ���ظ��ļ�", "title")
        
        # ��ʾ�ظ��ļ�Ԥ��
        for prefix, files in duplicate_groups.items():
            print(f"\n���� '{prefix}': {len(files)} ���ļ�")
            files.sort(key=lambda x: x['create_time'], reverse=True)
            for i, file_info in enumerate(files, 1):
                status = "����" if i == 1 else "ɾ��"
                print(f"  {i}. [{status}] {file_info['name']} (������: {file_info['create_datetime']})")
        
        # ѯ���Ƿ����
        total_to_delete = sum(len(files)-1 for files in duplicate_groups.values())
        confirm = get_user_input(f"\nȷ��Ҫɾ�� {total_to_delete} ���ظ��ļ���? (y/n)", "y")
        if confirm.lower() != 'y':
            print_status("������ȡ��", "warning")
            return False
        
        # ɾ���ظ��ļ�
        deleted_count = 0
        for prefix, files in duplicate_groups.items():
            # ������ʱ���������µ���ǰ��
            files.sort(key=lambda x: x['create_time'], reverse=True)
            
            # �������µ��ļ���ɾ��������
            for file_info in files[1:]:
                try:
                    file_info['path'].unlink()  # ɾ���ļ�
                    print_status(f"��ɾ��: {file_info['name']}")
                    deleted_count += 1
                except Exception as e:
                    print_status(f"ɾ��ʧ�� {file_info['name']}: {str(e)}", "error")
        
        remaining_files = len(json_files) - deleted_count
        
        print_status(f"ȥ�ظ���ɣ�", "success")
        print_status(f"ɾ���� {deleted_count} ���ظ��ļ�", "success")
        print_status(f"ʣ�� {remaining_files} ���ļ�", "success")
        
        return True
    
    def transfer_and_deduplicate(self):
        """��ת����ȥ�ظ�"""
        print_status("ִ��ת�Ʋ�ȥ�ظ�����", "title")
        
        # ��һ����ת��
        print_status("��һ����ת��JSON�ļ�", "title")
        if not self.transfer_json_files():
            print_status("ת��ʧ�ܣ�����ȥ�ظ�����", "error")
            return False
        
        # �ڶ�����ȥ�ظ�
        print_status("�ڶ�����ȥ�ظ�JSON�ļ�", "title")
        if not self.deduplicate_json_files():
            print_status("ȥ�ظ�ʧ��", "error")
            return False
        
        print_status("���в�����ɣ�", "success")
        return True

def main():
    # �����ļ�������ʵ��
    manager = JSONFileManager()
    
    while True:
        print_banner()
        print_menu()
        
        try:
            choice = input("������ѡ�� (0-5): ").strip()
            
            if choice == '0':
                print_status("��лʹ�ã��ټ���", "success")
                break
            
            elif choice == '1':
                manager.transfer_json_files()
            
            elif choice == '2':
                manager.deduplicate_json_files()
            
            elif choice == '3':
                manager.transfer_and_deduplicate()
            
            elif choice == '4':
                manager.show_current_config()
            
            elif choice == '5':
                manager.modify_config()
            
            else:
                print_status("��Ч��ѡ��������0-5֮�������", "error")
        
        except KeyboardInterrupt:
            print_status("\n�������û��ж�", "warning")
            break
        except Exception as e:
            print_status(f"�������г���: {str(e)}", "error")
        
        # �ȴ��û���Enter����
        input("\n��Enter������...")

if __name__ == "__main__":
    main()