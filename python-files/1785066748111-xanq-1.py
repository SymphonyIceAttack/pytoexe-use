import os

def split_txt_by_keywords():
    print("==== TXT按关键词批量分割工具 ====")
    # ====================== 【在这里修改配置】======================
    # 1. 原始文件路径（把txt放到同文件夹，直接写文件名）
    source_file = "E:\360MoveData\Users\Administrator\Desktop\200.txt"
    # 2. 关键词列表，每个关键词触发新建一个文件
    keywords = [
        "文案"
    ]
    # 3. 输出文件夹名称
    out_folder = "分割结果"
    # 4. 编码，一般用utf-8；如果乱码改成 "gbk"
    encoding = "utf-8"
    # ==============================================================

    # 创建输出目录
    if not os.path.exists(out_folder):
        os.makedirs(out_folder)

    try:
        with open(source_file, "r", encoding=encoding) as f:
            content = f.read()
    except Exception as e:
        print(f"读取文件失败：{e}")
        input("\n按回车退出...")
        return

    blocks = []
    current_block = []
    lines = content.splitlines()

    for line in lines:
        # 判断当前行是否包含任意关键词 → 新块开始
        hit_keyword = any(k in line for k in keywords)
        if hit_keyword:
            if current_block:
                blocks.append("\n".join(current_block))
                current_block = []
        current_block.append(line)
    # 加入最后一块
    if current_block:
        blocks.append("\n".join(current_block))

    # 依次保存每个文本块
    for idx, text in enumerate(blocks, start=1):
        save_path = os.path.join(out_folder, f"文案_{idx:03d}.txt")
        with open(save_path, "w", encoding=encoding) as f:
            f.write(text)
        print(f"已生成：{save_path}")

    print(f"\n分割完成！一共输出 {len(blocks)} 个txt文件")
    input("\n按回车键关闭窗口...")


if __name__ == "__main__":
    split_txt_by_keywords()