import pygame
import chess
import chess.pgn
import os
import time
import tkinter as tk
from tkinter import filedialog

pygame.init()

# ── Layout constants ──────────────────────────────────────────────────────────
MARGIN = 25
LABEL_H = 22
UI_H = 58
BOTTOM_H = LABEL_H + UI_H
PANEL_MIN_W = 170
PANEL_PAD = 8
ROW_H = 22
PANEL_HDR_H = 26
NAV_H = 44

# ── Piece Editor Palette ─────────────────────────────────────────────────────
PALETTE_PAD = 6
PALETTE_BTN_SZ = 52
PALETTE_W = 2 * PALETTE_BTN_SZ + 3 * PALETTE_PAD + 8  # = 130
EDITOR_BG = (25, 25, 30)

# ── Colors ───────────────────────────────────────────────────────────────────
LIGHT = (245, 222, 179)
DARK = (100, 140, 80)
HIGHLIGHT = (124, 252, 0, 110)
MOVE_HIGHLIGHT = (0, 255, 255, 90)
ARROW_COLOR = (255, 140, 0, 210)
BG = (30, 30, 35)
BTN_NORMAL = (65, 65, 80)
BTN_HOVER = (100, 100, 125)
BTN_BORDER = (150, 150, 165)
BTN_TEXT = (220, 220, 220)
UI_BG = (35, 35, 40)
PANEL_BG = (28, 28, 33)
PANEL_HDR_BG = (40, 40, 52)
PANEL_ROW_A = (28, 28, 33)
PANEL_ROW_B = (34, 34, 42)
PANEL_CUR = (48, 80, 138)
PANEL_HOVER = (44, 44, 58)
PANEL_TXT = (210, 210, 215)
PANEL_NUM = (108, 108, 130)
SCROLLBAR_BG = (45, 45, 55)
SCROLLBAR_FG = (110, 110, 140)

# ── Piece map ────────────────────────────────────────────────────────────────
_PIECE_MAP = {
    'P':'wP','R':'wR','N':'wN','B':'wB','Q':'wQ','K':'wK',
    'p':'bP','r':'bR','n':'bN','b':'bB','q':'bQ','k':'bK',
}

_GLYPH_W = {'K':'♔','Q':'♕','R':'♖','B':'♗','N':'♘'}
_GLYPH_B = {'K':'♚','Q':'♛','R':'♜','B':'♝','N':'♞'}

def _san_with_glyph(san: str, white: bool) -> str:
    if san and san[0] in _GLYPH_W:
        table = _GLYPH_W if white else _GLYPH_B
        return table[san[0]] + san[1:]
    return san


