"""Small reusable UI widgets: a button and the pawn-promotion picker."""

from __future__ import annotations

from typing import List, Optional, Tuple

import chess
import pygame

from chessmind.ui import theme
from chessmind.ui.board_view import BoardView

PROMOTION_CHOICES = (chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT)


class Button:
    def __init__(self, label: str, rect: pygame.Rect) -> None:
        self.label = label
        self.rect = rect

    def contains(self, pos: Tuple[int, int]) -> bool:
        return self.rect.collidepoint(pos)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font,
             mouse_pos: Tuple[int, int], enabled: bool = True) -> None:
        if not enabled:
            background, text_color = theme.BUTTON_DISABLED, theme.MUTED_TEXT
        elif self.contains(mouse_pos):
            background, text_color = theme.BUTTON_HOVER, theme.TEXT_COLOR
        else:
            background, text_color = theme.BUTTON_BG, theme.TEXT_COLOR
        pygame.draw.rect(surface, background, self.rect, border_radius=6)
        text = font.render(self.label, True, text_color)
        surface.blit(text, text.get_rect(center=self.rect.center))


class PromotionDialog:
    """Four piece choices shown in the middle of the board."""

    PADDING = 12

    def __init__(self, board_size: int, square_size: int) -> None:
        self.board_size = board_size
        left = board_size // 2 - 2 * square_size
        top = board_size // 2 - square_size // 2
        self.rects: List[pygame.Rect] = [
            pygame.Rect(left + i * square_size, top, square_size, square_size)
            for i in range(len(PROMOTION_CHOICES))
        ]
        self.panel_rect = pygame.Rect(
            left - self.PADDING,
            top - self.PADDING,
            len(PROMOTION_CHOICES) * square_size + 2 * self.PADDING,
            square_size + 2 * self.PADDING,
        )

    def choice_at(self, pos: Tuple[int, int]) -> Optional[chess.PieceType]:
        for rect, piece_type in zip(self.rects, PROMOTION_CHOICES):
            if rect.collidepoint(pos):
                return piece_type
        return None

    def draw(self, surface: pygame.Surface, board_view: BoardView,
             color: chess.Color, mouse_pos: Tuple[int, int]) -> None:
        dim = pygame.Surface((self.board_size, self.board_size), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 140))
        surface.blit(dim, (0, 0))
        pygame.draw.rect(surface, theme.DIALOG_BG, self.panel_rect, border_radius=10)
        for rect, piece_type in zip(self.rects, PROMOTION_CHOICES):
            hovered = rect.collidepoint(mouse_pos)
            pygame.draw.rect(surface, theme.DARK_SQUARE if hovered else theme.LIGHT_SQUARE,
                             rect, border_radius=6)
            image = board_view.piece_image(chess.Piece(piece_type, color))
            surface.blit(image, image.get_rect(center=rect.center))