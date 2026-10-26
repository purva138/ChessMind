import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import chess
import pygame
import pytest

from chessmind.ui.board_view import BoardView
from chessmind.ui.widgets import PROMOTION_CHOICES, Button, PromotionDialog


@pytest.fixture(autouse=True)
def pygame_ready():
    pygame.init()  # an earlier test may have called pygame.quit()


def test_button_contains():
    button = Button("Undo", pygame.Rect(10, 10, 100, 30))
    assert button.contains((10, 10))
    assert button.contains((109, 39))
    assert not button.contains((110, 10))
    assert not button.contains((9, 10))


def test_promotion_dialog_choice_at():
    dialog = PromotionDialog(640, 80)
    for rect, piece_type in zip(dialog.rects, PROMOTION_CHOICES):
        assert dialog.choice_at(rect.center) == piece_type
    assert dialog.choice_at((5, 5)) is None


def test_promotion_dialog_is_centered_on_board():
    dialog = PromotionDialog(640, 80)
    assert dialog.panel_rect.center == (320, 320)
    assert pygame.Rect(0, 0, 640, 640).contains(dialog.panel_rect)


def test_widgets_draw_without_error():
    surface = pygame.Surface((920, 640))
    font = pygame.font.SysFont("arial", 16)
    Button("New Game", pygame.Rect(660, 100, 110, 36)).draw(surface, font, (0, 0))
    Button("Undo", pygame.Rect(780, 100, 110, 36)).draw(surface, font, (0, 0), enabled=False)
    PromotionDialog(640, 80).draw(surface, BoardView(80, (0, 0)), chess.WHITE, (0, 0))