import os
from datetime import datetime
from pathlib import Path

def create_machine_folder():
    # 1. 自動取得使用者電腦的「桌面」路徑
    desktop_path = Path.home() / "Desktop"
    
    # 2. 定義基礎資料夾路徑 (桌面/機台照片管理)
    base_folder = desktop_path / "機台照片管理"
    base_folder.mkdir(parents=True, exist_ok=True)
    
    # 3. 取得當天日期 (格式：YYYYMMDD)
    today_str = datetime.now().strftime("%Y%m%d")
    
    # 4. 跳出提示，要求手動輸入「機台類型與編號」
    print("="*40)
    print("📸 機台照片資料夾產生器 (含自動分類子資料夾)")
    print("="*40)
    machine_info = input("請輸入「機台類型與編號」(例如：U2_11503009)：")
    
    # 防呆：如果什麼都沒輸入就按 Enter
    if not machine_info.strip():
        print("❌ 未輸入機台資訊，取消建立資料夾。")
        return
        
    # 5. 組合最終的主資料夾名稱與完整路徑
    folder_name = f"{today_str}_{machine_info}"
    target_folder = base_folder / folder_name
    
    # ★ 新增：定義要自動建立的子資料夾清單
    subfolders = [
        "1. 吊牌與螢幕",
        "2. 電路圖版本",
        "3. PLC 版本",
        "4. 板子序號"
    ]
    
    # 6. 建立主資料夾與子資料夾
    try:
        # 建立主資料夾
        target_folder.mkdir(exist_ok=False)
        
        # ★ 新增：自動在主資料夾內建立所有子資料夾
        for sub in subfolders:
            (target_folder / sub).mkdir()
            
        print(f"\n✅ 成功建立主資料夾與 {len(subfolders)} 個子資料夾！")
        print(f"📂 路徑：{target_folder}")
        
        # 自動幫您打開剛剛建好的主資料夾 (僅限 Windows)
        if os.name == 'nt':
            os.startfile(target_folder)
            
    except FileExistsError:
        print(f"\n⚠️ 建立失敗：今天已經建過這個機台的資料夾了！")
        print(f"📂 路徑：{target_folder}")
    except Exception as e:
        print(f"\n❌ 建立資料夾時發生未知的錯誤：{e}")

if __name__ == "__main__":
    create_machine_folder()
    
    # 讓終端機視窗停住，方便您看清楚執行結果
    input("\n請按 Enter 鍵結束視窗...")