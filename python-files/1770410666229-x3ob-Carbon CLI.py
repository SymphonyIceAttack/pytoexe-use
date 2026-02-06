import os
import platform

# 欢迎语句
print("Welcome to use Carbon CLI")

# 定义命令常量
command_1 = "ver"
command_2 = "exit"
command_3 = "help"
command_4 = "dir"
command_5 = "edit"
command_6 = "type"
command_7 = "cd"  # 新增cd命令

# 定义DIR常量（文件夹标识）
DIR = "DIR"

# 存储编辑的临时内容（key: 文件名, value: 文件内容）
edit_cache = {}

# 获取系统适配的路径分隔符（Windows用\，其他用/）
PATH_SEP = "\\" if platform.system() == "Windows" else "/"

# 初始化当前工作目录（默认是运行脚本的目录）
current_dir = os.getcwd()

# 生成带当前目录的提示符（更贴近DOS风格）
def get_prompt():
    # 把路径转为DOS风格（非Windows系统也模拟C:\开头）
    dos_dir = current_dir.replace("/", PATH_SEP)
    if not dos_dir.startswith("C:") and platform.system() != "Windows":
        dos_dir = f"C:{dos_dir}"
    return f"{dos_dir}>"

# 处理dir命令：查看目录文件
def handle_dir_command(args):
    global current_dir
    # 确定要查看的目录：有参数则用参数路径，无参数则用当前目录
    target_dir = args.strip() if args else current_dir
    
    # 处理相对路径/绝对路径
    try:
        # 把DOS风格路径转成系统可识别的路径
        target_dir_sys = target_dir.replace(PATH_SEP, os.sep)
        # 如果是相对路径，拼接当前目录
        if not os.path.isabs(target_dir_sys):
            target_dir_sys = os.path.join(current_dir, target_dir_sys)
        
        # 检查目录是否存在
        if not os.path.isdir(target_dir_sys):
            print(f"Directory not found: {target_dir}")
            return
        
        # 获取目录下的所有文件/文件夹
        items = os.listdir(target_dir_sys)
        # 按DOS风格格式化输出
        print(f"\n Directory of {target_dir}\n")
        # 统计文件/文件夹数量
        file_count = 0
        dir_count = 0
        # 遍历并显示每个项
        for item in sorted(items):
            item_path = os.path.join(target_dir_sys, item)
            if os.path.isdir(item_path):
                # 文件夹：加[DIR]标识
                print(f"[{DIR}]  {item}")
                dir_count += 1
            else:
                # 文件：显示大小（字节）
                file_size = os.path.getsize(item_path)
                print(f"      {item} ({file_size} bytes)")
                file_count += 1
        # 显示统计信息
        print(f"\n    {dir_count} Dir(s), {file_count} File(s)")
    except Exception as e:
        print(f"Error listing directory: {str(e)}")

# 处理edit命令：纯终端内编辑/新建文件
def handle_edit_command(args):
    global current_dir, edit_cache
    # 无参数时提示用法
    if not args.strip():
        print("Usage:")
        print("  edit <filename>          - Edit a file (create if not exists)")
        print("  edit <filename> save     - Save edited content to disk")
        return
    
    # 拆分参数：文件名 + 操作（可选save）
    args_parts = args.strip().split(maxsplit=1)
    filename = args_parts[0]
    action = args_parts[1].lower() if len(args_parts) > 1 else ""

    # 处理文件路径
    file_path_dos = filename
    file_path_sys = file_path_dos.replace(PATH_SEP, os.sep)
    if not os.path.isabs(file_path_sys):
        file_path_sys = os.path.join(current_dir, file_path_sys)

    # 1. 编辑/查看文件内容
    if action != "save":
        print(f"\n=== Editing {file_path_dos} ===")
        print("Enter your content (type 'EOF' on a new line to finish editing):")
        print("(Content will be stored in cache, use 'edit <file> save' to save to disk)\n")
        
        # 读取现有文件内容（如果文件存在）
        file_content = ""
        if os.path.exists(file_path_sys):
            try:
                with open(file_path_sys, "r", encoding="utf-8") as f:
                    file_content = f.read()
                print("Current content:")
                print(file_content)
                print("\n--- Start editing (overwrite above content) ---\n")
            except Exception as e:
                print(f"Warning: Failed to read existing file: {e}")
                print("Will create new content instead.\n")
        
        # 接收用户输入（直到输入EOF结束）
        new_content = []
        while True:
            try:
                line = input("> ")  # 编辑模式提示符
                if line.strip().upper() == "EOF":
                    break
                new_content.append(line)
            except KeyboardInterrupt:
                print("\nEditing cancelled (no changes saved)")
                return
        
        # 合并内容并存储到缓存
        edit_content = "\n".join(new_content)
        edit_cache[file_path_sys] = edit_content
        print(f"\n=== Edit finished ===")
        print(f"Content cached for {file_path_dos} (total {len(edit_content)} characters)")
        print(f"Use 'edit {file_path_dos} save' to save to disk.\n")
    
    # 2. 保存缓存内容到磁盘
    elif action == "save":
        if file_path_sys not in edit_cache:
            print(f"Error: No cached content for {file_path_dos} (edit first)")
            return
        
        try:
            # 写入文件
            with open(file_path_sys, "w", encoding="utf-8") as f:
                f.write(edit_cache[file_path_sys])
            # 保存后清除该文件的缓存
            del edit_cache[file_path_sys]
            print(f"Successfully saved {file_path_dos} to disk!")
        except Exception as e:
            print(f"Error saving file: {e}")

