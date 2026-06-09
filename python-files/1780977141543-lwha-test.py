print("Este es un test de groomeo")

gusto=int(input("cual es tu edad de preferencia? "))
if (gusto==0):
    gusto=int(input("dudo que se puedan tener 0 años... cual es tu edad de preferencia? "))

while(gusto<18):
    print("sos cypher?")
    gusto=int(input("cual es tu edad de preferencia? "))
print("felicidades, usted no es un groomer")