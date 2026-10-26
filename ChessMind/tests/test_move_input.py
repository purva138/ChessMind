import chess

from chessmind.game.game_state import GameState
from chessmind.game.move_input import MoveInput

PROMOTION_FEN = "4k3/P7/8/8/8/8/8/4K3 w - - 0 1"
CASTLING_FEN = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
STALEMATE_FEN = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"


def make(fen=None, **kwargs):
    game = GameState(fen)
    return game, MoveInput(game, **kwargs)


def play(game, *san_moves):
    for san in san_moves:
        game.make_move(game.board.parse_san(san))


def test_selecting_own_piece_shows_targets():
    game, inp = make()
    assert inp.click(chess.E2) is None
    assert inp.selected == chess.E2
    assert inp.targets == {chess.E3, chess.E4}


def test_cannot_select_enemy_piece():
    game, inp = make()
    inp.click(chess.E7)
    assert inp.selected is None
    assert inp.targets == set()


def test_clicking_empty_square_clears_selection():
    game, inp = make()
    inp.click(chess.E2)
    inp.click(chess.D5)
    assert inp.selected is None
    assert inp.targets == set()


def test_piece_with_no_moves_is_selected_but_has_no_targets():
    game, inp = make()
    inp.click(chess.A1)
    assert inp.selected == chess.A1
    assert inp.targets == set()


def test_clicking_target_plays_the_move():
    game, inp = make()
    inp.click(chess.E2)
    move = inp.click(chess.E4)
    assert move == chess.Move.from_uci("e2e4")
    assert game.board.piece_at(chess.E4) == chess.Piece(chess.PAWN, chess.WHITE)
    assert game.turn == chess.BLACK
    assert inp.selected is None
    assert inp.targets == set()


def test_clicking_unreachable_enemy_piece_clears_selection():
    game, inp = make()
    inp.click(chess.E2)
    assert inp.click(chess.E7) is None
    assert inp.selected is None
    assert game.ply_count == 0


def test_clicking_another_own_piece_switches_selection():
    game, inp = make()
    inp.click(chess.E2)
    inp.click(chess.G1)
    assert inp.selected == chess.G1
    assert inp.targets == {chess.F3, chess.H3}


def test_capture_by_click():
    game, inp = make()
    play(game, "e4", "d5")
    inp.click(chess.E4)
    assert chess.D5 in inp.targets
    move = inp.click(chess.D5)
    assert move == chess.Move.from_uci("e4d5")
    assert game.board.piece_at(chess.D5) == chess.Piece(chess.PAWN, chess.WHITE)


def test_en_passant_by_click():
    game, inp = make()
    play(game, "e4", "a6", "e5", "d5")
    inp.click(chess.E5)
    assert chess.D6 in inp.targets
    inp.click(chess.D6)
    assert game.board.piece_at(chess.D6) == chess.Piece(chess.PAWN, chess.WHITE)
    assert game.board.piece_at(chess.D5) is None  # the captured pawn is gone


def test_castling_by_click():
    game, inp = make(CASTLING_FEN)
    inp.click(chess.E1)
    assert {chess.G1, chess.C1} <= inp.targets
    inp.click(chess.G1)
    assert game.board.piece_at(chess.G1) == chess.Piece(chess.KING, chess.WHITE)
    assert game.board.piece_at(chess.F1) == chess.Piece(chess.ROOK, chess.WHITE)


def test_promotion_requires_choice():
    game, inp = make(PROMOTION_FEN)
    inp.click(chess.A7)
    assert inp.click(chess.A8) is None           # no move yet: a piece must be chosen
    assert inp.is_choosing_promotion
    assert len(inp.pending_promotion) == 4
    assert game.board.piece_at(chess.A7) == chess.Piece(chess.PAWN, chess.WHITE)
    assert inp.choose_promotion(chess.KING) is None  # not a valid promotion piece
    assert inp.is_choosing_promotion
    move = inp.choose_promotion(chess.KNIGHT)
    assert move is not None and move.promotion == chess.KNIGHT
    assert game.board.piece_at(chess.A8) == chess.Piece(chess.KNIGHT, chess.WHITE)
    assert not inp.is_choosing_promotion
    assert inp.selected is None


def test_cancel_promotion_leaves_board_unchanged():
    game, inp = make(PROMOTION_FEN)
    inp.click(chess.A7)
    inp.click(chess.A8)
    inp.cancel_promotion()
    assert not inp.is_choosing_promotion
    assert inp.selected == chess.A7
    assert game.board.piece_at(chess.A7) == chess.Piece(chess.PAWN, chess.WHITE)
    assert game.ply_count == 0


def test_clicks_ignored_while_choosing_promotion():
    game, inp = make(PROMOTION_FEN)
    inp.click(chess.A7)
    inp.click(chess.A8)
    assert inp.click(chess.E1) is None
    assert inp.is_choosing_promotion
    assert inp.selected == chess.A7


def test_no_input_after_game_over():
    game, inp = make(STALEMATE_FEN)
    assert game.is_game_over
    inp.click(chess.H8)
    assert inp.selected is None


def test_controlled_colors_blocks_other_side():
    game, inp = make(controlled_colors=(chess.BLACK,))
    inp.click(chess.E2)                      # it is White's turn, human controls Black
    assert inp.selected is None
    play(game, "e4")
    inp.click(chess.E7)
    assert inp.selected == chess.E7


def test_clear_resets_everything():
    game, inp = make(PROMOTION_FEN)
    inp.click(chess.A7)
    inp.click(chess.A8)
    inp.clear()
    assert inp.selected is None
    assert inp.targets == set()
    assert not inp.is_choosing_promotion