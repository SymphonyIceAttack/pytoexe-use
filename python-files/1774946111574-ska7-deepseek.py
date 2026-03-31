# 最簡單的 Python 程式 - 打招呼

print("=" * 30)
print("哈囉！這是一個 Python 程式")
print("=" * 30)

# 取得使用者輸入
name = input("你叫什麼名字？ ")

# 顯示結果
print(f"\n你好，{name}！")
print("歡迎使用 Python！")

# 簡單的計數
print("\n從 1 數到 5：")
for i in range(1, 6):
    print(i, end=" ")

print("\n" + "=" * 30)
print("程式執行完畢！")