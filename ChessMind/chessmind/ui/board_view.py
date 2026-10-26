"""Draws the chessboard and pieces from a GameState."""

from __future__ import annotations

from typing import Dict, Iterable, Optional, Tuple

import chess
import pygame

from chessmind.game.game_state import GameState
from chessmind.ui import theme

PIECE_GLYPHS = {
    chess.PAWN: "\u265f",
    chess.KNIGHT: "\u265e",
    chess.BISHOP: "\u265d",
    chess.ROOK: "\u265c",
    chess.QUEEN: "\u265b",
    chess.KING: "\u265a",
}
PIECE_LETTERS = {
    chess.PAWN: "P", chess.KNIGHT: "N", chess.BISHOP: "B",
    chess.ROOK: "R", chess.QUEEN: "Q", chess.KING: "K",
}
_FONT_CANDIDATES = ("segoeuisymbol", "dejavusans", "arialunicodems", "freeserif", "symbola")


def _load_piece_font(size: int) -> Optional[pygame.font.Font]:
    """Return a font that really contains the chess glyphs, or None."""
    probe = PIECE_GLYPHS[chess.KING] + PIECE_GLYPHS[chess.PAWN]
    for name in _FONT_CANDIDATES:
        path = pygame.font.match_font(name)
        if path is None:
            continue
        try:
            font = pygame.font.Font(path, size)
            if all(metric is not None for metric in font.metrics(probe)):
                return font
        except (pygame.error, OSError):
            continue
    return None


