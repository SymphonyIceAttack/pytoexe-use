from random import *
money = 100
while money >0 :
    n1 =randint(1,10)
    n2=randint(1,10)
    n3=randint(1,10)
    kakoe = randint(1,3)
    if kakoe == 1 :
        kakoe =n1
    elif kakoe == 2 :
        kakoe =n2
    elif kakoe == 3 :
        kakoe =n3
    print("Ваш баланс:", money)
    bet = int(input("Введите ставку:"))

    if bet>money:
        print('У вас недостаточно денег')
        break
    else:

        print(n1, n2, n3)
        betnum =int (input ("введите число на которое хотите поставить(из предложенных выше):"))
    if betnum == kakoe :
        money +=bet
        print("Вы выйграли")
    elif betnum != kakoe :
        money-=bet
        print("Вы проиграли")