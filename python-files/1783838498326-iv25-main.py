import customtkinter as ctk
from tkinter import filedialog, messagebox
import openai
import os

# ==================== 界面外观设置 ====================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("🤖 AI 通用代码注释生成器")
app.geometry("1200x700")

# ==================== 🆕 模型与 API 地址的映射表（自动填充的核心） ====================
MODEL_BASE_URL_MAP = {
    # ---- OpenAI 系列 ----
    "gpt-3.5-turbo": "https://api.openai.com/v1",
    "gpt-4": "https://api.openai.com/v1",
    "gpt-4-turbo": "https://api.openai.com/v1",
    "gpt-4o": "https://api.openai.com/v1",
    # ---- DeepSeek 系列 ----
    "deepseek-v4-flash": "https://api.deepseek.com",
    "deepseek-v4-pro": "https://api.deepseek.com",
    # ---- 阿里通义千问 ----
    "qwen-max": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "qwen-plus": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "qwen-turbo": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    # ---- 智谱 GLM ----
    "glm-4": "https://open.bigmodel.cn/api/paas/v4",
    "glm-3-turbo": "https://open.bigmodel.cn/api/paas/v4",
    # ---- 月之暗面 Moonshot ----
    "moonshot-v1-8k": "https://api.moonshot.cn/v1",
    "moonshot-v1-32k": "https://api.moonshot.cn/v1",
    # ---- 百川 ----
    "Baichuan4": "https://api.baichuan-ai.com/v1",
    "Baichuan3-Turbo": "https://api.baichuan-ai.com/v1",
    # ---- 本地 Ollama（需启动服务） ----
    "llama3": "http://localhost:11434/v1",
    "qwen:7b": "http://localhost:11434/v1",
    "mistral": "http://localhost:11434/v1",
}

# ==================== 1. 顶部标题 ====================
title_label = ctk.CTkLabel(
    app,
    text="🤖 AI 通用代码注释生成器",
    font=("Arial", 26, "bold")
)
title_label.pack(pady=20)

# ==================== 2. 编程语言选择 ====================
lang_frame = ctk.CTkFrame(app)
lang_frame.pack(pady=10, padx=20, fill="x")

lang_label = ctk.CTkLabel(lang_frame, text="编程语言：", font=("Arial", 16))
lang_label.pack(side="left", padx=10)

language_options = [
    "Python", "Java", "JavaScript", "TypeScript", "C", "C++", "C#",
    "Go", "Rust", "PHP", "Ruby", "Swift", "Kotlin", "R",
    "Shell (Bash)", "PowerShell", "SQL", "HTML/CSS", "Vue", "React JSX",
    "Lua", "Dart", "Scala", "Perl"
]
language_menu = ctk.CTkOptionMenu(lang_frame, values=language_options, width=200)
language_menu.pack(side="left", padx=10)
language_menu.set("Python")

# ==================== 3. 文件选择 ====================
file_frame = ctk.CTkFrame(app)
file_frame.pack(pady=10, padx=20, fill="x")

file_label = ctk.CTkLabel(file_frame, text="选择文件：", font=("Arial", 16))
file_label.pack(side="left", padx=10)

file_entry = ctk.CTkEntry(file_frame, width=400, placeholder_text="请点击右侧按钮选择代码文件")
file_entry.pack(side="left", padx=10)

def select_file():
    file_path = filedialog.askopenfilename(
        title="请选择你的代码文件",
        filetypes=[
            ("代码文件", "*.py *.java *.js *.ts *.c *.cpp *.h *.cs *.go *.rs *.php *.rb *.swift *.kt *.r *.sh *.ps1 *.sql *.html *.css *.vue *.jsx *.lua *.dart *.scala *.pl"),
            ("所有文件", "*.*")
        ]
    )
    if file_path:
        file_entry.delete(0, "end")
        file_entry.insert(0, file_path)

browse_button = ctk.CTkButton(file_frame, text="📂 浏览", command=select_file)
browse_button.pack(side="left", padx=10)

# ==================== 4. API 设置区 ====================
api_frame = ctk.CTkFrame(app)
api_frame.pack(pady=10, padx=20, fill="x")

# 4.1 API Key（第一行）
api_key_label = ctk.CTkLabel(api_frame, text="API Key：", font=("Arial", 16))
api_key_label.pack(side="left", padx=10)

api_key_entry = ctk.CTkEntry(
    api_frame,
    width=250,
    placeholder_text="sk-... 或你的密钥",
    show="*"
)
api_key_entry.pack(side="left", padx=10)

# 4.2 🆕 API 地址（自动填充 + 支持手动修改）
base_url_label = ctk.CTkLabel(api_frame, text="API 地址：", font=("Arial", 16))
base_url_label.pack(side="left", padx=(20, 5))

base_url_entry = ctk.CTkEntry(
    api_frame,
    width=250,
    placeholder_text="选择模型后自动填写，也可手动改"
)
base_url_entry.pack(side="left", padx=5)

