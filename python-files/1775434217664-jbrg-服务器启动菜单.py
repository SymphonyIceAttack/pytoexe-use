import os
import subprocess
import sys

def main():
    # 服务器路径（按你给的路径，注意bat路径有空格，必须用原始字符串）
    bedrock_path = r"D:\桌面\我的世界服务器\bedrock_server.exe"
    java_path = r"D:\桌面\我的世界服务器\java\新建 文本文档.bat"

    while True:
        # 清屏（Windows专用）
        os.system("cls")

        print("===== 我的世界服务器启动器 =====")
        print("1 → 启动 基岩版服务器")
        print("2 → 启动 Java版服务器")
        print("3 → 退出程序")
        print("===============================\n")

        choice = input("请输入数字选择：")

        if choice == "1":
            print("\n正在启动 基岩版服务器...")
            try:
                # 切换到服务器所在目录（解决找不到server.properties的核心问题！）
                os.chdir(r"D:\桌面\我的世界服务器")
                # 启动服务器，启动器直接退出
                subprocess.Popen(bedrock_path, cwd=r"D:\桌面\我的世界服务器")
                # 启动器直接关闭
                sys.exit(0)
            except Exception as e:
                print(f"错误：{str(e)}")
                input("\n按回车返回菜单...")

        elif choice == "2":
            print("\n正在启动 Java版服务器...")
            try:
                # 切换到bat所在目录，避免路径问题
                os.chdir(r"D:\桌面\我的世界服务器\java")
                # 启动bat，启动器直接退出
                subprocess.Popen(java_path, shell=True, cwd=r"D:\桌面\我的世界服务器\java")
                # 启动器直接关闭
                sys.exit(0)
            except Exception as e:
                print(f"错误：{str(e)}")
                input("\n按回车返回菜单...")

        elif choice == "3":
            print("\n退出程序...")
            break

        else:
            print("\n输入错误，请输入 1/2/3！")
            input("按回车继续...")

if __name__ == "__main__":
    main()