#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
屏幕文字提取翻译工具
功能：使用PowerToys Text Extractor提取屏幕文字，通过豆包API翻译
作者：AI助手
日期：2026-02-24
"""

import os
import sys
import time
import json
import subprocess
import threading
import configparser
from pathlib import Path

import pyperclip
import requests
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog


class ScreenTranslator:
    """屏幕文字提取翻译工具主类"""
    
    def __init__(self):
        """初始化应用"""
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("屏幕文字提取翻译工具")
        self.root.geometry("850x600")
        self.root.minsize(800, 500)
        self.root.iconbitmap(self._get_icon_path())
        
        # 设置主题样式
        self.style = ttk.Style()
        self.style.configure("TButton", padding=6)
        self.style.configure("TLabel", padding=4)
        
        # 初始化配置
        self.config = self._load_config()
        
        # 创建界面
        self._create_widgets()
        
        # 绑定事件
        self._bind_events()
        
        # 初始化状态
        self.is_extracting = False
        self.previous_clipboard = pyperclip.paste()
    
    def _get_icon_path(self):
        """获取应用图标路径"""
        # 这里可以添加自定义图标
        return ""
    
    def _load_config(self):
        """加载配置文件"""
        config_path = Path.home() / ".screen_translator.ini"
        config = configparser.ConfigParser()
        
        # 默认配置
        default_config = {
            "api": {
                "access_key": "",
                "secret_key": "",
                "use_doubaotrans": "False"
            },
            "settings": {
                "default_target_lang": "zh",
                "auto_translate": "True",
                "save_history": "True",
                "powertoys_path": ""
            }
        }
        
        # 如果配置文件存在，读取配置
        if config_path.exists():
            config.read(config_path)
            
            # 验证配置完整性
            for section, options in default_config.items():
                if section not in config:
                    config[section] = options
                else:
                    for key, value in options.items():
                        if key not in config[section]:
                            config[section][key] = value
        else:
            # 使用默认配置
            config = default_config
            
            # 保存默认配置
            with open(config_path, 'w', encoding='utf-8') as f:
                for section, options in config.items():
                    f.write(f"[{section}]\n")
                    for key, value in options.items():
                        f.write(f"{key} = {value}\n")
                    f.write("\n")
        
        return config
    
    def _save_config(self):
        """保存配置文件"""
        config_path = Path.home() / ".screen_translator.ini"
        
        with open(config_path, 'w', encoding='utf-8') as f:
            for section, options in self.config.items():
                f.write(f"[{section}]\n")
                for key, value in options.items():
                    f.write(f"{key} = {value}\n")
                f.write("\n")
    
    def _create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建顶部按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 提取按钮
        self.extract_btn = ttk.Button(
            button_frame, 
            text="提取屏幕文字 (Win+Shift+T)", 
            command=self.start_extraction,
            style="TButton"
        )
        self.extract_btn.pack(side=tk.LEFT, padx=5)
        
        # 语言选择
        ttk.Label(button_frame, text="目标语言:").pack(side=tk.LEFT, padx=(10, 0))
        self.target_lang_var = tk.StringVar(value=self.config["settings"]["default_target_lang"])
        self.lang_combo = ttk.Combobox(
            button_frame, 
            textvariable=self.target_lang_var,
            state="readonly",
            width=10
        )
        self.lang_combo['values'] = (
            '中文(zh)', '英文(en)', '日语(ja)', '韩语(ko)', 
            '法语(fr)', '德语(de)', '俄语(ru)', '西班牙语(es)',
            '葡萄牙语(pt)', '意大利语(it)', '阿拉伯语(ar)', '荷兰语(nl)'
        )
        self.lang_combo.current(0)
        self.lang_combo.pack(side=tk.LEFT, padx=5)
        
        # 翻译按钮
        self.translate_btn = ttk.Button(
            button_frame, 
            text="翻译", 
            command=self.translate_text,
            style="TButton"
        )
        self.translate_btn.pack(side=tk.LEFT, padx=5)
        
        # 设置按钮
        self.settings_btn = ttk.Button(
            button_frame, 
            text="设置", 
            command=self.open_settings,
            style="TButton"
        )
        self.settings_btn.pack(side=tk.RIGHT, padx=5)
        
        # 创建原文显示区域
        source_frame = ttk.LabelFrame(main_frame, text="原文")
        source_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.source_text = scrolledtext.ScrolledText(
            source_frame, 
            wrap=tk.WORD, 
            font=("SimHei", 10)
        )
        self.source_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建翻译结果显示区域
        result_frame = ttk.LabelFrame(main_frame, text="翻译结果")
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        self.result_text = scrolledtext.ScrolledText(
            result_frame, 
            wrap=tk.WORD, 
            font=("SimHei", 10)
        )
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建底部状态栏
        self.status_var = tk.StringVar(value="就绪")
        self.status_bar = ttk.Label(
            self.root, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _bind_events(self):
        """绑定事件处理"""
        # 绑定Ctrl+T快捷键进行翻译
        self.root.bind("<Control-t>", lambda event: self.translate_text())
        
        # 绑定Ctrl+E快捷键进行提取
        self.root.bind("<Control-e>", lambda event: self.start_extraction())
        
        # 绑定Ctrl+S快捷键保存配置
        self.root.bind("<Control-s>", lambda event: self._save_config())
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def start_extraction(self):
        """开始屏幕文字提取"""
        if self.is_extracting:
            return
        
        self.status_var.set("正在提取屏幕文字...")
        self.root.update_idletasks()
        
        # 保存当前剪贴板内容
        self.previous_clipboard = pyperclip.paste()
        
        # 创建并启动提取线程
        self.is_extracting = True
        extraction_thread = threading.Thread(target=self._extract_text_thread)
        extraction_thread.daemon = True
        extraction_thread.start()
    
    def _extract_text_thread(self):
        """提取文字的线程函数"""
        try:
            # 最小化窗口
            self.root.iconify()
            
            # 调用PowerToys Text Extractor
            self._call_powertoys_text_extractor()
            
            # 等待用户选择区域并复制到剪贴板
            time.sleep(1)
            
            # 监控剪贴板变化
            start_time = time.time()
            timeout = 15  # 15秒超时
            
            while time.time() - start_time < timeout:
                current_clipboard = pyperclip.paste()
                if current_clipboard != self.previous_clipboard:
                    # 获取到新内容，恢复窗口
                    self.root.deiconify()
                    
                    # 更新原文文本框
                    self.source_text.delete(1.0, tk.END)
                    self.source_text.insert(tk.END, current_clipboard)
                    
                    self.status_var.set("文字提取成功")
                    self.is_extracting = False
                    
                    # 如果启用自动翻译，执行翻译
                    if self.config["settings"]["auto_translate"] == "True":
                        self.translate_text()
                    
                    return
                
                time.sleep(0.5)
            
            # 超时，恢复窗口
            self.root.deiconify()
            self.status_var.set("文字提取超时，请重试")
            self.is_extracting = False
            
        except Exception as e:
            # 发生错误，恢复窗口
            self.root.deiconify()
            self.status_var.set(f"提取出错: {str(e)}")
            self.is_extracting = False
    
    def _call_powertoys_text_extractor(self):
        """调用PowerToys Text Extractor"""
        # 检查是否配置了PowerToys路径
        powertoys_path = self.config["settings"]["powertoys_path"]
        
        if powertoys_path and os.path.exists(powertoys_path):
            # 如果配置了路径，直接调用
            try:
                subprocess.Popen([powertoys_path])
                time.sleep(1)  # 等待PowerToys启动
            except Exception as e:
                self.status_var.set(f"启动PowerToys失败: {str(e)}")
        
        # 无论是否配置了路径，都发送Win+Shift+T快捷键
        # 因为PowerToys通常需要保持运行状态
        self._send_win_shift_t()
    
    def _send_win_shift_t(self):
        """发送Win+Shift+T快捷键"""
        # 使用PowerShell发送快捷键
        powershell_command = """
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.SendKeys]::SendWait('+{LWin}T')
        """
        
        try:
            subprocess.run(
                ["powershell", "-Command", powershell_command],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            # 如果PowerShell方法失败，尝试使用其他方法
            self.status_var.set(f"发送快捷键失败: {e.stderr}")
            
            # 尝试使用ctypes (仅Windows)
            if sys.platform == 'win32':
                try:
                    import ctypes
                    from ctypes import wintypes
                    
                    # 定义键盘事件常量
                    KEYEVENTF_KEYDOWN = 0x0000
                    KEYEVENTF_KEYUP = 0x0002
                    
                    # 获取keybd_event函数
                    user32 = ctypes.WinDLL('user32', use_last_error=True)
                    keybd_event = user32.keybd_event
                    keybd_event.argtypes = [wintypes.BYTE, wintypes.BYTE, wintypes.DWORD, wintypes.ULONG_PTR]
                    
                    # 虚拟键码
                    VK_LWIN = 0x5B  # 左Windows键
                    VK_SHIFT = 0x10  # Shift键
                    VK_T = 0x54      # T键
                    
                    # 按下Win+Shift+T
                    keybd_event(VK_LWIN, 0, KEYEVENTF_KEYDOWN, 0)
                    keybd_event(VK_SHIFT, 0, KEYEVENTF_KEYDOWN, 0)
                    keybd_event(VK_T, 0, KEYEVENTF_KEYDOWN, 0)
                    
                    # 释放Win+Shift+T
                    keybd_event(VK_T, 0, KEYEVENTF_KEYUP, 0)
                    keybd_event(VK_SHIFT, 0, KEYEVENTF_KEYUP, 0)
                    keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)
                    
                except Exception as e:
                    self.status_var.set(f"使用ctypes发送快捷键也失败: {str(e)}")
    
    def translate_text(self):
        """翻译文本"""
        # 获取原文
        text = self.source_text.get(1.0, tk.END).strip()
        if not text:
            self.status_var.set("没有可翻译的文本")
            return
        
        self.status_var.set("正在翻译...")
        self.root.update_idletasks()
        
        # 获取目标语言
        target_lang = self.target_lang_var.get().split('(')[1].strip(')')
        
        # 创建并启动翻译线程
        translation_thread = threading.Thread(
            target=self._translate_thread,
            args=(text, target_lang)
        )
        translation_thread.daemon = True
        translation_thread.start()
    
    def _translate_thread(self, text, target_lang):
        """翻译线程函数"""
        try:
            # 检查API配置
            access_key = self.config["api"]["access_key"]
            secret_key = self.config["api"]["secret_key"]
            
            if not access_key or not secret_key:
                self.status_var.set("请先配置API密钥")
                return
            
            # 调用翻译API
            if self.config["api"]["use_doubaotrans"] == "True":
                # 尝试使用doubaotrans包
                try:
                    from doubao_trans import DoubaoTranslator
                    
                    translator = DoubaoTranslator(api_key=access_key)
                    result = translator.doubao_translate(text, dest=target_lang)
                    
                    translated_text = result.text
                except ImportError:
                    self.status_var.set("未安装doubaotrans包，使用默认API调用")
                    translated_text = self._call_translate_api(text, target_lang)
                except Exception as e:
                    self.status_var.set(f"使用doubaotrans出错: {str(e)}")
                    translated_text = self._call_translate_api(text, target_lang)
            else:
                # 使用直接API调用
                translated_text = self._call_translate_api(text, target_lang)
            
            # 更新翻译结果
            if translated_text:
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(tk.END, translated_text)
                self.status_var.set("翻译完成")
                
                # 如果启用历史记录，保存翻译历史
                if self.config["settings"]["save_history"] == "True":
                    self._save_translation_history(text, translated_text, target_lang)
            else:
                self.status_var.set("翻译失败")
        
        except Exception as e:
            self.status_var.set(f"翻译出错: {str(e)}")
    
    def _call_translate_api(self, text, target_lang):
        """调用豆包翻译API"""
        # 这里使用火山引擎的翻译API
        # 注意：实际使用时需要根据豆包API的最新文档进行调整
        
        access_key = self.config["api"]["access_key"]
        secret_key = self.config["api"]["secret_key"]
        
        # 构建请求参数
        url = "https://translate.volcengineapi.com"
        action = "TranslateText"
        version = "2020-06-01"
        
        # 构建请求头
        headers = {
            "Content-Type": "application/json",
            "X-Date": self._get_rfc3339_timestamp(),
            "Authorization": self._generate_signature(
                access_key, secret_key, action, version
            )
        }
        
        # 构建请求体
        body = {
            "TargetLanguage": target_lang,
            "TextList": [text]
        }
        
        try:
            # 发送请求
            response = requests.post(
                f"{url}?Action={action}&Version={version}",
                headers=headers,
                json=body,
                timeout=10
            )
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            
            if "TranslationList" in result and result["TranslationList"]:
                return result["TranslationList"][0]["Translation"]
            else:
                self.status_var.set(f"API返回格式异常: {result}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.status_var.set(f"API请求失败: {str(e)}")
            return None
    
    def _get_rfc3339_timestamp(self):
        """生成RFC3339格式的时间戳"""
        import datetime
        
        dt = datetime.datetime.utcnow()
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    def _generate_signature(self, access_key, secret_key, action, version):
        """生成API签名"""
        # 注意：这是一个简化的签名生成方法
        # 实际使用时需要根据豆包API的签名规则进行调整
        
        import hmac
        import hashlib
        
        # 构建签名字符串
        timestamp = self._get_rfc3339_timestamp()
        sign_string = f"GET\n*\n*\n{timestamp}\n/Action={action}&Version={version}"
        
        # 使用HMAC-SHA256生成签名
        signature = hmac.new(
            secret_key.encode('utf-8'),
            sign_string.encode('utf-8'),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        # 返回Authorization头
        return f"HV1 {access_key}:{signature}"
    
    def _save_translation_history(self, source_text, translated_text, target_lang):
        """保存翻译历史"""
        history_path = Path.home() / ".screen_translator_history.json"
        
        # 读取现有历史
        history = []
        if history_path.exists():
            try:
                with open(history_path, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except json.JSONDecodeError:
                history = []
        
        # 添加新记录
        history.append({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source_text": source_text,
            "translated_text": translated_text,
            "target_lang": target_lang
        })
        
        # 限制历史记录数量
        if len(history) > 100:
            history = history[-100:]
        
        # 保存历史
        try:
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史记录失败: {str(e)}")
    
    def open_settings(self):
        """打开设置对话框"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("设置")
        settings_window.geometry("500x400")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # 创建设置框架
        settings_frame = ttk.Frame(settings_window, padding="10")
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        # API设置
        api_frame = ttk.LabelFrame(settings_frame, text="API设置")
        api_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Access Key
        ttk.Label(api_frame, text="Access Key:").grid(row=0, column=0, sticky=tk.W, pady=5)
        access_key_var = tk.StringVar(value=self.config["api"]["access_key"])
        ttk.Entry(api_frame, textvariable=access_key_var, width=40).grid(row=0, column=1, pady=5)
        
        # Secret Key
        ttk.Label(api_frame, text="Secret Key:").grid(row=1, column=0, sticky=tk.W, pady=5)
        secret_key_var = tk.StringVar(value=self.config["api"]["secret_key"])
        ttk.Entry(api_frame, textvariable=secret_key_var, width=40, show="*").grid(row=1, column=1, pady=5)
        
        # 使用doubaotrans包
        use_doubaotrans_var = tk.BooleanVar(value=self.config["api"]["use_doubaotrans"] == "True")
        ttk.Checkbutton(
            api_frame, 
            text="使用doubaotrans包(需要额外安装)", 
            variable=use_doubaotrans_var
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # 应用设置
        app_frame = ttk.LabelFrame(settings_frame, text="应用设置")
        app_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 默认目标语言
        ttk.Label(app_frame, text="默认目标语言:").grid(row=0, column=0, sticky=tk.W, pady=5)
        default_lang_var = tk.StringVar(value=self.config["settings"]["default_target_lang"])
        default_lang_combo = ttk.Combobox(
            app_frame, 
            textvariable=default_lang_var,
            state="readonly",
            width=10
        )
        default_lang_combo['values'] = (
            'zh', 'en', 'ja', 'ko', 'fr', 'de', 'ru', 'es', 'pt', 'it', 'ar', 'nl'
        )
        default_lang_combo.current(0)
        default_lang_combo.grid(row=0, column=1, pady=5)
        
        # 自动翻译
        auto_translate_var = tk.BooleanVar(value=self.config["settings"]["auto_translate"] == "True")
        ttk.Checkbutton(
            app_frame, 
            text="提取文字后自动翻译", 
            variable=auto_translate_var
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # 保存历史
        save_history_var = tk.BooleanVar(value=self.config["settings"]["save_history"] == "True")
        ttk.Checkbutton(
            app_frame, 
            text="保存翻译历史", 
            variable=save_history_var
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # PowerToys路径
        ttk.Label(app_frame, text="PowerToys路径(可选):").grid(row=3, column=0, sticky=tk.W, pady=5)
        powertoys_path_var = tk.StringVar(value=self.config["settings"]["powertoys_path"])
        ttk.Entry(app_frame, textvariable=powertoys_path_var, width=40).grid(row=3, column=1, pady=5)
        
        # 按钮区域
        button_frame = ttk.Frame(settings_window)
        button_frame.pack(fill=tk.X, pady=10)
        
        # 保存按钮
        def save_settings():
            """保存设置"""
            # 更新配置
            self.config["api"]["access_key"] = access_key_var.get()
            self.config["api"]["secret_key"] = secret_key_var.get()
            self.config["api"]["use_doubaotrans"] = str(use_doubaotrans_var.get())
            
            self.config["settings"]["default_target_lang"] = default_lang_var.get()
            self.config["settings"]["auto_translate"] = str(auto_translate_var.get())
            self.config["settings"]["save_history"] = str(save_history_var.get())
            self.config["settings"]["powertoys_path"] = powertoys_path_var.get()
            
            # 保存配置
            self._save_config()
            
            # 更新界面
            self.target_lang_var.set(default_lang_var.get())
            
            # 关闭设置窗口
            settings_window.destroy()
            
            self.status_var.set("设置已保存")
        
        # 取消按钮
        def cancel_settings():
            """取消设置"""
            settings_window.destroy()
        
        # 安装doubaotrans按钮
        def install_doubaotrans():
            """安装doubaotrans包"""
            try:
                import subprocess
                subprocess.check_call([sys.executable, "-m", "pip", "install", "doubao-trans"])
                messagebox.showinfo("安装成功", "doubaotrans包安装成功")
            except subprocess.CalledProcessError as e:
                messagebox.showerror("安装失败", f"安装doubaotrans包失败: {str(e)}")
        
        # 添加按钮
        ttk.Button(button_frame, text="安装doubaotrans", command=install_doubaotrans).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="保存", command=save_settings).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=cancel_settings).pack(side=tk.RIGHT, padx=5)
    
    def on_closing(self):
        """窗口关闭事件处理"""
        # 保存配置
        self._save_config()
        
        # 关闭窗口
        self.root.destroy()
    
    def run(self):
        """运行应用"""
        self.root.mainloop()


def main():
    """主函数"""
    # 检查依赖
    missing_deps = []
    
    try:
        import pyperclip
    except ImportError:
        missing_deps.append("pyperclip")
    
    try:
        import requests
    except ImportError:
        missing_deps.append("requests")
    
    # 如果缺少依赖，尝试安装
    if missing_deps:
        print(f"缺少依赖: {', '.join(missing_deps)}")
        print("尝试安装依赖...")
        
        try:
            import subprocess
            for dep in missing_deps:
                subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print("依赖安装成功")
        except subprocess.CalledProcessError as e:
            print(f"安装依赖失败: {str(e)}")
            print("请手动安装依赖: pip install pyperclip requests")
            sys.exit(1)
    
    # 启动应用
    app = ScreenTranslator()
    app.run()


if __name__ == "__main__":
    main()