# 4.3 🆕 模型名称下拉框（带联动事件）
model_label = ctk.CTkLabel(api_frame, text="模型：", font=("Arial", 16))
model_label.pack(side="left", padx=(20, 5))

model_presets = list(MODEL_BASE_URL_MAP.keys())  # 直接从映射表生成列表

# 🆕 定义联动函数：当选中预设模型时，自动填入 Base URL
def on_model_selected(choice):
    # 如果用户选择的模型在映射表里
    if choice in MODEL_BASE_URL_MAP:
        base_url_entry.delete(0, "end")
        base_url_entry.insert(0, MODEL_BASE_URL_MAP[choice])
        base_url_entry.configure(placeholder_text="已自动匹配地址")
    else:
        # 如果用户手动输入了不存在的模型名，清空地址框，提示用户手动填
        base_url_entry.delete(0, "end")
        base_url_entry.configure(placeholder_text="未匹配预设，请手动输入地址")

# 使用 CTkComboBox，并绑定选中事件
model_combobox = ctk.CTkComboBox(
    api_frame,
    values=model_presets,
    width=180,
    command=on_model_selected  # 🆕 关键：点击下拉选项时触发联动
)
model_combobox.pack(side="left", padx=5)
model_combobox.set("gpt-3.5-turbo")

# 初始化时自动填一次默认模型的地址
on_model_selected("gpt-3.5-turbo")

# ==================== 5. 核心处理函数 ====================
def on_generate_click():
    api_key = api_key_entry.get().strip()
    base_url = base_url_entry.get().strip()
    model_name = model_combobox.get().strip()
    file_path = file_entry.get().strip()
    language = language_menu.get()

    # --- 校验 ---
    if not api_key:
        messagebox.showwarning("警告", "请填写你的 API Key！")
        return
    if not base_url:
        messagebox.showwarning("警告", "请填写或选择有效的 API 地址！\n（提示：点击下拉模型可自动填充）")
        return
    if not file_path:
        messagebox.showwarning("警告", "请先选择一个代码文件！")
        return
    if not os.path.exists(file_path):
        messagebox.showerror("错误", "文件路径无效，请重新选择！")
        return

    # --- 读取文件 ---
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
        print(f"✅ 成功读取文件，共 {len(code_content)} 个字符")
        if not code_content.strip():
            messagebox.showerror("错误", "文件内容为空，请选择有效的代码文件！")
            return
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='gbk') as f:
                code_content = f.read()
            print("✅ 使用 GBK 编码成功读取文件")
        except Exception as e:
            messagebox.showerror("错误", f"读取文件失败（编码问题）：\n{e}")
            return
    except Exception as e:
        messagebox.showerror("错误", f"读取文件时出错：\n{e}")
        return

    # --- 构建提示词 ---
    system_prompt = f"""你是一位严谨的代码文档专家。
任务：为以下 {language} 代码添加高质量的注释。
铁律：
1. 【绝对禁止】改动任何已有的功能性代码（包括变量名、逻辑、缩进）。
2. 【选择性注释】仅在复杂业务逻辑、算法、接口调用等你认为有必要的地方添加注释，解释“为什么”（Why）和“是什么”（What），而不是“怎么做的”（How）。
3. 【输出格式】直接返回添加了注释的完整代码，不要包含任何多余的客套话或解释文字。"""

    user_content = f"请为这段 {language} 代码添加注释：\n\n```{language.lower()}\n{code_content}\n```"

    # --- 调用 AI API ---
    try:
        print(f"🚀 正在调用模型: {model_name} (地址: {base_url})，请稍候...")
        client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url
        )

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.2,
            max_tokens=4096
        )

        result_code = response.choices[0].message.content

        # --- 清洗多余标记 ---
        if result_code.startswith("```"):
            lines = result_code.splitlines()
            if len(lines) > 2 and lines[-1].strip() == "```":
                result_code = "\n".join(lines[1:-1])
            else:
                result_code = "\n".join(lines[1:])

        # --- 保存文件 ---
        base, ext = os.path.splitext(file_path)
        output_path = f"{base}_annotated{ext}"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result_code)

        print(f"🎉 注释生成成功！文件保存至：{output_path}")
        messagebox.showinfo("成功", f"✅ 注释生成完成！\n文件保存至：\n{output_path}")

    except openai.APIError as e:
        messagebox.showerror("API错误", f"调用失败，请检查：\n1. Key 是否有效\n2. 地址是否正确\n3. 模型是否支持\n\n错误：\n{e}")
    except Exception as e:
        messagebox.showerror("错误", f"程序运行出错：\n{e}")

# ==================== 6. 底部生成按钮 ====================
generate_button = ctk.CTkButton(
    app,
    text="🚀 生成注释",
    font=("Arial", 20, "bold"),
    height=55,
    command=on_generate_click
)
generate_button.pack(pady=40)

# ==================== 7. 启动程序 ====================
app.mainloop()