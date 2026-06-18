import os
print("starting ODOS... ")
print("1=help")
count=1
while count==1:
    m=int(input("OD:\ "))
    if m==1:
        print(" help   1 ")
        print(" dir    2 ")
        print(" prog   3 ")
        print(" manual 4 ")
        print(" upinfo 5 ")
        print(" ver    6 ")
        print(" news   7 ")
        print(" exit   8 ")
    if m==2:
        count=0
        print(" 1=n/a ")  
        print(" 2=n/a ")
        print(" 3=n/a ")
        print(" 4=go back ")
        a=int(input("ODD:\ "))
        if a==1:
            os.system("(your program or file)")
        if a==2:
            os.system("(your program or file)")
        if a==3:
            os.system("(your program or file)")
        if a==4:
            count=1
        else:
            print(" ")
    if m==4:
        os.system("C://программы_на_phyton//ODOS//user_manual.docx")
    if m==3:
        count=0
        print("programs for ODOS:")
        print(" 1=UCalculator_V3.3_For_ODOS.py")
        print(" 2=hack_the_pentagon_game.py")
        print(" 3=randomizer.py")
        print(" 4=go back in main directory")
        b=int(input("ODP:\ "))
        if b==1:
            count=1
            os.system("C:\\программы_на_phyton\\ODOS\\ODOS_programs\\UCalculator_V3.3_for_ODOS.py")
        if b==2:
            count=1
            os.system("C:\\программы_на_phyton\\ODOS\\ODOS_programs\\hack_the_pentagon_game.py")
        if b==3:
            count=1
            os.system("C:\\программы_на_phyton\\ODOS\\ODOS_programs\\randomizer.py")    
        if b==4:
            count=1
    if m==5:
        print(" specal update magazine for ODOS V1.2 ")
        print(" its update for users - lower places for data ")
        print(" ru version  for this magazine in main ODOS folder ")
    if m==6:
        print("your ODOS version 1.2")
    if m==8:
        count=0
        e=int(input("you sure? (1/0) "))
        if e==1:
            exit
        else:
            count=1
            print(" ")
    else:
        print(" ")
        
    

