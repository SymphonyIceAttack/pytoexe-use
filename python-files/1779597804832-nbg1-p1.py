a=int(input("Pon el valor de a: "))
x0=int(input("Pon el valor de x0: "))
c=int(input("Pon el valor de c: "))
m=int(input("Pon el valor de m: "))
xi=x0 
r=0
l=0
v=0
for l in range(m):
	print(l+1, ". x0: ", x0)
	r=((a*x0+c)/m)
	v=r-int(r)
	x0=v*m
	print("(ax0+c) mod m: ", int(r), "+", int(x0), "/", m,  "xn+1: ", int(x0), "Numeros rectangulares: ", int(x0), "/", m, "=", v)
	if l==(m-1) and x0==xi:
		print("Generador congruencial mixto confiable.")
		break
	if l==(m-1) and x0!=xi:
		print("Generador congruencial mixto no confiable.")
		break
	if x0==xi:
		print("Generador congruencial mixto no confiable.")
		break