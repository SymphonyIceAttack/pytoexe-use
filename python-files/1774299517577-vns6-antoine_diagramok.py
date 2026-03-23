import math
import matplotlib.pyplot as plt #Ez az ábrázoláshoz kell
matplotlib.use('TkAgg')
#Ezt a kód futtatása előtt telepíteni kell
from matplotlib.ticker import MultipleLocator #Ahhoz kell, hogy több beosztás legyen a diagrammokon

import numpy as np
#Ezt a kód futtatása előtt telepíteni kell
from sympy import symbols, Eq
#Ezt a kód futtatása előtt telepíteni kell
from sympy.solvers import solve
from sympy import nsolve
 #Ezt a kód futtatása előtt telepíteni kell

#propán-1-ol("p") Antoine-konstansok:
pA=5.31384
pB=1690.864
pC=-51.804

#etanol ("et") Antoine-konstansok:
etA=5.24677
etB=1598.673
etC=-46.424

#x2 pontok felvétele a diagramhoz
x2=[]
diagramlepeskoz=0.001
pontokszama=math.ceil(1/diagramlepeskoz) #Hogy egész számra tudjon futni i index, kerekíteni kell, és felfele a ceillel
segedvaltozo=0
for i in range(pontokszama+1):
    segedvaltozo = i*(diagramlepeskoz)
    x2.append(round(segedvaltozo,4))

#Adott összetételhez tartozó forrponti hőmérséklet megtallálása solverrel:
possz=1.01325 #[Bar] Az össz nyomás
homersekletek=[]
y2=[]
y2segedvaltozo=0
for i in range(pontokszama+1):
    segedvaltozo = round(i*(diagramlepeskoz),5)
    T = symbols("T")
    x = segedvaltozo
    expr = (
            x * 10 ** (etA - etB / (etC + T)) +
            (1 - x) * 10 ** (pA - pB / (pC + T))
            - possz )
    # 0-ra kell rendezni, hogy meg tudja oldani, ezért y-al és nem az össznyomással számolok
    megoldas = nsolve(expr, T,
                      360)  # A numerikus megoldás kezdőértékének az egyenlet tartományába eső 350 K-t állítottam be, hogy könnyen konvergáljon
    homersekletek.append(megoldas)
    y2segedvaltozo = x * 10 ** (etA - etB / (etC + megoldas))/possz
    y2.append(round(y2segedvaltozo,4))

#Forrpont-harmatpont ábrázolás:
plt.plot(x2, homersekletek, label="x (Folyadék)")
plt.plot(y2, homersekletek, label="y (Gőz)")
ax = plt.gca() # Az x tengely sűrítése
# X tengely beosztás
ax.xaxis.set_major_locator(MultipleLocator(0.1))
ax.xaxis.set_minor_locator(MultipleLocator(0.01))
# Y tengely beosztás
ax.yaxis.set_major_locator(MultipleLocator(2.5))
ax.yaxis.set_minor_locator(MultipleLocator(0.5))
# Minor tickek bekapcsolása
ax.minorticks_on()
# Rács beállítások
ax.set_axisbelow(True)  # Rács a görbék mögé kerüljön
ax.grid(which='major', linestyle='-', linewidth=0.8)
ax.grid(which='minor', linestyle=':', linewidth=0.5)
#X-Y tengely megfelelő metszetének beállítása
ax.set_xlim(0, 1)
#Ábrázolási beállítások
plt.title("1-propanol-etanol forrpont-harmatpont diagram")
plt.xlabel("Móltört [-]")
plt.ylabel("Hőmérséklet [K]")
plt.legend()
plt.show()



#Egyensúlyi diagram ábrázolás:
plt.plot(x2, y2, label="Egyensúlyi görbe")
plt.plot(x2, x2, label="Segédvonal")
ax = plt.gca() # A tengely sűrítése
# X tengely beosztás
ax.xaxis.set_major_locator(MultipleLocator(0.1))
ax.xaxis.set_minor_locator(MultipleLocator(0.01))
# Y tengely beosztás
ax.yaxis.set_major_locator(MultipleLocator(0.1))
ax.yaxis.set_minor_locator(MultipleLocator(0.01))
# Minor tickek bekapcsolása
ax.minorticks_on()
# Rács beállítások
ax.set_axisbelow(True)  # Rács a görbék mögé kerüljön
ax.grid(which='major', linestyle='-', linewidth=0.8)
ax.grid(which='minor', linestyle=':', linewidth=0.5)
#X-Y tengely megfelelő metszetének beállítása
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
#Ábrázolási beállítások
plt.title("1-propanol-etanol egyensúlyi diagram")
plt.xlabel("x2 [-]")
plt.ylabel("y2")
plt.legend()
plt.show()



#### Elméleti tányérszám meghatározás
xd=0.95
xw=0.05
xf=0.4
x=xd
y=xd
Nminykoor=[]
Nminxkoor=[]
mintanyerszam=0 #az elméleti tányérszámok darabja

Nminxkoor.append(x)
Nminykoor.append(y)
while x>xw:
    x = x2[y2.index(min(y2, key=lambda yi: abs(yi - y)))]  #key-el meg adhatom hogy y2 listában mi alapján keresse a minimumot lambda: olyan mint a def parancs, yi néven definilja az utána levő parancsot. yi az y2 lista eleme
    Nminxkoor.append(x)
    Nminykoor.append(y)
    y = x #Azért mert a segédvonalra lépcsőzünk, ahol x=y definíció szerint
    Nminxkoor.append(x)
    Nminykoor.append(y)
    mintanyerszam=mintanyerszam+1


# q vonal elkészítése
q=0.7 #Ez módosítható
if q==1:
    qmeredekseg=10000000
