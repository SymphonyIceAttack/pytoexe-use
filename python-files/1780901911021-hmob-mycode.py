import base64
import itertools

# 1. 生成所有 456,976 个组合
letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
all_combos = (
    "".join(p) for p in itertools.product(letters, repeat=4)
)  # 使用生成器节省内存
content = "\n".join(all_combos)

# 2. 将内容转换成 Base64 编码，方便网页安全传输
b64_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")

# 3. 构建一个点击就能触发浏览器下载的 HTML 链接
html_link = f'<a href="data:text/plain;base64,{b64_content}" download="all_combinations.txt" style="padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">👉 点击这里下载完整的45万个组合 👈</a>'

# 4. 尝试通过网页环境特有的方式输出
try:
    # 如果你在 Jupyter Notebook / Google Colab 环境
    from IPython.display import HTML, display

    display(HTML(html_link))
except ImportError:
    # 如果你在普通的网页 Python 运行框（如在线菜鸟工具等）
    print("\n" + "=" * 50)
    print("【请复制下方整行代码，粘进浏览器地址栏敲回车，或者直接点击控制台输出的链接】")
    print("=" * 50 + "\n")
    print(f"data:text/plain;base64,{b64_content}")