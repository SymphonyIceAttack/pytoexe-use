from turtle import *
#positionnement initial comme blockly
#setworldcoordinates(-100, -100, 300, 200)
left(90)
pensize(4)

def étoile(c):
  for i in range (0,5):
    forward(c)
    right(144)
    
def saut(l):
    penup()
    forward(l)
    pendown()
    
def multiétoiles(n,l,c):
    for i in range(n):
        étoile(c)
        saut(l)
        penup()
        #right(20)
        pendown()
        right(360//n)
    
    
multiétoiles(1500,30,200)
