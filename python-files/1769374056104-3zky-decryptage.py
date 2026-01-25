import sys


def encryptage():
    
    m = sys.argv[1]
    a=0
    m=list(m)
    b=len(m)
    
    while a!=b:
        if m[a]=="k":
            m[a]="a"
        elif m[a]=="s":
            m[a]="b"
        elif m[a]=="r":
            m[a]="c"
        elif m[a]=="v":
            m[a]="d"
        elif m[a]=="z":
            m[a]="e"
        elif m[a]=="b":
            m[a]="f"
        elif m[a]=="h":
            m[a]="g"
        elif m[a]=="q":
            m[a]="h"
        elif m[a]=="w":
            m[a]="i"
        elif m[a]=="a":
            m[a]="j"
        elif m[a]=="f":
            m[a]="k"
        elif m[a]=="d":
            m[a]="l"
        elif m[a]=="t":
            m[a]="m"
        elif m[a]=="i":
            m[a]="n"
        elif m[a]=="c":
            m[a]="o"
        elif m[a]=="e":
            m[a]="p"
        elif m[a]=="l":
            m[a]="q"
        elif m[a]=="p":
            m[a]="r"
        elif m[a]=="g":
            m[a]="s"
        elif m[a]=="o":
            m[a]="t"
        elif m[a]=="j":
            m[a]="u"
        elif m[a]=="m":
            m[a]="v"
        elif m[a]=="n":
            m[a]="w"
        elif m[a]=="y":
            m[a]="x"
        elif m[a]=="x":
            m[a]="y"
        elif m[a]=="u":
            m[a]="z" 
        elif m[a]=="P":
            m[a]=" "
        elif m[a]=="A":
            m[a]="'"
        elif m[a]=="G":
            m[a]="?"
        elif m[a]=="E":
            m[a]="!"     
        elif m[a]=="M":
            m[a]="-"      
        elif m[a]=="5":
            m[a]="é"
        elif m[a]=="8":
            m[a]="à"
        
        a+=1  
    m= ''.join(m)
    print(m)

encryptage()