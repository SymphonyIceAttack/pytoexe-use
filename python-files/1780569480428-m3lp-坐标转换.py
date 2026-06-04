import json
import os
import sys

def convert_json_folder(folder):
    dat_out = os.path.join(folder, "teleports.dat")
    txt_out = os.path.join(folder, "坐标汇总记事本.txt")
    index = 1
    all_lines = []

    for file_name in os.listdir(folder):
        if file_name.endswith(".json"):
            file_full = os.path.join(folder, file_name)
            try:
                with open(file_full, "r", encoding="utf-8") as f:
                    js_data = json.load(f)
                x = js_data["position"]["x"]
                y = js_data["position"]["y"]
                z = js_data["position"]["z"]
                line = f"{index}|{x}|{y}|{z}\n"
                all_lines.append(line)
                index += 1
            except Exception as e:
                print(f"出错跳过 {file_name}:{e}")

    with open(dat_out,"w",encoding="utf-8") as f1:
        f1.writelines(all_lines)
    with open(txt_out,"w",encoding="utf-8") as f2:
        f2.writelines(all_lines)

    print(f"\n生成完成！总共 {len(all_lines)} 条坐标")
    print("teleports.dat、坐标汇总记事本.txt 格式：序号|X|Y|Z")

if __name__ == "__main__":
    if len(sys.argv)>1 and os.path.isdir(sys.argv[1]):
        convert_json_folder(sys.argv[1])
    else:
        print("使用：把放JSON的文件夹拖拽到本程序上")
    os.system("pause")