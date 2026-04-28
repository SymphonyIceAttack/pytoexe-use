encyklopedia = {
    # === PODSTAWY ===
    "print": "print – pokazuje tekst lub wynik na ekranie.\n   Przykład: print('Witaj!') – zobaczysz: Witaj!",
    "input": "input – pyta użytkownika o tekst i czeka na wpisanie.\n   Przykład: imie = input('Jak się nazywasz?') – to co wpiszesz, trafi do zmiennej imie.",
    "zmienna": "Zmienna – pudełko z etykietką, w którym przechowujesz daną (liczbę, tekst itp.).\n   Przykład: wiek = 25 – od tej pory 'wiek' oznacza 25.",
    "typ": "Typ – rodzaj danej: tekst, liczba całkowita, liczba z kropką, prawda/fałsz.\n   Przykład: 'Ala' to tekst, 7 to liczba całkowita, 3.14 to liczba z kropką.",
    "str": "str (string) – rodzaj danych dla tekstu (liter, słów, zdań). Zapisujesz w cudzysłowie.\n   Przykład: powitanie = 'Cześć' – cudzysłów mówi Pythonowi, że to tekst.",
    "int": "int – rodzaj danych dla liczb całkowitych (bez kropki).\n   Przykład: liczba = 10 – możesz potem dodawać: liczba + 5 da 15.",
    "float": "float – rodzaj danych dla liczb z kropką (ułamki).\n   Przykład: temperatura = 36.6 – to float.",
    "bool": "bool – rodzaj danych dla odpowiedzi tak/nie. Tylko dwie możliwości: True (prawda) lub False (fałsz).\n   Przykład: czy_pada = False – znaczy, że nie pada.",
    
    # === OPERACJE NA NAPISACH I LICZBACH ===
    "konkatenacja": "Konkatenacja – łączenie tekstów za pomocą znaku +.\n   Przykład: 'Ala' + 'ma' + 'kota' daje 'Alamakota' (bez spacji).",
    "f-string": "f-string – sposób na wstawienie zmiennej do środka tekstu. Przed tekstem dajesz f, a zmienną w { }.\n   Przykład: imie='Ola'; print(f'Cześć, {imie}!') – pokaże 'Cześć, Ola!'.",
    "str()": "str() – zamienia dowolną wartość na tekst. Używasz, gdy chcesz połączyć tekst z liczbą.\n   Przykład: print('Wynik to ' + str(5)) – zadziała, bo liczba 5 stała się tekstem.",
    "int()": "int() – zamienia tekst (np. '123') lub liczbę z kropką na liczbę całkowitą.\n   Przykład: liczba = int('50') – teraz 50 to liczba, możesz mnożyć.",
    "float()": "float() – zamienia tekst lub liczbę na liczbę z kropką (ułamek).\n   Przykład: wynik = float('7.5') – teraz 7.5 to liczba zmiennoprzecinkowa.",
    "type()": "type() – sprawdza, jakiego rodzaju jest dana wartość.\n   Przykład: print(type(10)) – pokaże: <class 'int'> (czyli liczba całkowita).",
    
    # === STRUKTURY DANYCH ===
    "lista": "Lista – uporządkowana kolekcja rzeczy w nawiasach kwadratowych []. Możesz zmieniać jej zawartość.\n   Przykład: owoce = ['jabłko', 'banan'] – lista dwóch tekstów.",
    "krotka": "Krotka – jak lista, ale nie można jej zmienić po utworzeniu. Zapisujesz w nawiasach okrągłych ().\n   Przykład: kolory = ('czerwony', 'zielony') – krotki używasz, gdy coś ma być stałe.",
    "slownik": "Słownik – zbiór par: klucz -> wartość, w nawiasach klamrowych {}. Zamiast numerka używasz klucza.\n   Przykład: osoba = {'imię': 'Jan', 'wiek': 30} – aby dostać 'Jan', wpisz osoba['imię'].",
    "zbiór": "Zbiór – nieuporządkowana kolekcja unikalnych elementów (bez powtórzeń). Zapisujesz w {}.\n   Przykład: liczby = {1, 2, 3, 2} – zbiór będzie {1,2,3} (duplikat znika).",
    
    # === INSTRUKCJE WARUNKOWE ===
    "if": "if – sprawdza warunek: jeśli prawda, wykonuje kod pod spodem.\n   Przykład: if wiek >= 18: print('Pełnoletni') – jeśli wiek 18 lub więcej, wyświetli napis.",
    "else": "else – część if, wykonuje się gdy warunek w if jest fałszywy.\n   Przykład: if pogoda == 'deszcz': print('Weź parasol') else: print('Możesz wyjść bez parasola')",
    "elif": "elif – skrót od 'else if' – sprawdza kolejny warunek, gdy poprzedni był fałszywy.\n   Przykład: if x > 0: print('dodatnia') elif x < 0: print('ujemna') else: print('zero')",
    
    # === PĘTLE ===
    "for": "for – Dla każdego elementu z listy (lub innej grupy) wykonaj czynności.\n   Przykład: owoce=['jabłko','banan']; for owoc in owoce: [print](owoc) – wypisze jabłko, banan. (Zobacz też [range])",
    "while": "while – Powtarza czynności tak długo, jak długo warunek jest prawdziwy.\n   Przykład: i=0; while i<3: print(i); i+=1 – wypisze 0,1,2 (potem przestaje).",
    "range": "range – Tworzy ciąg liczb od 0 do podanej liczby (bez niej). Używane głównie w pętli [for].\n   Przykład: for i in range(3): print(i) – wypisze 0,1,2.",
    "break": "break – Natychmiast przerywa działanie pętli (wyskakuje z niej).\n   Przykład: for i in range(5): if i==3: break; print(i) – wypisze 0,1,2 i koniec.",
    "continue": "continue – Przeskakuje do następnego obrotu pętli (pomija dalszy kod w tej iteracji).\n   Przykład: for i in range(3): if i==1: continue; [print](i) – wypisze 0,2 (bez 1).",
    
    # === FUNKCJE ===
    "def": "def – Słowo, które tworzy własną funkcję (kawałek kodu do wielokrotnego użycia).\n   Przykład: def przywitaj(): print('Cześć!') – potem wywołujesz przywitaj()",
    "return": "return – Zwraca wartość z funkcji (i kończy jej działanie).\n   Przykład: def dodaj(a,b): return a+b – wynik = dodaj(2,3) da 5.",
    "parametr": "Parametr – zmienna w nawiasie funkcji, która przyjmuje dane przy wywołaniu.\n   Przykład: def powiedz(tekst): – 'tekst' to parametr.",
    "argument": "Argument – konkretna wartość, którą przekazujesz do funkcji.\n   Przykład: powiedz('Hello') – 'Hello' to argument.",
    
    # === KLASY I OBIEKTY ===
    "class": "class – Szablon do tworzenia obiektów (np. wzór dla psa, samochodu).\n   Przykład: class Pies: def szczekaj(self): print('Hau!') – potem moj_pies = Pies(); moj_pies.szczekaj()",
    "obiekt": "Obiekt – konkretny egzemplarz klasy (jak pies o imieniu Reksio).\n   Przykład: reksio = Pies() – reksio to obiekt.",
    "metoda": "Metoda – funkcja należąca do obiektu (coś co obiekt potrafi robić).\n   Przykład: reksio.szczekaj() – 'szczekaj' to metoda.",
    "atrybut": "Atrybut – zmienna należąca do obiektu (cecha obiektu).\n   Przykład: reksio.wiek = 5 – 'wiek' to atrybut.",
    "self": "self – Pierwszy parametr w metodzie klasy; odnosi się do konkretnego obiektu.\n   Przykład: def przedstaw(self): print(self.imie) – 'self' mówi, czyje imię.",
    "init": "__init__ – Specjalna metoda wywoływana automatycznie przy tworzeniu obiektu. Służy do ustawiania początkowych cech.\n   Przykład: def __init__(self, imie): self.imie = imie",
    "dziedziczenie": "Dziedziczenie – Klasa może przejąć cechy (atrybuty i metody) od innej klasy.\n   Przykład: class Kot(Zwierze): pass – Kot ma wszystko, co Zwierzę.",
    
    # === MODUŁY I IMPORTOWANIE ===
    "import": "import – Wczytuje gotowy zestaw dodatkowych funkcji (moduł) do twojego programu.\n   Przykład: import math – potem możesz użyć math.sqrt(16) do pierwiastka.",
    "from": "from ... import ... – Pozwala zaimportować tylko konkretną funkcję z modułu, bez pisania nazwy modułu.\n   Przykład: from math import pi – potem używasz same pi, nie math.pi.",
    "modul": "Moduł – plik z kodem Pythona, który zawiera przydatne funkcje. Importujesz go, by nie pisać wszystkiego od zera.\n   Przykład: moduł 'random' losuje liczby.",
    
    # === OBSŁUGA BŁĘDÓW ===
    "try": "try – Blok, w którym może wystąpić błąd (np. dzielenie przez zero). Używasz go z except.\n   Przykład: try: wynik = 10/0 except: print('Błąd!') – program nie wybuchnie.",
    "except": "except – Blok, który przechwytuje błąd z try i wykonuje własne instrukcje.\n   Przykład: except ValueError: print('To nie jest liczba')",
    "typeerror": "TypeError – Błąd pojawia się, gdy łączysz dwa różne typy, np. tekst + liczba.\n   Przykład: 'wynik: ' + 5 – Python krzyczy TypeError.",
    "valueerror": "ValueError – Błąd, gdy funkcja dostaje wartość poprawnego typu, ale niewłaściwą (np. int('abc')).\n   Przykład: int('pięć') – ValueError, bo 'pięć' nie jest cyfrą.",
    
    # === INNE ===
    "none": "None – Specjalna wartość oznaczająca 'nic', 'pustkę'. Funkcja często zwraca None, gdy nic nie zwraca.\n   Przykład: wynik = None – później możesz sprawdzić, czy coś tam wstawiono.",
    "komentarz": "Komentarz – Tekst ignorowany przez Pythona, zaczyna się od #. Służy do opisywania kodu.\n   Przykład: # to jest komentarz – Python go pomija.",
    "operatory porównania": "Operatory porównania – Służą do porównywania wartości: == (równe), != (różne), <, >, <=, >=. Wynik to True lub False.\n   Przykład: 5 > 3 daje True, 2 == 2 daje True.",
    "operatory logiczne": "Operatory logiczne – Łączą warunki: and (i), or (lub), not (nie).\n   Przykład: if wiek >= 18 and obywatel == 'PL': – oba warunki muszą być prawdziwe.",
    "pep8": "PEP 8 – Zbiór zasad, jak ładnie pisać kod Pythona (gdzie spacje, jak nazywać zmienne). Warto ich przestrzegać, by kod był czytelny.",
    "pętla nieskończona": "Pętla nieskończona – Pętla, która nigdy się nie kończy, bo warunek jest zawsze prawdziwy (np. while True:). Przerywa się ją [break].\n   Przykład: while True: print('ciągle') – będzie pisać w kółko.",
}