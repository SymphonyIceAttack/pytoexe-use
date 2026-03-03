import os # do clearowania głównie
import math # do pierwiastków

def poczatek(): # tutaj jest początek kalkulatora to wlasnie to jest jako pierwsze odpalane
    os.system("cls")
    print("""
Kalkulator (By Klapuzzz)

kliknij co chcesz obliczyć
""")
    print("1 - dodaj 2 liczby")
    print("2 - odejmij 2 liczby")
    print("3 - pomnóż 2 liczby")
    print("4 - oblicz pierwiastek o mocy 2")

    i = int(input())
    if i == 1:
        os.system("cls")
        dodawanie()
    if i == 2:
        os.system("cls")
        odejmowanie()
    if i == 3:
        os.system("cls")
        mnozenie()
    if i == 4:
        os.system("cls")
        pierwiastkowanie()

def dodawanie(): # tutaj dodawanie
    liczba1 = int(input("podaj pierwszą liczbe którą chcesz dodać "))
    liczba2 = int(input("podaj drugą liczbe którą chcesz dodać "))
    
    wynik = liczba1+liczba2

    print(f"wynik tego działania to: {wynik}")
    input()
    poczatek()

def odejmowanie(): # tutaj odejmowanie
    liczba1 = int(input("podaj pierwszą liczbe którą chcesz odjąć "))
    liczba2 = int(input("podaj drugą liczbe którą chcesz odjąć "))

    wynik = liczba1 - liczba2

    print(f"wynik tego działania to: {wynik}")
    input()
    poczatek()

def mnozenie(): # tutaj jest mnożenie
    liczba1 = int(input("Podaj pierwszą liczbe którą chcesz pomnożyć "))
    liczba2 = int(input("Podaj drugą liczbe którą chcesz pomnożyć "))

    wynik = liczba1 * liczba2
    print(f"wynik tego działania to: {wynik}")
    input()
    poczatek()

def pierwiastkowanie(): #tutaj zachodzi pierwiastkowanie
    pierwiastek = float(input("Podaj pierwiastek z danej liczby "))

    wynik = math.sqrt(pierwiastek)
    print(f"Pierwiastek z tej liczby to: {wynik}")
    input()
    poczatek()

poczatek()