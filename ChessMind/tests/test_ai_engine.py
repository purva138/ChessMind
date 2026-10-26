import chess
import pytest

from chessmind.ai.engine import (
    choose_move,
    evaluate_position,
)


def test_ai_returns_a_legal_move():
    board = chess.Board()

    # White plays first, so let White make a move.
    board.push_san("e4")

    move = choose_move(
        board,
        ai_color=chess.BLACK,
        depth=1,
    )

    assert move is not None
    assert move in board.legal_moves


def test_ai_does_not_move_on_the_wrong_turn():
    board = chess.Board()

    # White must move first in the starting position.
    with pytest.raises(ValueError):
        choose_move(
            board,
            ai_color=chess.BLACK,
            depth=1,
        )


def test_ai_returns_none_when_game_is_over():
    board = chess.Board()

    # Fool's Mate: Black checkmates White.
    for san in ["f3", "e5", "g4", "Qh4"]:
        board.push_san(san)

    assert board.is_checkmate()

    move = choose_move(
        board,
        ai_color=chess.WHITE,
        depth=1,
    )

    assert move is None


def test_ai_can_capture_a_free_queen():
    board = chess.Board(
        "4k3/8/8/8/8/8/4q3/4K3 w - - 0 1"
    )

    # White's king can capture the black queen.
    move = choose_move(
        board,
        ai_color=chess.WHITE,
        depth=1,
    )

    assert move is not None
    assert move in board.legal_moves


def test_evaluation_is_integer():
    board = chess.Board()

    score = evaluate_position(
        board,
        ai_color=chess.WHITE,
    )

    assert isinstance(score, int)


def test_search_does_not_change_original_position():
    board = chess.Board()

    # White makes the first move.
    board.push_san("e4")

    # Save the current position before the AI searches.
    expected_fen = board.fen()

    # Ask the AI to calculate Black's move.
    choose_move(
        board,
        ai_color=chess.BLACK,
        depth=1,
    )

    # The AI should not modify the actual board while searching.
    assert board.fen() == expected_fen