else:
    qmeredekseg=q/(q-1)
qx=xf
qy=xf
qxkoor=[]
qykoor=[]
for i in range(len(x2)): #A ciklus ha q pozitív, xf-től előre menjen
    y2segedvaltozo =y2[x2.index(min(x2, key=lambda xi: abs(xi - qx)))]
    if x2[i]>=xf and qy<=y2segedvaltozo and qmeredekseg>0:
       if q==1:
           qxkoor.append(qx)
           qykoor.append(qy)
           qy = qy + diagramlepeskoz
       else:
           qxkoor.append(qx)
           qykoor.append(qy)
           qx = qx + diagramlepeskoz
           qy = qy + diagramlepeskoz * qmeredekseg
for i in reversed(range(len(x2))): #A ciklus ha q pozitív, xf-től vissza menjen
    y2segedvaltozo = y2[x2.index(min(x2, key=lambda xi: abs(xi - qx)))]
    if x2[i]<=xf and qy<=y2segedvaltozo and qmeredekseg<0:
           qxkoor.append(qx)
           qykoor.append(qy)
           qx = qx - diagramlepeskoz
           qy = qy - diagramlepeskoz * qmeredekseg


#Minimális refluxarány szerkesztés:
Rminxkoor=[]
Rminykoor=[]
Rminx=xd
Rminy=xd
Rminxkoor.append(Rminx)
Rminykoor.append(Rminy)
Rminy=max(qykoor) #Mert definició szerint úgy állítottam be, hogy csak az egyenúlyi görbéig menjen a q vonal, ezért annak legnagyobb y értéke ahol metszi azt.
Rminx=x2[y2.index(min(y2, key=lambda yi: abs(yi - Rminy)))] #Az egyensúlyi görbénél metszi, annak y pontja már megvan, x pontját pedig meg lehet keresni
Rminxkoor.append(Rminx)
Rminykoor.append(Rminy)
Rminmeredekseg=(Rminykoor[1]-Rminykoor[0])/(Rminxkoor[1]-Rminxkoor[0]) #Ezzel kiszámolja a meredekséget, mert a tengely metszetekor x2=0, és a meredekség alapján ki lehet a hozzá tartozó y-t számolni
Rminx=0 #Mivel a tengelymetszetre vetítjük rá
Rminxkoor.append(Rminx)
Rminy=Rminy-Rminmeredekseg*(Rminxkoor[1]-Rminxkoor[2]) #Itt kivonja a nagyobb x-ből a kisebbet, hogy megnézzük hány egység volt a lépés., majd a meredekséggel beszorozza, mert annyi egységet válttozik y
Rminykoor.append(Rminy)
Rmin=xd/Rminy-1

#Elméleti tányérszám ábrázolás:
plt.plot(x2, y2, label="Egyensúlyi görbe")
plt.plot(x2, x2, label="Segédvonal")
plt.plot(xd, 0, label="xd:"+str(xd),marker='d', markerfacecolor='r')
plt.plot(xw, 0, label="xw:"+str(xw),marker='d', markerfacecolor='r')
plt.plot(Nminxkoor, Nminykoor, label="Lépcső")
ax = plt.gca() # A tengely sűrítése
# X tengely beosztás
ax.xaxis.set_major_locator(MultipleLocator(0.1))
ax.xaxis.set_minor_locator(MultipleLocator(0.01))
# Y tengely beosztás
ax.yaxis.set_major_locator(MultipleLocator(0.1))
ax.yaxis.set_minor_locator(MultipleLocator(0.01))
# Minor tickek bekapcsolása
ax.minorticks_on()
# Rács beállítások
ax.set_axisbelow(True)  # Rács a görbék mögé kerüljön
ax.grid(which='major', linestyle='-', linewidth=0.8)
ax.grid(which='minor', linestyle=':', linewidth=0.5)
#X-Y tengely megfelelő metszetének beállítása
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
#Ábrázolási beállítások
plt.title("1-propanol-etanol elmételeti tányérszám:" + str(mintanyerszam))
plt.xlabel("x2 [-]")
plt.ylabel("y2")
plt.legend()
plt.show()

#Minimális refluxarány ábrázolás:
plt.plot(x2, y2, label="Egyensúlyi görbe")
plt.plot(x2, x2, label="Segédvonal")
plt.plot(xd, 0, label="xd:"+str(xd),marker='d', markerfacecolor='r')
plt.plot(xw, 0, label="xw:"+str(xw),marker='d', markerfacecolor='r')
plt.plot(xf, 0, label="xf:"+str(xf),marker='d', markerfacecolor='r')
plt.plot(qxkoor, qykoor, label="q vonal, q="+str(q))
plt.plot(Rminxkoor,Rminykoor)
ax = plt.gca() # A tengely sűrítése
# X tengely beosztás
ax.xaxis.set_major_locator(MultipleLocator(0.1))
ax.xaxis.set_minor_locator(MultipleLocator(0.01))
# Y tengely beosztás
ax.yaxis.set_major_locator(MultipleLocator(0.1))
ax.yaxis.set_minor_locator(MultipleLocator(0.01))
# Minor tickek bekapcsolása
ax.minorticks_on()
# Rács beállítások
ax.set_axisbelow(True)  # Rács a görbék mögé kerüljön
ax.grid(which='major', linestyle='-', linewidth=0.8)
ax.grid(which='minor', linestyle=':', linewidth=0.5)
#X-Y tengely megfelelő metszetének beállítása
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
#Ábrázolási beállítások
plt.title("1-propanol-etanol minimális refluxarány:"+str(round(Rmin,4)))
plt.xlabel("x2 [-]")
plt.ylabel("y2")
plt.legend()
plt.show()