# 处理type命令：查看文件内容/编辑缓存
def handle_type_command(args):
    global current_dir, edit_cache
    # 无参数时提示用法
    if not args.strip():
        print("Usage:")
        print("  type <filename>          - View content of a file")
        print("  type <filename> cache    - View cached edit content (before save)")
        return
    
    # 拆分参数：文件名 + 操作（可选cache）
    args_parts = args.strip().split(maxsplit=1)
    filename = args_parts[0]
    action = args_parts[1].lower() if len(args_parts) > 1 else ""

    # 处理文件路径
    file_path_dos = filename
    file_path_sys = file_path_dos.replace(PATH_SEP, os.sep)
    if not os.path.isabs(file_path_sys):
        file_path_sys = os.path.join(current_dir, file_path_sys)

    # 1. 查看磁盘文件内容
    if action != "cache":
        if not os.path.exists(file_path_sys):
            print(f"Error: File {file_path_dos} not found on disk")
            return
        
        try:
            with open(file_path_sys, "r", encoding="utf-8") as f:
                content = f.read()
            print(f"\n=== Content of {file_path_dos} ===")
            print(content if content else "(Empty file)")
            print(f"=== End of content ===")
        except Exception as e:
            print(f"Error reading file: {e}")
    
    # 2. 查看编辑缓存内容
    elif action == "cache":
        if file_path_sys not in edit_cache:
            print(f"Error: No cached content for {file_path_dos}")
            return
        
        print(f"\n=== Cached content of {file_path_dos} (not saved) ===")
        print(edit_cache[file_path_sys] if edit_cache[file_path_sys] else "(Empty cache)")
        print(f"=== End of cached content ===")

# 处理cd命令：切换目录（支持cd ..返回上级）
def handle_cd_command(args):
    global current_dir
    # 无参数时：Windows返回当前盘符根目录，其他系统返回用户主目录
    if not args.strip():
        if platform.system() == "Windows":
            # Windows：返回当前盘符根目录（如C:\）
            drive, _ = os.path.splitdrive(current_dir)
            target_dir_sys = drive + os.sep if drive else current_dir
        else:
            # 非Windows：返回用户主目录
            target_dir_sys = os.path.expanduser("~")
    else:
        # 处理参数（支持cd .. / cd 目录名 / cd 绝对路径）
        target_dir_dos = args.strip()
        # 转成系统可识别的路径
        target_dir_sys = target_dir_dos.replace(PATH_SEP, os.sep)

        # 如果是相对路径（非绝对路径、非cd ..），拼接当前目录
        if not os.path.isabs(target_dir_sys) and target_dir_sys != "..":
            target_dir_sys = os.path.join(current_dir, target_dir_sys)

    try:
        # 规范化路径（处理..、.等特殊符号）
        target_dir_sys = os.path.normpath(target_dir_sys)
        
        # 检查目录是否存在
        if not os.path.isdir(target_dir_sys):
            print(f"Directory not found: {args.strip() or target_dir_dos}")
            return
        
        # 切换目录并更新current_dir
        os.chdir(target_dir_sys)
        current_dir = os.getcwd()
        # 提示切换成功（可选，DOS默认不提示，这里增加友好性）
        print(f"Changed directory to: {get_prompt().replace('>', '')}")
    except PermissionError:
        print(f"Permission denied: Cannot access {target_dir_sys}")
    except Exception as e:
        print(f"Error changing directory: {e}")

# 主循环
while True:
    # 显示带当前目录的提示符
    usr_input = input(get_prompt()).strip()
    if usr_input == "":
        continue
    
    # 拆分命令和参数（支持"命令 参数"格式）
    input_parts = usr_input.split(maxsplit=1)
    usr_command = input_parts[0].lower()  # 命令转小写，兼容大小写
    command_args = input_parts[1] if len(input_parts) > 1 else ""

    # 处理各命令
    if usr_command == command_1:
        print("Carbon CLI v1.0.0")
    elif usr_command == command_2:
        print("Exiting Carbon CLI")
        break
    elif usr_command == command_3:
        # 补充cd命令的帮助说明
        print("""
ver   Show the version of Carbon CLI
exit  Exit the Carbon CLI
dir   List files and directories (usage: dir [path])
edit  Edit file in CLI (usage: edit <file> / edit <file> save)
type  View file content (usage: type <file> / type <file> cache)
cd    Change directory (usage: cd / cd .. / cd <path>)""")
    elif usr_command == command_4:
        handle_dir_command(command_args)
    elif usr_command == command_5:
        handle_edit_command(command_args)
    elif usr_command == command_6:
        handle_type_command(command_args)
    elif usr_command == command_7:
        handle_cd_command(command_args)
    else:
        print("Unknown Command")
