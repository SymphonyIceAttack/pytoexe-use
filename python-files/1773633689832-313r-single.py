def count_username_occurrences():
    # 配置文件路径（确保脚本和1.txt、2.txt在同一文件夹）
    file1_path = "1.txt"  # 复制出来的记录文件
    file2_path = "2.txt"  # 用户名列表文件
    result_file_path = "统计结果.txt"  # 可选：保存统计结果的文件

    # ---------------------- 步骤1：读取并处理用户名列表（2.txt） ----------------------
    usernames = set()  # 用集合去重，避免重复统计同一个名字
    try:
        with open(file2_path, "r", encoding="utf-8") as f2:
            for line in f2:
                # 清理每行的空白字符（空格、换行、制表符等）
                username = line.strip()
                # 跳过空行
                if username:
                    usernames.add(username)
    except FileNotFoundError:
        print(f"错误：未找到 {file2_path} 文件，请检查路径是否正确！")
        return

    # ---------------------- 步骤2：读取记录文件（1.txt） ----------------------
    try:
        with open(file1_path, "r", encoding="utf-8") as f1:
            # 读取全部内容，方便全局匹配（大文件可改用逐行读取，这里适合常规大小文件）
            record_content = f1.read()
    except FileNotFoundError:
        print(f"错误：未找到 {file1_path} 文件，请检查路径是否正确！")
        return

    # ---------------------- 步骤3：统计每个用户名的出现次数 ----------------------
    result = []
    print("===== 统计结果 =====")
    for name in sorted(usernames):  # sorted() 让结果按名字排序，更易读
        # count() 统计字符串出现次数（中文/英文都适用）
        count = record_content.count(name)
        result_str = f"用户名「{name}」：出现 {count} 次"
        print(result_str)
        result.append(result_str)

    # ---------------------- 步骤4：可选：将结果保存到文件 ----------------------
    with open(result_file_path, "w", encoding="utf-8") as f_result:
        f_result.write("\n".join(result))
    print(f"\n统计结果已保存到 {result_file_path}")

# 执行统计
if __name__ == "__main__":
    count_username_occurrences()