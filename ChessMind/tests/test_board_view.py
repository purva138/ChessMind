import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import chess
import pygame
import pytest

from chessmind.game.game_state import GameState
from chessmind.ui import board_view as board_view_module
from chessmind.ui import theme
from chessmind.ui.board_view import BoardView

pygame.font.init()

SIZE = 80


@pytest.fixture
def view():
    return BoardView(SIZE, (0, 0))


@pytest.fixture
def surface():
    return pygame.Surface((SIZE * 8, SIZE * 8))


def probe(view, surface, square):
    """Colour near a square's bottom-left corner (labels and pieces never reach it)."""
    rect = view.square_to_rect(square)
    return tuple(surface.get_at((rect.x + 3, rect.bottom - 3)))[:3]


def play(game, *san_moves):
    for san in san_moves:
        game.make_move(game.board.parse_san(san))


def test_pixel_to_square_corners(view):
    edge = SIZE * 8 - 5
    assert view.pixel_to_square((5, 5)) == chess.A8
    assert view.pixel_to_square((edge, 5)) == chess.H8
    assert view.pixel_to_square((5, edge)) == chess.A1
    assert view.pixel_to_square((edge, edge)) == chess.H1


def test_pixel_to_square_outside_board_is_none(view):
    assert view.pixel_to_square((-1, 10)) is None
    assert view.pixel_to_square((10, SIZE * 8)) is None
    assert view.pixel_to_square((SIZE * 8, 10)) is None


def test_square_rect_round_trip(view):
    for square in chess.SQUARES:
        assert view.pixel_to_square(view.square_to_rect(square).center) == square


def test_origin_offset():
    offset_view = BoardView(SIZE, (100, 50))
    assert offset_view.square_to_rect(chess.A8).topleft == (100, 50)
    assert offset_view.pixel_to_square((99, 60)) is None
    assert offset_view.pixel_to_square((105, 55)) == chess.A8


def test_draw_plain_square_colours(view, surface):
    view.draw(surface, GameState())
    assert probe(view, surface, chess.D4) == theme.DARK_SQUARE
    assert probe(view, surface, chess.E4) == theme.LIGHT_SQUARE


def test_last_move_is_highlighted(view, surface):
    game = GameState()
    play(game, "e4")
    view.draw(surface, game)
    assert probe(view, surface, chess.E2) != theme.LIGHT_SQUARE
    assert probe(view, surface, chess.E4) != theme.LIGHT_SQUARE
    assert probe(view, surface, chess.D4) == theme.DARK_SQUARE  # untouched square


def test_check_square_is_highlighted(view, surface):
    game = GameState()
    play(game, "e4", "f6", "Qh5")
    view.draw(surface, game)
    assert probe(view, surface, chess.E8) != theme.LIGHT_SQUARE
    assert probe(view, surface, chess.D8) == theme.DARK_SQUARE


def test_draw_works_with_letter_fallback(monkeypatch, surface):
    monkeypatch.setattr(board_view_module, "_load_piece_font", lambda size: None)
    fallback_view = BoardView(SIZE, (0, 0))
    fallback_view.draw(surface, GameState())
    assert probe(fallback_view, surface, chess.D4) == theme.DARK_SQUARE



def pixel(surface, pos):
    return tuple(surface.get_at(pos))[:3]


def test_hints_and_selection_are_drawn(view, surface):
    game = GameState()
    plain = pygame.Surface(surface.get_size())
    view.draw(plain, game)
    view.draw(surface, game, selected=chess.E2, targets={chess.E3, chess.E4})
    e3_center = view.square_to_rect(chess.E3).center
    assert pixel(surface, e3_center) != pixel(plain, e3_center)      # dot on empty target
    e2 = view.square_to_rect(chess.E2)
    corner = (e2.x + 3, e2.bottom - 3)
    assert pixel(surface, corner) != pixel(plain, corner)            # selected square tinted


def test_capture_target_gets_a_ring(view, surface):
    game = GameState()
    play(game, "e4", "d5")
    plain = pygame.Surface(surface.get_size())
    view.draw(plain, game)
    view.draw(surface, game, selected=chess.E4, targets={chess.D5})
    d5 = view.square_to_rect(chess.D5)
    ring_point = (d5.centerx, d5.y + 5)
    assert pixel(surface, ring_point) != pixel(plain, ring_point)


def test_dragged_piece_leaves_origin_and_follows_pointer(view, surface):
    game = GameState()
    e2 = view.square_to_rect(chess.E2)
    e4 = view.square_to_rect(chess.E4)
    view.draw(surface, game, drag_square=chess.E2, drag_pos=e4.center)

    def colors_in(rect):
        return {pixel(surface, (x, y))
                for x in range(rect.x, rect.right, 2)
                for y in range(rect.y, rect.bottom, 2)}

    assert colors_in(e2) == {theme.LIGHT_SQUARE}   # the pawn is no longer drawn on e2
    assert len(colors_in(e4)) > 1                  # it appears under the pointer on e4