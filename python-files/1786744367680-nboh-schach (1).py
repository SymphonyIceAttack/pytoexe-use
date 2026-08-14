#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schach gegen den Computer
==========================
Starke KI: Minimax mit Alpha-Beta-Pruning, Zugsortierung (MVV-LVA),
Quiescence-Suche fuer Schlagzuege (verhindert Materialverlust durch den
"Horizont-Effekt") und einem Bewertungssystem, das stark auf Materialgewinn
und -erhalt optimiert ist.

Links neben dem Brett zeigt ein Panel laufend die Materialbilanz an:
Bauer=1, Springer=3, Laeufer=3, Turm=5, Dame=9, Koenig=unendlich (kein Wert).
"""

import copy
import random
import tkinter as tk
from tkinter import messagebox, ttk

# ---------------------------------------------------------------------------
# Grunddaten
# ---------------------------------------------------------------------------

WERTE = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
SYMBOLE = {
    ('w', 'K'): '\u2654', ('w', 'Q'): '\u2655', ('w', 'R'): '\u2656',
    ('w', 'B'): '\u2657', ('w', 'N'): '\u2658', ('w', 'P'): '\u2659',
    ('b', 'K'): '\u265A', ('b', 'Q'): '\u265B', ('b', 'R'): '\u265C',
    ('b', 'B'): '\u265D', ('b', 'N'): '\u265E', ('b', 'P'): '\u265F',
}
NAMEN = {'P': 'Bauer', 'N': 'Springer', 'B': 'Laeufer',
         'R': 'Turm', 'Q': 'Dame', 'K': 'Koenig'}

# Piece-Square-Tables (aus Sicht Weiss, Zeile 0 = Reihe 8)
PST_P = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [5, 5, 10, 25, 25, 10, 5, 5],
    [0, 0, 0, 20, 20, 0, 0, 0],
    [5, -5, -10, 0, 0, -10, -5, 5],
    [5, 10, 10, -20, -20, 10, 10, 5],
    [0, 0, 0, 0, 0, 0, 0, 0],
]
PST_N = [
    [-50, -40, -30, -30, -30, -30, -40, -50],
    [-40, -20, 0, 0, 0, 0, -20, -40],
    [-30, 0, 10, 15, 15, 10, 0, -30],
    [-30, 5, 15, 20, 20, 15, 5, -30],
    [-30, 0, 15, 20, 20, 15, 0, -30],
    [-30, 5, 10, 15, 15, 10, 5, -30],
    [-40, -20, 0, 5, 5, 0, -20, -40],
    [-50, -40, -30, -30, -30, -30, -40, -50],
]
PST_B = [
    [-20, -10, -10, -10, -10, -10, -10, -20],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-10, 0, 5, 10, 10, 5, 0, -10],
    [-10, 5, 5, 10, 10, 5, 5, -10],
    [-10, 0, 10, 10, 10, 10, 0, -10],
    [-10, 10, 10, 10, 10, 10, 10, -10],
    [-10, 5, 0, 0, 0, 0, 5, -10],
    [-20, -10, -10, -10, -10, -10, -10, -20],
]
PST_R = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [5, 10, 10, 10, 10, 10, 10, 5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [0, 0, 0, 5, 5, 0, 0, 0],
]
PST_Q = [
    [-20, -10, -10, -5, -5, -10, -10, -20],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-10, 0, 5, 5, 5, 5, 0, -10],
    [-5, 0, 5, 5, 5, 5, 0, -5],
    [0, 0, 5, 5, 5, 5, 0, -5],
    [-10, 5, 5, 5, 5, 5, 0, -10],
    [-10, 0, 5, 0, 0, 0, 0, -10],
    [-20, -10, -10, -5, -5, -10, -10, -20],
]
PST_K = [
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-20, -30, -30, -40, -40, -30, -30, -20],
    [-10, -20, -20, -20, -20, -20, -20, -10],
    [20, 20, 0, 0, 0, 0, 20, 20],
    [20, 30, 10, 0, 0, 10, 30, 20],
]
PST = {'P': PST_P, 'N': PST_N, 'B': PST_B, 'R': PST_R, 'Q': PST_Q, 'K': PST_K}


def pst_wert(typ, farbe, zeile, spalte):
    tabelle = PST[typ]
    if farbe == 'w':
        return tabelle[zeile][spalte]
    else:
        return tabelle[7 - zeile][spalte]


# ---------------------------------------------------------------------------
# Spielzustand & Regelwerk
# ---------------------------------------------------------------------------

class Zug:
    __slots__ = ('von', 'nach', 'flag', 'promo', 'geschlagen')

    def __init__(self, von, nach, flag='normal', promo=None, geschlagen=None):
        self.von = von
        self.nach = nach
        self.flag = flag        # normal, doppelt, enpassant, rochadeK, rochadeD, umwandlung
        self.promo = promo      # Zielfigur bei Umwandlung, z.B. 'Q'
        self.geschlagen = geschlagen  # ('farbe','typ') falls geschlagen wurde

    def __eq__(self, other):
        return (self.von == other.von and self.nach == other.nach
                and self.flag == other.flag and self.promo == other.promo)


class Board:
    def __init__(self):
        self.grid = [[None] * 8 for _ in range(8)]
        self.zugfarbe = 'w'
        self.rochade = {'wK': True, 'wQ': True, 'bK': True, 'bQ': True}
        self.en_passant = None  # (zeile, spalte) Zielfeld eines moeglichen en-passant-Schlags
        self.history = []       # fuer Zuglisten-Anzeige
        self._setup()

    def _setup(self):
        ordnung = ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
        for s in range(8):
            self.grid[0][s] = ('b', ordnung[s])
            self.grid[1][s] = ('b', 'P')
            self.grid[6][s] = ('w', 'P')
            self.grid[7][s] = ('w', ordnung[s])
        self.wk = (7, 4)
        self.bk = (0, 4)

    def klon(self):
        neu = Board.__new__(Board)
        neu.grid = [row[:] for row in self.grid]
        neu.zugfarbe = self.zugfarbe
        neu.rochade = dict(self.rochade)
        neu.en_passant = self.en_passant
        neu.history = self.history  # wird fuer Suche nicht veraendert
        neu.wk = self.wk
        neu.bk = self.bk
        return neu

    def koenig_feld(self, farbe):
        return self.wk if farbe == 'w' else self.bk

    # ---- schnelle Legalitaetspruefung ohne vollstaendigen Klon ----
    def _anwenden_fuer_check(self, zug, farbe):
        touched = []

        def setze(z, s, wert):
            touched.append((z, s, self.grid[z][s]))
            self.grid[z][s] = wert

        z0, s0 = zug.von
        z1, s1 = zug.nach
        figur = self.grid[z0][s0]
        if zug.flag == 'enpassant':
            setze(z0, s1, None)
        setze(z1, s1, figur if zug.flag != 'umwandlung' else (farbe, zug.promo))
        setze(z0, s0, None)
        if zug.flag in ('rochadeK', 'rochadeD'):
            reihe = z0
            if zug.flag == 'rochadeK':
                setze(reihe, 7, None)
                setze(reihe, 5, (farbe, 'R'))
            else:
                setze(reihe, 0, None)
                setze(reihe, 3, (farbe, 'R'))
        koenig_geaendert = False
        alter_koenig = None
        if figur[1] == 'K':
            koenig_geaendert = True
            if farbe == 'w':
                alter_koenig = self.wk
                self.wk = (z1, s1)
            else:
                alter_koenig = self.bk
                self.bk = (z1, s1)
        return touched, koenig_geaendert, alter_koenig

    def _rueckgaengig_fuer_check(self, touched, koenig_geaendert, alter_koenig, farbe):
        for z, s, wert in reversed(touched):
            self.grid[z][s] = wert
        if koenig_geaendert:
            if farbe == 'w':
                self.wk = alter_koenig
            else:
                self.bk = alter_koenig

    # ---------------- Angriffserkennung ----------------
    def feld_angegriffen(self, feld, von_farbe):
        z0, s0 = feld
        # Bauern
        richtung = 1 if von_farbe == 'w' else -1
        for ds in (-1, 1):
            z, s = z0 + richtung, s0 + ds
            if 0 <= z < 8 and 0 <= s < 8 and self.grid[z][s] == (von_farbe, 'P'):
                return True
        # Springer
        for dz, ds in ((-2, -1), (-2, 1), (-1, -2), (-1, 2),
                       (1, -2), (1, 2), (2, -1), (2, 1)):
            z, s = z0 + dz, s0 + ds
            if 0 <= z < 8 and 0 <= s < 8 and self.grid[z][s] == (von_farbe, 'N'):
                return True
        # Koenig
        for dz in (-1, 0, 1):
            for ds in (-1, 0, 1):
                if dz == 0 and ds == 0:
                    continue
                z, s = z0 + dz, s0 + ds
                if 0 <= z < 8 and 0 <= s < 8 and self.grid[z][s] == (von_farbe, 'K'):
                    return True
        # Laeufer/Dame diagonal
        for dz, ds in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            z, s = z0 + dz, s0 + ds
            while 0 <= z < 8 and 0 <= s < 8:
                p = self.grid[z][s]
                if p is not None:
                    if p[0] == von_farbe and p[1] in ('B', 'Q'):
                        return True
                    break
                z += dz
                s += ds
        # Turm/Dame gerade
        for dz, ds in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            z, s = z0 + dz, s0 + ds
            while 0 <= z < 8 and 0 <= s < 8:
                p = self.grid[z][s]
                if p is not None:
                    if p[0] == von_farbe and p[1] in ('R', 'Q'):
                        return True
                    break
                z += dz
                s += ds
        return False

    def im_schach(self, farbe):
        kf = self.koenig_feld(farbe)
        if kf is None:
            return False
        gegner = 'b' if farbe == 'w' else 'w'
        return self.feld_angegriffen(kf, gegner)

    # ---------------- Zuggenerierung ----------------
    def pseudo_zuege(self, farbe):
        zuege = []
        for z in range(8):
            for s in range(8):
                p = self.grid[z][s]
                if p is None or p[0] != farbe:
                    continue
                typ = p[1]
                if typ == 'P':
                    zuege.extend(self._bauern_zuege(z, s, farbe))
                elif typ == 'N':
                    zuege.extend(self._sprung_zuege(z, s, farbe))
                elif typ == 'B':
                    zuege.extend(self._gleit_zuege(z, s, farbe, ((-1, -1), (-1, 1), (1, -1), (1, 1))))
                elif typ == 'R':
                    zuege.extend(self._gleit_zuege(z, s, farbe, ((-1, 0), (1, 0), (0, -1), (0, 1))))
                elif typ == 'Q':
                    zuege.extend(self._gleit_zuege(z, s, farbe, ((-1, -1), (-1, 1), (1, -1), (1, 1),
                                                                  (-1, 0), (1, 0), (0, -1), (0, 1))))
                elif typ == 'K':
                    zuege.extend(self._koenig_zuege(z, s, farbe))
        return zuege

    def _bauern_zuege(self, z, s, farbe):
        zuege = []
        richtung = -1 if farbe == 'w' else 1
        start_reihe = 6 if farbe == 'w' else 1
        promo_reihe = 0 if farbe == 'w' else 7
        # ein Feld vor
        nz = z + richtung
        if 0 <= nz < 8 and self.grid[nz][s] is None:
            if nz == promo_reihe:
                for pf in ('Q', 'R', 'B', 'N'):
                    zuege.append(Zug((z, s), (nz, s), 'umwandlung', pf))
            else:
                zuege.append(Zug((z, s), (nz, s)))
            if z == start_reihe:
                nz2 = z + 2 * richtung
                if self.grid[nz2][s] is None:
                    zuege.append(Zug((z, s), (nz2, s), 'doppelt'))
        # Schlagzuege
        for ds in (-1, 1):
            ns = s + ds
            if 0 <= nz < 8 and 0 <= ns < 8:
                ziel = self.grid[nz][ns]
                if ziel is not None and ziel[0] != farbe:
                    if nz == promo_reihe:
                        for pf in ('Q', 'R', 'B', 'N'):
                            zuege.append(Zug((z, s), (nz, ns), 'umwandlung', pf, ziel))
                    else:
                        zuege.append(Zug((z, s), (nz, ns), geschlagen=ziel))
                elif self.en_passant == (nz, ns):
                    geschlagen = (('b' if farbe == 'w' else 'w'), 'P')
                    zuege.append(Zug((z, s), (nz, ns), 'enpassant', geschlagen=geschlagen))
        return zuege

    def _sprung_zuege(self, z, s, farbe):
        zuege = []
        for dz, ds in ((-2, -1), (-2, 1), (-1, -2), (-1, 2),
                       (1, -2), (1, 2), (2, -1), (2, 1)):
            nz, ns = z + dz, s + ds
            if 0 <= nz < 8 and 0 <= ns < 8:
                ziel = self.grid[nz][ns]
                if ziel is None:
                    zuege.append(Zug((z, s), (nz, ns)))
                elif ziel[0] != farbe:
                    zuege.append(Zug((z, s), (nz, ns), geschlagen=ziel))
        return zuege

    def _koenig_zuege(self, z, s, farbe):
        zuege = []
        for dz in (-1, 0, 1):
            for ds in (-1, 0, 1):
                if dz == 0 and ds == 0:
                    continue
                nz, ns = z + dz, s + ds
                if 0 <= nz < 8 and 0 <= ns < 8:
                    ziel = self.grid[nz][ns]
                    if ziel is None:
                        zuege.append(Zug((z, s), (nz, ns)))
                    elif ziel[0] != farbe:
                        zuege.append(Zug((z, s), (nz, ns), geschlagen=ziel))
        # Rochade
        reihe = 7 if farbe == 'w' else 0
        if (z, s) == (reihe, 4) and not self.im_schach(farbe):
            gegner = 'b' if farbe == 'w' else 'w'
            if self.rochade[farbe + 'K']:
                if self.grid[reihe][5] is None and self.grid[reihe][6] is None:
                    if (not self.feld_angegriffen((reihe, 5), gegner)
                            and not self.feld_angegriffen((reihe, 6), gegner)):
                        zuege.append(Zug((z, s), (reihe, 6), 'rochadeK'))
            if self.rochade[farbe + 'Q']:
                if self.grid[reihe][1] is None and self.grid[reihe][2] is None and self.grid[reihe][3] is None:
                    if (not self.feld_angegriffen((reihe, 3), gegner)
                            and not self.feld_angegriffen((reihe, 2), gegner)):
                        zuege.append(Zug((z, s), (reihe, 2), 'rochadeD'))
        return zuege

    def _gleit_zuege(self, z, s, farbe, richtungen):
        zuege = []
        for dz, ds in richtungen:
            nz, ns = z + dz, s + ds
            while 0 <= nz < 8 and 0 <= ns < 8:
                ziel = self.grid[nz][ns]
                if ziel is None:
                    zuege.append(Zug((z, s), (nz, ns)))
                else:
                    if ziel[0] != farbe:
                        zuege.append(Zug((z, s), (nz, ns), geschlagen=ziel))
                    break
                nz += dz
                ns += ds
        return zuege

    def zug_ausfuehren(self, zug):
        z0, s0 = zug.von
        z1, s1 = zug.nach
        figur = self.grid[z0][s0]
        farbe, typ = figur

        self.en_passant_neu = None
        if zug.flag == 'enpassant':
            self.grid[z0][s1] = None  # geschlagener Bauer steht neben dem Zielfeld
        if zug.flag == 'doppelt':
            self.en_passant_neu = ((z0 + z1) // 2, s0)

        self.grid[z1][s1] = figur
        self.grid[z0][s0] = None

        if zug.flag == 'umwandlung':
            self.grid[z1][s1] = (farbe, zug.promo)

        if zug.flag in ('rochadeK', 'rochadeD'):
            reihe = z0
            if zug.flag == 'rochadeK':
                turm = self.grid[reihe][7]
                self.grid[reihe][7] = None
                self.grid[reihe][5] = turm
            else:
                turm = self.grid[reihe][0]
                self.grid[reihe][0] = None
                self.grid[reihe][3] = turm

        if typ == 'K':
            self.rochade[farbe + 'K'] = False
            self.rochade[farbe + 'Q'] = False
        if typ == 'R':
            if (z0, s0) == (7, 0):
                self.rochade['wQ'] = False
            elif (z0, s0) == (7, 7):
                self.rochade['wK'] = False
            elif (z0, s0) == (0, 0):
                self.rochade['bQ'] = False
            elif (z0, s0) == (0, 7):
                self.rochade['bK'] = False
        # falls ein Turm geschlagen wurde, Rochaderecht des Gegners aktualisieren
        if (z1, s1) == (7, 0):
            self.rochade['wQ'] = False
        elif (z1, s1) == (7, 7):
            self.rochade['wK'] = False
        elif (z1, s1) == (0, 0):
            self.rochade['bQ'] = False
        elif (z1, s1) == (0, 7):
            self.rochade['bK'] = False

        self.en_passant = self.en_passant_neu
        self.zugfarbe = 'b' if farbe == 'w' else 'w'
        if typ == 'K':
            if farbe == 'w':
                self.wk = (z1, s1)
            else:
                self.bk = (z1, s1)

    def legale_zuege(self, farbe):
        legale = []
        for zug in self.pseudo_zuege(farbe):
            touched, kc, ok = self._anwenden_fuer_check(zug, farbe)
            if not self.im_schach(farbe):
                legale.append(zug)
            self._rueckgaengig_fuer_check(touched, kc, ok, farbe)
        return legale

    def spielende(self, farbe):
        """Gibt ('matt'|'patt'|None) zurueck fuer die ziehende Farbe."""
        if self.legale_zuege(farbe):
            return None
        return 'matt' if self.im_schach(farbe) else 'patt'


# ---------------------------------------------------------------------------
# Bewertung & KI
# ---------------------------------------------------------------------------

def bewertung(board):
    """Positive Werte = Vorteil Weiss, negative = Vorteil Schwarz (in Bauerneinheiten*100)."""
    summe = 0
    for z in range(8):
        for s in range(8):
            p = board.grid[z][s]
            if p is None:
                continue
            farbe, typ = p
            wert = WERTE[typ] * 100 + pst_wert(typ, farbe, z, s)
            summe += wert if farbe == 'w' else -wert
    return summe


def mvv_lva_sortierschluessel(zug):
    if zug.geschlagen is None:
        return 0
    angreifer_typ = 'P'  # grobe Naeherung reicht fuer Sortierung
    return 10 * WERTE.get(zug.geschlagen[1], 0)


class KI:
    def __init__(self, farbe, tiefe=4):
        self.farbe = farbe
        self.tiefe = tiefe
        self.knoten = 0

    def bester_zug(self, board):
        self.knoten = 0
        farbe = self.farbe
        zuege = board.legale_zuege(farbe)
        if not zuege:
            return None
        zuege.sort(key=mvv_lva_sortierschluessel, reverse=True)
        bester = None
        alpha, beta = -10 ** 9, 10 ** 9
        maximiere = (farbe == 'w')
        best_wert = -10 ** 9 if maximiere else 10 ** 9
        for zug in zuege:
            probe = board.klon()
            probe.zug_ausfuehren(zug)
            wert = self._suche(probe, self.tiefe - 1, alpha, beta, not maximiere)
            if maximiere and wert > best_wert:
                best_wert = wert
                bester = zug
                alpha = max(alpha, wert)
            elif not maximiere and wert < best_wert:
                best_wert = wert
                bester = zug
                beta = min(beta, wert)
        return bester or random.choice(zuege)

    def _suche(self, board, tiefe, alpha, beta, maximiere):
        self.knoten += 1
        farbe = 'w' if maximiere else 'b'
        zuege = board.legale_zuege(farbe)
        if not zuege:
            if board.im_schach(farbe):
                # Matt: je naeher am Zug desto besser/schlechter -> Tiefe beruecksichtigen
                return (-1_000_000 - tiefe) if maximiere else (1_000_000 + tiefe)
            return 0  # Patt
        if tiefe <= 0:
            return self._quiescence(board, alpha, beta, maximiere)

        zuege.sort(key=mvv_lva_sortierschluessel, reverse=True)
        if maximiere:
            wert = -10 ** 9
            for zug in zuege:
                probe = board.klon()
                probe.zug_ausfuehren(zug)
                wert = max(wert, self._suche(probe, tiefe - 1, alpha, beta, False))
                alpha = max(alpha, wert)
                if alpha >= beta:
                    break
            return wert
        else:
            wert = 10 ** 9
            for zug in zuege:
                probe = board.klon()
                probe.zug_ausfuehren(zug)
                wert = min(wert, self._suche(probe, tiefe - 1, alpha, beta, True))
                beta = min(beta, wert)
                if alpha >= beta:
                    break
            return wert

    def _quiescence(self, board, alpha, beta, maximiere, tiefe_limit=4):
        """Sucht Schlagzuege weiter, um den Horizont-Effekt zu vermeiden -
        entscheidend, um Materialverlust durch kurzsichtige Zuege zu verhindern."""
        self.knoten += 1
        stand_pat = bewertung(board)
        farbe = 'w' if maximiere else 'b'
        if maximiere:
            if stand_pat >= beta:
                return stand_pat
            alpha = max(alpha, stand_pat)
        else:
            if stand_pat <= alpha:
                return stand_pat
            beta = min(beta, stand_pat)

        if tiefe_limit <= 0:
            return stand_pat

        schlagzuege = [z for z in board.legale_zuege(farbe) if z.geschlagen is not None]
        if not schlagzuege:
            return stand_pat
        schlagzuege.sort(key=mvv_lva_sortierschluessel, reverse=True)

        if maximiere:
            wert = stand_pat
            for zug in schlagzuege:
                probe = board.klon()
                probe.zug_ausfuehren(zug)
                wert = max(wert, self._quiescence(probe, alpha, beta, False, tiefe_limit - 1))
                alpha = max(alpha, wert)
                if alpha >= beta:
                    break
            return wert
        else:
            wert = stand_pat
            for zug in schlagzuege:
                probe = board.klon()
                probe.zug_ausfuehren(zug)
                wert = min(wert, self._quiescence(probe, alpha, beta, True, tiefe_limit - 1))
                beta = min(beta, wert)
                if alpha >= beta:
                    break
            return wert


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

FELD_GROESSE = 64
HELL = '#EEEED2'
DUNKEL = '#769656'
MARKIERT = '#F6F669'
ZIEL = '#8CA2AD'


class SchachGUI:
    def __init__(self, root):
        self.root = root
        self.root.title('Schach gegen den Computer')
        self.root.resizable(False, False)

        self.board = Board()
        self.spieler_farbe = 'w'
        self.ki_farbe = 'b'
        self.tiefe = 4
        self.ki = KI(self.ki_farbe, self.tiefe)

        self.ausgewaehlt = None
        self.legale_ziele = []
        self.geschlagen_weiss = []  # von Weiss geschlagene schwarze Figuren
        self.geschlagen_schwarz = []
        self.spiel_laeuft = True

        self._baue_layout()
        self._zeichne_brett()
        self._aktualisiere_material()

    # ---------------- Layout ----------------
    def _baue_layout(self):
        aussen = tk.Frame(self.root, bg='#222')
        aussen.pack(padx=8, pady=8)

        # Linkes Panel: Materialbilanz
        self.panel = tk.Frame(aussen, width=220, bg='#2b2b2b')
        self.panel.pack(side='left', fill='y', padx=(0, 10))
        self.panel.pack_propagate(False)

        tk.Label(self.panel, text='Materialbilanz', bg='#2b2b2b', fg='white',
                 font=('Segoe UI', 14, 'bold')).pack(pady=(10, 4))

        self.bilanz_label = tk.Label(self.panel, text='+0', bg='#2b2b2b', fg='#7CFC00',
                                      font=('Segoe UI', 28, 'bold'))
        self.bilanz_label.pack(pady=(0, 10))

        self.bilanz_text = tk.Label(self.panel, text='', bg='#2b2b2b', fg='#cccccc',
                                     font=('Segoe UI', 10), justify='left')
        self.bilanz_text.pack(pady=(0, 10))

        tk.Label(self.panel, text='Geschlagen (von dir):', bg='#2b2b2b', fg='white',
                 font=('Segoe UI', 10, 'bold')).pack(anchor='w', padx=10)
        self.geschlagen_w_label = tk.Label(self.panel, text='-', bg='#2b2b2b', fg='#7CFC00',
                                            font=('Segoe UI', 16), wraplength=200, justify='left')
        self.geschlagen_w_label.pack(anchor='w', padx=10, pady=(0, 10))

        tk.Label(self.panel, text='Geschlagen (vom Gegner):', bg='#2b2b2b', fg='white',
                 font=('Segoe UI', 10, 'bold')).pack(anchor='w', padx=10)
        self.geschlagen_s_label = tk.Label(self.panel, text='-', bg='#2b2b2b', fg='#ff6b6b',
                                            font=('Segoe UI', 16), wraplength=200, justify='left')
        self.geschlagen_s_label.pack(anchor='w', padx=10, pady=(0, 10))

        tk.Label(self.panel, text='Punktwerte:\nBauer 1  Springer 3\nLaeufer 3  Turm 5\nDame 9  Koenig -',
                 bg='#2b2b2b', fg='#999999', font=('Segoe UI', 9), justify='left').pack(
            anchor='w', padx=10, pady=(10, 10))

        tk.Label(self.panel, text='KI-Staerke:', bg='#2b2b2b', fg='white',
                 font=('Segoe UI', 10, 'bold')).pack(anchor='w', padx=10, pady=(10, 0))
        self.staerke_var = tk.StringVar(value='Stark (Tiefe 4)')
        auswahl = ttk.Combobox(self.panel, textvariable=self.staerke_var, state='readonly',
                                values=['Mittel (Tiefe 3)', 'Stark (Tiefe 4)', 'Sehr stark (Tiefe 5)'])
        auswahl.pack(padx=10, fill='x')
        auswahl.bind('<<ComboboxSelected>>', self._staerke_geaendert)

        tk.Button(self.panel, text='Neues Spiel', command=self._neues_spiel).pack(
            padx=10, pady=(16, 4), fill='x')

        self.status_label = tk.Label(self.panel, text='Du bist am Zug (Weiss)',
                                      bg='#2b2b2b', fg='white', font=('Segoe UI', 10),
                                      wraplength=200, justify='left')
        self.status_label.pack(padx=10, pady=(10, 10))

        # Rechts: Schachbrett
        self.canvas = tk.Canvas(aussen, width=FELD_GROESSE * 8, height=FELD_GROESSE * 8,
                                 highlightthickness=0)
        self.canvas.pack(side='left')
        self.canvas.bind('<Button-1>', self._klick)

    def _staerke_geaendert(self, _event=None):
        text = self.staerke_var.get()
        if 'Tiefe 3' in text:
            self.tiefe = 3
        elif 'Tiefe 5' in text:
            self.tiefe = 5
        else:
            self.tiefe = 4
        self.ki.tiefe = self.tiefe

    def _neues_spiel(self):
        self.board = Board()
        self.ausgewaehlt = None
        self.legale_ziele = []
        self.geschlagen_weiss = []
        self.geschlagen_schwarz = []
        self.spiel_laeuft = True
        self._zeichne_brett()
        self._aktualisiere_material()
        self.status_label.config(text='Du bist am Zug (Weiss)')

    # ---------------- Zeichnen ----------------
    def _zeichne_brett(self):
        self.canvas.delete('all')
        for z in range(8):
            for s in range(8):
                x0, y0 = s * FELD_GROESSE, z * FELD_GROESSE
                x1, y1 = x0 + FELD_GROESSE, y0 + FELD_GROESSE
                farbe = HELL if (z + s) % 2 == 0 else DUNKEL
                if self.ausgewaehlt == (z, s):
                    farbe = MARKIERT
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=farbe, outline='')
                if (z, s) in [zug.nach for zug in self.legale_ziele]:
                    cx, cy = x0 + FELD_GROESSE // 2, y0 + FELD_GROESSE // 2
                    self.canvas.create_oval(cx - 8, cy - 8, cx + 8, cy + 8, fill=ZIEL, outline='')
                p = self.board.grid[z][s]
                if p is not None:
                    symbol = SYMBOLE[p]
                    self.canvas.create_text(x0 + FELD_GROESSE // 2, y0 + FELD_GROESSE // 2,
                                             text=symbol, font=('DejaVu Sans', 40))

    def _aktualisiere_material(self):
        wert_w = sum(WERTE[t] for (_, t) in self.geschlagen_weiss)
        wert_s = sum(WERTE[t] for (_, t) in self.geschlagen_schwarz)
        bilanz = wert_w - wert_s
        vorzeichen = '+' if bilanz >= 0 else ''
        self.bilanz_label.config(text=f'{vorzeichen}{bilanz}',
                                  fg='#7CFC00' if bilanz >= 0 else '#ff6b6b')
        self.bilanz_text.config(
            text=f'Du hast Figuren im Wert von {wert_w} geschlagen.\n'
                 f'Der Gegner hat Figuren im Wert von {wert_s} geschlagen.')

        def liste(figuren):
            if not figuren:
                return '-'
            return '  '.join(SYMBOLE[('b', t)] if False else SYMBOLE.get(('b', t), t) for (_, t) in figuren)

        # Symbole neutral (grau) darstellen, hier vereinfachend schwarze Symbole nutzen
        self.geschlagen_w_label.config(text=' '.join(SYMBOLE[(f, t)] for (f, t) in self.geschlagen_weiss) or '-')
        self.geschlagen_s_label.config(text=' '.join(SYMBOLE[(f, t)] for (f, t) in self.geschlagen_schwarz) or '-')

    # ---------------- Interaktion ----------------
    def _klick(self, event):
        if not self.spiel_laeuft or self.board.zugfarbe != self.spieler_farbe:
            return
        s = event.x // FELD_GROESSE
        z = event.y // FELD_GROESSE
        if not (0 <= z < 8 and 0 <= s < 8):
            return

        if self.ausgewaehlt is None:
            p = self.board.grid[z][s]
            if p is not None and p[0] == self.spieler_farbe:
                self.ausgewaehlt = (z, s)
                alle = self.board.legale_zuege(self.spieler_farbe)
                self.legale_ziele = [zg for zg in alle if zg.von == (z, s)]
                self._zeichne_brett()
            return

        ziel_zuege = [zg for zg in self.legale_ziele if zg.nach == (z, s)]
        if ziel_zuege:
            zug = ziel_zuege[0]
            if zug.flag == 'umwandlung' and len(ziel_zuege) > 1:
                zug = self._waehle_umwandlung(ziel_zuege)
            self._zug_anwenden(zug, self.spieler_farbe)
            self.ausgewaehlt = None
            self.legale_ziele = []
            self._zeichne_brett()
            self._aktualisiere_material()
            if self._pruefe_spielende():
                return
            self.status_label.config(text='Computer denkt nach ...')
            self.root.after(50, self._ki_zug)
        else:
            p = self.board.grid[z][s]
            if p is not None and p[0] == self.spieler_farbe:
                self.ausgewaehlt = (z, s)
                alle = self.board.legale_zuege(self.spieler_farbe)
                self.legale_ziele = [zg for zg in alle if zg.von == (z, s)]
            else:
                self.ausgewaehlt = None
                self.legale_ziele = []
            self._zeichne_brett()

    def _waehle_umwandlung(self, kandidaten):
        fenster = tk.Toplevel(self.root)
        fenster.title('Bauernumwandlung')
        fenster.grab_set()
        auswahl = {'zug': kandidaten[0]}

        def waehlen(zug):
            auswahl['zug'] = zug
            fenster.destroy()

        tk.Label(fenster, text='Figur waehlen:').pack(padx=10, pady=10)
        rahmen = tk.Frame(fenster)
        rahmen.pack(padx=10, pady=10)
        for zug in kandidaten:
            symbol = SYMBOLE[(self.spieler_farbe, zug.promo)]
            tk.Button(rahmen, text=symbol, font=('DejaVu Sans', 24),
                      command=lambda zg=zug: waehlen(zg)).pack(side='left', padx=4)
        self.root.wait_window(fenster)
        return auswahl['zug']

    def _zug_anwenden(self, zug, farbe):
        if zug.geschlagen is not None:
            if farbe == 'w':
                self.geschlagen_weiss.append(zug.geschlagen)
            else:
                self.geschlagen_schwarz.append(zug.geschlagen)
        self.board.zug_ausfuehren(zug)

    def _ki_zug(self):
        if not self.spiel_laeuft:
            return
        zug = self.ki.bester_zug(self.board)
        if zug is None:
            self._pruefe_spielende()
            return
        self._zug_anwenden(zug, self.ki_farbe)
        self._zeichne_brett()
        self._aktualisiere_material()
        if not self._pruefe_spielende():
            self.status_label.config(text='Du bist am Zug (Weiss)')

    def _pruefe_spielende(self):
        ergebnis = self.board.spielende(self.board.zugfarbe)
        if ergebnis is None:
            if self.board.im_schach(self.board.zugfarbe):
                wer = 'Du stehst' if self.board.zugfarbe == self.spieler_farbe else 'Der Computer steht'
                self.status_label.config(text=f'{wer} im Schach!')
            return False
        self.spiel_laeuft = False
        if ergebnis == 'matt':
            gewinner = 'Schwarz (Computer)' if self.board.zugfarbe == 'w' else 'Weiss (Du)'
            messagebox.showinfo('Schachmatt', f'Schachmatt! {gewinner} gewinnt.')
            self.status_label.config(text=f'Schachmatt - {gewinner} gewinnt.')
        else:
            messagebox.showinfo('Patt', 'Patt! Das Spiel endet unentschieden.')
            self.status_label.config(text='Patt - Unentschieden.')
        return True


def main():
    root = tk.Tk()
    SchachGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
