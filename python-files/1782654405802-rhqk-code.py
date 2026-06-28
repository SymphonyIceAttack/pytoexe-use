import random
sjm=input("Please input the code:")
e=1
o=int(sjm[7])^e
if o>7:
	o=o-8
n=(int(sjm[o])-o+10)%10
s=""
for i in range(7):
	if i==o:
		s=s+str(n)
	else:
		s=s+str((int(sjm[i])+10-n)%10)
c=random.randint(0, 6)
a=int(s[c])
r=""
for i in range(7):
	jia=c if i==c else a
	r=r+str((int(s[i])+jia)%10)
print(r+str(e^c))