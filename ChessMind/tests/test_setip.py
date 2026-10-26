"""Library sanity tests.

These confirm that python-chess behaves as the rest of the project will
assume. We rely on it for the rules, so we verify the rules we care about.
Tests for our own code start in later milestones.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import chess


def test_starting_position_has_20_legal_moves():
    assert chess.Board().legal_moves.count() == 20


def test_fools_mate_is_checkmate():
    board = chess.Board()
    for san in ["f3", "e5", "g4", "Qh4"]:
        board.push_san(san)
    assert board.is_checkmate()
    assert board.is_game_over()


def test_stalemate_is_detected():
    board = chess.Board("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    assert board.is_stalemate()
    assert not board.is_checkmate()
    assert board.is_game_over()


def test_pawn_promotion_requires_a_piece_choice():
    board = chess.Board("4k3/P7/8/8/8/8/8/4K3 w - - 0 1")
    assert chess.Move.from_uci("a7a8q") in board.legal_moves
    assert chess.Move.from_uci("a7a8n") in board.legal_moves
    assert chess.Move.from_uci("a7a8") not in board.legal_moves


def test_castling_is_legal_when_allowed():
    board = chess.Board("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
    kingside = chess.Move.from_uci("e1g1")
    queenside = chess.Move.from_uci("e1c1")
    assert kingside in board.legal_moves and board.is_castling(kingside)
    assert queenside in board.legal_moves and board.is_castling(queenside)


def test_en_passant_is_legal():
    board = chess.Board()
    for san in ["e4", "a6", "e5", "d5"]:
        board.push_san(san)
    capture = chess.Move.from_uci("e5d6")
    assert capture in board.legal_moves
    assert board.is_en_passant(capture)


def test_undo_restores_position():
    board = chess.Board()
    start = board.fen()
    board.push_san("e4")
    board.pop()
    assert board.fen() == start


def test_pygame_can_initialise_headless():
    import pygame

    pygame.init()
    pygame.display.set_mode((50, 50))
    pygame.quit()


def test_numpy_dot_product():
    import numpy as np

    weights = np.array([1.0, 2.0])
    features = np.array([3.0, 4.0])
    assert float(weights @ features) == 11.0