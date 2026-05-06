import hashlib
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

def calc_md5(file_path: Path) -> str:
    data = file_path.read_bytes()
    return hashlib.md5(data).hexdigest()

def modify_xml(xml_path: Path, new_com: str):
    if not xml_path.exists():
        print(f"文件不存在: {xml_path}")
        return

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        node = root.find("HardwareConfiguration")

        if node is None:
            print("没有找到 <HardwareConfiguration> 节点")
            return

        old_value = node.text
        node.text = new_com

        output_xml = xml_path.with_name(
            xml_path.stem + f"_{new_com}" + xml_path.suffix
        )

        tree.write(output_xml, encoding="utf-8", xml_declaration=False)

        md5_value = calc_md5(output_xml)

        output_md5 = output_xml.with_suffix(".md5")
        output_md5.write_text(md5_value, encoding="utf-8")

        print("\\n修改完成")
        print(f"原值: {old_value}")
        print(f"新值: {new_com}")
        print(f"XML文件: {output_xml}")
        print(f"MD5文件: {output_md5}")
        print(f"MD5: {md5_value}")

    except Exception as e:
        print(f"处理失败: {e}")

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("使用方法:")
        print("1. 把 XML 文件拖到 bat 文件上")
        print("2. 或命令行执行:")
        print("python modify_dorc_com_custom.py DORC.xml")
        input("\\n按回车退出...")
        sys.exit()

    xml_file = Path(sys.argv[1])

    com_value = input("请输入 COM 端口（例如 COM01 / COM07 / COM12）: ").strip()

    if not com_value:
        print("COM 不能为空")
    else:
        modify_xml(xml_file, com_value)

    input("\\n按回车退出...")
