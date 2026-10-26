import chess
import pytest

from chessmind.game.game_state import GameState

STALEMATE_FEN = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"
BARE_KINGS_FEN = "8/8/4k3/8/8/4K3/8/8 w - - 0 1"
PROMOTION_FEN = "4k3/P7/8/8/8/8/8/4K3 w - - 0 1"
BLACK_FIRST_FEN = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"


def play(game, *san_moves):
    for san in san_moves:
        game.make_move(game.board.parse_san(san))


def test_initial_state():
    game = GameState()
    assert game.turn == chess.WHITE
    assert len(game.legal_moves()) == 20
    assert not game.is_game_over
    assert game.result() is None
    assert game.last_move is None
    assert game.status_text() == "White to move"
    assert game.check_square() is None


def test_make_legal_move_updates_state():
    game = GameState()
    game.make_move(chess.Move.from_uci("e2e4"))
    assert game.turn == chess.BLACK
    assert game.last_move == chess.Move.from_uci("e2e4")
    assert game.status_text() == "Black to move"
    assert game.move_list_text() == ["1. e4"]
    assert game.ply_count == 1


def test_illegal_move_raises_and_leaves_board_unchanged():
    game = GameState()
    before = game.board.fen()
    with pytest.raises(ValueError):
        game.make_move(chess.Move.from_uci("e2e5"))
    assert game.board.fen() == before
    assert game.move_list_text() == []


def test_undo_restores_previous_position():
    game = GameState()
    start = game.board.fen()
    play(game, "e4")
    assert game.undo() is True
    assert game.board.fen() == start
    assert game.move_list_text() == []
    assert game.last_move is None


def test_undo_on_fresh_game_returns_false():
    assert GameState().undo() is False


def test_legal_moves_from_square():
    game = GameState()
    pawn_targets = {m.to_square for m in game.legal_moves_from(chess.E2)}
    knight_targets = {m.to_square for m in game.legal_moves_from(chess.G1)}
    assert pawn_targets == {chess.E3, chess.E4}
    assert knight_targets == {chess.F3, chess.H3}
    assert game.legal_moves_from(chess.E4) == []  # empty square


def test_checkmate_status():
    game = GameState()
    play(game, "f3", "e5", "g4", "Qh4")
    assert game.is_game_over
    assert game.result() == "0-1"
    assert game.status_text() == "Checkmate - Black wins"
    assert game.check_square() == chess.E1


def test_stalemate_status():
    game = GameState(STALEMATE_FEN)
    assert game.is_game_over
    assert game.result() == "1/2-1/2"
    assert game.status_text() == "Draw - Stalemate"
    assert game.check_square() is None


def test_insufficient_material_status():
    game = GameState(BARE_KINGS_FEN)
    assert game.is_game_over
    assert game.status_text() == "Draw - Insufficient material"


def test_check_status_and_check_square():
    game = GameState()
    play(game, "e4", "f6", "Qh5")
    assert game.status_text() == "Black to move - check!"
    assert game.check_square() == chess.E8
    assert not game.is_game_over


def test_move_list_text_from_start():
    game = GameState()
    play(game, "e4", "e5", "Nf3")
    assert game.move_list_text() == ["1. e4 e5", "2. Nf3"]


def test_move_list_text_when_black_moves_first():
    game = GameState(BLACK_FIRST_FEN)
    play(game, "e5")
    assert game.move_list_text() == ["1... e5"]
    play(game, "Nf3")
    assert game.move_list_text() == ["1... e5", "2. Nf3"]


def test_reset_returns_to_start():
    game = GameState()
    play(game, "e4", "e5")
    game.reset()
    assert game.board.fen() == chess.STARTING_FEN
    assert game.move_list_text() == []
    assert game.undo() is False


def test_promotion_move_is_recorded_in_san():
    game = GameState(PROMOTION_FEN)
    assert not game.is_legal(chess.Move.from_uci("a7a8"))  # piece choice is required
    game.make_move(chess.Move.from_uci("a7a8q"))
    assert game.move_list_text() == ["1. a8=Q+"]
    assert game.board.piece_at(chess.A8) == chess.Piece(chess.QUEEN, chess.WHITE)