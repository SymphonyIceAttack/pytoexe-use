"""
Eigene Schach-Engine (reines Python, keine externen Bibliotheken).
Enthaelt: Zugregeln, Rochade, En-passant, Umwandlung, Schach/Matt/Patt-Erkennung,
sowie eine einfache KI (Minimax mit Alpha-Beta-Pruning).
"""

import copy
import json
import os
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


# ---------- KI ----------
class ChessAI:
    def __init__(self, depth=3):
        self.depth = depth

    def choose_move(self, state, memory=None, san_prefix=None):
        color = state.turn
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
        return sorted(moves, key=lambda m: 1 if m.captured else 0, reverse=True)

    def _minimax(self, state, depth, alpha, beta, maximizing):
        if depth == 0:
            return state.evaluate()
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
