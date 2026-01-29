import os
import shutil
import re
import json
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

class FileManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JSON�ļ���������")
        self.root.geometry("500x300")
        
        # ������ʽ
        style = ttk.Style()
        style.theme_use('clam')
        
        # �����
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ����
        title_label = ttk.Label(main_frame, text="JSON�ļ�������", 
                               font=("΢���ź�", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # ��ť���
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # ת�����ذ�ť
        self.transfer_btn = ttk.Button(
            button_frame, 
            text="ת������JSON�ļ�", 
            command=self.transfer_json_files,
            width=25
        )
        self.transfer_btn.pack(pady=10)
        
        # ȥ�ظ���ť
        self.deduplicate_btn = ttk.Button(
            button_frame, 
            text="ȥ�ظ�JSON�ļ�", 
            command=self.deduplicate_json_files,
            width=25
        )
        self.deduplicate_btn.pack(pady=10)
        
        # ��־�ı���
        log_label = ttk.Label(main_frame, text="������־:", font=("΢���ź�", 10))
        log_label.pack(anchor=tk.W, pady=(20, 5))
        
        # ����������
        log_frame = ttk.Frame(main_frame)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_frame, height=8, width=50, 
                               font=("Consolas", 9), wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ״̬��
        self.status_var = tk.StringVar(value="����")
        status_bar = ttk.Label(root, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # ·������
        self.source_dir = Path("D:/Backup/Downloads")
        self.target_dir = Path("E:/youxix/databak")
        
        # ���Ŀ¼�Ƿ����
        self.check_directories()
    
    def check_directories(self):
        """���Ŀ¼�Ƿ����"""
        if not self.source_dir.exists():
            self.log_message(f"����: ԴĿ¼������ - {self.source_dir}")
        if not self.target_dir.exists():
            self.log_message(f"����: Ŀ��Ŀ¼������ - {self.target_dir}")
    
    def log_message(self, message):
        """������־��Ϣ"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.root.update()
    
    def transfer_json_files(self):
        """ת��JSON�ļ�"""
        try:
            self.status_var.set("����ת���ļ�...")
            self.transfer_btn.configure(state=tk.DISABLED)
            
            if not self.source_dir.exists():
                messagebox.showerror("����", f"ԴĿ¼������:\n{self.source_dir}")
                return
            
            if not self.target_dir.exists():
                self.target_dir.mkdir(parents=True, exist_ok=True)
                self.log_message(f"�Ѵ���Ŀ��Ŀ¼: {self.target_dir}")
            
            json_files = list(self.source_dir.glob("*.json"))
            
            if not json_files:
                self.log_message("δ�ҵ�JSON�ļ�")
                messagebox.showinfo("��ʾ", "ԴĿ¼��û��JSON�ļ�")
                return
            
            transferred_count = 0
            for json_file in json_files:
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
                    self.log_message(f"�Ѹ���: {json_file.name}")
                    transferred_count += 1
                    
                except Exception as e:
                    self.log_message(f"����ʧ�� {json_file.name}: {str(e)}")
            
            self.log_message(f"ת����ɣ���ת�� {transferred_count}/{len(json_files)} ���ļ�")
            messagebox.showinfo("���", f"�ɹ�ת�� {transferred_count} ��JSON�ļ�")
            
        except Exception as e:
            self.log_message(f"ת�ƹ��̳���: {str(e)}")
            messagebox.showerror("����", f"ת���ļ�ʱ����:\n{str(e)}")
        finally:
            self.status_var.set("����")
            self.transfer_btn.configure(state=tk.NORMAL)
    
    def extract_file_prefix(self, filename):
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
    
    def deduplicate_json_files(self):
        """ȥ�ظ�JSON�ļ�"""
        try:
            self.status_var.set("����ȥ�ظ�...")
            self.deduplicate_btn.configure(state=tk.DISABLED)
            
            if not self.target_dir.exists():
                messagebox.showerror("����", f"Ŀ��Ŀ¼������:\n{self.target_dir}")
                return
            
            json_files = list(self.target_dir.glob("*.json"))
            
            if not json_files:
                self.log_message("Ŀ��Ŀ¼��û��JSON�ļ�")
                messagebox.showinfo("��ʾ", "Ŀ��Ŀ¼��û��JSON�ļ�")
                return
            
            # ��ǰ׺����
            file_groups = {}
            file_info_list = []
            
            for json_file in json_files:
                try:
                    prefix = self.extract_file_prefix(json_file.name)
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
                    file_info_list.append(file_info)
                    
                except Exception as e:
                    self.log_message(f"�����ļ� {json_file.name} ʱ����: {str(e)}")
            
            self.log_message(f"�ҵ� {len(json_files)} ��JSON�ļ�����Ϊ {len(file_groups)} ��")
            
            # ��ÿ������д���
            deleted_count = 0
            for prefix, files in file_groups.items():
                if not prefix:  # ������ǰ׺
                    continue
                
                if len(files) > 1:
                    # ������ʱ���������µ���ǰ��
                    files.sort(key=lambda x: x['create_time'], reverse=True)
                    
                    # �������µ��ļ���ɾ��������
                    for file_info in files[1:]:
                        try:
                            file_info['path'].unlink()  # ɾ���ļ�
                            self.log_message(f"��ɾ��: {file_info['name']} (������: {file_info['create_datetime']})")
                            deleted_count += 1
                        except Exception as e:
                            self.log_message(f"ɾ��ʧ�� {file_info['name']}: {str(e)}")
                    
                    self.log_message(f"�� '{prefix}': ���� {files[0]['name']} (����), ɾ�� {len(files)-1} ���ļ�")
            
            remaining_files = len(json_files) - deleted_count
            self.log_message(f"ȥ�ظ���ɣ�ɾ���� {deleted_count} ���ļ���ʣ�� {remaining_files} ���ļ�")
            messagebox.showinfo("���", f"ȥ�ظ���ɣ�\nɾ�� {deleted_count} ���ظ��ļ�\nʣ�� {remaining_files} ���ļ�")
            
        except Exception as e:
            self.log_message(f"ȥ�ظ����̳���: {str(e)}")
            messagebox.showerror("����", f"ȥ�ظ�ʱ����:\n{str(e)}")
        finally:
            self.status_var.set("����")
            self.deduplicate_btn.configure(state=tk.NORMAL)

def main():
    root = tk.Tk()
    app = FileManagerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()