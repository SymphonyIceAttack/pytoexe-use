"""
Eigene Schach-Engine (reines Python, keine externen Bibliotheken).
Enthaelt: Zugregeln, Rochade, En-passant, Umwandlung, Schach/Matt/Patt-Erkennung,
sowie eine KI (Minimax mit Alpha-Beta-Pruning, MVV-LVA-Zugsortierung und einer
Ruhesuche/Quiescence-Suche fuer Schlagzuege, Bauernumwandlungen, en passant und
Schachgebote). Diese Staerke-Verbesserungen stammen aus der frueher bereits
verstaerkten "schach.py" und wurden hier vollstaendig in die KI dieser
vollstaendigen Version (mit Menues, Lernfunktion, Eroeffnungsbuch, PGN-Import
und Partie-Analyse) integriert, ohne dass dabei etwas an den bestehenden
Funktionen entfernt wurde.
"""

import copy
import json
import os
import random
import re

WHITE, BLACK = "w", "b"

PIECE_VALUES = {"P": 100, "N": 300, "B": 300, "R": 500, "Q": 900, "K": 20000}

# Positions-Bewertungstabellen (Standard, vereinfachte Werte) - aus Sicht Weiss, Reihe 0 = Rang1
PST_PAWN = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [5, 10, 10, -20, -20, 10, 10, 5],
    [5, -5, -10, 0, 0, -10, -5, 5],
    [0, 0, 0, 20, 20, 0, 0, 0],
    [5, 5, 10, 25, 25, 10, 5, 5],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [0, 0, 0, 0, 0, 0, 0, 0],
]
PST_KNIGHT = [
    [-50, -40, -30, -30, -30, -30, -40, -50],
    [-40, -20, 0, 5, 5, 0, -20, -40],
    [-30, 5, 10, 15, 15, 10, 5, -30],
    [-30, 0, 15, 20, 20, 15, 0, -30],
    [-30, 5, 15, 20, 20, 15, 5, -30],
    [-30, 0, 10, 15, 15, 10, 0, -30],
    [-40, -20, 0, 0, 0, 0, -20, -40],
    [-50, -40, -30, -30, -30, -30, -40, -50],
]
PST_BISHOP = [
    [-20, -10, -10, -10, -10, -10, -10, -20],
    [-10, 5, 0, 0, 0, 0, 5, -10],
    [-10, 10, 10, 10, 10, 10, 10, -10],
    [-10, 0, 10, 10, 10, 10, 0, -10],
    [-10, 5, 5, 10, 10, 5, 5, -10],
    [-10, 0, 5, 10, 10, 5, 0, -10],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-20, -10, -10, -10, -10, -10, -10, -20],
]
PST_ROOK = [
    [0, 0, 0, 5, 5, 0, 0, 0],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [5, 10, 10, 10, 10, 10, 10, 5],
    [0, 0, 0, 0, 0, 0, 0, 0],
]
PST_QUEEN = [
    [-20, -10, -10, -5, -5, -10, -10, -20],
    [-10, 0, 5, 0, 0, 0, 0, -10],
    [-10, 5, 5, 5, 5, 5, 0, -10],
    [0, 0, 5, 5, 5, 5, 0, -5],
    [-5, 0, 5, 5, 5, 5, 0, -5],
    [-10, 0, 5, 5, 5, 5, 0, -10],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-20, -10, -10, -5, -5, -10, -10, -20],
]
PST_KING = [
    [20, 30, 10, 0, 0, 10, 30, 20],
    [20, 20, 0, 0, 0, 0, 20, 20],
    [-10, -20, -20, -20, -20, -20, -20, -10],
    [-20, -30, -30, -40, -40, -30, -30, -20],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
]
PST = {"P": PST_PAWN, "N": PST_KNIGHT, "B": PST_BISHOP, "R": PST_ROOK, "Q": PST_QUEEN, "K": PST_KING}

KNIGHT_DELTAS = [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)]
KING_DELTAS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
BISHOP_DIRS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
ROOK_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def in_bounds(r, c):
    return 0 <= r <= 7 and 0 <= c <= 7


def piece_color(piece):
    if piece == "":
        return None
    return WHITE if piece.isupper() else BLACK


def square_name(r, c):
    return "abcdefgh"[c] + str(r + 1)


class Move:
    def __init__(self, fr, fc, tr, tc, piece, captured="", special=None, promotion=None):
        self.fr, self.fc, self.tr, self.tc = fr, fc, tr, tc
        self.piece = piece
        self.captured = captured
        self.special = special  # 'ep', 'castle_k', 'castle_q', None
        self.promotion = promotion  # 'Q','R','B','N' or None
        self.san = ""  # wird nachtraeglich gesetzt

    def coords(self):
        return (self.fr, self.fc, self.tr, self.tc)


