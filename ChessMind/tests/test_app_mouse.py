import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import chess
import pytest

from chessmind.game.game_state import GameState
from chessmind.ui.app import App

PROMOTION_FEN = "4k3/P7/8/8/8/8/8/4K3 w - - 0 1"


@pytest.fixture
def app():
    return App()


def center(app, square):
    return app.board_view.square_to_rect(square).center


def click(app, pos):
    app.on_mouse_down(pos)
    app.on_mouse_up(pos)


def click_square(app, square):
    click(app, center(app, square))


def drag(app, start, end):
    app.on_mouse_down(center(app, start))
    app.on_mouse_up(center(app, end))


def test_click_then_click_moves_piece(app):
    click_square(app, chess.E2)
    assert app.input.selected == chess.E2
    assert app.drag_square is None
    click_square(app, chess.E4)
    assert app.game.board.piece_at(chess.E4) == chess.Piece(chess.PAWN, chess.WHITE)
    assert app.game.ply_count == 1


def test_drag_and_drop_moves_piece(app):
    app.on_mouse_down(center(app, chess.E2))
    assert app.drag_square == chess.E2
    app.on_mouse_up(center(app, chess.E4))
    assert app.game.board.piece_at(chess.E4) == chess.Piece(chess.PAWN, chess.WHITE)
    assert app.drag_square is None


def test_drop_on_illegal_square_snaps_back(app):
    drag(app, chess.E2, chess.E5)
    assert app.game.ply_count == 0
    assert app.game.board.piece_at(chess.E2) == chess.Piece(chess.PAWN, chess.WHITE)
    assert app.input.selected == chess.E2


def test_drop_outside_board_does_nothing(app):
    app.on_mouse_down(center(app, chess.E2))
    app.on_mouse_up((900, 300))
    assert app.game.ply_count == 0
    assert app.drag_square is None


def test_clicking_enemy_piece_does_nothing(app):
    click_square(app, chess.E7)
    assert app.input.selected is None
    assert app.drag_square is None


def test_new_game_button_resets(app):
    click_square(app, chess.E2)
    click_square(app, chess.E4)
    click(app, app.new_game_button.rect.center)
    assert app.game.ply_count == 0
    assert app.game.board.fen() == chess.STARTING_FEN
    assert app.input.selected is None


def test_undo_button_takes_back_move(app):
    click_square(app, chess.E2)
    click_square(app, chess.E4)
    click(app, app.undo_button.rect.center)
    assert app.game.ply_count == 0
    assert app.game.board.fen() == chess.STARTING_FEN


def test_undo_on_fresh_game_is_harmless(app):
    click(app, app.undo_button.rect.center)
    assert app.game.ply_count == 0


def test_promotion_dialog_flow(app):
    app.use_game(GameState(PROMOTION_FEN))
    click_square(app, chess.A7)
    click_square(app, chess.A8)
    assert app.input.is_choosing_promotion
    app.draw()  # the dialog must render without errors
    click(app, app.dialog.rects[3].center)  # index 3 = knight
    assert app.game.board.piece_at(chess.A8) == chess.Piece(chess.KNIGHT, chess.WHITE)
    assert not app.input.is_choosing_promotion


def test_clicking_outside_dialog_cancels_promotion(app):
    app.use_game(GameState(PROMOTION_FEN))
    click_square(app, chess.A7)
    click_square(app, chess.A8)
    click(app, (5, 5))
    assert not app.input.is_choosing_promotion
    assert app.game.board.piece_at(chess.A7) == chess.Piece(chess.PAWN, chess.WHITE)
    assert app.game.ply_count == 0


def test_clicks_in_panel_are_ignored(app):
    click(app, (700, 400))
    assert app.game.ply_count == 0
    assert app.input.selected is None


def test_draw_while_dragging(app):
    app.on_mouse_down(center(app, chess.E2))
    app.draw()