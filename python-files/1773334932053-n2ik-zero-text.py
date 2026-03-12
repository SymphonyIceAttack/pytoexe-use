import tkinter as tk
import pyperclip

ZW0 = "\u200B"
ZW1 = "\u200C"

def encode_hidden(text):
    result = ""
    for c in text:
        binary = format(ord(c), '08b')
        for b in binary:
            result += ZW0 if b == "0" else ZW1
    return result


def decode_hidden(text):
    bits = ""
    for c in text:
        if c == ZW0:
            bits += "0"
        elif c == ZW1:
            bits += "1"

    chars = []
    for i in range(0, len(bits), 8):
        byte = bits[i:i+8]
        if len(byte) == 8:
            chars.append(chr(int(byte, 2)))

    return "".join(chars)


def generate():
    visible = visible_text.get("1.0", tk.END).strip()
    hidden = hidden_text.get("1.0", tk.END).strip()

    zw = encode_hidden(hidden)

    if len(visible) > 0:
        mid = len(visible) // 2
        result = visible[:mid] + zw + visible[mid:]
    else:
        result = zw

    output.delete("1.0", tk.END)
    output.insert(tk.END, result)


def decode():
    cipher = decode_input.get("1.0", tk.END)
    plain = decode_hidden(cipher)

    decode_output.delete("1.0", tk.END)
    decode_output.insert(tk.END, plain)


def copy_output(event=None):
    text = output.get("1.0", tk.END)
    pyperclip.copy(text)


root = tk.Tk()
root.title("Zero Width Text Tool")
root.geometry("520x520")

tk.Label(root, text="可见文本").pack()
visible_text = tk.Text(root, height=3)
visible_text.pack(fill="x")

tk.Label(root, text="隐藏文本 (QQ号等)").pack()
hidden_text = tk.Text(root, height=2)
hidden_text.pack(fill="x")

tk.Button(root, text="生成零宽字符文本", command=generate).pack(pady=5)

tk.Label(root, text="输出文本 (右键复制)").pack()
output = tk.Text(root, height=5)
output.pack(fill="x")

output.bind("<Button-3>", copy_output)

tk.Button(root, text="复制输出", command=copy_output).pack(pady=5)

tk.Label(root, text="------------ 解密区域 ------------").pack(pady=5)

tk.Label(root, text="输入含零宽字符的文本").pack()
decode_input = tk.Text(root, height=4)
decode_input.pack(fill="x")

tk.Button(root, text="解密隐藏文本", command=decode).pack(pady=5)

tk.Label(root, text="解密结果").pack()
decode_output = tk.Text(root, height=2)
decode_output.pack(fill="x")

root.mainloop()