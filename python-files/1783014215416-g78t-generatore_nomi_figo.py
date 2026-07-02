import random,string,time,os
GREEN="\033[92m";CYAN="\033[96m";YELLOW="\033[93m";RESET="\033[0m"
os.system("cls" if os.name=="nt" else "clear")
print(GREEN+'\n ██████╗ ██╗███╗   ██╗ █████╗ ███████╗\n ██╔══██╗██║████╗  ██║██╔══██╗██╔════╝\n ██████╔╝██║██╔██╗ ██║███████║███████╗\n ██╔══██╗██║██║╚██╗██║██╔══██║╚════██║\n ██║  ██║██║██║ ╚████║██║  ██║███████║\n ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝\n'+RESET)
print(CYAN+"Developed By Rinascere\n"+RESET)
q=int(input("➜ Inserisci Quanti Nomi Generare: "))
l=int(input("➜ Inserisci Lunghezza: "))
print(YELLOW+"\nAvvio generatore..."+RESET)
for i in range(51):
    print("\r["+"█"*i+"░"*(50-i)+f"] {i*2}%",end="",flush=True)
    time.sleep(0.03)
chars=string.ascii_lowercase+string.digits
print(GREEN+"\n\n=== NOMI GENERATI ===\n"+RESET)
with open("nomi.txt","w") as f:
    for i in range(1,q+1):
        n="".join(random.choice(chars) for _ in range(l))
        print(f"[{i:03}] > {n}")
        f.write(n+"\n")
print(CYAN+"\nSalvati anche in nomi.txt"+RESET)
input("\nPremi INVIO per uscire...")