class BoardView:
    def __init__(self, square_size: int = theme.SQUARE_SIZE,
                 origin: Tuple[int, int] = (0, 0)) -> None:
        pygame.font.init()
        self.square_size = square_size
        self.origin = origin
        self._piece_font = _load_piece_font(int(square_size * 0.8))
        self._fallback_font = pygame.font.SysFont("arial", int(square_size * 0.6), bold=True)
        self._label_font = pygame.font.SysFont("arial", max(10, square_size // 6), bold=True)
        self._overlay = pygame.Surface((square_size, square_size), pygame.SRCALPHA)
        self._dot = self._make_hint(filled=True)     # legal move to an empty square
        self._ring = self._make_hint(filled=False)   # legal capture
        self._piece_cache: Dict[Tuple[int, bool], pygame.Surface] = {}

    def _make_hint(self, filled: bool) -> pygame.Surface:
        size = self.square_size
        hint = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        if filled:
            pygame.draw.circle(hint, theme.HINT_COLOR, center, size // 6)
        else:
            pygame.draw.circle(hint, theme.HINT_COLOR, center, size // 2 - 2, max(3, size // 12))
        return hint

    # ---- coordinate conversion ----------------------------------------

    def square_to_rect(self, square: chess.Square) -> pygame.Rect:
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        x = self.origin[0] + file * self.square_size
        y = self.origin[1] + (7 - rank) * self.square_size  # screen y grows downward
        return pygame.Rect(x, y, self.square_size, self.square_size)

    def pixel_to_square(self, pos: Tuple[int, int]) -> Optional[chess.Square]:
        col = (pos[0] - self.origin[0]) // self.square_size
        row = (pos[1] - self.origin[1]) // self.square_size
        if 0 <= col < 8 and 0 <= row < 8:
            return chess.square(col, 7 - row)
        return None

    # ---- drawing -------------------------------------------------------

    def draw(
        self,
        surface: pygame.Surface,
        game: GameState,
        selected: Optional[chess.Square] = None,
        targets: Iterable[chess.Square] = (),
        drag_square: Optional[chess.Square] = None,
        drag_pos: Optional[Tuple[int, int]] = None,
    ) -> None:
        """Draw the whole board.

        selected / targets: the selected piece's square and its legal destinations.
        drag_square / drag_pos: a piece being dragged, and where the mouse is.
        """
        self._draw_squares(surface)
        self._draw_highlights(surface, game, selected)
        self._draw_coordinates(surface)
        self._draw_pieces(surface, game.board, skip=drag_square)
        self._draw_move_hints(surface, game.board, selected, targets)
        if drag_square is not None and drag_pos is not None:
            piece = game.board.piece_at(drag_square)
            if piece is not None:
                image = self.piece_image(piece)
                surface.blit(image, image.get_rect(center=drag_pos))

    def _draw_squares(self, surface: pygame.Surface) -> None:
        for square in chess.SQUARES:
            surface.fill(self._square_color(square), self.square_to_rect(square))

    @staticmethod
    def _square_color(square: chess.Square) -> Tuple[int, int, int]:
        is_dark = (chess.square_file(square) + chess.square_rank(square)) % 2 == 0
        return theme.DARK_SQUARE if is_dark else theme.LIGHT_SQUARE

    def _tint(self, surface: pygame.Surface, square: chess.Square,
              color: Tuple[int, int, int, int]) -> None:
        self._overlay.fill(color)
        surface.blit(self._overlay, self.square_to_rect(square).topleft)

    def _draw_highlights(self, surface: pygame.Surface, game: GameState,
                         selected: Optional[chess.Square]) -> None:
        last = game.last_move
        if last is not None:
            self._tint(surface, last.from_square, theme.LAST_MOVE_COLOR)
            self._tint(surface, last.to_square, theme.LAST_MOVE_COLOR)
        check_square = game.check_square()
        if check_square is not None:
            self._tint(surface, check_square, theme.CHECK_COLOR)
        if selected is not None:
            self._tint(surface, selected, theme.SELECTED_COLOR)

    def _draw_move_hints(self, surface: pygame.Surface, board: chess.Board,
                         selected: Optional[chess.Square],
                         targets: Iterable[chess.Square]) -> None:
        if selected is None:
            return
        for target in targets:
            hint = self._ring if self._is_capture_target(board, selected, target) else self._dot
            surface.blit(hint, self.square_to_rect(target).topleft)

    @staticmethod
    def _is_capture_target(board: chess.Board, selected: chess.Square,
                           target: chess.Square) -> bool:
        if board.piece_at(target) is not None:
            return True
        piece = board.piece_at(selected)
        # A pawn moving to the en-passant square is capturing, though the square is empty.
        return piece is not None and piece.piece_type == chess.PAWN and target == board.ep_square

    def _draw_coordinates(self, surface: pygame.Surface) -> None:
        for i in range(8):
            # File letters along the bottom row (rank 1), bottom-right corner.
            bottom = chess.square(i, 0)
            rect = self.square_to_rect(bottom)
            text = self._label_font.render(chr(ord("a") + i), True, self._label_color(bottom))
            surface.blit(text, (rect.right - text.get_width() - 3, rect.bottom - text.get_height() - 2))
            # Rank numbers down the left column (file a), top-left corner.
            left = chess.square(0, i)
            rect = self.square_to_rect(left)
            text = self._label_font.render(str(i + 1), True, self._label_color(left))
            surface.blit(text, (rect.x + 3, rect.y + 2))

    def _label_color(self, square: chess.Square) -> Tuple[int, int, int]:
        # Use the opposite square colour so the label is readable.
        return theme.LIGHT_SQUARE if self._square_color(square) == theme.DARK_SQUARE else theme.DARK_SQUARE

    def _draw_pieces(self, surface: pygame.Surface, board: chess.Board,
                     skip: Optional[chess.Square] = None) -> None:
        for square, piece in board.piece_map().items():
            if square == skip:
                continue
            image = self.piece_image(piece)
            surface.blit(image, image.get_rect(center=self.square_to_rect(square).center))

    def piece_image(self, piece: chess.Piece) -> pygame.Surface:
        """Cached image of a piece (also used by the promotion dialog)."""
        key = (piece.piece_type, piece.color)
        image = self._piece_cache.get(key)
        if image is None:
            image = self._render_piece(piece)
            self._piece_cache[key] = image
        return image

    def _render_piece(self, piece: chess.Piece) -> pygame.Surface:
        is_white = piece.color == chess.WHITE
        fill = theme.WHITE_PIECE_FILL if is_white else theme.BLACK_PIECE_FILL
        outline = theme.WHITE_PIECE_OUTLINE if is_white else theme.BLACK_PIECE_OUTLINE
        if self._piece_font is not None:
            font, text = self._piece_font, PIECE_GLYPHS[piece.piece_type]
        else:
            font, text = self._fallback_font, PIECE_LETTERS[piece.piece_type]

        fill_image = font.render(text, True, fill)
        outline_image = font.render(text, True, outline)
        pad = 2
        width, height = fill_image.get_size()
        result = pygame.Surface((width + 2 * pad, height + 2 * pad), pygame.SRCALPHA)
        for dx in (-pad, 0, pad):          # draw the outline colour shifted in 8
            for dy in (-pad, 0, pad):      # directions, then the fill on top
                if (dx, dy) != (0, 0):
                    result.blit(outline_image, (pad + dx, pad + dy))
        result.blit(fill_image, (pad, pad))
        return result