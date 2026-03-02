import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

def generate_prompt():
    core_anchor = """## 【核心强锚定】
纯次世代3D游戏角色建模，PBR静帧渲染，100%无真人实拍、2D手绘、卡通、动漫、插画元素，全程严格遵循3D建模行业标准，**强化3D建模原生质感，弱化真人皮肤肌理/五官特征**，面部特征严格贴合指定国家人种特征，无其他地域面部特征混杂"""

    style_direct = f"""## 【风格定向锚定】
{style_var.get()}"""

    face_region = f"""## 【面部地域定向】
{face_var.get()}"""

    appearance = f"""## 【角色颜值定位】
{appearance_var.get()}"""

    style_ref = """## 【风格参考限定要求】
仅参考上传图片的【整体画风、渲染质感、光影逻辑、色彩调性】，100%保留本提示词所有核心要求，3D风格锁定、多视图Layout布局、人物人设与外貌特征、服饰设计与所有细节、纯白色背景要求，不得修改，不得复刻参考图人物/服饰/构图/场景"""

    layout_norm = """## 【Layout 3D角色行业标准规范】
Complex professional character sheet layout，无任何透视畸变，所有视图严格遵循「同机位、同光源、同焦距、1:1统一人物比例、五官、服饰细节」：
- Top区域：Front正视图、Side侧视图、Back背视图 正交三视图，标准T-pose，无肢体遮挡，完整展示建模结构
- Left区域：8K超高清面部特写肖像 + 角色标准色卡（精准标注皮肤、头发、服饰的固有色值）
- Bottom区域：脚部+鞋履特写，严格遵循人体解剖学结构，细节完整无缺失
- Right区域：完整全身立绘，正面视角，完整展示人物体态、服饰、配饰的全部细节"""

    char_appearance = char_appearance_entry.get("1.0", tk.END).strip()
    clothing_desc = clothing_entry.get("1.0", tk.END).strip()
    multi_view_lock = "所有视图的服饰款式、颜色、细节、配饰位置完全统一，无任何差异"
    char_section = f"""## 【人物核心外貌+服饰完整描述】
// 人物核心外貌
{char_appearance}
// 服饰核心描述（按从上到下顺序，核心设计点加粗标注，无限制）
{clothing_desc}
// 多视图一致性强制锁定
{multi_view_lock}"""

    material_norm_fixed = "PBR物理基于渲染，3S次表面散射皮肤材质（精准控制表皮/真皮/皮下三层散射参数），**面部特征贴合角色定位，高颜值五官立体精致/普通长相五官自然协调/丑感五官比例违和/挫感面部轮廓扁平**，皮肤质感贴合定位（高颜值无瑕疵通透/普通长相自然肌理/胖丑感皮肤粗糙有瑕疵）"
    clothing_material = clothing_material_entry.get("1.0", tk.END).strip()
    material_norm = f"""## 【材质与渲染规范】
{material_norm_fixed}
// 服饰材质专项补充（对应自主填写的服饰描述，精准控制3D质感）
{clothing_material}
物理级光影追踪，柔和均匀无影棚布光，主光+辅光+轮廓光三层布光，无死黑区域，无过曝，明暗过渡自然，8K超高清，画面干净通透"""

    modeling_norm = """## 【3D建模专业规范】
符合美院人体解剖标准，7.5头身东方人标准比例/欧美人物标准头身比例（按需选），解剖学精准3D人体结构，肌肉线条/体态特征贴合角色定位（高颜值流畅紧致/普通长相自然匀称/胖丑感体态臃肿/挫感比例紧凑），拓扑结构规范均匀，四边面为主，无三角面错误，肢体建模无拉伸，关节衔接自然，手脚建模结构精准，无建模畸形"""

    env_params = """## 【环境与基础参数】
纯白色纯色背景，背景虚化，无多余场景元素，人物主体100%突出
--ar 1:1 --style raw --stylize 50"""

    negative = """## 【负面排除词】
穿模, 法线翻转, 拓扑错误, 贴图拉伸, 顶点错位, 面数不足, 硬边断层, UV拉伸, 面数缺失
五官畸形, 肢体扭曲, 头身比错误, 手脚畸形, 手指数量错误, 关节错位, 人体结构错误
画面崩坏, 杂乱背景, 多余场景元素, 水印, 文字, logo, 噪点, 过曝, 欠曝, 光影漏光
服饰设计错误, 服饰细节丢失, 不同视图服饰不一致
硅胶质感, 塑料假人感, AI合成脸, 绘画感"""

    full_prompt = f"{core_anchor}\n\n{style_direct}\n\n{face_region}\n\n{appearance}\n\n{style_ref}\n\n{layout_norm}\n\n{char_section}\n\n{material_norm}\n\n{modeling_norm}\n\n{env_params}\n\n{negative}\n\n---"

    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, full_prompt)

def copy_to_clipboard():
    root.clipboard_clear()
    root.clipboard_append(output_text.get("1.0", tk.END).strip())
    messagebox.showinfo("Copied", "Prompt copied to clipboard!")

# GUI Setup
root = tk.Tk()
root.title("3D Character Prompt Generator")
root.geometry("800x800")

