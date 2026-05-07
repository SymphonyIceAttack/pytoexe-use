import random
import time

# 读取英文书籍文本
f=open("book.txt", "r", encoding="utf-8")
book=f.read()
f.close()
words=book.split()

score=0
wrong=0

print("——————英文打字游戏——————")
print("规则：输入一致的字母和标点，超时或打错计1次错误，错3次结束 答对+5分\n")

while wrong<3:
    # 随机挑出1-3个单词组成短语
    p=random.randint(0,len(words)-3)
    n=random.randint(1,3)
    a=" ".join(words[p:p+n])
    
    # 输出题目和时限
    print("\n请输入：",a)
    limit=len(a)
    print("限时：",limit,"秒")
    
    # 计时开始（不显示）
    start=time.time()
    b=input("输入：")
    used=time.time()-start #输入时长

    # 超时判断
    if used>limit:
        print("超时！")
        wrong+=1
        print("错误次数：",wrong)
        continue

    # 核对正误并计分
    for i in range(max(len(a), len(b))):
        if i>=len(a) or i>=len(b) or a[i]!=b[i]:
            wrong+=1
            print("第",i+1,"个字符错误！错误次数：",wrong)
            break
    else:
        score+=5
        print("输入正确!得分：",score)
    
# 结束
print("\n游戏结束！")
print("最终得分：",score)