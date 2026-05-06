
import hashlib
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
import xml.etree.ElementTree as ET


def calc_md5(file_path: Path) -> str:
    return hashlib.md5(file_path.read_bytes()).hexdigest()


def modify_xml(xml_path: Path, new_com: str) -> tuple[Path, Path, str, str]:
    if not xml_path.exists():
        raise FileNotFoundError(f"文件不存在: {xml_path}")

    if not new_com:
        raise ValueError("COM 不能为空")

    tree = ET.parse(xml_path)
    root = tree.getroot()
    node = root.find("HardwareConfiguration")

    if node is None:
        raise ValueError("没有找到 <HardwareConfiguration> 节点")

    old_value = node.text or ""
    node.text = new_com

    output_xml = xml_path.with_name(xml_path.stem + f"_{new_com}" + xml_path.suffix)
    tree.write(output_xml, encoding="utf-8", xml_declaration=False)

    md5_value = calc_md5(output_xml)
    output_md5 = output_xml.with_suffix(".md5")
    output_md5.write_text(md5_value, encoding="utf-8")

    return output_xml, output_md5, md5_value, old_value


class DorcComMd5App:
    def __init__(self, root):
        self.root = root
        self.root.title("DORC XML COM 修改 + MD5 生成工具")
        self.root.geometry("620x360")
        self.root.resizable(False, False)

        self.xml_path_var = tk.StringVar()
        self.com_var = tk.StringVar(value="COM01")
        self.result_var = tk.StringVar(value="请选择 XML 文件，然后输入 COM 值。")

        frame = tk.Frame(root, padx=18, pady=18)
        frame.pack(fill="both", expand=True)

        title = tk.Label(
            frame,
            text="DORC XML COM 修改 + MD5 生成工具",
            font=("Microsoft YaHei", 15, "bold")
        )
        title.pack(anchor="w", pady=(0, 15))

        file_frame = tk.Frame(frame)
        file_frame.pack(fill="x", pady=5)

        tk.Label(file_frame, text="XML 文件：", font=("Microsoft YaHei", 10)).pack(anchor="w")

        file_input_frame = tk.Frame(file_frame)
        file_input_frame.pack(fill="x", pady=(4, 0))

        tk.Entry(file_input_frame, textvariable=self.xml_path_var, width=62).pack(side="left", fill="x", expand=True)
        tk.Button(file_input_frame, text="选择文件", command=self.choose_file, width=10).pack(side="left", padx=(8, 0))

        com_frame = tk.Frame(frame)
        com_frame.pack(fill="x", pady=12)

        tk.Label(com_frame, text="HardwareConfiguration：", font=("Microsoft YaHei", 10)).pack(anchor="w")
        tk.Entry(com_frame, textvariable=self.com_var, width=20, font=("Consolas", 12)).pack(anchor="w", pady=(4, 0))

        tk.Button(
            frame,
            text="生成新的 XML 和 MD5",
            command=self.generate,
            height=2,
            font=("Microsoft YaHei", 11, "bold")
        ).pack(fill="x", pady=10)

        result_box = tk.Label(
            frame,
            textvariable=self.result_var,
            justify="left",
            anchor="nw",
            bg="#f2f2f2",
            relief="sunken",
            padx=10,
            pady=10,
            font=("Microsoft YaHei", 9),
            wraplength=560
        )
        result_box.pack(fill="both", expand=True, pady=(8, 0))

    def choose_file(self):
        path = filedialog.askopenfilename(
            title="选择 XML 文件",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")]
        )
        if path:
            self.xml_path_var.set(path)

    def generate(self):
        try:
            xml_path = Path(self.xml_path_var.get().strip())
            new_com = self.com_var.get().strip()

            output_xml, output_md5, md5_value, old_value = modify_xml(xml_path, new_com)

            result = (
                "生成完成！\n\n"
                f"原值: {old_value}\n"
                f"新值: {new_com}\n\n"
                f"XML: {output_xml}\n"
                f"MD5: {output_md5}\n\n"
                f"MD5值: {md5_value}"
            )
            self.result_var.set(result)
            messagebox.showinfo("完成", "新的 XML 和 MD5 文件已生成。")

        except Exception as e:
            messagebox.showerror("错误", str(e))
            self.result_var.set(f"处理失败：{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = DorcComMd5App(root)
    root.mainloop()