class ChessState:
    def __init__(self):
        self.board = [["" for _ in range(8)] for _ in range(8)]
        self._setup()
        self.turn = WHITE
        self.castling = {"wk": True, "wq": True, "bk": True, "bq": True}
        self.ep_target = None  # (r,c) Feld, das per en passant geschlagen werden kann
        self.history = []  # Liste von (Move, castling_snapshot, ep_snapshot)
        self.redo_stack = []

    def _setup(self):
        back = ["R", "N", "B", "Q", "K", "B", "N", "R"]
        for c in range(8):
            self.board[0][c] = back[c]
            self.board[1][c] = "P"
            self.board[6][c] = "p"
            self.board[7][c] = back[c].lower()

    def clone_light(self):
        st = ChessState.__new__(ChessState)
        st.board = [row[:] for row in self.board]
        st.turn = self.turn
        st.castling = dict(self.castling)
        st.ep_target = self.ep_target
        st.history = []
        st.redo_stack = []
        return st

    # ---------- Zuggenerierung ----------
    def pseudo_moves(self, color):
        moves = []
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p == "" or piece_color(p) != color:
                    continue
                kind = p.upper()
                if kind == "P":
                    moves.extend(self._pawn_moves(r, c, color))
                elif kind == "N":
                    moves.extend(self._step_moves(r, c, KNIGHT_DELTAS, color, "N"))
                elif kind == "B":
                    moves.extend(self._slide_moves(r, c, BISHOP_DIRS, color, "B"))
                elif kind == "R":
                    moves.extend(self._slide_moves(r, c, ROOK_DIRS, color, "R"))
                elif kind == "Q":
                    moves.extend(self._slide_moves(r, c, BISHOP_DIRS + ROOK_DIRS, color, "Q"))
                elif kind == "K":
                    moves.extend(self._king_moves(r, c, color))
        return moves

    def _pawn_moves(self, r, c, color):
        moves = []
        piece = "P" if color == WHITE else "p"
        direction = 1 if color == WHITE else -1
        start_row = 1 if color == WHITE else 6
        promo_row = 7 if color == WHITE else 0
        one = r + direction
        if in_bounds(one, c) and self.board[one][c] == "":
            if one == promo_row:
                for promo in ("Q", "R", "B", "N"):
                    moves.append(Move(r, c, one, c, piece, promotion=promo))
            else:
                moves.append(Move(r, c, one, c, piece))
            two = r + 2 * direction
            if r == start_row and in_bounds(two, c) and self.board[two][c] == "":
                moves.append(Move(r, c, two, c, piece, special="double"))
        for dc in (-1, 1):
            nr, nc = r + direction, c + dc
            if not in_bounds(nr, nc):
                continue
            target = self.board[nr][nc]
            if target != "" and piece_color(target) != color:
                if nr == promo_row:
                    for promo in ("Q", "R", "B", "N"):
                        moves.append(Move(r, c, nr, nc, piece, captured=target, promotion=promo))
                else:
                    moves.append(Move(r, c, nr, nc, piece, captured=target))
            elif self.ep_target == (nr, nc):
                captured_pawn = "p" if color == WHITE else "P"
                moves.append(Move(r, c, nr, nc, piece, captured=captured_pawn, special="ep"))
        return moves

    def _step_moves(self, r, c, deltas, color, kind):
        moves = []
        piece = kind if color == WHITE else kind.lower()
        for dr, dc in deltas:
            nr, nc = r + dr, c + dc
            if not in_bounds(nr, nc):
                continue
            target = self.board[nr][nc]
            if target == "" or piece_color(target) != color:
                moves.append(Move(r, c, nr, nc, piece, captured=target))
        return moves

    def _slide_moves(self, r, c, dirs, color, kind):
        moves = []
        piece = kind if color == WHITE else kind.lower()
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            while in_bounds(nr, nc):
                target = self.board[nr][nc]
                if target == "":
                    moves.append(Move(r, c, nr, nc, piece))
                else:
                    if piece_color(target) != color:
                        moves.append(Move(r, c, nr, nc, piece, captured=target))
                    break
                nr += dr
                nc += dc
        return moves

    def _king_moves(self, r, c, color):
        moves = self._step_moves(r, c, KING_DELTAS, color, "K")
        # Rochade
        row = 0 if color == WHITE else 7
        if r == row and c == 4:
            k_flag = "wk" if color == WHITE else "bk"
            q_flag = "wq" if color == WHITE else "bq"
            if self.castling.get(k_flag) and self.board[row][5] == "" and self.board[row][6] == "":
                if self.board[row][7] == ("R" if color == WHITE else "r"):
                    if not self.square_attacked(row, 4, opponent(color)) and \
                       not self.square_attacked(row, 5, opponent(color)) and \
                       not self.square_attacked(row, 6, opponent(color)):
                        piece = "K" if color == WHITE else "k"
                        moves.append(Move(r, c, row, 6, piece, special="castle_k"))
            if self.castling.get(q_flag) and self.board[row][1] == "" and self.board[row][2] == "" and self.board[row][3] == "":
                if self.board[row][0] == ("R" if color == WHITE else "r"):
                    if not self.square_attacked(row, 4, opponent(color)) and \
                       not self.square_attacked(row, 3, opponent(color)) and \
                       not self.square_attacked(row, 2, opponent(color)):
                        piece = "K" if color == WHITE else "k"
                        moves.append(Move(r, c, row, 2, piece, special="castle_q"))
        return moves

    def square_attacked(self, r, c, by_color):
        # Bauern
        direction = -1 if by_color == WHITE else 1
        for dc in (-1, 1):
            pr, pc = r + direction, c + dc
            if in_bounds(pr, pc):
                p = self.board[pr][pc]
                if p != "" and piece_color(p) == by_color and p.upper() == "P":
                    return True
        # Springer
        for dr, dc in KNIGHT_DELTAS:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc):
                p = self.board[nr][nc]
                if p != "" and piece_color(p) == by_color and p.upper() == "N":
                    return True
        # Koenig
        for dr, dc in KING_DELTAS:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc):
                p = self.board[nr][nc]
                if p != "" and piece_color(p) == by_color and p.upper() == "K":
                    return True
        # Laeufer/Dame diagonal
        for dr, dc in BISHOP_DIRS:
            nr, nc = r + dr, c + dc
            while in_bounds(nr, nc):
                p = self.board[nr][nc]
                if p != "":
                    if piece_color(p) == by_color and p.upper() in ("B", "Q"):
                        return True
                    break
                nr += dr
                nc += dc
        # Turm/Dame gerade
        for dr, dc in ROOK_DIRS:
            nr, nc = r + dr, c + dc
            while in_bounds(nr, nc):
                p = self.board[nr][nc]
                if p != "":
                    if piece_color(p) == by_color and p.upper() in ("R", "Q"):
                        return True
                    break
                nr += dr
                nc += dc
        return False

    def find_king(self, color):
        target = "K" if color == WHITE else "k"
        for r in range(8):
            for c in range(8):
                if self.board[r][c] == target:
                    return r, c
        return None

    def in_check(self, color):
        kr, kc = self.find_king(color)
        return self.square_attacked(kr, kc, opponent(color))

    def legal_moves(self, color=None):
        color = color or self.turn
        legal = []
        for m in self.pseudo_moves(color):
            self.make_move(m, record=False)
            if not self.in_check(color):
                legal.append(m)
            self.unmake_move()
        return legal

    def is_checkmate(self):
        return self.in_check(self.turn) and len(self.legal_moves()) == 0

    def is_stalemate(self):
        return not self.in_check(self.turn) and len(self.legal_moves()) == 0

    # ---------- Zug ausfuehren / rueckgaengig ----------
    def make_move(self, move, record=True, clear_redo=True):
        snapshot = {
            "castling": dict(self.castling),
            "ep_target": self.ep_target,
            "board_from": self.board[move.fr][move.fc],
            "board_to": self.board[move.tr][move.tc],
        }
        color = piece_color(move.piece)
        self.board[move.fr][move.fc] = ""
        placed = move.piece
        if move.promotion:
            placed = move.promotion if color == WHITE else move.promotion.lower()
        self.board[move.tr][move.tc] = placed

        if move.special == "ep":
            cap_row = move.fr
            snapshot["ep_captured_square"] = (cap_row, move.tc)
            snapshot["ep_captured_piece"] = self.board[cap_row][move.tc]
            self.board[cap_row][move.tc] = ""
        elif move.special == "castle_k":
            row = move.fr
            rook = self.board[row][7]
            self.board[row][7] = ""
            self.board[row][5] = rook
        elif move.special == "castle_q":
            row = move.fr
            rook = self.board[row][0]
            self.board[row][0] = ""
            self.board[row][3] = rook

        # Rochaderechte aktualisieren
        if move.piece.upper() == "K":
            if color == WHITE:
                self.castling["wk"] = False
                self.castling["wq"] = False
            else:
                self.castling["bk"] = False
                self.castling["bq"] = False
        if move.piece.upper() == "R":
            if (move.fr, move.fc) == (0, 0):
                self.castling["wq"] = False
            elif (move.fr, move.fc) == (0, 7):
                self.castling["wk"] = False
            elif (move.fr, move.fc) == (7, 0):
                self.castling["bq"] = False
            elif (move.fr, move.fc) == (7, 7):
                self.castling["bk"] = False
        if move.captured and move.captured.upper() == "R":
            if (move.tr, move.tc) == (0, 0):
                self.castling["wq"] = False
            elif (move.tr, move.tc) == (0, 7):
                self.castling["wk"] = False
            elif (move.tr, move.tc) == (7, 0):
                self.castling["bq"] = False
            elif (move.tr, move.tc) == (7, 7):
                self.castling["bk"] = False

        # En-passant Zielfeld setzen
        if move.special == "double":
            self.ep_target = ((move.fr + move.tr) // 2, move.fc)
        else:
            self.ep_target = None

        self.turn = opponent(self.turn)

        if record:
            self.history.append((move, snapshot))
            if clear_redo:
                self.redo_stack = []
        else:
            if not hasattr(self, "_temp_stack"):
                self._temp_stack = []
            self._temp_stack.append((move, snapshot))

    def unmake_move(self):
        if hasattr(self, "_temp_stack") and self._temp_stack:
            move, snapshot = self._temp_stack.pop()
        else:
            move, snapshot = self.history.pop()
        self.board[move.fr][move.fc] = snapshot["board_from"]
        self.board[move.tr][move.tc] = snapshot["board_to"]
        if move.special == "ep":
            r, c = snapshot["ep_captured_square"]
            self.board[r][c] = snapshot["ep_captured_piece"]
        elif move.special == "castle_k":
            row = move.fr
            rook = self.board[row][5]
            self.board[row][5] = ""
            self.board[row][7] = rook
        elif move.special == "castle_q":
            row = move.fr
            rook = self.board[row][3]
            self.board[row][3] = ""
            self.board[row][0] = rook
        self.castling = snapshot["castling"]
        self.ep_target = snapshot["ep_target"]
        self.turn = opponent(self.turn)

    def undo(self):
        if not self.history:
            return None
        move, snapshot = self.history[-1]
        self.unmake_move()
        self.redo_stack.append((move, snapshot))
        return move

    def redo(self):
        if not self.redo_stack:
            return None
        move, snapshot = self.redo_stack.pop()
        self.make_move(move, record=True, clear_redo=False)
        return move

    # ---------- Bewertung ----------
    def _rochade_und_bauernschild_bonus(self, color):
        """Zusaetzlicher strategischer Bonus (in Centipawn) fuer eine Seite:
        - Rochaderecht ist etwas wert (noch nicht durch Koenig-/Turmzug verspielt).
        - Ist bereits rochiert, zaehlt vor allem ein intakter Bauernschild auf
          genau der Seite, auf die rochiert wurde (a/b/c bei 0-0-0, f/g/h bei 0-0).
        - Ist noch nicht rochiert, lohnt es sich meist, beide Fluegel vorerst
          geschlossen zu halten und stattdessen im Zentrum (d/e-Bauern) zu
          spielen - klassisches Eroeffnungsprinzip.
        - Der Bonus wird mit sinkendem Nicht-Bauern-Material (= Uebergang ins
          Endspiel) automatisch schwaecher gewichtet: sobald ein Materialvorteil
          herausgespielt und ausgebaut ist, darf/soll auch die Randstruktur
          geoeffnet werden, ohne dass die reine Bewertungsfunktion dagegenhaelt.
        Taktische Sicherheit geht davon unberuehrt immer vor: droht ein frueher
        Schach oder gar Matt, dominieren die um Groessenordnungen groesseren
        Matt-/Materialwerte in der Suche jede dieser kleinen Positionsboni."""
        board = self.board
        pawn = "P" if color == WHITE else "p"
        start_row = 1 if color == WHITE else 6
        back_row = 0 if color == WHITE else 7
        kr, kc = self.find_king(color)

        non_pawn_material = sum(
            PIECE_VALUES[board[r][c].upper()]
            for r in range(8) for c in range(8)
            if board[r][c] and board[r][c].upper() not in ("P", "K")
        )
        # zu Beginn ca. 6400 Centipawn Nicht-Bauern-Material pro Seite;
        # phase faellt Richtung Endspiel gegen einen kleinen Restwert ab
        phase = 1.0 if non_pawn_material >= 4000 else max(0.15, non_pawn_material / 4000)

        kingside_rechte = self.castling["wk" if color == WHITE else "bk"]
        queenside_rechte = self.castling["wq" if color == WHITE else "bq"]
        bereits_kingside = (kr == back_row and kc == 6)
        bereits_queenside = (kr == back_row and kc == 2)

        kingside_spalten = (5, 6, 7)
        queenside_spalten = (0, 1, 2)

        def schild_intakt(spalten):
            return sum(1 for sc in spalten if board[start_row][sc] == pawn)

        bonus = 0.0
        if kingside_rechte or queenside_rechte:
            bonus += 6.0

        if bereits_kingside:
            bonus += 18.0 * phase + 5.0 * phase * schild_intakt(kingside_spalten)
        elif bereits_queenside:
            bonus += 18.0 * phase + 5.0 * phase * schild_intakt(queenside_spalten)
        else:
            if kingside_rechte:
                bonus += 2.5 * phase * schild_intakt(kingside_spalten)
            if queenside_rechte:
                bonus += 2.5 * phase * schild_intakt(queenside_spalten)

        for col in (3, 4):  # d- und e-Linie
            if board[start_row][col] != pawn:
                bonus += 3.0

        return bonus

    def evaluate(self):
        score = 0
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p == "":
                    continue
                kind = p.upper()
                val = PIECE_VALUES[kind]
                pst_row = r if p.isupper() else 7 - r
                pst_val = PST[kind][pst_row][c]
                if p.isupper():
                    score += val + pst_val
                else:
                    score -= val + pst_val
        score += self._rochade_und_bauernschild_bonus(WHITE)
        score -= self._rochade_und_bauernschild_bonus(BLACK)
        return score

    def game_result(self):
        if self.is_checkmate():
            return "0-1" if self.turn == WHITE else "1-0"
        if self.is_stalemate():
            return "1/2-1/2"
        return None


def opponent(color):
    return BLACK if color == WHITE else WHITE


def analyze_game(move_records, depth=2):
    """Geht eine gespielte Partie (Liste aus (Move, snapshot)-Paaren) nochmal durch
    und markiert Zuege, die deutlich schlechter waren als der beste verfuegbare Zug.
    Liefert eine Liste von Dicts mit ply, san, mover, diff (in Centipawn), tag."""
    state = ChessState()
    ai = ChessAI(depth=depth)
    results = []
    for idx, (move, _snapshot) in enumerate(move_records):
        mover = state.turn
        legal = state.legal_moves()
        san = to_san(state, move, legal)
        best_move, best_score = ai.choose_move(state)
        best_mover_score = best_score if mover == WHITE else -best_score

        state.make_move(move, record=True)
        if not state.legal_moves():
            if state.in_check(state.turn):
                # Die Seite am Zug ist mattgesetzt
                played_score = -999999 if state.turn == WHITE else 999999
            else:
                played_score = 0  # Patt
        elif depth - 1 > 0:
            played_score = ai._minimax(state, depth - 1, -999999, 999999, state.turn == WHITE)
        else:
            played_score = state.evaluate()
        played_mover_score = played_score if mover == WHITE else -played_score

        diff = max(0, best_mover_score - played_mover_score)
        if diff >= 300:
            tag = "Grober Fehler"
        elif diff >= 120:
            tag = "Fehler"
        elif diff >= 50:
            tag = "Ungenauigkeit"
        else:
            tag = None
        results.append({
            "ply": idx + 1,
            "san": san,
            "mover": mover,
            "diff": diff,
            "tag": tag,
        })
    return results


def to_san(state_before, move, legal_moves_before):
    """Vereinfachte algebraische Notation."""
    if move.special == "castle_k":
        base = "O-O"
    elif move.special == "castle_q":
        base = "O-O-O"
    else:
        piece_letter = "" if move.piece.upper() == "P" else move.piece.upper()
        capture = move.captured != "" or move.special == "ep"
        dest = square_name(move.tr, move.tc)
        disamb = ""
        if piece_letter:
            others = [m for m in legal_moves_before
                      if m.piece == move.piece and (m.tr, m.tc) == (move.tr, move.tc)
                      and (m.fr, m.fc) != (move.fr, move.fc)]
            if others:
                same_file = any(m.fc == move.fc for m in others)
                if not same_file:
                    disamb = "abcdefgh"[move.fc]
                else:
                    same_rank = any(m.fr == move.fr for m in others)
                    if not same_rank:
                        disamb = str(move.fr + 1)
                    else:
                        disamb = "abcdefgh"[move.fc] + str(move.fr + 1)
        from_file = "abcdefgh"[move.fc] if (move.piece.upper() == "P" and capture) else ""
        base = f"{piece_letter}{disamb}{from_file}{'x' if capture else ''}{dest}"
        if move.promotion:
            base += "=" + move.promotion
    return base


# ---------- Selbstlernender Speicher ----------
LEARN_PLIES = 8          # nur die ersten N Halbzuege werden gelernt (Eroeffnungsverhalten)
LEARN_BIAS_SCALE = 6.0   # wie stark gelernte Erfahrung die Zugwahl beeinflusst


class LearningMemory:
    """Speichert dauerhaft (in einer JSON-Datei), welche Eroeffnungszuege der
    Computer bisher gespielt hat und wie erfolgreich sie waren, sowie welche
    eigenen Zuege in der Nachanalyse als Fehler erkannt wurden. Mit jeder
    gespielten/trainierten Partie wird die Datei aktualisiert - das Programm
    'lernt' also aus eigener Erfahrung, wenn auch nur eingeschraenkt auf
    Eroeffnungswahl und Fehlervermeidung, nicht auf Stellungsverstaendnis
    generell."""

    def __init__(self, path="schach_lernen.json"):
        self.path = path
        self.data = {}           # key: "|".join(vorherige SAN-Zuege) -> {san: {"score":float,"n":int}}
        self.games_trained = 0
        self.load()

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                self.data = raw.get("data", {})
                self.games_trained = raw.get("games_trained", 0)
            except (OSError, json.JSONDecodeError):
                self.data = {}
                self.games_trained = 0

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump({"data": self.data, "games_trained": self.games_trained}, f, ensure_ascii=False, indent=1)
        except OSError:
            pass

    def bias_for(self, prefix_key, san):
        entry = self.data.get(prefix_key, {}).get(san)
        if not entry or entry["n"] == 0:
            return 0.0
        avg = entry["score"] / entry["n"]
        # je mehr Erfahrung (n), desto staerker vertrauen wir dem Wert (bis zu einer Grenze)
        confidence = min(1.0, entry["n"] / 8.0)
        return avg * confidence * LEARN_BIAS_SCALE

    def update_from_game(self, san_history, learner_color, result_value, mistake_plies):
        """result_value: +1 = Sieg des Lerners, 0 = Remis, -1 = Niederlage.
        mistake_plies: dict ply_index(0-basiert) -> Strafe (0.3 Ungenauigkeit,
        0.6 Fehler, 1.0 grober Fehler)."""
        prefix = []
        for i, san in enumerate(san_history):
            mover = WHITE if i % 2 == 0 else BLACK
            if mover == learner_color and i < LEARN_PLIES:
                key = "|".join(prefix)
                entry = self.data.setdefault(key, {}).setdefault(san, {"score": 0.0, "n": 0})
                penalty = mistake_plies.get(i, 0.0)
                entry["score"] += result_value - penalty
                entry["n"] += 1
            prefix.append(san)
        self.games_trained += 1


# ---------- Selbstlernender Speicher Ende ----------

def train_self_play(memory, num_games=20, depth=2, analyze_depth=1, max_plies=90,
                     exploration_plies=6, exploration_chance=0.35, progress_callback=None):
    """Laesst die KI mehrere Partien gegen sich selbst spielen und aktualisiert
    dabei den LearningMemory-Speicher (Eroeffnungserfahrung + erkannte eigene Fehler).
    In den ersten Zuegen wird bewusst etwas Zufall eingestreut, sonst waeren alle
    Trainingspartien identisch (gleiche KI spielt sonst immer exakt gleich)."""
    import random
    ai = ChessAI(depth=depth)
    for g in range(num_games):
        state = ChessState()
        san_history = []
        prefix = []
        for ply in range(max_plies):
            legal = state.legal_moves()
            if not legal:
                break
            if ply < exploration_plies and random.random() < exploration_chance:
                mv = random.choice(legal)
            else:
                mv, _score = ai.choose_move(state, memory=memory, san_prefix=prefix)
            san = to_san(state, mv, legal)
            mv.san = san
            state.make_move(mv, record=True)
            san_history.append(san)
            prefix.append(san)
            if len(san_history) >= 10 and san_history[-4:] == san_history[-8:-4]:
                break  # simple Stellungswiederholung erkannt -> Remis annehmen, Zeit sparen

        result = state.game_result()
        if result == "1-0":
            white_result, black_result = 1.0, -1.0
        elif result == "0-1":
            white_result, black_result = -1.0, 1.0
        else:
            white_result, black_result = 0.0, 0.0

        analysis = analyze_game(state.history, depth=analyze_depth)
        mistakes_white, mistakes_black = {}, {}
        penalty_map = {"Ungenauigkeit": 0.3, "Fehler": 0.6, "Grober Fehler": 1.0}
        for r in analysis:
            penalty = penalty_map.get(r["tag"], 0.0)
            if penalty:
                target = mistakes_white if r["mover"] == WHITE else mistakes_black
                target[r["ply"] - 1] = penalty

        memory.update_from_game(san_history, WHITE, white_result, mistakes_white)
        memory.update_from_game(san_history, BLACK, black_result, mistakes_black)

        if progress_callback:
            progress_callback(g + 1, num_games, result or "Remis (Wiederholung/Limit)")

    memory.save()
    return memory


# ---------- Import eingefuegter Partien (Copy/Paste) ----------
def _clean_san_token(token):
    tok = token.strip()
    while tok and tok[-1] in "+#!?":
        tok = tok[:-1]
    if tok in ("0-0", "O-O"):
        return "O-O"
    if tok in ("0-0-0", "O-O-O"):
        return "O-O-O"
    return tok


def parse_san_move(state, token):
    """Sucht unter den aktuell legalen Zuegen denjenigen, der zur eingegebenen
    Notation (z.B. 'Nf3', 'exd5', 'O-O', 'e8=Q') passt. Gibt None zurueck,
    wenn der Zug nicht gefunden/gelesen werden konnte."""
    clean = _clean_san_token(token)
    if not clean:
        return None
    legal = state.legal_moves()
    for m in legal:
        if to_san(state, m, legal) == clean:
            return m
    if "=" in clean:
        base, promo = clean.split("=", 1)
        clean2 = base + "=" + promo.upper()
        for m in legal:
            if to_san(state, m, legal) == clean2:
                return m
    return None


def _strip_pgn_headers(text):
    lines = [ln for ln in text.splitlines() if not ln.strip().startswith("[")]
    return "\n".join(lines)


def split_pgn_games(text):
    """Zerlegt eingefuegten Text in einzelne Partien (Liste von Zug-Tokens)
    plus optionalem Ergebnis ('1-0','0-1','1/2-1/2' oder None)."""
    text = _strip_pgn_headers(text)
    text = re.sub(r"\{[^}]*\}", " ", text)          # Kommentare entfernen
    text = re.sub(r"\$\d+", " ", text)               # NAG-Symbole entfernen
    text = re.sub(r"\([^()]*\)", " ", text)           # einfache Nebenvarianten entfernen
    raw_tokens = text.split()

    games = []
    current = []
    for tok in raw_tokens:
        if tok in ("1-0", "0-1", "1/2-1/2", "*"):
            if current:
                games.append((current, tok if tok != "*" else None))
                current = []
            continue
        m = re.match(r"^\d+\.+(.*)$", tok)
        if m:
            tok = m.group(1)
        if tok:
            current.append(tok)
    if current:
        games.append((current, None))
    return games


def import_games_text(memory, text, analyze_depth=1, progress_callback=None):
    """Liest eingefuegten Partie-Text (eine oder mehrere Partien, PGN-aehnliche
    Notation), spielt jede Partie intern nach und speist Ergebnis + erkannte
    Fehler in den Lernspeicher ein. Gibt eine Liste von Berichten zurueck."""
    games = split_pgn_games(text)
    reports = []
    for idx, (tokens, result_tag) in enumerate(games):
        state = ChessState()
        san_history = []
        error = None
        for tok in tokens:
            mv = parse_san_move(state, tok)
            if mv is None:
                error = f"Zug '{tok}' nicht erkannt (nach {len(san_history)} gelesenen Zuegen)"
                break
            legal = state.legal_moves()
            san = to_san(state, mv, legal)
            mv.san = san
            state.make_move(mv, record=True)
            san_history.append(san)

        if san_history:
            if result_tag == "1-0":
                white_res, black_res = 1.0, -1.0
            elif result_tag == "0-1":
                white_res, black_res = -1.0, 1.0
            elif result_tag == "1/2-1/2":
                white_res, black_res = 0.0, 0.0
            elif state.is_checkmate():
                winner = opponent(state.turn)
                white_res, black_res = (1.0, -1.0) if winner == WHITE else (-1.0, 1.0)
            else:
                white_res, black_res = 0.0, 0.0

            analysis = analyze_game(state.history, depth=analyze_depth)
            mistakes_w, mistakes_b = {}, {}
            penalty_map = {"Ungenauigkeit": 0.3, "Fehler": 0.6, "Grober Fehler": 1.0}
            for r in analysis:
                p = penalty_map.get(r["tag"], 0.0)
                if p:
                    (mistakes_w if r["mover"] == WHITE else mistakes_b)[r["ply"] - 1] = p

            memory.update_from_game(san_history, WHITE, white_res, mistakes_w)
            memory.update_from_game(san_history, BLACK, black_res, mistakes_b)

        reports.append({
            "game": idx + 1,
            "plies_imported": len(san_history),
            "tokens_total": len(tokens),
            "error": error,
            "result": result_tag,
        })
        if progress_callback:
            progress_callback(idx + 1, len(games), error)

    memory.save()
    return reports


def apply_san_sequence(state, tokens):
    """Wendet eine Liste von Zug-Tokens (z.B. aus eingefuegtem Text) direkt auf
    den gegebenen ChessState an - zum Fortsetzen einer eingefuegten Partie.
    Gibt (liste_der_erfolgreich_gelesenen_san, fehler_token_oder_None) zurueck."""
    applied = []
    for tok in tokens:
        mv = parse_san_move(state, tok)
        if mv is None:
            return applied, tok
        legal = state.legal_moves()
        san = to_san(state, mv, legal)
        mv.san = san
        state.make_move(mv, record=True)
        applied.append(san)
    return applied, None


# ---------- KI ----------
# ============================================================
# Eroeffnungsbuch (Opening Book)
# ============================================================
# Enthaelt die Hauptvarianten der 15 wichtigsten Schacheroeffnungen
# (nach Staerke/Beliebtheit sortiert) zusammen mit dem jeweils besten
# Konter, wie sie in der Schachtheorie gelten. Die Engine "kennt" diese
# Zuege dadurch auswendig und spielt in den ersten Zuegen nicht mehr
# blind per Suche, sondern nach anerkannter Eroeffnungstheorie - das
# macht das Programm in der Eroeffnungsphase spuerbar staerker.
#
# Format: jede Zeile ist eine vollstaendige Zugfolge in Standard-SAN
# (Sf3 = Nf3 usw., englische Bezeichner wie im Rest der Engine).
OPENING_BOOK_LINES = [
    # 1. Spanische Partie (Ruy Lopez) - Berliner Verteidigung
    ["e4", "e5", "Nf3", "Nc6", "Bb5", "Nf6", "O-O", "Nxe4", "d4", "Nd6",
     "Bxc6", "dxc6", "dxe5", "Nf5", "Qxd8", "Kxd8"],
    # 1b. Spanische Partie - Geschlossenes System / Vorstufe zum Marshall-Angriff
    ["e4", "e5", "Nf3", "Nc6", "Bb5", "a6", "Ba4", "Nf6", "O-O", "Be7",
     "Re1", "b5", "Bb3", "O-O", "c3", "d5"],
    # 2. Damengambit (Abgelehnt) - Karlsbader Struktur
    ["d4", "d5", "c4", "e6", "Nc3", "Nf6", "cxd5", "exd5", "Bg5", "Be7",
     "e3", "O-O", "Nf3", "Nbd7", "Bd3", "c6"],
    # 2b. Damengambit - Slawische Verteidigung als Konter
    ["d4", "d5", "c4", "c6", "Nf3", "Nf6", "Nc3", "dxc4", "a4", "Bf5",
     "e3", "e6", "Bxc4", "Bb4"],
    # 3. Italienische Partie - Zwei-Springer-Verteidigung
    ["e4", "e5", "Nf3", "Nc6", "Bc4", "Nf6", "Ng5", "d5", "exd5", "Na5",
     "Bb5", "c6", "dxc6", "bxc6"],
    # 4. Sizilianische Verteidigung - Offenes Sizilianisch (Najdorf-Aufbau)
    ["e4", "c5", "Nf3", "d6", "d4", "cxd4", "Nxd4", "Nf6", "Nc3", "a6",
     "Be2", "e5", "Nb3", "Be7", "O-O", "O-O"],
    # 5. Londoner System
    ["d4", "d5", "Nf3", "Nf6", "Bf4", "c5", "e3", "Nc6", "c3", "Qb6",
     "Qb3", "c4", "Qxb6", "axb6"],
    # 6. Franzoesische Verteidigung - Vorstossvariante
    ["e4", "e6", "d4", "d5", "e5", "c5", "c3", "Nc6", "Nf3", "Qb6",
     "Be2", "Nh6", "Na3", "cxd4"],
    # 7. Caro-Kann-Verteidigung - Vorstossvariante
    ["e4", "c6", "d4", "d5", "e5", "Bf5", "Nf3", "e6", "Be2", "c5",
     "O-O", "Nc6", "c3", "Nge7"],
    # 8. Koenigsindische Verteidigung - Klassisches System
    ["d4", "Nf6", "c4", "g6", "Nc3", "Bg7", "e4", "d6", "Nf3", "O-O",
     "Be2", "e5", "O-O", "Nc6", "d5", "Ne7"],
    # 9. Nimzo-Indische Verteidigung - Rubinstein-Variante
    ["d4", "Nf6", "c4", "e6", "Nc3", "Bb4", "e3", "O-O", "Bd3", "d5",
     "Nf3", "c5", "O-O", "Nc6"],
    # 10. Skandinavische Verteidigung - Hauptvariante 2.exd5
    ["e4", "d5", "exd5", "Qxd5", "Nc3", "Qa5", "d4", "Nf6", "Nf3", "c6",
     "Bc4", "Bf5"],
    # 11. Gruenfeld-Indische Verteidigung - Abtauschvariante
    ["d4", "Nf6", "c4", "g6", "Nc3", "d5", "cxd5", "Nxd5", "e4", "Nxc3",
     "bxc3", "Bg7", "Bc4", "c5"],
    # 12. Aljechin-Verteidigung - Moderne Variante
    ["e4", "Nf6", "e5", "Nd5", "d4", "d6", "Nf3", "g6", "Bc4", "Nb6",
     "Bb3", "Bg7"],
    # 13. Pirc-Defensive - Oesterreichischer Angriff
    ["e4", "d6", "d4", "Nf6", "Nc3", "g6", "f4", "Bg7", "Nf3", "O-O",
     "Bd3", "Na6"],
    # 14. Reti-Eroeffnung - Zentrumsbesetzung durch Schwarz
    ["Nf3", "d5", "c4", "d4", "b4", "Bg4", "Bb2", "Nd7"],
    # 15. Englische Eroeffnung - Symmetrische Variante
    ["c4", "c5", "Nf3", "Nf6", "Nc3", "Nc6", "g3", "g6", "Bg2", "Bg7",
     "O-O", "O-O"],
]


def _build_opening_book(lines):
    """Baut aus den vollstaendigen Musterpartien ein Nachschlage-Woerterbuch:
    Zugfolge-bis-hierher (Tupel) -> Liste moeglicher, theoretisch guter
    naechster Zuege."""
    book = {}
    for line in lines:
        prefix = []
        for san in line:
            key = tuple(prefix)
            book.setdefault(key, [])
            if san not in book[key]:
                book[key].append(san)
            prefix.append(san)
    return book


OPENING_BOOK = _build_opening_book(OPENING_BOOK_LINES)
OPENING_BOOK_MAX_PLIES = 16  # ab wann die Engine das Buch verlaesst und selbst rechnet


def book_move(state, san_prefix):
    """Sucht in der Eroeffnungstheorie nach einem passenden, anerkannt
    starken Zug fuer die aktuelle Stellung. Gibt das Move-Objekt zurueck,
    oder None, wenn die Stellung nicht (mehr) im Buch steht."""
    if san_prefix is None or len(san_prefix) >= OPENING_BOOK_MAX_PLIES:
        return None
    candidates = OPENING_BOOK.get(tuple(san_prefix))
    if not candidates:
        return None
    legal = state.legal_moves()
    options = list(candidates)
    random.shuffle(options)
    for san in options:
        for m in legal:
            if to_san(state, m, legal) == san:
                return m
    return None


class ChessAI:
    def __init__(self, depth=3):
        self.depth = depth

    def choose_move(self, state, memory=None, san_prefix=None):
        color = state.turn

        buch_zug = book_move(state, san_prefix)
        if buch_zug is not None:
            return buch_zug, state.evaluate()

        best_move = None
        best_score = -999999 if color == WHITE else 999999
        alpha, beta = -999999, 999999
        moves = state.legal_moves(color)
        legal_for_san = moves
        moves = self._order_moves(moves)
        use_learning = memory is not None and san_prefix is not None and len(san_prefix) < LEARN_PLIES
        prefix_key = "|".join(san_prefix) if use_learning else None
        for m in moves:
            state.make_move(m, record=False)
            score = self._minimax(state, self.depth - 1, alpha, beta, color == BLACK)
            state.unmake_move()
            if use_learning:
                san = to_san(state, m, legal_for_san)
                bias = memory.bias_for(prefix_key, san)
                score = score + bias if color == WHITE else score - bias
            if color == WHITE and score > best_score:
                best_score = score
                best_move = m
                alpha = max(alpha, score)
            elif color == BLACK and score < best_score:
                best_score = score
                best_move = m
                beta = min(beta, score)
        return best_move, best_score

    def _order_moves(self, moves):
        """MVV-LVA-Sortierung (Most Valuable Victim - Least Valuable Attacker):
        Schlagzuege werden zuerst nach dem Wert der geschlagenen Figur sortiert
        (abzueglich des Werts der eigenen ziehenden Figur), Bauernumwandlungen
        und en-passant-Schlaege werden ebenfalls nach vorn gezogen. Das sorgt
        dafuer, dass die Alpha-Beta-Suche vielversprechende Zuege zuerst prueft
        und dadurch deutlich mehr Aeste abschneiden kann - macht die KI bei
        gleicher Suchtiefe spuerbar staerker."""

        def schluessel(m):
            wert = 0
            if m.captured:
                angreifer_wert = PIECE_VALUES.get(m.piece.upper(), 0)
                opfer_wert = PIECE_VALUES.get(m.captured.upper(), 0)
                wert += 10 * opfer_wert - angreifer_wert
            if m.promotion:
                wert += PIECE_VALUES.get(m.promotion, 0)
            if m.special == "ep":
                wert += PIECE_VALUES["P"]
            return wert

        return sorted(moves, key=schluessel, reverse=True)

    def _quiescence(self, state, alpha, beta, maximizing, qdepth=4, pruefe_schach=True):
        """Ruhesuche (Quiescence-Suche): wird am Ende der eigentlichen Suchtiefe
        aufgerufen und sucht Schlagzuege, Bauernumwandlungen und en-passant-
        Schlaege konsequent weiter, bis eine "ruhige" Stellung erreicht ist.
        Das verhindert den Horizont-Effekt (z.B. einen scheinbar guten Zug, der
        eine Figur nur deshalb gewinnt, weil die Suche genau vor dem Rueckschlag
        aufhoert).

        Zusaetzlich wird direkt hinter der eigentlichen Suchtiefe eine Ebene lang
        auch nach Zuegen gesucht, die dem Gegner Schach bieten - so erkennt die
        KI drohende Schachs und Mattangriffe (inklusive Mattnetzen ueber
        Bauernabtausch/-umwandlung und en passant), die eine reine Schlagzug-
        Ruhesuche uebersehen wuerde."""
        stand_pat = state.evaluate()
        if maximizing:
            if stand_pat >= beta:
                return stand_pat
            alpha = max(alpha, stand_pat)
        else:
            if stand_pat <= alpha:
                return stand_pat
            beta = min(beta, stand_pat)

        farbe = state.turn
        moves = state.legal_moves(farbe)
        if not moves:
            if state.in_check(farbe):
                # Matt: je naeher am Zug, desto staerker gewichtet
                return (-999999 - qdepth) if maximizing else (999999 + qdepth)
            return 0  # Patt

        unruhig = [m for m in moves if m.captured or m.promotion or m.special == "ep"]

        if qdepth > 0 and pruefe_schach:
            # Nur eine Ebene tief zusaetzlich nach Schachgeboten suchen, um die
            # Suche nicht explodieren zu lassen - reicht aber aus, um drohende
            # Schachs/Mattangriffe direkt hinter dem Suchhorizont zu erkennen.
            schon_erfasst = set(id(m) for m in unruhig)
            for m in moves:
                if id(m) in schon_erfasst:
                    continue
                state.make_move(m, record=False)
                gibt_schach = state.in_check(state.turn)
                state.unmake_move()
                if gibt_schach:
                    unruhig.append(m)

        if not unruhig or qdepth <= 0:
            return stand_pat

        unruhig = self._order_moves(unruhig)
        if maximizing:
            wert = stand_pat
            for m in unruhig:
                state.make_move(m, record=False)
                wert = max(wert, self._quiescence(state, alpha, beta, False, qdepth - 1, False))
                state.unmake_move()
                alpha = max(alpha, wert)
                if alpha >= beta:
                    break
            return wert
        else:
            wert = stand_pat
            for m in unruhig:
                state.make_move(m, record=False)
                wert = min(wert, self._quiescence(state, alpha, beta, True, qdepth - 1, False))
                state.unmake_move()
                beta = min(beta, wert)
                if alpha >= beta:
                    break
            return wert

    def _minimax(self, state, depth, alpha, beta, maximizing):
        if depth == 0:
            return self._quiescence(state, alpha, beta, maximizing)
        moves = state.legal_moves(state.turn)
        if not moves:
            if state.in_check(state.turn):
                return -999999 + (10 - depth) if maximizing else 999999 - (10 - depth)
            return 0
        moves = self._order_moves(moves)
        if maximizing:
            value = -999999
            for m in moves:
                state.make_move(m, record=False)
                value = max(value, self._minimax(state, depth - 1, alpha, beta, False))
                state.unmake_move()
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = 999999
            for m in moves:
                state.make_move(m, record=False)
                value = min(value, self._minimax(state, depth - 1, alpha, beta, True))
                state.unmake_move()
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value


# ============================================================
# Ab hier: grafische Oberflaeche (urspruenglich schach.py)
# ============================================================

# -*- coding: utf-8 -*-
"""
Schach fuer Windows - eigenstaendiges Spiel mit eigener Engine.
Enthaelt: 2D-Brett (Holzoptik), Figuren in Marmor-Optik, Mensch-vs-Mensch
und Mensch-vs-Computer, Zugliste mit Navigation, Rueckgaengig/Wiederholen,
Partie-Analyse nach Spielende, Speichern der Statistik als .txt.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import datetime
import os

from tkinter import simpledialog

# ---------- Farben ----------
TITLE_BG = "#ffffff"        # weisse Menueleiste, wie gewuenscht
TITLE_FG = "#222222"
CLOSE_RED = "#e81123"
APP_BG = "#f4f1ea"

LIGHT_SQ = "#e8c99b"        # helles Holz
DARK_SQ = "#8b5a2b"         # dunkles Holz
SELECT_COLOR = "#ffef5c"
MOVE_HINT_COLOR = "#5c9c5c"
CHECK_COLOR = "#e05a5a"

WHITE_PIECE_FILL = "#f7f5f0"     # helle Marmor-Optik
WHITE_PIECE_OUTLINE = "#555555"
BLACK_PIECE_FILL = "#2b2b2e"     # dunkle Marmor-Optik
BLACK_PIECE_OUTLINE = "#9a9a9a"

UNICODE_PIECES = {
    "K": "\u2654", "Q": "\u2655", "R": "\u2656", "B": "\u2657", "N": "\u2658", "P": "\u2659",
    "k": "\u265A", "q": "\u265B", "r": "\u265C", "b": "\u265D", "n": "\u265E", "p": "\u265F",
}


SQUARE_SIZE = 64
BOARD_PIXELS = SQUARE_SIZE * 8

DIFFICULTIES = {"Leicht": 2, "Mittel": 3, "Schwer": 4, "Sehr stark": 5}


class ChessApp(tk.Tk):
    def __init__(self):
        super().__init__()
        # WICHTIG: kein overrideredirect mehr! Ein rahmenloses Fenster taucht unter
        # Windows nicht in der Taskleiste auf und ist per Alt+Tab nicht auffindbar -
        # dadurch konnte das Spiel unsichtbar im Hintergrund haengen bleiben.
        # Stattdessen: normaler, garantiert sichtbarer Fensterrahmen + XP-blaue
        # Werkzeugleiste innen fuers Aussehen.
        self.title("Schach")
        self.geometry("980x700+150+60")
        self.configure(bg=APP_BG)
        # Fenster frei skalierbar und ueber die native Maximieren-Schaltflaeche
        # (bzw. Doppelklick auf die Titelleiste) auf Vollbild aufzoombar -
        # funktioniert so unter Windows 10 und 11 mit den normalen
        # Fenster-Bedienelementen (Minimieren/Maximieren/Schliessen).
        self.resizable(True, True)
        self.minsize(860, 560)
        self.lift()
        self.attributes("-topmost", True)
        self.after(300, lambda: self.attributes("-topmost", False))
        self.focus_force()

        self.state_ = None
        self.ai = None
        self.memory = LearningMemory()  # persistenter Lernspeicher (schach_lernen.json)
        self.mode = None            # "computer" oder "mensch"
        self.human_color = WHITE
        self.selected_sq = None
        self.legal_targets = []
        self.view_ptr = 0           # wie viele Zuege aus der Historie aktuell sichtbar sind
        self.game_over_shown = False
        self.square_size = SQUARE_SIZE  # aktuelle Feldkantenlaenge, passt sich der Fenstergroesse an

        # persistente Auswahl, auch von der Menueleiste aus nutzbar
        self.pref_mode = "computer"
        self.pref_color = "Weiß"
        self.pref_diff = "Mittel"

        self._build_titlebar()
        self._build_menubar()
        self.container = tk.Frame(self, bg=APP_BG)
        self.container.pack(fill="both", expand=True)

        # Tastenkuerzel: Zug zurueck/vor, klassisch wie in vielen Programmen
        self.bind_all("<Control-z>", lambda _e: self._nav_back())
        self.bind_all("<Control-y>", lambda _e: self._nav_forward())
        self.bind_all("<Control-Shift-Z>", lambda _e: self._nav_forward())

        self._show_menu()

    # ---------- Echte Windows-Menueleiste (immer sichtbar, auch im Spiel) ----------
    def _build_menubar(self):
        menubar = tk.Menu(self)

        spiel_menu = tk.Menu(menubar, tearoff=0)
        spiel_menu.add_command(label="Neustart", command=lambda: self._quick_start())
        spiel_menu.add_command(label="Zurück zum Hauptmenü", command=self._show_menu)
        spiel_menu.add_separator()
        spiel_menu.add_command(label="Beenden", command=self.destroy)
        menubar.add_cascade(label="Spiel", menu=spiel_menu)

        modus_menu = tk.Menu(menubar, tearoff=0)
        modus_menu.add_command(label="Spieler gegen Spieler",
                                command=lambda: self._quick_start(mode="mensch"))
        modus_menu.add_command(label="Spieler gegen Computer",
                                command=lambda: self._quick_start(mode="computer"))
        menubar.add_cascade(label="Modus", menu=modus_menu)

        farbe_menu = tk.Menu(menubar, tearoff=0)
        farbe_menu.add_command(label="Als Weiß spielen", command=lambda: self._quick_start(color="Weiß"))
        farbe_menu.add_command(label="Als Schwarz spielen", command=lambda: self._quick_start(color="Schwarz"))
        menubar.add_cascade(label="Farbe", menu=farbe_menu)

        partie_menu = tk.Menu(menubar, tearoff=0)
        partie_menu.add_command(label="Zug zurücknehmen\tStrg+Z", command=self._nav_back)
        partie_menu.add_command(label="Zug wiederholen (vorwärts)\tStrg+Y", command=self._nav_forward)
        partie_menu.add_command(label="Zum Partieanfang springen", command=self._nav_start)
        partie_menu.add_command(label="Ans Partieende springen", command=self._nav_end)
        partie_menu.add_separator()
        partie_menu.add_command(label="Züge einfügen & fortsetzen...", command=self._open_continue_dialog)
        partie_menu.add_command(label="Partie analysieren", command=self._show_analysis)
        partie_menu.add_command(label="Statistik als TXT speichern", command=self._save_stats)
        partie_menu.add_separator()
        partie_menu.add_command(label="KI trainieren (Selbstspiel)...", command=self._open_training_dialog)
        partie_menu.add_command(label="Partien einfügen & lernen...", command=self._open_import_dialog)
        menubar.add_cascade(label="Partie", menu=partie_menu)

        self.config(menu=menubar)

    def _quick_start(self, mode=None, color=None, diff=None):
        """Startet sofort ein neues Spiel mit den (ggf. per Menue geaenderten)
        zuletzt gewaehlten Einstellungen - ohne erst zum Menue zurueckzumuessen."""
        if mode:
            self.pref_mode = mode
        if color:
            self.pref_color = color
        if diff:
            self.pref_diff = diff
        self.mode = self.pref_mode
        self.human_color = WHITE if self.pref_color == "Weiß" else BLACK
        depth = DIFFICULTIES.get(self.pref_diff, 3)
        self.ai = ChessAI(depth=depth)
        self.state_ = ChessState()
        self.selected_sq = None
        self.legal_targets = []
        self.view_ptr = 0
        self.game_over_shown = False
        self._show_board_screen()
        if self.mode == "computer" and self.human_color == BLACK:
            self.after(400, self._computer_turn)

    # ---------- XP-blaue Werkzeugleiste (nur Optik, Fenster selbst ist normal) ----------
    def _build_titlebar(self):
        self.titlebar = tk.Frame(self, bg=TITLE_BG, height=32)
        self.titlebar.pack(side="top", fill="x")
        tk.Label(
            self.titlebar, text="♟ Schach", bg=TITLE_BG, fg=TITLE_FG,
            font=("Tahoma", 11, "bold")
        ).pack(side="left", padx=10)
        close_btn = tk.Button(
            self.titlebar, text="X", bg=CLOSE_RED, fg="white",
            font=("Tahoma", 10, "bold"), width=4, bd=0,
            activebackground="#ff4444", activeforeground="white",
            command=self.destroy, cursor="hand2"
        )
        close_btn.pack(side="right", padx=4, pady=3)

    def _start_move(self, event):
        self._offset_x, self._offset_y = event.x, event.y

    def _do_move(self, event):
        x = self.winfo_pointerx() - self._offset_x
        y = self.winfo_pointery() - self._offset_y
        self.geometry(f"+{x}+{y}")

    def _clear_container(self):
        for w in self.container.winfo_children():
            w.destroy()

    def _open_continue_dialog(self):
        win = tk.Toplevel(self)
        win.title("Züge einfügen & fortsetzen")
        win.geometry("560x480")
        win.configure(bg="#ffffff")
        win.transient(self)

        tk.Label(
            win, text="Bereits gespielte Züge einfügen", bg="#ffffff",
            font=("Tahoma", 12, "bold")
        ).pack(pady=(10, 2))
        tk.Label(
            win, text="Beispiel: 1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 ...\n"
                      "Die Partie wird nachgespielt, analysiert, und du kannst direkt\n"
                      "ab dieser Stellung weiterspielen (aktueller Modus/Farbe bleibt erhalten).",
            bg="#ffffff", fg="#666666", font=("Tahoma", 9), justify="left"
        ).pack(pady=(0, 8))

        text_frame = tk.Frame(win, bg="#ffffff")
        text_frame.pack(fill="both", expand=True, padx=10)
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        input_text = tk.Text(text_frame, font=("Consolas", 10), wrap="word", yscrollcommand=scrollbar.set)
        input_text.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=input_text.yview)

        result_label = tk.Label(win, text="", bg="#ffffff", fg="#333333", font=("Tahoma", 9),
                                 justify="left", wraplength=520)
        result_label.pack(pady=6, fill="x", padx=10)

        def do_continue():
            content = input_text.get("1.0", tk.END).strip()
            if not content:
                messagebox.showwarning("Leer", "Bitte zuerst Züge einfügen.", parent=win)
                return
            games = split_pgn_games(content)
            tokens = games[0][0] if games else []
            new_state = ChessState()
            applied, error_tok = apply_san_sequence(new_state, tokens)

            if not applied:
                result_label.config(
                    text=f"Kein einziger Zug konnte gelesen werden"
                         + (f" (bei '{error_tok}')." if error_tok else ".")
                )
                return

            # neue Stellung uebernehmen, aktuellen Modus/Farbe/Schwierigkeit beibehalten
            self.mode = self.pref_mode
            self.human_color = WHITE if self.pref_color == "Weiß" else BLACK
            self.ai = ChessAI(depth=DIFFICULTIES.get(self.pref_diff, 3))
            self.state_ = new_state
            self.selected_sq = None
            self.legal_targets = []
            self.view_ptr = 0
            self.game_over_shown = False

            summary = f"{len(applied)} von {len(tokens)} Zügen geladen."
            if error_tok:
                summary += f"\nAbgebrochen bei nicht erkanntem Zug: '{error_tok}'."
            result_label.config(text=summary)

            win.destroy()
            self._show_board_screen()
            if self.state_.is_checkmate() or self.state_.is_stalemate():
                pass  # _update_status() in _show_board_screen loest _on_game_over() bereits aus
            elif self.mode == "computer" and self.state_.turn != self.human_color:
                self.after(400, self._computer_turn)

        btn_frame = tk.Frame(win, bg="#ffffff")
        btn_frame.pack(pady=8)
        tk.Button(btn_frame, text="Laden & fortsetzen", bg="#7a4a9c", fg="white", bd=0,
                  command=do_continue).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Abbrechen", bg="#888888", fg="white", bd=0,
                  command=win.destroy).pack(side="left", padx=5)

    def _open_training_dialog(self):
        n = simpledialog.askinteger(
            "Training", "Wie viele Partien soll die KI gegen sich selbst spielen?\n"
                        "(mehr Partien = längeres Training, z. B. 20-50)",
            initialvalue=20, minvalue=1, maxvalue=300, parent=self
        )
        if not n:
            return

        win = tk.Toplevel(self)
        win.title("Training läuft...")
        win.geometry("360x120")
        win.configure(bg="#ffffff")
        win.transient(self)
        label = tk.Label(win, text="Training startet...", bg="#ffffff", font=("Tahoma", 11))
        label.pack(pady=20)
        detail = tk.Label(win, text="", bg="#ffffff", fg="#666666", font=("Tahoma", 9))
        detail.pack()

        def progress(g, total, result):
            label.config(text=f"Partie {g} von {total} gespielt")
            detail.config(text=f"Letztes Ergebnis: {result}")
            win.update_idletasks()

        train_self_play(self.memory, num_games=n, depth=2, analyze_depth=1, progress_callback=progress)
        win.destroy()
        messagebox.showinfo(
            "Training fertig",
            f"{n} Trainingspartien gespielt.\nInsgesamt trainierte Partien: {self.memory.games_trained}"
        )
        self._show_menu()

    def _open_import_dialog(self):
        win = tk.Toplevel(self)
        win.title("Partien einfügen")
        win.geometry("560x480")
        win.configure(bg="#ffffff")
        win.transient(self)

        tk.Label(
            win, text="Partien einfügen (PGN oder einfache Zugliste)", bg="#ffffff",
            font=("Tahoma", 12, "bold")
        ).pack(pady=(10, 2))
        tk.Label(
            win, text="Beispiel: 1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 ...  (mehrere Partien\n"
                      "hintereinander einfügen geht auch, z. B. mit 1-0 / 0-1 / 1/2-1/2 dazwischen)",
            bg="#ffffff", fg="#666666", font=("Tahoma", 9), justify="left"
        ).pack(pady=(0, 8))

        text_frame = tk.Frame(win, bg="#ffffff")
        text_frame.pack(fill="both", expand=True, padx=10)
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        input_text = tk.Text(text_frame, font=("Consolas", 10), wrap="word", yscrollcommand=scrollbar.set)
        input_text.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=input_text.yview)

        result_label = tk.Label(win, text="", bg="#ffffff", fg="#333333", font=("Tahoma", 9), justify="left")
        result_label.pack(pady=6, fill="x", padx=10)

        def do_import():
            content = input_text.get("1.0", tk.END).strip()
            if not content:
                messagebox.showwarning("Leer", "Bitte zuerst Partie(n) einfügen.", parent=win)
                return
            reports = import_games_text(self.memory, content, analyze_depth=1)
            ok = sum(1 for r in reports if not r["error"])
            failed = [r for r in reports if r["error"]]
            summary = f"{ok} von {len(reports)} Partie(n) erfolgreich gelesen und gelernt."
            if failed:
                summary += f"\n{len(failed)} Partie(n) mit Problem:\n"
                for r in failed:
                    summary += f"  Partie {r['game']}: {r['error']} " \
                               f"({r['plies_imported']}/{r['tokens_total']} Zügen gelesen)\n"
            result_label.config(text=summary)

        btn_frame = tk.Frame(win, bg="#ffffff")
        btn_frame.pack(pady=8)
        tk.Button(btn_frame, text="Importieren & lernen", bg="#7a4a9c", fg="white", bd=0,
                  command=do_import).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Schließen", bg="#888888", fg="white", bd=0,
                  command=win.destroy).pack(side="left", padx=5)

    # ---------- Menue ----------
    def _show_menu(self):
        self._clear_container()
        tk.Label(
            self.container, text="Schach", bg=APP_BG, fg="#333333",
            font=("Georgia", 32, "bold")
        ).pack(pady=(50, 10))
        tk.Label(
            self.container, text="Wähle einen Modus", bg=APP_BG, fg="#555555",
            font=("Tahoma", 12)
        ).pack(pady=(0, 25))

        self.mode_var = tk.StringVar(value="mensch")
        mode_frame = tk.Frame(self.container, bg=APP_BG)
        mode_frame.pack(pady=5)
        tk.Radiobutton(
            mode_frame, text="Mensch gegen Mensch", variable=self.mode_var, value="mensch",
            bg=APP_BG, font=("Tahoma", 11), command=self._toggle_difficulty
        ).pack(anchor="w", pady=3)
        tk.Radiobutton(
            mode_frame, text="Mensch gegen Computer", variable=self.mode_var, value="computer",
            bg=APP_BG, font=("Tahoma", 11), command=self._toggle_difficulty
        ).pack(anchor="w", pady=3)

        self.diff_frame = tk.Frame(self.container, bg=APP_BG)
        self.diff_frame.pack(pady=15)
        tk.Label(self.diff_frame, text="Schwierigkeit:", bg=APP_BG, font=("Tahoma", 10)).grid(row=0, column=0, padx=5)
        self.diff_var = tk.StringVar(value="Mittel")
        for i, d in enumerate(DIFFICULTIES):
            tk.Radiobutton(
                self.diff_frame, text=d, variable=self.diff_var, value=d,
                bg=APP_BG, font=("Tahoma", 10)
            ).grid(row=0, column=i + 1, padx=5)
        self._set_diff_state("disabled")

        self.color_frame = tk.Frame(self.container, bg=APP_BG)
        self.color_frame.pack(pady=5)
        tk.Label(self.color_frame, text="Deine Farbe:", bg=APP_BG, font=("Tahoma", 10)).grid(row=0, column=0, padx=5)
        self.color_var = tk.StringVar(value="Weiß")
        tk.Radiobutton(self.color_frame, text="Weiß", variable=self.color_var, value="Weiß",
                        bg=APP_BG, font=("Tahoma", 10)).grid(row=0, column=1, padx=5)
        tk.Radiobutton(self.color_frame, text="Schwarz", variable=self.color_var, value="Schwarz",
                        bg=APP_BG, font=("Tahoma", 10)).grid(row=0, column=2, padx=5)

        tk.Button(
            self.container, text="Spiel starten", font=("Tahoma", 13, "bold"),
            bg="#4a7a4a", fg="white", width=18, height=2, bd=0, cursor="hand2",
            command=self._start_game
        ).pack(pady=15)

        tk.Button(
            self.container, text="KI trainieren (Selbstspiel)", font=("Tahoma", 10),
            bg="#3a6ea5", fg="white", width=24, bd=0, cursor="hand2",
            command=self._open_training_dialog
        ).pack(pady=(0, 6))
        tk.Button(
            self.container, text="Partien einfügen & lernen (PGN)", font=("Tahoma", 10),
            bg="#7a4a9c", fg="white", width=24, bd=0, cursor="hand2",
            command=self._open_import_dialog
        ).pack(pady=(0, 10))
        tk.Label(
            self.container,
            text=f"Bisher trainierte Partien: {self.memory.games_trained}",
            bg=APP_BG, fg="#777777", font=("Tahoma", 9)
        ).pack()

    def _toggle_difficulty(self):
        self._set_diff_state("normal" if self.mode_var.get() == "computer" else "disabled")

    def _set_diff_state(self, state):
        for child in self.diff_frame.winfo_children():
            try:
                child.configure(state=state)
            except tk.TclError:
                pass

    def _start_game(self):
        self.pref_mode = self.mode_var.get()
        self.pref_color = self.color_var.get()
        self.pref_diff = self.diff_var.get()
        self._quick_start()

    # ---------- Spielbildschirm ----------
    def _show_board_screen(self):
        self._clear_container()

        main = tk.Frame(self.container, bg=APP_BG)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        left = tk.Frame(main, bg=APP_BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.status_label = tk.Label(
            left, text="", bg=APP_BG, fg="#333333", font=("Tahoma", 13, "bold")
        )
        self.status_label.pack(pady=(0, 6))

        # Das Brett fuellt den verfuegbaren Platz und passt seine Feldgroesse
        # dynamisch an - dadurch wird das Brett beim Vergroessern/Maximieren
        # des Fensters automatisch mitgroesser statt nur leeren Platz zu lassen.
        self.canvas = tk.Canvas(left, bg=APP_BG, highlightthickness=0,
                                 width=BOARD_PIXELS + 30, height=BOARD_PIXELS + 30)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self._on_board_click)
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        # Mittlere Spalte: geschlagene Figuren aufgelistet (aus schach.py
        # uebernommen), zwischen Spielbrett und der Zugliste rechts.
        middle = tk.Frame(main, bg=APP_BG, width=190)
        middle.pack(side="left", fill="y", padx=(0, 10))
        middle.pack_propagate(False)

        tk.Label(middle, text="Materialbilanz", bg=APP_BG, fg="#333333",
                 font=("Tahoma", 12, "bold")).pack(anchor="w", pady=(0, 4))
        self.material_label = tk.Label(middle, text="+0", bg=APP_BG, fg="#2f6f2f",
                                        font=("Tahoma", 20, "bold"))
        self.material_label.pack(anchor="w", pady=(0, 12))

        tk.Label(middle, text="Weiß hat geschlagen:", bg=APP_BG, fg="#555555",
                 font=("Tahoma", 9, "bold")).pack(anchor="w")
        self.captured_by_white_list = tk.Listbox(
            middle, height=8, bg=APP_BG, bd=0, highlightthickness=0,
            font=("Segoe UI Symbol", 13), activestyle="none")
        self.captured_by_white_list.pack(anchor="w", fill="x", pady=(2, 10))

        tk.Label(middle, text="Schwarz hat geschlagen:", bg=APP_BG, fg="#555555",
                 font=("Tahoma", 9, "bold")).pack(anchor="w")
        self.captured_by_black_list = tk.Listbox(
            middle, height=8, bg=APP_BG, bd=0, highlightthickness=0,
            font=("Segoe UI Symbol", 13), activestyle="none")
        self.captured_by_black_list.pack(anchor="w", fill="x", pady=(2, 10))

        right = tk.Frame(main, bg=APP_BG, width=280)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        tk.Label(right, text="Züge", bg=APP_BG, font=("Tahoma", 12, "bold")).pack(anchor="w")
        list_frame = tk.Frame(right, bg=APP_BG)
        list_frame.pack(fill="both", expand=True, pady=5)
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        self.move_listbox = tk.Listbox(
            list_frame, yscrollcommand=scrollbar.set, font=("Consolas", 11),
            activestyle="dotbox"
        )
        self.move_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.move_listbox.yview)
        self.move_listbox.bind("<<ListboxSelect>>", self._on_move_select)

        nav = tk.Frame(right, bg=APP_BG)
        nav.pack(pady=6)
        tk.Button(nav, text="|<", width=4, command=self._nav_start).grid(row=0, column=0, padx=2)
        tk.Button(nav, text="<", width=4, command=self._nav_back).grid(row=0, column=1, padx=2)
        tk.Button(nav, text=">", width=4, command=self._nav_forward).grid(row=0, column=2, padx=2)
        tk.Button(nav, text=">|", width=4, command=self._nav_end).grid(row=0, column=3, padx=2)

        ctrl = tk.Frame(right, bg=APP_BG)
        ctrl.pack(pady=10, fill="x")
        tk.Button(ctrl, text="Neustart", bg="#4a7a4a", fg="white", bd=0,
                  command=lambda: self._quick_start()).pack(fill="x", pady=2)
        tk.Button(ctrl, text="Zurück zum Menü", bg="#888888", fg="white", bd=0,
                  command=self._show_menu).pack(fill="x", pady=2)
        tk.Button(ctrl, text="Computer soll jetzt ziehen", bg="#2f6f4f", fg="white", bd=0,
                  command=self._force_computer_move).pack(fill="x", pady=2)
        tk.Button(ctrl, text="Züge einfügen & fortsetzen", bg="#7a4a9c", fg="white", bd=0,
                  command=self._open_continue_dialog).pack(fill="x", pady=2)
        self.analyze_btn = tk.Button(ctrl, text="Partie analysieren", bg="#3a6ea5", fg="white", bd=0,
                                      state="disabled", command=self._show_analysis)
        self.analyze_btn.pack(fill="x", pady=2)
        tk.Button(ctrl, text="Statistik als TXT speichern", bg="#a5763a", fg="white", bd=0,
                  command=self._save_stats).pack(fill="x", pady=2)

        self._redraw_board()
        self._update_status()
        self._update_analyze_button()

    def _update_analyze_button(self):
        if hasattr(self, "analyze_btn"):
            state = "normal" if self.state_ and self.state_.history else "disabled"
            self.analyze_btn.config(state=state)

    def _on_canvas_resize(self, event):
        """Wird bei jeder Groessenaenderung des Brett-Canvas aufgerufen (z.B.
        beim Ziehen am Fensterrand oder beim Maximieren/Vollbild) und passt die
        Feldgroesse entsprechend an, damit das Brett den verfuegbaren Platz
        ausfuellt statt in der festen 980x700-Groesse stehen zu bleiben."""
        rand = 30
        nutzbar = max(160, min(event.width, event.height) - rand)
        neue_groesse = max(28, nutzbar // 8)
        if neue_groesse != self.square_size:
            self.square_size = neue_groesse
            if self.state_ is not None:
                self._redraw_board()

    def _force_computer_move(self):
        """Button: laesst die Engine sofort fuer die Seite ziehen, die gerade
        am Zug ist - unabhaengig vom gewaehlten Modus (nuetzlich z.B. nach dem
        Einfuegen einer Partie, oder um sich in Mensch-vs-Mensch einen Zug
        vorschlagen/spielen zu lassen)."""
        if self.state_ is None or self.state_.is_checkmate() or self.state_.is_stalemate():
            return
        # Zieht der Computer waehrend einer Zugwiedergabe (also nach "Zug
        # zurueck"), wird ab hier eine neue Variante begonnen - alle zuvor
        # zurueckgenommenen Zuege werden dabei verworfen (bewusst gewollt,
        # damit man einen Fehlzug korrigieren und anders weiterspielen kann).
        self.state_.redo_stack = []
        self.selected_sq = None
        self.legal_targets = []
        self._computer_turn()

    # ---------- Brett zeichnen ----------
    def _redraw_board(self):
        self.canvas.delete("all")
        board = self.state_.board
        king_in_check_sq = None
        if self.state_.in_check(self.state_.turn):
            king_in_check_sq = self.state_.find_king(self.state_.turn)

        size = self.square_size
        rand = 15 if size <= 48 else 20
        board_px = size * 8

        for r in range(8):
            for c in range(8):
                x0 = c * size + rand
                y0 = (7 - r) * size + rand
                x1, y1 = x0 + size, y0 + size

                farbe = LIGHT_SQ if (r + c) % 2 == 1 else DARK_SQ
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=farbe, outline="")

                if self.selected_sq == (r, c):
                    # halbtransparente Markierung per Stipple-Raster, damit die
                    # Feldfarbe darunter weiterhin durchscheint
                    self.canvas.create_rectangle(x0, y0, x1, y1, fill=SELECT_COLOR,
                                                  outline="", stipple="gray50")
                if king_in_check_sq == (r, c):
                    self.canvas.create_rectangle(x0, y0, x1, y1, outline=CHECK_COLOR, width=4)

                piece = board[r][c]
                if piece:
                    is_white = piece.isupper()
                    fill = WHITE_PIECE_FILL if is_white else BLACK_PIECE_FILL
                    outline = WHITE_PIECE_OUTLINE if is_white else BLACK_PIECE_OUTLINE
                    cx, cy = x0 + size / 2, y0 + size / 2
                    glyph = UNICODE_PIECES[piece]
                    fontgroesse = max(10, int(size * 0.62))
                    # Pseudo-Kontur fuer Marmor-Look: Umriss leicht versetzt, dann Fuellung
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        self.canvas.create_text(cx + dx, cy + dy, text=glyph,
                                                 font=("Segoe UI Symbol", fontgroesse), fill=outline)
                    self.canvas.create_text(cx, cy, text=glyph,
                                             font=("Segoe UI Symbol", fontgroesse), fill=fill)

                if (r, c) in self.legal_targets:
                    cx, cy = x0 + size / 2, y0 + size / 2
                    radius = max(5, size * 0.15)
                    self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius,
                                             fill=MOVE_HINT_COLOR, outline="")

        labelgroesse = max(7, min(9, size // 7))
        for c in range(8):
            self.canvas.create_text(c * size + rand + size / 2, board_px + rand + 10,
                                     text="abcdefgh"[c], font=("Tahoma", labelgroesse), fill="#555555")
        for r in range(8):
            self.canvas.create_text(rand // 2, (7 - r) * size + rand + size / 2,
                                     text=str(r + 1), font=("Tahoma", labelgroesse), fill="#555555")

        self._update_material_panel()

    def _update_material_panel(self):
        """Aktualisiert die Materialbilanz-Anzeige (Liste der geschlagenen
        Figuren pro Seite) anhand von self.state_.history - funktioniert dadurch
        automatisch auch beim Zurueck-/Vorblaettern in der Zugliste."""
        if not hasattr(self, "material_label") or self.state_ is None:
            return
        von_weiss_geschlagen = []   # schwarze Figuren, die Weiß geschlagen hat
        von_schwarz_geschlagen = []  # weiße Figuren, die Schwarz geschlagen hat
        for move, _snap in self.state_.history:
            if not move.captured:
                continue
            if move.captured.isupper():
                von_schwarz_geschlagen.append(move.captured)
            else:
                von_weiss_geschlagen.append(move.captured)

        wert_weiss = sum(PIECE_VALUES.get(p.upper(), 0) for p in von_weiss_geschlagen) // 100
        wert_schwarz = sum(PIECE_VALUES.get(p.upper(), 0) for p in von_schwarz_geschlagen) // 100
        bilanz = wert_weiss - wert_schwarz
        vorzeichen = "+" if bilanz >= 0 else ""
        self.material_label.config(text=f"{vorzeichen}{bilanz}",
                                    fg="#2f6f2f" if bilanz >= 0 else "#b33333")

        NAMEN = {"P": "Bauer", "N": "Springer", "B": "Läufer", "R": "Turm", "Q": "Dame", "K": "König"}

        def befuellen(listbox, figuren):
            listbox.delete(0, tk.END)
            if not figuren:
                listbox.insert(tk.END, "  -")
                return
            # haeufigste zuerst zaehlen, wie in einer typischen "geschlagene
            # Figuren"-Leiste (z.B. 3x Bauer statt drei einzelnen Zeilen)
            zaehler = {}
            for p in figuren:
                zaehler[p.upper()] = zaehler.get(p.upper(), 0) + 1
            reihenfolge = sorted(zaehler.items(), key=lambda kv: -PIECE_VALUES.get(kv[0], 0))
            for letter, anzahl in reihenfolge:
                glyph = UNICODE_PIECES[letter if figuren[0].isupper() else letter.lower()]
                suffix = f"  ×{anzahl}" if anzahl > 1 else ""
                listbox.insert(tk.END, f"  {glyph} {NAMEN.get(letter, letter)}{suffix}")

        befuellen(self.captured_by_white_list, von_weiss_geschlagen)
        befuellen(self.captured_by_black_list, von_schwarz_geschlagen)

    def _update_status(self):
        if self.state_.is_checkmate():
            winner = "Schwarz" if self.state_.turn == WHITE else "Weiß"
            self.status_label.config(text=f"Schachmatt! {winner} gewinnt.")
            self._on_game_over()
        elif self.state_.is_stalemate():
            self.status_label.config(text="Patt – Unentschieden.")
            self._on_game_over()
        else:
            player = "Weiß" if self.state_.turn == WHITE else "Schwarz"
            check_txt = " (Schach!)" if self.state_.in_check(self.state_.turn) else ""
            self.status_label.config(text=f"{player} ist am Zug{check_txt}")

    def _on_game_over(self):
        if not self.game_over_shown:
            self.game_over_shown = True
            self.analyze_btn.config(state="normal")
            self._learn_from_finished_game()

    def _learn_from_finished_game(self):
        if self.mode != "computer" or not self.state_.history:
            return
        computer_color = opponent(self.human_color)
        san_history = [getattr(m, "san", "?") for m, _snap in self.state_.history]

        if self.state_.is_checkmate():
            winner = opponent(self.state_.turn)  # wer zuletzt gezogen hat, hat matt gesetzt
            result_value = 1.0 if winner == computer_color else -1.0
        else:
            result_value = 0.0  # Patt / Remis

        analysis = analyze_game(self.state_.history, depth=1)
        mistakes = {}
        penalty_map = {"Ungenauigkeit": 0.3, "Fehler": 0.6, "Grober Fehler": 1.0}
        for r in analysis:
            if r["mover"] == computer_color:
                penalty = penalty_map.get(r["tag"], 0.0)
                if penalty:
                    mistakes[r["ply"] - 1] = penalty

        self.memory.update_from_game(san_history, computer_color, result_value, mistakes)
        self.memory.save()

    # ---------- Zugliste ----------
    def _refresh_move_list(self):
        self.move_listbox.delete(0, tk.END)
        entries = []
        buffer = None
        for i, (move, _snap) in enumerate(self.state_.history):
            san = getattr(move, "san", None) or "?"
            if i % 2 == 0:
                buffer = f"{i // 2 + 1}. {san}"
            else:
                buffer += f"   {san}"
                entries.append(buffer)
                buffer = None
        if buffer:
            entries.append(buffer)
        for e in entries:
            self.move_listbox.insert(tk.END, e)
        self.move_listbox.yview_moveto(1.0)

    # ---------- Interaktion Brett ----------
    def _on_board_click(self, event):
        # Ein Klick waehrend der Zugwiedergabe (nach "Zug zurueck") ist
        # ausdruecklich erlaubt: der Spieler kann so einen Fehlzug
        # zurueeknehmen, hier einen anderen Zug spielen und damit eine neue
        # Variante beginnen. Die zuvor zurueckgenommenen (jetzt ueberholten)
        # Zuege werden dabei verworfen - siehe make_move(clear_redo=True).
        if self.state_.is_checkmate() or self.state_.is_stalemate():
            return
        if self.mode == "computer" and self.state_.turn != self.human_color:
            return

        rand = 15 if self.square_size <= 48 else 20
        col = (event.x - rand) // self.square_size
        row = 7 - (event.y - rand) // self.square_size
        if not (0 <= row <= 7 and 0 <= col <= 7):
            return

        piece = self.state_.board[row][col]
        if self.selected_sq is None:
            if piece and self._piece_color(piece) == self.state_.turn:
                self.selected_sq = (row, col)
                self.legal_targets = [
                    (m.tr, m.tc) for m in self.state_.legal_moves()
                    if (m.fr, m.fc) == (row, col)
                ]
        else:
            if (row, col) == self.selected_sq:
                self.selected_sq = None
                self.legal_targets = []
            elif piece and self._piece_color(piece) == self.state_.turn:
                self.selected_sq = (row, col)
                self.legal_targets = [
                    (m.tr, m.tc) for m in self.state_.legal_moves()
                    if (m.fr, m.fc) == (row, col)
                ]
            elif (row, col) in self.legal_targets:
                self._make_human_move(self.selected_sq, (row, col))
                self.selected_sq = None
                self.legal_targets = []
            else:
                self.selected_sq = None
                self.legal_targets = []

        self._redraw_board()

    @staticmethod
    def _piece_color(piece):
        return WHITE if piece.isupper() else BLACK

    def _make_human_move(self, frm, to):
        candidates = [
            m for m in self.state_.legal_moves()
            if (m.fr, m.fc) == frm and (m.tr, m.tc) == to
        ]
        if not candidates:
            return
        move = candidates[0]
        if move.promotion and move.promotion != "Q":
            for m in candidates:
                if m.promotion == "Q":
                    move = m
                    break
        legal_before = self.state_.legal_moves()
        move.san = to_san(self.state_, move, legal_before)
        self.state_.make_move(move, record=True)
        self._after_move()

    def _after_move(self):
        self._refresh_move_list()
        self._redraw_board()
        self._update_status()
        self._update_analyze_button()
        if self.mode == "computer" and not self.state_.is_checkmate() and not self.state_.is_stalemate():
            if self.state_.turn != self.human_color:
                self.after(300, self._computer_turn)

    def _computer_turn(self):
        if self.state_.is_checkmate() or self.state_.is_stalemate():
            return
        legal_before = self.state_.legal_moves()
        san_prefix = [getattr(m, "san", "?") for m, _snap in self.state_.history]
        move, _score = self.ai.choose_move(self.state_, memory=self.memory, san_prefix=san_prefix)
        if move is None:
            return
        move.san = to_san(self.state_, move, legal_before)
        self.state_.make_move(move, record=True)
        self._after_move()

    # ---------- Navigation (Wiedergabe) ----------
    def _apply_view(self, target_index):
        if self.state_ is None:
            return
        current = len(self.state_.history)
        if target_index < current:
            for _ in range(current - target_index):
                self.state_.undo()
        elif target_index > current:
            for _ in range(target_index - current):
                self.state_.redo()
        self.selected_sq = None
        self.legal_targets = []
        self._redraw_board()
        self._update_status()
        total = len(self.state_.history) + len(self.state_.redo_stack)
        if len(self.state_.history) < total:
            player = "Weiß" if self.state_.turn == WHITE else "Schwarz"
            self.status_label.config(
                text=f"Zurückgeblättert – {player} ist hier am Zug. "
                     f"Mit '>|' weiterblättern, oder direkt einen neuen Zug spielen, "
                     f"um ab hier anders weiterzuspielen (neue Variante)."
            )

    def _nav_start(self):
        self._apply_view(0)

    def _nav_back(self):
        self._apply_view(max(0, len(self.state_.history) - 1))

    def _nav_forward(self):
        total = len(self.state_.history) + len(self.state_.redo_stack)
        self._apply_view(min(total, len(self.state_.history) + 1))

    def _nav_end(self):
        total = len(self.state_.history) + len(self.state_.redo_stack)
        self._apply_view(total)

    def _on_move_select(self, _event):
        sel = self.move_listbox.curselection()
        if not sel:
            return
        row_idx = sel[0]
        target_index = min((row_idx + 1) * 2, len(self.state_.history) + len(self.state_.redo_stack))
        self._apply_view(target_index)

    # ---------- Analyse ----------
    def _show_analysis(self):
        report = analyze_game(self.state_.history, depth=2)

        win = tk.Toplevel(self)
        win.title("Partie-Analyse")
        win.geometry("480x520")
        win.configure(bg="#ffffff")

        tk.Label(win, text="Analyse der Partie", font=("Tahoma", 14, "bold"), bg="#ffffff").pack(pady=10)
        tk.Label(win, text="(einfache Analyse durch die eingebaute Engine, keine Profi-Datenbank)",
                 font=("Tahoma", 8), fg="#777777", bg="#ffffff").pack()

        text = tk.Text(win, font=("Consolas", 10), wrap="word")
        text.pack(fill="both", expand=True, padx=10, pady=10)

        text.tag_config("grob", foreground="#c0392b")
        text.tag_config("fehler", foreground="#d68910")
        text.tag_config("ungenau", foreground="#7d6608")
        text.tag_config("ok", foreground="#333333")

        white_mistakes = 0
        black_mistakes = 0
        for r in report:
            spieler = "Weiß" if r["mover"] == WHITE else "Schwarz"
            line = f"Zug {r['ply']:>3} ({spieler}): {r['san']:<8}"
            if r["tag"]:
                line += f"  -> {r['tag']} (~{r['diff']} cp)\n"
                tag = {"Grober Fehler": "grob", "Fehler": "fehler", "Ungenauigkeit": "ungenau"}[r["tag"]]
                if r["tag"] in ("Grober Fehler", "Fehler"):
                    if r["mover"] == WHITE:
                        white_mistakes += 1
                    else:
                        black_mistakes += 1
            else:
                line += "\n"
                tag = "ok"
            text.insert(tk.END, line, tag)

        text.insert(tk.END, f"\nZusammenfassung:\nWeiß: {white_mistakes} nennenswerte Fehler\n"
                             f"Schwarz: {black_mistakes} nennenswerte Fehler\n")
        text.config(state="disabled")
        self._last_analysis = report

    # ---------- Statistik speichern ----------
    def _save_stats(self):
        folder = filedialog.askdirectory(title="Ordner zum Speichern wählen")
        if not folder:
            return

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"schachpartie_{timestamp}.txt"
        path = os.path.join(folder, filename)

        result = "Läuft noch"
        if self.state_.is_checkmate():
            result = "1-0 (Weiß gewinnt)" if self.state_.turn == BLACK else "0-1 (Schwarz gewinnt)"
        elif self.state_.is_stalemate():
            result = "1/2-1/2 (Patt)"

        lines = []
        lines.append("Schachpartie - Statistik")
        lines.append(f"Datum: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        lines.append(f"Modus: {'Mensch vs. Computer' if self.mode == 'computer' else 'Mensch vs. Mensch'}")
        if self.mode == "computer":
            lines.append(f"Schwierigkeit: {self.diff_var.get()}")
            lines.append(f"Mensch spielte: {'Weiß' if self.human_color == WHITE else 'Schwarz'}")
        lines.append(f"Ergebnis: {result}")
        lines.append("")
        lines.append("Zugliste:")
        for i, (move, _snap) in enumerate(self.state_.history):
            san = getattr(move, "san", "?")
            prefix = f"{i // 2 + 1}." if i % 2 == 0 else "   "
            sep = "\n" if i % 2 == 1 else " "
            lines.append(f"{prefix} {san}" if i % 2 == 0 else f"{san}")
        # sauberer neu zusammenbauen (Zugpaare je Zeile)
        move_lines = []
        buf = ""
        for i, (move, _snap) in enumerate(self.state_.history):
            san = getattr(move, "san", "?")
            if i % 2 == 0:
                buf = f"{i // 2 + 1}. {san}"
            else:
                buf += f"  {san}"
                move_lines.append(buf)
                buf = ""
        if buf:
            move_lines.append(buf)

        report_lines = []
        if getattr(self, "_last_analysis", None):
            report_lines.append("")
            report_lines.append("Analyse (Fehler-Erkennung):")
            for r in self._last_analysis:
                if r["tag"]:
                    spieler = "Weiß" if r["mover"] == WHITE else "Schwarz"
                    report_lines.append(f"  Zug {r['ply']} ({spieler}) {r['san']}: {r['tag']} (~{r['diff']} cp)")

        content = "\n".join(
            lines[:6] + [""] + move_lines + report_lines
        )
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Gespeichert", f"Statistik gespeichert unter:\n{path}")
        except OSError as e:
            messagebox.showerror("Fehler", f"Konnte Datei nicht speichern:\n{e}")


if __name__ == "__main__":
    import sys
    import traceback

    try:
        app = ChessApp()
        app.mainloop()
    except Exception:
        error_text = traceback.format_exc()
        # Fehler in eine Log-Datei neben dem Programm schreiben
        try:
            log_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            log_path = os.path.join(log_dir, "schach_fehler.log")
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(error_text)
        except OSError:
            log_path = None
        # Fehler zusaetzlich als Fenster anzeigen, damit er sichtbar ist,
        # auch ohne Konsole (--windowed Build)
        try:
            import tkinter.messagebox as mb
            hint = f"\n\nDetails wurden gespeichert in:\n{log_path}" if log_path else ""
            mb.showerror("Schach - Fehler beim Start", error_text[-1500:] + hint)
        except Exception:
            pass
