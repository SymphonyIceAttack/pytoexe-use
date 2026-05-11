import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json

os.makedirs('data', exist_ok=True)

class App:
    def __init__(self, root):
        self.root = root
        self.root.title('厦门地铁通风空调系统培训平台')
        self.root.geometry('1200x800')
        
        self.is_admin = False
        self.current_page = 'home'
        self.panorama_path = ''
        
        self.load_config()
        self.init_ui()
    
    def load_config(self):
        config_path = 'data/config.json'
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            if 'panorama_path' in self.config:
                self.panorama_path = self.config['panorama_path']
        else:
            self.config = {
                "admin": {"username": "123", "password": "123"},
                "files": [],
                "devices": [],
                "work_condition_images": {},
                "panorama_path": ""
            }
    
    def save_config(self):
        with open('data/config.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def init_ui(self):
        self.init_top_bar()
        self.init_status_bar()
        
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, side=tk.BOTTOM)
        
        self.left_panel = tk.Frame(self.main_frame, width=240, bg='#f0f0f0')
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y)
        self.left_panel.pack_propagate(False)
        
        self.right_panel = tk.Frame(self.main_frame)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.init_left_panel()
        self.init_right_panel()
    
    def init_left_panel(self):
        title_label = tk.Label(self.left_panel, text='规章材料', font=('Arial', 14, 'bold'))
        title_label.pack(pady=10)
        
        self.add_file_btn = tk.Button(self.left_panel, text='添加文件', command=self.add_file)
        self.add_file_btn.pack(pady=5)
        self.add_file_btn.config(state=tk.DISABLED)
        
        self.file_list = tk.Listbox(self.left_panel)
        self.file_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.file_list.bind('<Double-1>', self.open_file)
        self.file_list.bind('<Button-3>', self.show_file_menu)
        
        self.load_files()
    
    def load_files(self):
        self.file_list.delete(0, tk.END)
        for file in self.config['files']:
            self.file_list.insert(tk.END, file['name'])
    
    def add_file(self):
        files = filedialog.askopenfilenames(filetypes=[('文档文件', '*.pdf *.doc *.docx *.xls *.xlsx')])
        for file_path in files:
            if file_path:
                file_name = os.path.basename(file_path)
                file_ext = os.path.splitext(file_name)[1].lower()
                file_info = {
                    'id': str(hash(file_path + str(os.path.getctime(file_path)))),
                    'name': file_name,
                    'path': file_path,
                    'type': file_ext[1:].upper()
                }
                self.config['files'].append(file_info)
        self.save_config()
        self.load_files()
    
    def show_file_menu(self, event):
        if not self.is_admin:
            return
        index = self.file_list.nearest(event.y)
        if index >= 0:
            self.file_list.selection_clear(0, tk.END)
            self.file_list.selection_set(index)
            
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label='删除', command=self.delete_file)
            menu.post(event.x_root, event.y_root)
    
    def delete_file(self):
        selected = self.file_list.curselection()
        if selected:
            index = selected[0]
            file_info = self.config['files'][index]
            if messagebox.askyesno('确认删除', f'确定删除 "{file_info["name"]}" 吗？'):
                del self.config['files'][index]
                self.save_config()
                self.load_files()
    
    def open_file(self, event):
        selected = self.file_list.curselection()
        if selected:
            index = selected[0]
            file_path = self.config['files'][index]['path']
            os.startfile(file_path)
    
    def init_right_panel(self):
        self.page_frame = tk.Frame(self.right_panel)
        self.page_frame.pack(fill=tk.BOTH, expand=True)
        
        self.show_home_page()
    
    def init_status_bar(self):
        self.status_bar = tk.Frame(self.root, bd=1, relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = tk.Label(self.status_bar, text='当前身份：用户', bd=1)
        self.status_label.pack(side=tk.LEFT, padx=10)
    
    def init_top_bar(self):
        self.top_bar = tk.Frame(self.root, bd=1, relief=tk.RAISED)
        self.top_bar.pack(side=tk.TOP, fill=tk.X)
        
        title_label = tk.Label(self.top_bar, text='厦门地铁通风空调系统培训平台', font=('Arial', 12, 'bold'))
        title_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        self.login_btn = tk.Button(self.top_bar, text='登录', command=self.login)
        self.login_btn.pack(side=tk.RIGHT, padx=10, pady=5)
    
    def login(self):
        try:
            print(f"Admin config: {self.config.get('admin', {})}")
            dialog = LoginDialog(self.root)
            if dialog.result:
                self.is_admin = True
                self.status_label.config(text='当前身份：管理员')
                self.login_btn.config(text='退出', command=self.logout)
                self.add_file_btn.config(state=tk.NORMAL)
                if hasattr(self, 'wc_add_btn'):
                    self.wc_add_btn.config(state=tk.NORMAL)
                if hasattr(self, 'wc_replace_btn'):
                    self.wc_replace_btn.config(state=tk.NORMAL)
                if hasattr(self, 'wc_delete_btn'):
                    self.wc_delete_btn.config(state=tk.NORMAL)
                if hasattr(self, 'dl_add_marker_btn'):
                    self.dl_add_marker_btn.config(state=tk.NORMAL)
                if hasattr(self, 'dl_upload_btn'):
                    self.dl_upload_btn.config(state=tk.NORMAL)
                if hasattr(self, 'dl_edit_btn'):
                    self.dl_edit_btn.config(state=tk.NORMAL)
                messagebox.showinfo('登录成功', '已成功登录管理员账户')
        except Exception as e:
            messagebox.showerror('登录错误', f'登录过程中发生错误：{str(e)}')
            print(f'Login error: {e}')
    
    def logout(self):
        self.is_admin = False
        self.status_label.config(text='当前身份：用户')
        self.login_btn.config(text='登录', command=self.login)
        self.add_file_btn.config(state=tk.DISABLED)
        if hasattr(self, 'wc_add_btn'):
            self.wc_add_btn.config(state=tk.DISABLED)
        if hasattr(self, 'wc_replace_btn'):
            self.wc_replace_btn.config(state=tk.DISABLED)
        if hasattr(self, 'wc_delete_btn'):
            self.wc_delete_btn.config(state=tk.DISABLED)
        if hasattr(self, 'dl_add_marker_btn'):
            self.dl_add_marker_btn.config(state=tk.DISABLED)
        if hasattr(self, 'dl_upload_btn'):
            self.dl_upload_btn.config(state=tk.DISABLED)
        if hasattr(self, 'dl_edit_btn'):
            self.dl_edit_btn.config(state=tk.DISABLED)
    
    def show_home_page(self):
        self.clear_page()
        self.current_page = 'home'
        
        home_frame = tk.Frame(self.page_frame)
        home_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = tk.Label(home_frame, text='厦门地铁通风空调系统培训平台', font=('Arial', 24, 'bold'))
        title_label.pack(pady=20)
        
        subtitle_label = tk.Label(home_frame, text='首页 - 线网图', font=('Arial', 16))
        subtitle_label.pack(pady=10)
        
        map_area = tk.Frame(home_frame, bg='#f5f5f5', relief=tk.SUNKEN, bd=1)
        map_area.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        map_label = tk.Label(map_area, text='线网图区域（暂为空，后续提供材料）', bg='#f5f5f5', fg='#999')
        map_label.pack(pady=100)
        
        btn_frame = tk.Frame(home_frame)
        btn_frame.pack(pady=20)
        
        wc_btn = tk.Button(btn_frame, text='工况示例', width=15, height=2, font=('Arial', 14), command=self.show_work_condition_page)
        wc_btn.pack(side=tk.LEFT, padx=20)
        
        dl_btn = tk.Button(btn_frame, text='现场设备学习', width=15, height=2, font=('Arial', 14), command=self.show_device_learning_page)
        dl_btn.pack(side=tk.RIGHT, padx=20)
    
    def show_work_condition_page(self):
        self.clear_page()
        self.current_page = 'work_condition'
        
        wc_frame = tk.Frame(self.page_frame)
        wc_frame.pack(fill=tk.BOTH, expand=True)
        
        top_bar = tk.Frame(wc_frame)
        top_bar.pack(fill=tk.X, pady=10)
        
        back_btn = tk.Button(top_bar, text='返回首页', command=self.show_home_page)
        back_btn.pack(side=tk.LEFT, padx=10)
        
        title_label = tk.Label(top_bar, text='工况示例', font=('Arial', 18, 'bold'))
        title_label.pack(side=tk.TOP, pady=10)
        
        systems = ['通风大系统', '通风小系统', '空调水系统', '隧道通风系统']
        conditions = ['全新风工况', '小新风工况', '通风季工况', '火灾工况']
        
        self.current_system = ''
        self.current_condition = ''
        
        system_frame = tk.Frame(wc_frame)
        system_frame.pack(fill=tk.X, pady=10)
        
        self.system_buttons = []
        for system in systems:
            btn = tk.Button(system_frame, text=system, width=15, command=lambda s=system: self.select_system(s))
            btn.pack(side=tk.LEFT, padx=5)
            self.system_buttons.append(btn)
        
        condition_frame = tk.Frame(wc_frame)
        condition_frame.pack(fill=tk.X, pady=10)
        
        self.condition_buttons = []
        for condition in conditions:
            btn = tk.Button(condition_frame, text=condition, width=15, command=lambda c=condition: self.select_condition(c))
            btn.pack(side=tk.LEFT, padx=5)
            self.condition_buttons.append(btn)
        
        self.image_frame = tk.Frame(wc_frame, bg='#f5f5f5', relief=tk.SUNKEN, bd=1)
        self.image_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        btn_frame = tk.Frame(self.image_frame)
        btn_frame.pack(fill=tk.X, pady=5, padx=5)
        
        self.wc_add_btn = tk.Button(btn_frame, text='添加图片', command=self.add_wc_image, state=tk.DISABLED)
        self.wc_add_btn.pack(side=tk.LEFT, padx=5)
        
        self.wc_replace_btn = tk.Button(btn_frame, text='更换图片', command=self.replace_wc_image, state=tk.DISABLED)
        self.wc_replace_btn.pack(side=tk.LEFT, padx=5)
        
        self.wc_delete_btn = tk.Button(btn_frame, text='删除图片', command=self.delete_wc_image, state=tk.DISABLED)
        self.wc_delete_btn.pack(side=tk.LEFT, padx=5)
        
        self.image_label = tk.Label(self.image_frame, text='请选择工况组合', bg='#f5f5f5', fg='#999')
        self.image_label.pack(fill=tk.BOTH, expand=True, pady=5)
        
        if self.is_admin:
            self.wc_add_btn.config(state=tk.NORMAL)
    
    def select_system(self, system):
        self.current_system = system
        for btn in self.system_buttons:
            if btn['text'] == system:
                btn.config(bg='#4a90d9', fg='white')
            else:
                btn.config(bg='SystemButtonFace', fg='black')
        self.update_wc_image()
    
    def select_condition(self, condition):
        self.current_condition = condition
        for btn in self.condition_buttons:
            if btn['text'] == condition:
                btn.config(bg='#4a90d9', fg='white')
            else:
                btn.config(bg='SystemButtonFace', fg='black')
        self.update_wc_image()
    
    def update_wc_image(self):
        if self.current_system and self.current_condition:
            images = self.config.get('work_condition_images', {})
            image_path = images.get(self.current_system, {}).get(self.current_condition, '')
            if image_path and os.path.exists(image_path):
                try:
                    from PIL import Image, ImageTk
                    
                    img = Image.open(image_path)
                    target_width = self.image_frame.winfo_width() - 40
                    target_height = self.image_frame.winfo_height() - 80
                    
                    if hasattr(self, 'gif_animation_id'):
                        self.root.after_cancel(self.gif_animation_id)
                    
                    if img.format == 'GIF' and img.n_frames > 1:
                        self.gif_frames = []
                        self.gif_frame_index = 0
                        
                        for i in range(img.n_frames):
                            img.seek(i)
                            frame = img.copy()
                            frame = frame.resize((target_width, target_height), Image.Resampling.LANCZOS)
                            self.gif_frames.append(ImageTk.PhotoImage(frame))
                        
                        self.image_label.config(image=self.gif_frames[0], text='')
                        self.image_label.image = self.gif_frames[0]
                        self.gif_animation_id = self.root.after(100, self.play_gif)
                    else:
                        img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        self.image_label.config(image=photo, text='')
                        self.image_label.image = photo
                    
                    if self.is_admin:
                        self.wc_add_btn.config(state=tk.DISABLED)
                        self.wc_replace_btn.config(state=tk.NORMAL)
                        self.wc_delete_btn.config(state=tk.NORMAL)
                except Exception as e:
                    print(f"Error loading image: {e}")
                    self.image_label.config(text=f'{self.current_system} - {self.current_condition}\n图片加载失败', image='')
                    if self.is_admin:
                        self.wc_add_btn.config(state=tk.NORMAL)
                        self.wc_replace_btn.config(state=tk.DISABLED)
                        self.wc_delete_btn.config(state=tk.DISABLED)
            else:
                self.image_label.config(text=f'{self.current_system} - {self.current_condition}\n（暂无图片）', image='')
                if self.is_admin:
                    self.wc_add_btn.config(state=tk.NORMAL)
    
    def play_gif(self):
        if hasattr(self, 'gif_frames') and len(self.gif_frames) > 0:
            self.gif_frame_index = (self.gif_frame_index + 1) % len(self.gif_frames)
            self.image_label.config(image=self.gif_frames[self.gif_frame_index])
            self.image_label.image = self.gif_frames[self.gif_frame_index]
            self.gif_animation_id = self.root.after(100, self.play_gif)
    
    def add_wc_image(self):
        if not self.current_system or not self.current_condition:
            messagebox.showwarning('提示', '请先选择系统和工况')
            return
        
        file_path = filedialog.askopenfilename(filetypes=[('图片文件', '*.jpg *.jpeg *.png *.gif *.bmp')])
        if file_path:
            if 'work_condition_images' not in self.config:
                self.config['work_condition_images'] = {}
            if self.current_system not in self.config['work_condition_images']:
                self.config['work_condition_images'][self.current_system] = {}
            self.config['work_condition_images'][self.current_system][self.current_condition] = file_path
            self.save_config()
            self.update_wc_image()
            messagebox.showinfo('成功', '图片添加成功')
    
    def replace_wc_image(self):
        if not self.current_system or not self.current_condition:
            messagebox.showwarning('提示', '请先选择系统和工况')
            return
        
        current_path = self.config.get('work_condition_images', {}).get(self.current_system, {}).get(self.current_condition, '')
        
        file_path = filedialog.askopenfilename(filetypes=[('图片文件', '*.jpg *.jpeg *.png *.gif *.bmp')], initialdir=os.path.dirname(current_path) if current_path else None)
        if file_path:
            if 'work_condition_images' not in self.config:
                self.config['work_condition_images'] = {}
            if self.current_system not in self.config['work_condition_images']:
                self.config['work_condition_images'][self.current_system] = {}
            self.config['work_condition_images'][self.current_system][self.current_condition] = file_path
            self.save_config()
            self.update_wc_image()
            messagebox.showinfo('成功', '图片更换成功')
    
    def delete_wc_image(self):
        if not self.current_system or not self.current_condition:
            messagebox.showwarning('提示', '请先选择系统和工况')
            return
        
        if messagebox.askyesno('确认删除', '确定要删除该图片吗？'):
            if 'work_condition_images' in self.config:
                if self.current_system in self.config['work_condition_images']:
                    if self.current_condition in self.config['work_condition_images'][self.current_system]:
                        del self.config['work_condition_images'][self.current_system][self.current_condition]
                        self.save_config()
                        self.update_wc_image()
                        messagebox.showinfo('成功', '图片删除成功')
    
    def show_device_learning_page(self):
        self.clear_page()
        self.current_page = 'device_learning'
        
        dl_frame = tk.Frame(self.page_frame)
        dl_frame.pack(fill=tk.BOTH, expand=True)
        
        top_bar = tk.Frame(dl_frame)
        top_bar.pack(fill=tk.X, pady=10)
        
        back_btn = tk.Button(top_bar, text='返回首页', command=self.show_home_page)
        back_btn.pack(side=tk.LEFT, padx=10)
        
        title_label = tk.Label(top_bar, text='现场设备学习', font=('Arial', 18, 'bold'))
        title_label.pack(side=tk.TOP, pady=10)
        
        self.dl_add_marker_btn = tk.Button(top_bar, text='添加标点', command=self.add_device_marker, state=tk.DISABLED)
        self.dl_add_marker_btn.pack(side=tk.RIGHT, padx=5)
        
        self.dl_upload_btn = tk.Button(top_bar, text='上传全景图', command=self.upload_panorama, state=tk.DISABLED)
        self.dl_upload_btn.pack(side=tk.RIGHT, padx=5)
        
        content_frame = tk.Frame(dl_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        self.device_info_panel = tk.Frame(content_frame, width=240, bg='#f8f8f8')
        self.device_info_panel.pack(side=tk.LEFT, fill=tk.Y)
        self.device_info_panel.pack_propagate(False)
        
        self.device_name_label = tk.Label(self.device_info_panel, text='设备名称', font=('Arial', 14, 'bold'))
        self.device_name_label.pack(pady=10)
        
        self.device_image_label = tk.Label(self.device_info_panel, bg='white', width=150, height=150, relief=tk.SUNKEN)
        self.device_image_label.pack(pady=10)
        self.device_image_label.config(text='暂无图片')
        
        self.device_desc_label = tk.Label(self.device_info_panel, text='设备介绍')
        self.device_desc_label.pack(pady=5)
        
        self.device_desc_text = tk.Text(self.device_info_panel, height=10, wrap=tk.WORD)
        self.device_desc_text.pack(fill=tk.BOTH, expand=True, padx=5)
        self.device_desc_text.insert(tk.END, '点击图片上的设备标点查看详情')
        self.device_desc_text.config(state=tk.DISABLED)
        
        self.dl_edit_btn = tk.Button(self.device_info_panel, text='编辑设备信息', command=self.edit_device, state=tk.DISABLED)
        self.dl_edit_btn.pack(pady=10)
        
        self.panorama_panel = tk.Frame(content_frame, bg='#f5f5f5', relief=tk.SUNKEN, bd=1)
        self.panorama_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.panorama_canvas = tk.Canvas(self.panorama_panel, bg='#f5f5f5')
        self.panorama_canvas.pack(fill=tk.BOTH, expand=True)
        self.panorama_canvas.create_text(400, 200, text='设备房全景图片区域（管理员可上传）', fill='#999')
        
        self.panorama_canvas.bind('<Button-1>', self.on_panorama_click)
        self.panorama_canvas.bind('<Button-3>', self.on_panorama_right_click)
        
        self.markers = []
        for device in self.config.get('devices', []):
            if 'x' in device and 'y' in device and 'id' in device:
                self.markers.append({'x': device['x'], 'y': device['y'], 'device_id': device['id']})
        
        if self.is_admin:
            self.dl_add_marker_btn.config(state=tk.NORMAL)
            self.dl_upload_btn.config(state=tk.NORMAL)
            self.dl_edit_btn.config(state=tk.NORMAL)
        
        if hasattr(self, 'panorama_path') and self.panorama_path:
            self.root.after(100, self.load_panorama_image)
    
    def upload_panorama(self):
        file_path = filedialog.askopenfilename(filetypes=[('图片文件', '*.jpg *.jpeg *.png *.gif *.bmp')])
        if file_path:
            self.panorama_path = file_path
            self.config['panorama_path'] = file_path
            self.save_config()
            self.load_panorama_image()
            messagebox.showinfo('成功', '全景图上传成功')
    
    def load_panorama_image(self):
        if self.panorama_path and os.path.exists(self.panorama_path):
            try:
                from PIL import Image, ImageTk
                img = Image.open(self.panorama_path)
                img = img.resize((self.panorama_panel.winfo_width()-20, self.panorama_panel.winfo_height()-20), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.panorama_canvas.delete('all')
                self.panorama_canvas.create_image(10, 10, image=photo, anchor=tk.NW)
                self.panorama_canvas.photo = photo
                self.draw_markers()
            except Exception as e:
                print(f"Error loading panorama: {e}")
    
    def draw_markers(self):
        for marker in self.markers:
            x, y = marker['x'], marker['y']
            self.panorama_canvas.create_oval(x-8, y-8, x+8, y+8, outline='white', width=2, fill='')
    
    def on_panorama_click(self, event):
        x, y = event.x, event.y
        for marker in self.markers:
            distance = ((x - marker['x']) ** 2 + (y - marker['y']) ** 2) ** 0.5
            if distance < 15:
                self.select_device(marker['device_id'])
                return
    
    def on_panorama_right_click(self, event):
        if not self.is_admin:
            return
        
        x, y = event.x, event.y
        nearby_marker = None
        
        for marker in self.markers:
            distance = ((x - marker['x']) ** 2 + (y - marker['y']) ** 2) ** 0.5
            if distance < 15:
                nearby_marker = marker
                break
        
        menu = tk.Menu(self.root, tearoff=0)
        
        if nearby_marker:
            menu.add_command(label='删除标点', command=lambda: self.delete_marker(nearby_marker))
        else:
            menu.add_command(label='添加设备标点', command=lambda: self.show_add_marker_dialog(event.x, event.y))
        
        menu.post(event.x_root, event.y_root)
    
    def delete_marker(self, marker):
        if messagebox.askyesno('确认删除', '确定要删除此标点及其绑定的设备信息吗？'):
            self.markers = [m for m in self.markers if m['device_id'] != marker['device_id']]
            
            self.config['devices'] = [d for d in self.config['devices'] if d['id'] != marker['device_id']]
            
            self.save_config()
            
            self.panorama_canvas.delete('all')
            if hasattr(self, 'panorama_path') and self.panorama_path and os.path.exists(self.panorama_path):
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(self.panorama_path)
                    img = img.resize((self.panorama_panel.winfo_width()-20, self.panorama_panel.winfo_height()-20), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.panorama_canvas.create_image(10, 10, image=photo, anchor=tk.NW)
                    self.panorama_canvas.photo = photo
                except:
                    pass
            
            self.draw_markers()
            
            self.device_name_label.config(text='')
            self.device_image_label.config(image='', text='暂无图片')
            if hasattr(self, 'device_photo'):
                del self.device_photo
            self.device_desc_text.config(state=tk.NORMAL)
            self.device_desc_text.delete(1.0, tk.END)
            self.device_desc_text.insert(tk.END, '点击图片上的设备标点查看详情')
            self.device_desc_text.config(state=tk.DISABLED)
    
    def add_device_marker(self):
        self.show_add_marker_dialog(100, 100)
    
    def show_add_marker_dialog(self, x, y):
        dialog = AddMarkerDialog(self.root, x, y, self)
    
    def select_device(self, device_id):
        device = next((d for d in self.config['devices'] if d['id'] == device_id), None)
        if device:
            self.device_name_label.config(text=device['name'])
            self.device_desc_text.config(state=tk.NORMAL)
            self.device_desc_text.delete(1.0, tk.END)
            self.device_desc_text.insert(tk.END, device.get('description', ''))
            self.device_desc_text.config(state=tk.DISABLED)
            
            if device.get('image_path') and os.path.exists(device['image_path']):
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(device['image_path'])
                    img = img.resize((150, 150), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.device_image_label.config(image=photo, text='')
                    self.device_image_label.image = photo
                except:
                    self.device_image_label.config(text='图片加载失败', image='')
            else:
                self.device_image_label.config(text='暂无图片', image='')
    
    def edit_device(self):
        device_name = self.device_name_label.cget('text')
        if device_name == '设备名称':
            messagebox.showwarning('提示', '请先选择一个设备')
            return
        
        device = next((d for d in self.config['devices'] if d['name'] == device_name), None)
        if device:
            dialog = AddMarkerDialog(self.root, device.get('x', 0), device.get('y', 0), self, device)
    
    def clear_page(self):
        for widget in self.page_frame.winfo_children():
            widget.destroy()

class LoginDialog:
    def __init__(self, parent):
        self.parent = parent
        self.result = False
        self.dialog = None
        
        try:
            self.dialog = tk.Toplevel(parent)
            self.dialog.title('管理员登录')
            self.dialog.geometry('300x180')
            self.dialog.transient(parent)
            self.dialog.grab_set()
            
            main_frame = tk.Frame(self.dialog)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            tk.Label(main_frame, text='账号：').pack(anchor=tk.W, pady=(0, 5))
            self.username_entry = tk.Entry(main_frame, width=30)
            self.username_entry.pack(fill=tk.X, pady=(0, 10))
            
            tk.Label(main_frame, text='密码：').pack(anchor=tk.W, pady=(0, 5))
            self.password_entry = tk.Entry(main_frame, show='*', width=30)
            self.password_entry.pack(fill=tk.X, pady=(0, 15))
            
            btn_frame = tk.Frame(main_frame)
            btn_frame.pack(fill=tk.X)
            
            self.login_btn = tk.Button(btn_frame, text='登录', command=self.login, width=10)
            self.login_btn.pack(side=tk.RIGHT, padx=5)
            
            cancel_btn = tk.Button(btn_frame, text='取消', command=self.cancel, width=10)
            cancel_btn.pack(side=tk.RIGHT)
            
            self.dialog.protocol('WM_DELETE_WINDOW', self.cancel)
            
            self.username_entry.focus_set()
            
            self.dialog.wait_window()
            
        except Exception as e:
            messagebox.showerror('错误', f'创建登录对话框失败：{str(e)}')
            print(f'Login dialog error: {e}')
    
    def login(self):
        try:
            username = self.username_entry.get().strip()
            password = self.password_entry.get().strip()
            
            if username == '123' and password == '123':
                self.result = True
                if self.dialog:
                    self.dialog.grab_release()
                    self.dialog.destroy()
            else:
                messagebox.showwarning('登录失败', '账号或密码错误\n账号：123\n密码：123')
        except Exception as e:
            messagebox.showerror('登录错误', f'登录验证失败：{str(e)}')
    
    def cancel(self):
        if self.dialog:
            self.dialog.grab_release()
            self.dialog.destroy()

class AddMarkerDialog:
    def __init__(self, parent, x, y, app, device=None):
        self.parent = parent
        self.app = app
        self.x = x
        self.y = y
        self.device = device
        self.image_path = ''
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title('添加/编辑设备标点')
        self.dialog.geometry('350x350')
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        tk.Label(self.dialog, text='设备名称：').pack(pady=5)
        self.name_entry = tk.Entry(self.dialog)
        self.name_entry.pack(pady=5)
        
        tk.Button(self.dialog, text='选择设备图片', command=self.select_image).pack(pady=5)
        
        tk.Label(self.dialog, text='设备介绍：').pack(pady=5)
        self.desc_text = tk.Text(self.dialog, height=5, wrap=tk.WORD)
        self.desc_text.pack(fill=tk.X, padx=10)
        
        btn_frame = tk.Frame(self.dialog)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text='确定', command=self.ok).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text='取消', command=self.cancel).pack(side=tk.RIGHT, padx=10)
        
        if device:
            self.name_entry.insert(tk.END, device['name'])
            self.desc_text.insert(tk.END, device.get('description', ''))
            self.image_path = device.get('image_path', '')
    
    def select_image(self):
        file_path = filedialog.askopenfilename(filetypes=[('图片文件', '*.jpg *.jpeg *.png *.gif *.bmp')])
        if file_path:
            self.image_path = file_path
    
    def ok(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning('提示', '请输入设备名称')
            return
        
        description = self.desc_text.get(1.0, tk.END).strip()
        
        if self.device:
            device_info = {
                'id': self.device['id'],
                'name': name,
                'description': description,
                'image_path': self.image_path if self.image_path else self.device.get('image_path', ''),
                'x': self.x,
                'y': self.y
            }
            index = next((i for i, d in enumerate(self.app.config['devices']) if d['id'] == self.device['id']), -1)
            if index >= 0:
                self.app.config['devices'][index] = device_info
        else:
            device_info = {
                'id': str(hash(name + str(self.x) + str(self.y))),
                'name': name,
                'description': description,
                'image_path': self.image_path,
                'x': self.x,
                'y': self.y
            }
            self.app.config['devices'].append(device_info)
            self.app.markers.append({'x': self.x, 'y': self.y, 'device_id': device_info['id']})
        
        self.app.save_config()
        self.app.draw_markers()
        self.dialog.destroy()
        messagebox.showinfo('成功', '设备信息保存成功')
    
    def cancel(self):
        self.dialog.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()
