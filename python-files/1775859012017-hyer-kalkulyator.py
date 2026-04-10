cc = ["topla","vurma","bölmə", "çıxma","qüvvət"]
a = int(input("first number:"))
b = int(input("second number:"))
c = input("vurma or çıxma or topla or bölmə or qüvvət::")
if c == "topla":
    print(a+b)
elif c == "vurma":
    print(a*b)
elif c == "cixma":
    print(a-b)
elif c == "qüvvət":
    print(a**b)    
    