class ChessPracticeGUI:
    def __init__(self):
        self.board = chess.Board()
        self.base_fen = chess.STARTING_FEN
        self.move_history = []
        self.current_index = -1
        self.arrows = []
        self.flipped = False
        self.selected = None
        self.legal_moves = []
        self.free_move = False
        self.arrow_start = None

        self.fullscreen = False
        self.windowed_size = (920, 660)

        self.playing = False
        self.play_speed = 0.85
        self._last_play_t = 0.0

        self.panel_scroll = 0
        self._san_cache: dict[int, str] = {}

        self.editor_active = False
        self.selected_piece = None
        self.palette_rect = None
        self.palette_buttons = []

        self.win_w = self.win_h = 0
        self.show_panel = False
        self.panel_x = self.panel_w = 0
        self.nav_rects: list[pygame.Rect] = []

        # New: Game over handling
        self.game_over_timestamp = 0.0
        self.GAME_OVER_DISPLAY_TIME = 3.0   # seconds the overlay stays visible

        self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
        pygame.display.set_caption("Chess Practice Tool")
       
        self._load_pieces()
        self._layout(*self.windowed_size)

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.windowed_size = self.screen.get_size()
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
        aw, ah = self.screen.get_size()
        self._layout(aw, ah)

    def _load_pieces(self):
        self._raw_imgs = {}
        for sym, fname in _PIECE_MAP.items():
            path = os.path.join("pieces", f"{fname}.png")
            if os.path.exists(path):
                try:
                    self._raw_imgs[sym] = pygame.image.load(path).convert_alpha()
                except Exception as e:
                    print(f"Warning: {path}: {e}")

    def _layout(self, w: int, h: int, force: bool = False):
        if not force and w == self.win_w and h == self.win_h:
            return
        self.win_w, self.win_h = w, h

        self.editor_active = self.free_move

        extra_right = PALETTE_W + MARGIN if self.editor_active else 0
        extra_panel = PANEL_MIN_W + MARGIN if w > 720 else 0
        self.show_panel = extra_panel > 0

        avail_w = w - 2 * MARGIN - extra_right - extra_panel
        avail_h = h - MARGIN - BOTTOM_H

        board_size = max(64, (min(avail_w, avail_h) // 8) * 8)
        self.board_size = board_size
        self.square_size = board_size // 8

        board_x = MARGIN
        self.panel_x = board_x + board_size + MARGIN

        if self.show_panel:
            self.panel_w = min(PANEL_MIN_W + 80, w - self.panel_x - MARGIN - extra_right)
        else:
            self.panel_w = 0

        sprite_sz = max(4, self.square_size - 8)
        self.piece_imgs = {s: pygame.transform.smoothscale(img, (sprite_sz, sprite_sz))
                           for s, img in self._raw_imgs.items()}

        cp = max(10, self.square_size // 4)
        self.coord_font = pygame.font.SysFont("Arial", cp, bold=True)
        self.ui_font = pygame.font.SysFont("Arial", 17)
        self.small_font = pygame.font.SysFont("Arial", 14)
        self.btn_font = pygame.font.SysFont("Arial", 14, bold=True)
        self.move_font = pygame.font.SysFont("Segoe UI Symbol", 13)
        self.hdr_font = pygame.font.SysFont("Arial", 13, bold=True)

        self._ui_top = MARGIN + board_size + LABEL_H

        strip_right = w - 15
        bw, bh = 72, 26
        self.reset_rect = pygame.Rect(strip_right - bw, self._ui_top + (UI_H - bh)//2, bw, bh)

        if self.show_panel and self.panel_w > 0:
            px = self.panel_x
            ph = h - 2 * MARGIN
            self.panel_rect = pygame.Rect(px, MARGIN, self.panel_w, ph)
            self.panel_hdr_rect = pygame.Rect(px, MARGIN, self.panel_w, PANEL_HDR_H)
            list_y = MARGIN + PANEL_HDR_H
            list_h = ph - PANEL_HDR_H - NAV_H
            self.panel_list_rect = pygame.Rect(px, list_y, self.panel_w, max(0, list_h))
            nav_y = MARGIN + ph - NAV_H
            self.nav_rect = pygame.Rect(px, nav_y, self.panel_w, NAV_H)
            self._build_nav_rects()

        self.palette_buttons = []
        self.palette_rect = None
        if self.editor_active:
            palette_x = w - PALETTE_W - MARGIN
            self.palette_rect = pygame.Rect(palette_x, MARGIN, PALETTE_W, h - 2 * MARGIN)

            pieces = ['K','Q','R','B','N','P', 'k','q','r','b','n','p']
            btn_size = PALETTE_BTN_SZ
            cols = 2
            start_y = MARGIN + 35

            for i, sym in enumerate(pieces):
                row = i // cols
                col = i % cols
                x = palette_x + PALETTE_PAD + col * (btn_size + PALETTE_PAD)
                y = start_y + row * (btn_size + PALETTE_PAD)
                rect = pygame.Rect(x, y, btn_size, btn_size)
                self.palette_buttons.append((rect, sym))

        self._clamp_scroll()

    def _build_nav_rects(self):
        px, pw = self.panel_x, self.panel_w
        nav_y = self.nav_rect.y
        n = 5
        usable = pw - 2 * PANEL_PAD
        bw = usable // n
        bh = NAV_H - 2 * PANEL_PAD
        by = nav_y + PANEL_PAD
        self.nav_rects = [pygame.Rect(px + PANEL_PAD + i * bw, by, bw - 2, bh) for i in range(n)]

    def _nav_labels(self) -> list[str]:
        return ["|<", "<", ("⏸" if self.playing else "▶"), ">", ">|"]

    def _clamp_scroll(self):
        if not self.show_panel:
            self.panel_scroll = 0
            return
        total = (len(self.move_history) + 1) // 2
        visible = self.panel_list_rect.height // ROW_H
        self.panel_scroll = max(0, min(self.panel_scroll, max(0, total - visible)))

    def _scroll_to_current(self):
        if not self.show_panel: return
        row = max(0, self.current_index // 2) if self.current_index >= 0 else 0
        visible = self.panel_list_rect.height // ROW_H
        if row < self.panel_scroll:
            self.panel_scroll = row
        elif row >= self.panel_scroll + visible:
            self.panel_scroll = row - visible + 1
        self._clamp_scroll()

    def _get_san(self, idx: int) -> str:
        if idx in self._san_cache:
            return self._san_cache[idx]
        if idx < 0 or idx >= len(self.move_history):
            return "?"

        cached_before = [k for k in self._san_cache if k < idx]
        start_idx = max(cached_before) if cached_before else -1

        b = chess.Board(self.base_fen)
        for i in range(start_idx + 1):
            self._apply_move(b, self.move_history[i])

        for i in range(start_idx + 1, idx + 1):
            if i >= len(self.move_history):
                break
            try:
                self._san_cache[i] = b.san(self.move_history[i])
            except Exception:
                self._san_cache[i] = self.move_history[i].uci()
            self._apply_move(b, self.move_history[i])

        return self._san_cache.get(idx, "?")

    def _invalidate_san_from(self, idx: int):
        for k in list(self._san_cache.keys()):
            if k >= idx:
                del self._san_cache[k]

    # ====================== Drawing ======================
    def draw_board(self):
        ss = self.square_size
        for rank in range(8):
            for file in range(8):
                x = file * ss + MARGIN
                y = (7 - rank) * ss + MARGIN if not self.flipped else rank * ss + MARGIN
                cf = (7 - file) if self.flipped else file
                color = DARK if (cf + rank) % 2 == 0 else LIGHT
                pygame.draw.rect(self.screen, color, (x, y, ss, ss))

    def draw_coordinates(self):
        ss = self.square_size
        ly = MARGIN + self.board_size + 6
        files = 'abcdefgh' if not self.flipped else 'hgfedcba'
        for i, ch in enumerate(files):
            t = self.coord_font.render(ch, True, (255, 255, 255))
            cx = i * ss + ss // 2 + MARGIN
            self.screen.blit(t, (cx - t.get_width() // 2, ly))
        for i in range(8):
            cy = (7 - i) * ss + ss // 2 + MARGIN if not self.flipped else i * ss + ss // 2 + MARGIN
            t = self.coord_font.render(str(i + 1), True, (255, 255, 255))
            self.screen.blit(t, (max(2, MARGIN - t.get_width() - 4), cy - t.get_height() // 2))

    def draw_pieces(self):
        ss = self.square_size
        for sq in range(64):
            piece = self.board.piece_at(sq)
            if not piece: continue
            x, y = self.square_to_coord(sq)
            sym = piece.symbol()
            if sym in self.piece_imgs:
                self.screen.blit(self.piece_imgs[sym], (x + 4, y + 4))

    def draw_highlights(self):
        ss = self.square_size
        if self.selected is not None:
            x, y = self.square_to_coord(self.selected)
            s = pygame.Surface((ss, ss), pygame.SRCALPHA)
            s.fill(HIGHLIGHT)
            self.screen.blit(s, (x, y))

        for mv in self.legal_moves:
            tx, ty = self.square_to_coord(mv.to_square)
            s = pygame.Surface((ss, ss), pygame.SRCALPHA)
            s.fill(MOVE_HIGHLIGHT)
            self.screen.blit(s, (tx, ty))

        self._draw_king_endgame_highlights()

    def _draw_king_endgame_highlights(self):
        """Highlight winning/losing kings"""
        try:
            if not (self.board.is_checkmate() or self.board.is_stalemate()):
                return
        except:
            return

        white_king = black_king = None
        for sq in range(64):
            p = self.board.piece_at(sq)
            if p and p.piece_type == chess.KING:
                if p.color == chess.WHITE:
                    white_king = sq
                else:
                    black_king = sq

        ss = self.square_size
        if self.board.is_checkmate():
            winner_is_white = self.board.turn == chess.BLACK
            win_sq = white_king if winner_is_white else black_king
            lose_sq = black_king if winner_is_white else white_king

            if win_sq is not None:
                x, y = self.square_to_coord(win_sq)
                s = pygame.Surface((ss, ss), pygame.SRCALPHA)
                s.fill((0, 255, 100, 160))
                self.screen.blit(s, (x, y))

            if lose_sq is not None:
                x, y = self.square_to_coord(lose_sq)
                s = pygame.Surface((ss, ss), pygame.SRCALPHA)
                s.fill((255, 50, 50, 160))
                self.screen.blit(s, (x, y))

        elif self.board.is_stalemate():
            for sq in (white_king, black_king):
                if sq is not None:
                    x, y = self.square_to_coord(sq)
                    s = pygame.Surface((ss, ss), pygame.SRCALPHA)
                    s.fill((255, 240, 0, 120))
                    self.screen.blit(s, (x, y))

    def draw_arrows(self):
        surf = pygame.Surface((self.win_w, self.win_h), pygame.SRCALPHA)
        for from_sq, to_sq in self.arrows:
            start = self.get_center(from_sq)
            end = self.get_center(to_sq)
            dx = chess.square_file(to_sq) - chess.square_file(from_sq)
            dy = chess.square_rank(to_sq) - chess.square_rank(from_sq)
            knight = (abs(dx) == 1 and abs(dy) == 2) or (abs(dx) == 2 and abs(dy) == 1)
            if knight:
                mid = (end[0], start[1]) if abs(dx) == 2 else (start[0], end[1])
                shaft_end = self._arrowhead(surf, mid, end)
                pygame.draw.line(surf, ARROW_COLOR, start, mid, 11)
                pygame.draw.line(surf, ARROW_COLOR, mid, shaft_end, 11)
                pygame.draw.circle(surf, ARROW_COLOR, mid, 6)
            else:
                shaft_end = self._arrowhead(surf, start, end)
                pygame.draw.line(surf, ARROW_COLOR, start, shaft_end, 11)
        self.screen.blit(surf, (0, 0))

    def _arrowhead(self, surface, start, end):
        dx, dy = end[0] - start[0], end[1] - start[1]
        length = (dx ** 2 + dy ** 2) ** 0.5
        if length < 1: return end
        ux, uy = dx / length, dy / length
        px, py = -uy, ux
        back = (end[0] - ux * 18, end[1] - uy * 18)
        left = (back[0] + px * 12, back[1] + py * 12)
        right = (back[0] - px * 12, back[1] - py * 12)
        pygame.draw.polygon(surface, ARROW_COLOR, [end, left, right])
        return back

    def draw_piece_palette(self):
        if not self.editor_active or not self.palette_rect: return
        pygame.draw.rect(self.screen, EDITOR_BG, self.palette_rect)
        pygame.draw.rect(self.screen, (60, 60, 70), self.palette_rect, 2)

        title = self.hdr_font.render("Piece Tool", True, (200, 200, 230))
        self.screen.blit(title, (self.palette_rect.centerx - title.get_width()//2, self.palette_rect.y + 8))

        mx, my = pygame.mouse.get_pos()
        for rect, sym in self.palette_buttons:
            hover = rect.collidepoint(mx, my)
            selected = self.selected_piece == sym
            color = (70, 120, 200) if selected else (45, 45, 55)
            if hover: color = (90, 140, 220)

            pygame.draw.rect(self.screen, color, rect, border_radius=8)
            pygame.draw.rect(self.screen, (180, 180, 200), rect, 2, border_radius=8)

            if sym in self.piece_imgs:
                img = self.piece_imgs[sym]
                self.screen.blit(img, (rect.centerx - img.get_width()//2, rect.centery - img.get_height()//2))

        instr_y = self.palette_rect.bottom - 110
        lines = ["L-Click: Place", "R-Click: Remove", "Click piece again to deselect"]
        for i, line in enumerate(lines):
            t = self.small_font.render(line, True, (160, 160, 170))
            self.screen.blit(t, (self.palette_rect.centerx - t.get_width()//2, instr_y + i*18))

    def draw_game_over_overlay(self, message: str):
        bs = self.board_size
        veil = pygame.Surface((bs, bs), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 160))
        self.screen.blit(veil, (MARGIN, MARGIN))
        fb = pygame.font.SysFont("Arial", max(28, self.square_size // 2), bold=True)
        fs = pygame.font.SysFont("Arial", max(16, self.square_size // 4))
        lbl = fb.render(message, True, (255, 230, 80))
        sub = fs.render("You can now review the game", True, (200, 200, 200))
        cx = MARGIN + bs // 2
        cy = MARGIN + bs // 2
        self.screen.blit(lbl, (cx - lbl.get_width() // 2, cy - lbl.get_height() // 2 - 10))
        self.screen.blit(sub, (cx - sub.get_width() // 2, cy + lbl.get_height() // 2 + 8))

    def draw_ui(self):
        W, ui_y = self.win_w, self._ui_top
        strip_w = (self.panel_x - MARGIN // 2) if self.show_panel else W
        pygame.draw.rect(self.screen, UI_BG, (0, ui_y, strip_w, UI_H))

        is_checkmate, is_stalemate, is_check = self._board_status()

        if is_checkmate:
            winner = "Black" if self.board.turn == chess.WHITE else "White"
            status = f"Checkmate — {winner} wins • {self.current_index + 1} moves"
            sc = (255, 100, 100)
        elif is_stalemate:
            status = f"Stalemate — Draw • {self.current_index + 1} moves"
            sc = (180, 180, 100)
        elif is_check:
            side = "White" if self.board.turn == chess.WHITE else "Black"
            status = f"{side} is in CHECK! • Move {self.current_index + 1}"
            sc = (255, 165, 60)
        else:
            tag = " • FREE MOVE" if self.free_move else ""
            status = f"{'White' if self.board.turn else 'Black'} to move • Move {self.current_index + 1}{tag}"
            sc = (255, 255, 255)

        self.screen.blit(self.ui_font.render(status, True, sc), (MARGIN, ui_y + 8))
        hint = "F11:Fullscreen  F:Flip  U:Undo  R:Redo  C:Clear  M:Free  P:Save  L:Load  N:Reset  Space:Play"
        self.screen.blit(self.small_font.render(hint, True, (155, 155, 155)), (MARGIN, ui_y + 34))

        mx, my = pygame.mouse.get_pos()
        hover = self.reset_rect.collidepoint(mx, my)
        pygame.draw.rect(self.screen, BTN_HOVER if hover else BTN_NORMAL, self.reset_rect, border_radius=5)
        pygame.draw.rect(self.screen, BTN_BORDER, self.reset_rect, 1, border_radius=5)
        lbl = self.btn_font.render("Reset", True, BTN_TEXT)
        self.screen.blit(lbl, (self.reset_rect.centerx - lbl.get_width() // 2,
                               self.reset_rect.centery - lbl.get_height() // 2))

    def draw_panel(self):
        if not self.show_panel: return
        pygame.draw.rect(self.screen, PANEL_BG, self.panel_rect)
        pygame.draw.rect(self.screen, PANEL_HDR_BG, self.panel_hdr_rect)
        t = self.hdr_font.render("Move List", True, (195, 200, 215))
        self.screen.blit(t, (self.panel_hdr_rect.x + PANEL_PAD, self.panel_hdr_rect.centery - t.get_height() // 2))
        self._draw_move_rows()
        self._draw_nav_buttons()

    def _draw_move_rows(self):
        lr = self.panel_list_rect
        if lr.height <= 0: return
        total_rows = (len(self.move_history) + 1) // 2
        if total_rows == 0:
            msg = self.move_font.render("No moves yet", True, PANEL_NUM)
            self.screen.blit(msg, (lr.x + PANEL_PAD, lr.y + PANEL_PAD))
            return
        pw = lr.width
        SCROLL_W = 7
        num_w = 30
        col_w = (pw - num_w - SCROLL_W) // 2

        total = (len(self.move_history) + 1) // 2
        visible_rows = lr.height // ROW_H
        if total > visible_rows:
            sb_x = lr.right - SCROLL_W
            sb_track_h = lr.height
            thumb_h = max(20, int(sb_track_h * visible_rows / total))
            thumb_top = lr.top + int((sb_track_h - thumb_h) * self.panel_scroll / max(1, total - visible_rows))
            pygame.draw.rect(self.screen, SCROLLBAR_BG, (sb_x, lr.top, SCROLL_W, sb_track_h))
            pygame.draw.rect(self.screen, SCROLLBAR_FG, (sb_x, thumb_top, SCROLL_W, thumb_h), border_radius=3)

        mx, my = pygame.mouse.get_pos()
        self.screen.set_clip(lr)
        for row in range(self.panel_scroll, total_rows):
            vy = lr.top + (row - self.panel_scroll) * ROW_H
            if vy >= lr.bottom: break
            pygame.draw.rect(self.screen, PANEL_ROW_B if row % 2 else PANEL_ROW_A, (lr.x, vy, pw - SCROLL_W, ROW_H))
            nt = self.move_font.render(f"{row + 1}.", True, PANEL_NUM)
            self.screen.blit(nt, (lr.x + 4, vy + (ROW_H - nt.get_height()) // 2))

            wi = row * 2
            if wi < len(self.move_history):
                self._draw_move_cell(wi, True, lr.x + num_w, vy, col_w, ROW_H, mx, my)
            bi = row * 2 + 1
            if bi < len(self.move_history):
                self._draw_move_cell(bi, False, lr.x + num_w + col_w, vy, col_w, ROW_H, mx, my)
        self.screen.set_clip(None)

    def _draw_move_cell(self, idx, is_white, cx, cy, cw, ch, mx, my):
        is_cur = (idx == self.current_index)
        if is_cur:
            pygame.draw.rect(self.screen, PANEL_CUR, (cx, cy, cw, ch))
        elif cx <= mx < cx + cw and cy <= my < cy + ch:
            pygame.draw.rect(self.screen, PANEL_HOVER, (cx, cy, cw, ch))
        san = self._get_san(idx)
        glyph = _san_with_glyph(san, is_white)
        col = (255, 255, 255) if is_cur else PANEL_TXT
        t = self.move_font.render(glyph, True, col)
        self.screen.blit(t, (cx + 5, cy + (ch - t.get_height()) // 2))

    def _draw_nav_buttons(self):
        pygame.draw.rect(self.screen, PANEL_HDR_BG, self.nav_rect)
        mx, my = pygame.mouse.get_pos()
        for rect, lbl in zip(self.nav_rects, self._nav_labels()):
            hover = rect.collidepoint(mx, my)
            pygame.draw.rect(self.screen, BTN_HOVER if hover else BTN_NORMAL, rect, border_radius=4)
            pygame.draw.rect(self.screen, BTN_BORDER, rect, 1, border_radius=4)
            t = self.btn_font.render(lbl, True, BTN_TEXT)
            self.screen.blit(t, (rect.centerx - t.get_width() // 2, rect.centery - t.get_height() // 2))

    def square_to_coord(self, sq: int):
        f, r = chess.square_file(sq), chess.square_rank(sq)
        ss = self.square_size
        if self.flipped:
            return (7 - f) * ss + MARGIN, r * ss + MARGIN
        return f * ss + MARGIN, (7 - r) * ss + MARGIN

    def get_center(self, sq: int):
        x, y = self.square_to_coord(sq)
        h = self.square_size // 2
        return x + h, y + h

    def coord_to_square(self, x: int, y: int):
        ss = self.square_size
        x -= MARGIN
        y -= MARGIN
        if self.flipped:
            f, r = 7 - (x // ss), y // ss
        else:
            f, r = x // ss, 7 - (y // ss)
        if not (0 <= f <= 7 and 0 <= r <= 7):
            return None
        return chess.square(f, r)

    def _apply_move(self, board: chess.Board, move: chess.Move):
        try:
            board.push(move)
        except Exception:
            piece = board.piece_at(move.from_square)
            if piece:
                board.set_piece_at(move.from_square, None)
                dest = chess.Piece(move.promotion, piece.color) if move.promotion else piece
                board.set_piece_at(move.to_square, dest)
            board.turn = not board.turn

    def _board_status(self):
        try:
            return self.board.is_checkmate(), self.board.is_stalemate(), self.board.is_check()
        except Exception:
            return False, False, False

    def goto_move(self, idx: int):
        idx = max(-1, min(idx, len(self.move_history) - 1))
        b = chess.Board(self.base_fen)
        for i in range(idx + 1):
            self._apply_move(b, self.move_history[i])
        self.board = b
        self.current_index = idx
        self.selected = None
        self.legal_moves = []
        self.arrows = []
        self._scroll_to_current()

    def undo(self):
        self.playing = False
        self.goto_move(self.current_index - 1)

    def redo(self):
        self.playing = False
        self.goto_move(self.current_index + 1)

    def reset(self):
        self.board = chess.Board()
        self.base_fen = chess.STARTING_FEN
        self.move_history = []
        self.current_index = -1
        self.selected = None
        self.legal_moves = []
        self.arrows = []
        self.playing = False
        self.panel_scroll = 0
        self._san_cache = {}
        self.selected_piece = None
        self.game_over_timestamp = 0.0

    def toggle_play(self):
        self.playing = not self.playing
        self._last_play_t = time.time()
        if self.playing and self.current_index >= len(self.move_history) - 1:
            self.goto_move(-1)
            self._last_play_t = time.time()

    def tick_playback(self):
        if not self.playing:
            return
        if time.time() - self._last_play_t < self.play_speed:
            return
        self._last_play_t = time.time()
        if self.current_index >= len(self.move_history) - 1:
            self.playing = False
        else:
            self.goto_move(self.current_index + 1)

    def _nav_action(self, i: int):
        if i == 0:
            self.playing = False
            self.goto_move(-1)
        elif i == 1:
            self.playing = False
            self.goto_move(self.current_index - 1)
        elif i == 2:
            self.toggle_play()
        elif i == 3:
            self.playing = False
            self.goto_move(self.current_index + 1)
        elif i == 4:
            self.playing = False
            self.goto_move(len(self.move_history) - 1)

    def load_pgn(self):
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        path = filedialog.askopenfilename(title="Load PGN", filetypes=[("PGN files", "*.pgn")])
        root.destroy()
        if not path:
            return
        try:
            with open(path) as f:
                pgn_game = chess.pgn.read_game(f)
            if pgn_game:
                moves = list(pgn_game.mainline_moves())
                self.reset()
                self.move_history = moves
                self.goto_move(len(moves) - 1)
                print(f"✅ Loaded {len(moves)} moves.")
        except Exception as e:
            print(f"❌ Error: {e}")

    def handle_click(self, pos, button: int):
        mx, my = pos
        if button == 1 and self.reset_rect.collidepoint(mx, my):
            self.reset()
            return

        if button == 1 and self.show_panel:
            for i, rect in enumerate(self.nav_rects):
                if rect.collidepoint(mx, my):
                    self._nav_action(i)
                    return

            if self.panel_list_rect.collidepoint(mx, my):
                lr = self.panel_list_rect
                SCROLL_W = 7
                num_w = 30
                col_w = (lr.width - num_w - SCROLL_W) // 2
                row = self.panel_scroll + (my - lr.top) // ROW_H
                total_rows = (len(self.move_history) + 1) // 2
                if row < total_rows:
                    wi = row * 2
                    bi = row * 2 + 1
                    white_x = lr.x + num_w
                    black_x = white_x + col_w
                    if white_x <= mx < white_x + col_w and wi < len(self.move_history):
                        self.playing = False
                        self.goto_move(wi)
                    elif black_x <= mx < black_x + col_w and bi < len(self.move_history):
                        self.playing = False
                        self.goto_move(bi)
                return

        if self.editor_active and self.palette_rect and self.palette_rect.collidepoint(mx, my):
            for rect, sym in self.palette_buttons:
                if rect.collidepoint(mx, my):
                    self.selected_piece = sym if self.selected_piece != sym else None
                    return

        if my > MARGIN + self.board_size + 5:
            return
        sq = self.coord_to_square(mx, my)
        if sq is None:
            return

        if button == 1:
            self.arrows.clear()

            if self.editor_active and self.selected_piece:
                piece = chess.Piece.from_symbol(self.selected_piece)
                self.board.set_piece_at(sq, piece)
                self.move_history = self.move_history[:self.current_index + 1]
                self._san_cache = {}
                self.base_fen = self.board.fen()
                self.current_index = -1
                self.move_history = []
                return

            if not self.free_move and (self.board.is_checkmate() or self.board.is_stalemate()):
                return

            if self.selected is not None and sq != self.selected:
                move = chess.Move(self.selected, sq)
                piece = self.board.piece_at(self.selected)
                if piece and piece.piece_type == chess.PAWN and sq // 8 in (0, 7):
                    move = chess.Move(self.selected, sq, promotion=chess.QUEEN)

                if self.free_move or move in self.board.legal_moves:
                    if self.free_move and piece:
                        self.board.turn = piece.color
                    self._apply_move(self.board, move)
                    trunc = self.current_index + 1
                    self.move_history = self.move_history[:trunc]
                    self._invalidate_san_from(trunc)
                    self.move_history.append(move)
                    self.current_index += 1
                    self._scroll_to_current()
                self.selected = None
                self.legal_moves = []
            else:
                piece = self.board.piece_at(sq)
                if piece and (self.free_move or piece.color == self.board.turn):
                    self.selected = sq
                    try:
                        if self.free_move:
                            orig = self.board.turn
                            self.board.turn = piece.color
                            self.legal_moves = [m for m in self.board.legal_moves if m.from_square == sq]
                            self.board.turn = orig
                        else:
                            self.legal_moves = [m for m in self.board.legal_moves if m.from_square == sq]
                    except Exception:
                        self.legal_moves = []

        elif button == 3:
            if self.editor_active:
                self.board.set_piece_at(sq, None)
                self._san_cache = {}
                self.base_fen = self.board.fen()
                self.current_index = -1
                self.move_history = []
            else:
                self.arrow_start = sq

    def handle_right_release(self, pos):
        if self.arrow_start is None:
            return
        mx, my = pos
        if my < MARGIN + self.board_size + 5:
            end = self.coord_to_square(mx, my)
            if end and end != self.arrow_start:
                self.arrows.append((self.arrow_start, end))
        self.arrow_start = None

    def handle_scroll(self, delta: int):
        if not self.show_panel:
            return
        mx, my = pygame.mouse.get_pos()
        if self.panel_list_rect.collidepoint(mx, my):
            self.panel_scroll = max(0, self.panel_scroll - delta)
            self._clamp_scroll()

    def handle_resize(self, w: int, h: int):
        if self.fullscreen:
            return
        w, h = max(400, w), max(400, h)
        self.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
        self._layout(w, h)

    def _update_game_over(self):
        try:
            cm, sm, _ = self._board_status()
            if cm or sm:
                if self.game_over_timestamp == 0.0:
                    self.game_over_timestamp = time.time()
            else:
                self.game_over_timestamp = 0.0
        except:
            self.game_over_timestamp = 0.0


def main():
    game = ChessPracticeGUI()
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.VIDEORESIZE:
                game.handle_resize(event.w, event.h)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                game.handle_click(event.pos, event.button)
                if event.button == 4:
                    game.handle_scroll(1)
                if event.button == 5:
                    game.handle_scroll(-1)
            elif event.type == pygame.MOUSEWHEEL:
                game.handle_scroll(event.y)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 3:
                game.handle_right_release(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    game.toggle_fullscreen()
                elif event.key == pygame.K_f:
                    game.flipped = not game.flipped
                elif event.key == pygame.K_u:
                    game.undo()
                elif event.key == pygame.K_r:
                    game.redo()
                elif event.key == pygame.K_c:
                    game.arrows.clear()
                elif event.key == pygame.K_n:
                    game.reset()
                elif event.key == pygame.K_SPACE:
                    game.toggle_play()
                elif event.key == pygame.K_LEFT:
                    game.undo()
                elif event.key == pygame.K_RIGHT:
                    game.redo()
                elif event.key == pygame.K_m:
                    game.free_move = not game.free_move
                    game.selected_piece = None
                    print(f"Free Move: {'ON' if game.free_move else 'OFF'}")
                    aw, ah = game.screen.get_size()
                    game._layout(aw, ah, force=True)
                elif event.key == pygame.K_l:
                    game.load_pgn()
                elif event.key == pygame.K_p:
                    with open("practice_game.pgn", "w") as f:
                        g = chess.pgn.Game()
                        node = g
                        for mv in game.move_history:
                            node = node.add_main_variation(mv)
                        f.write(str(g))
                    print("✅ Saved practice_game.pgn")

        aw, ah = game.screen.get_size()
        if aw != game.win_w or ah != game.win_h:
            game._layout(aw, ah)

        game.tick_playback()
        game._update_game_over()

        game.screen.fill(BG)
        game.draw_board()
        game.draw_highlights()
        game.draw_pieces()
        game.draw_arrows()
        game.draw_coordinates()

        if game.editor_active:
            game.draw_piece_palette()

        # Temporary overlay
        if game.game_over_timestamp > 0:
            if time.time() - game.game_over_timestamp < game.GAME_OVER_DISPLAY_TIME:
                try:
                    cm, sm, _ = game._board_status()
                    if cm:
                        winner = "Black" if game.board.turn == chess.WHITE else "White"
                        game.draw_game_over_overlay(f"Checkmate — {winner} wins!")
                    elif sm:
                        game.draw_game_over_overlay("Stalemate — Draw!")
                except:
                    pass

        game.draw_ui()
        game.draw_panel()
        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()