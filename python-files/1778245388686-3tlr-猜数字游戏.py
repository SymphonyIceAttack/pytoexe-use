import random
def guess_number():
   number_to_guess = random.randint(1, 100)
   guess = None
   print("欢迎来到猜数字游戏！")
   print("我已经想好了一个1到100之间的数字。")
   while guess != number_to_guess:
       guess = int(input("请输入你的猜测："))
       if guess < number_to_guess:
           print("太小了！")
       elif guess > number_to_guess:
           print("太大了！")
       else:
           print("恭喜你，猜对了！")
if __name__ == "__main__":
   guess_number()