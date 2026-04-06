import os
import random
import shutil
import glob
import uuid

def process_folder(folder_path, candidate_numbers, point_map):
    print(f"\n▶ 处理: {os.path.basename(folder_path)}")
    
    jpg_files = glob.glob(os.path.join(folder_path, "*.jpg"))
    if not jpg_files:
        print("   └─ 没有jpg文件，跳过")
        return False

    name_map = {}
    for f in jpg_files:
        name = os.path.splitext(os.path.basename(f))[0]
        name_map[name] = f

    if not name_map:
        print("   └─ 没有有效文件，跳过")
        return False

    available = [n for n in candidate_numbers if n in name_map]
    if not available:
        print(f"   └─ 候选图片 {candidate_numbers} 都不存在，跳过")
        return False

    selected = random.choice(available)
    print(f"   └─ 随机选中首图: {selected}.jpg")

    all_names = list(name_map.keys())
    remaining = [n for n in all_names if n != selected]

    if point_map:
        fixed_names = list(point_map.values())
        others = [n for n in remaining if n not in fixed_names]
        new_order = []
        idx = 0
        for i in range(len(remaining)):
            if i+1 in point_map:
                new_order.append(point_map[i+1])
            else:
                new_order.append(others[idx])
                idx += 1
        remaining = new_order

    rename_plan = {}
    rename_plan[name_map[selected]] = os.path.join(folder_path, "1.jpg")
    
    for i, name in enumerate(remaining, start=2):
        rename_plan[name_map[name]] = os.path.join(folder_path, f"{i}.jpg")

    print("   └─ 重命名计划:")
    for old, new in rename_plan.items():
        print(f"       {os.path.basename(old)} → {os.path.basename(new)}")

    temp_dir = os.path.join(folder_path, f"__temp_{uuid.uuid4().hex[:6]}__")
    try:
        os.makedirs(temp_dir)
        temp_paths = {}
        for old_path in rename_plan:
            temp_path = os.path.join(temp_dir, os.path.basename(old_path))
            shutil.move(old_path, temp_path)
            temp_paths[old_path] = temp_path
        
        for old_path, new_path in rename_plan.items():
            shutil.move(temp_paths[old_path], new_path)
        
        os.rmdir(temp_dir)
        print(f"   └─ ✓ 完成！")
        return True
    except Exception as e:
        print(f"   └─ ✗ 出错: {e}")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        return False

def main():
    print("=" * 55)
    print("       图片批量重命名工具")
    print("=" * 55)
    print("\n功能：遍历文件夹内所有子文件夹，重命名里面的jpg图片")
    print("-" * 55)
    
    while True:
        print("\n【1】选择文件夹")
        root = input("请输入路径（直接回车使用当前目录）: ").strip()
        if not root:
            root = os.getcwd()
        if os.path.isdir(root):
            print(f"   ✓ 目录: {root}")
            break
        print("   ✗ 路径不存在，请重新输入")
    
    print("\n【2】候选图片（从这些图中随机选一张作为1.jpg）")
    print("   格式：用英文逗号分隔，例如: 0_0,1_0,3_0,4_0")
    while True:
        candidates_input = input("请输入: ").strip()
        if candidates_input:
            candidates = [c.strip() for c in candidates_input.split(",")]
            if candidates:
                print(f"   ✓ 候选: {candidates}")
                break
        print("   ✗ 不能为空")
    
    print("\n【3】固定位置（可选，直接回车跳过）")
    print("   格式：位置:图片名,位置:图片名  例如: 3:2_1,5:3_1")
    fixed_input = input("请输入: ").strip()
    
    fixed_map = {}
    if fixed_input:
        for item in fixed_input.split(","):
            if ":" in item:
                pos, name = item.split(":")
                fixed_map[int(pos)] = name.strip()
        if fixed_map:
            print(f"   ✓ 固定: {fixed_map}")
    
    print("\n" + "=" * 55)
    print("【配置确认】")
    print(f"   处理目录: {root}")
    print(f"   候选图片: {candidates}")
    print(f"   固定位置: {fixed_map if fixed_map else '无'}")
    print("=" * 55)
    
    confirm = input("\n确认执行？(y=确认 / n=取消) [y]: ").strip().lower()
    if confirm == 'n':
        print("已取消")
        input("按回车键退出...")
        return
    
    print("\n开始处理...")
    print("-" * 55)
    
    folders = [entry.path for entry in os.scandir(root) if entry.is_dir()]
    if not folders:
        print("没有找到子文件夹")
    else:
        success = 0
        for folder in folders:
            if process_folder(folder, candidates, fixed_map):
                success += 1
        print("\n" + "-" * 55)
        print(f"处理完成！共 {len(folders)} 个文件夹，成功 {success} 个")
    
    input("\n按回车键退出...")

if __name__ == "__main__":
    main()