import os
import shutil

# 日文/日本特征关键词整合版（不区分大小写匹配）
KEYWORDS = [
    # === 写真站/平台 ===
    "cosdoki", "digi-gra", "lovepop", "girlz-high", "graphis",
    "minisuka.tv", "ys-web", "wpb-net", "sabra.net", "dgc",
    # === 女团/偶像 ===
    "乃木坂46", "欅坂46", "日向坂46", "akb48", "ske48", "nmb48", "hkt48",
    # === 日文假名片段 ===
    "さく", "りの", "ありあ", "ななほ", "あさみ", "りさ", "はるな",
    "ここみ", "りん", "れな", "なぎさ", "りお", "ゆうか", "にーな",
    "ことね", "リィナ", "ひなの", "えりか", "なつ", "みゆき", "しおり",
    "ももか", "ゆきね", "あおい", "ひかり", "ゆあ", "なつか", "りおん", "らん",
    # === 日本姓氏/名 ===
    "黒崎", "高梨", "愛葉", "美泉", "山中", "加瀬", "桜木", "咲々原",
    "河北", "吉永", "倉木", "春原", "千葉", "望月", "西村", "黒江",
    "神坂", "香椎", "宮崎", "池田", "倉栗", "安藤", "平嶋", "片岡",
    "川上", "田島", "松下", "上西", "志田", "飛鳥", "宮内",
    # === 写真/视频分类标签（英文短语整体匹配） ===
    "photoset", "regular gallery", "secret gallery", "limited gallery",
    "special gallery", "platinum gallery", "digital books", "first gravure",
    # === 其他编码/缩写 ===
    "bfaa", "bfaz", "ghwb", "pmvr",
    # === 日文专属词汇 ===
    "競泳水着", "leotard", "グラビア", "グラドル",
    # === 二次元/游戏/文化 ===
    "東方", "lovelive", "艦これ", "fate",
    "アイドル", "コミック", "コスプレ",
]

def get_target_dir():
    while True:
        path = input("请输入要清理的文件夹路径: ").strip()
        if os.path.isdir(path):
            return path
        print(f"错误：路径不存在或不是文件夹 -> {path}")

def scan_first_level_folders(target_dir):
    """返回目标目录下的所有一级文件夹名称列表"""
    folders = []
    try:
        for name in os.listdir(target_dir):
            full_path = os.path.join(target_dir, name)
            if os.path.isdir(full_path):
                folders.append(name)
    except Exception as e:
        print(f"扫描文件夹时出错: {e}")
    return folders

def match_japanese(name):
    """检查文件夹名是否包含任意关键词（不区分大小写）"""
    name_lower = name.lower()
    return any(keyword.lower() in name_lower for keyword in KEYWORDS)

def delete_folders(target_dir, folder_names):
    """逐个删除给定的文件夹（一级子目录）"""
    deleted = []
    failed = []
    for name in folder_names:
        full_path = os.path.join(target_dir, name)
        try:
            shutil.rmtree(full_path)
            deleted.append(name)
            print(f"  ✅ 已删除: {name}")
        except Exception as e:
            failed.append((name, str(e)))
            print(f"  ❌ 删除失败: {name} ({e})")
    return deleted, failed

def main():
    print("=" * 50)
    print("  日本特征文件夹 一键清理工具 (Python)")
    print("=" * 50)
    target_dir = get_target_dir()

    # 扫描一级文件夹
    print("\n[1/3] 正在扫描一级文件夹 ...")
    all_folders = scan_first_level_folders(target_dir)
    print(f"扫描完成，共发现 {len(all_folders)} 个文件夹")

    # 显示所有文件夹
    print("\n[2/3] 所有一级文件夹:")
    print("-" * 40)
    for f in all_folders:
        print(f"  {f}")
    print("-" * 40)

    # 匹配日本特征
    matched = [f for f in all_folders if match_japanese(f)]
    if not matched:
        print("\n没有匹配到任何日本特征文件夹，无需删除。")
        return

    print("\n[3/3] 匹配到以下文件夹（将被删除）:")
    print("-" * 40)
    for f in matched:
        print(f"  🗑️  {f}")
    print("-" * 40)

    # 确认交互
    confirm = input("\n确认永久删除以上文件夹吗？(输入 y 继续，其他键取消): ").strip().lower()
    if confirm != "y":
        print("已取消操作，未删除任何文件夹。")
        return

    # 执行删除
    print("\n开始删除 ...")
    deleted, failed = delete_folders(target_dir, matched)

    # 汇总
    print("\n" + "=" * 50)
    print(f"操作完成：成功删除 {len(deleted)} 个，失败 {len(failed)} 个")
    if failed:
        print("失败列表:")
        for name, reason in failed:
            print(f"  - {name}: {reason}")
    print("=" * 50)

if __name__ == "__main__":
    main()
    input("\n按回车键退出...")