tk.Label(root, text="风格定向锚定:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
style_var = tk.StringVar(value="古风 3D")
styles = ["古风 3D", "仙侠 3D", "赛博 3D", "都市写实 3D", "二次元质感 3D", "暗黑写实 3D", "基础写实 3D"]
ttk.Combobox(root, textvariable=style_var, values=styles, width=50).grid(row=0, column=1, pady=5)

tk.Label(root, text="面部地域定向:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
face_var = tk.StringVar(value="侧重中国人脸")
faces = ["侧重中国人脸", "侧重日本人脸", "侧重韩国人脸", "侧重欧美人脸", "侧重东南亚人脸"]
ttk.Combobox(root, textvariable=face_var, values=faces, width=50).grid(row=1, column=1, pady=5)

tk.Label(root, text="性别:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
gender_var = tk.StringVar(value="男性")
ttk.Radiobutton(root, text="男性", variable=gender_var, value="男性").grid(row=2, column=1, sticky="w")
ttk.Radiobutton(root, text="女性", variable=gender_var, value="女性").grid(row=2, column=2, sticky="w")

tk.Label(root, text="角色颜值定位:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
appearance_var = tk.StringVar()
male_appearance_options = [
    "3D顶配神颜帅哥（骨相皮相双优，五官黄金比例，3D建模精致度拉满）",
    "3D高颜值俊朗帅哥（五官立体精致，轮廓流畅，少年感/英气感拉满）",
    "3D清秀干净帅哥（眉眼柔和，面部无瑕疵，清爽少年感/斯文感）",
    "3D普通耐看男性（五官比例协调，无明显亮点/瑕疵，贴合日常自然感）",
    "3D微瑕疵普通男性（轻微塌鼻/单眼皮/圆脸，无丑感，偏生活化）",
    "3D粗犷硬朗男性（面部棱角分明，五官粗线条，无精致感，硬汉感）",
    "3D矮挫普通男性（面部扁平，五官平淡，下颌线模糊，无立体感）",
    "3D丑感男性（五官比例违和，面部臃肿/凸嘴/斜眼，皮肤粗糙有瑕疵）"
]
female_appearance_options = [
    "3D顶配神颜美女（骨相皮相双优，五官黄金比例，3D建模精致度拉满）",
    "3D高颜值绝美美女（五官精致立体，轮廓流畅，清冷/甜美/御姐感拉满）",
    "3D清秀温婉美女（眉眼柔和，面部小巧，古典/邻家感拉满，无瑕疵）",
    "3D普通耐看女性（五官比例协调，无明显亮点/瑕疵，贴合日常自然感）",
    "3D微瑕疵普通女性（轻微塌鼻/小眼睛/方脸，无丑感，偏生活化）",
    "3D明艳飒爽女性（面部线条利落，五官粗线条，无柔美感，御姐/酷感）",
    "3D矮挫普通女性（面部扁平，五官平淡，脸颊圆润，无立体感）",
    "3D丑感女性（五官比例违和，面部臃肿/龅牙/小眼距，皮肤粗糙有瑕疵）"
]
appearance_combo = ttk.Combobox(root, textvariable=appearance_var, values=male_appearance_options, width=50)
appearance_combo.grid(row=3, column=1, pady=5)

def update_appearance_options(*args):
    if gender_var.get() == "男性":
        appearance_combo['values'] = male_appearance_options
    else:
        appearance_combo['values'] = female_appearance_options
    if appearance_combo['values']:
        appearance_var.set(appearance_combo['values'][0])

gender_var.trace("w", update_appearance_options)
update_appearance_options()

tk.Label(root, text="人物核心外貌 (例: 25岁男性，黑色寸头):").grid(row=4, column=0, sticky="w", padx=10, pady=5)
char_appearance_entry = tk.Text(root, height=3, width=60)
char_appearance_entry.grid(row=4, column=1, pady=5)

tk.Label(root, text="服饰核心描述 (例: 上衣：**做旧破洞**牛仔外套；下装：黑色工装裤):").grid(row=5, column=0, sticky="w", padx=10, pady=5)
clothing_entry = tk.Text(root, height=5, width=60)
clothing_entry.grid(row=5, column=1, pady=5)

tk.Label(root, text="服饰材质专项补充 (例: 牛仔面料：做旧磨白质感，破洞毛边精准还原):").grid(row=6, column=0, sticky="w", padx=10, pady=5)
clothing_material_entry = tk.Text(root, height=5, width=60)
clothing_material_entry.grid(row=6, column=1, pady=5)

ttk.Button(root, text="Generate Prompt", command=generate_prompt).grid(row=7, column=0, columnspan=2, pady=10)

tk.Label(root, text="Generated Prompt (可复制):").grid(row=8, column=0, sticky="w", padx=10, pady=5)
output_text = scrolledtext.ScrolledText(root, height=15, width=80)
output_text.grid(row=8, column=1, pady=5)

ttk.Button(root, text="Copy to Clipboard", command=copy_to_clipboard).grid(row=9, column=0, columnspan=2, pady=10)

root.mainloop()