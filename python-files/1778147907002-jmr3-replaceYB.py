import json
import os
import sys

def main():
    print("="*50)
    print("医保数据自动替换工具 v1.0")
    print("="*50)

    # --- 1. 定义默认数据 (方便测试，不用每次粘贴) ---
    # 这里预置了你提供的示例数据，如果检测不到文件，程序会默认使用这些数据进行演示
    default_source = """
    {
      "TranID": "d9a3c5b42d9c42e58bfd35d6b1b7cfcc",
      "OutData_2207": {
        "setlinfo": {
          "psn_no": "42020000000000100077041214",
          "mdtrt_id": "420200G9101580148422",
          "setl_id": "420200G9102288375856",
          "setl_time": "2026-04-10 14:56:25"
        }
      }
    }
    """
    
    default_template = """
    {
      "infno": "2208",
      "msgid": "H42020200050202603280856209219",
      "mdtrtarea_admvs": "420200",
      "insuplc_admdvs": "420299",
      "recer_sys_code": "接收方系统代码",
      "dev_no": "M0101X05",
      "dev_safe_info": "设备安全信息",
      "cainfo": "123",
      "signtype": "SM2",
      "infver": "1",
      "opter_type": "1",
      "opter": "9037",
      "opter_name": "自助",
      "inf_time": "2026-03-18 09:50:39",
      "fixmedins_code": "H42020200050",
      "fixmedins_name": "黄石市中心医院",
      "sign_no": "420200G9100044532036",
      "input": {
        "data": {
          "psn_no": "42020000000000000011585185",
          "setl_id": "420200G9102290233033",
          "mdtrt_id": "420200G9101581397050"
        }
      }
    }
    """

    source_json_str = default_source
    template_json_str = default_template

    # --- 2. 尝试读取外部文件 (如果存在) ---
    # 如果你把数据保存成 source.json 和 template.json 放在同目录下，程序会自动读取
    if os.path.exists("source.json"):
        print("发现 source.json，正在读取...")
        with open("source.json", "r", encoding="utf-8") as f:
            source_json_str = f.read()
    
    if os.path.exists("template.json"):
        print("发现 template.json，正在读取...")
        with open("template.json", "r", encoding="utf-8") as f:
            template_json_str = f.read()

    # --- 3. 执行逻辑 ---
    try:
        # 解析 JSON
        source_data = json.loads(source_json_str)
        template_data = json.loads(template_json_str)

        # 提取字段
        setl_info = source_data.get("OutData_2207", {}).get("setlinfo", {})
        
        new_psn_no = setl_info.get("psn_no")
        new_mdtrt_id = setl_info.get("mdtrt_id")
        new_setl_id = setl_info.get("setl_id")
        new_setl_time = setl_info.get("setl_time")

        if not all([new_psn_no, new_mdtrt_id, new_setl_id]):
            print("❌ 错误：源数据中缺少必要字段 (psn_no, mdtrt_id, setl_id)")
            input("按回车键退出...")
            return

        # 替换字段
        if "input" in template_data and "data" in template_data["input"]:
            template_data["input"]["data"]["psn_no"] = new_psn_no
            template_data["input"]["data"]["mdtrt_id"] = new_mdtrt_id
            template_data["input"]["data"]["setl_id"] = new_setl_id
            
            # 同步更新时间
            if new_setl_time:
                template_data["inf_time"] = new_setl_time
            
            # 输出结果
            result_json = json.dumps(template_data, ensure_ascii=False, indent=4)
            
            print("\n" + "="*50)
            print("✅ 处理成功！替换后的结果如下：")
            print("="*50)
            print(result_json)
            
            # 保存到文件
            with open("result.json", "w", encoding="utf-8") as f:
                f.write(result_json)
            print("\n💾 结果已自动保存为: result.json")

        else:
            print("❌ 错误：目标模板格式不正确")

    except Exception as e:
        print(f"❌ 发生错误: {e}")

    print("\n程序运行结束。")
    input("按回车键关闭窗口...")

if __name__ == "__main__":
    main()