"""
ChessMind AI Engine

A chess AI that uses:
1. Material evaluation
2. Minimax search
3. Alpha-beta pruning
4. Move ordering

Uses python-chess for chess rules and legal move generation.
"""

from __future__ import annotations

from typing import Optional

import chess


# --------------------------------------------------
# Configuration
# --------------------------------------------------

# Approximate material values in centipawns.
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

# A score larger than any ordinary material advantage.
MATE_SCORE = 100_000


# --------------------------------------------------
# Position evaluation
# --------------------------------------------------

def evaluate_position(
    board: chess.Board,
    ai_color: chess.Color,
) -> int:
    """
    Evaluate a board position from the AI's perspective.

    Positive score:
        Good for the AI.

    Negative score:
        Good for the opponent.

    The initial version evaluates material balance and
    gives a small bonus for central piece placement.
    """

    outcome = board.outcome()

    # Checkmate and draw positions are handled separately.
    if outcome is not None:
        if outcome.winner is None:
            return 0

        if outcome.winner == ai_color:
            return MATE_SCORE

        return -MATE_SCORE

    white_score = 0

    # Material balance.
    for square, piece in board.piece_map().items():
        value = PIECE_VALUES[piece.piece_type]

        # Small positional bonus for occupying central squares.
        file_distance = abs(chess.square_file(square) - 3.5)
        rank_distance = abs(chess.square_rank(square) - 3.5)

        center_bonus = int(
            max(0, 4 - file_distance - rank_distance) * 4
        )

        piece_score = value + center_bonus

        if piece.color == chess.WHITE:
            white_score += piece_score
        else:
            white_score -= piece_score

    # Convert the score into the AI's perspective.
    if ai_color == chess.WHITE:
        return white_score

    return -white_score


# --------------------------------------------------
# Move ordering
# --------------------------------------------------

def order_moves(
    board: chess.Board,
    moves: list[chess.Move],
) -> list[chess.Move]:
    """
    Examine promising moves earlier.

    Captures and promotions receive higher priority.
    This helps alpha-beta pruning work more efficiently.
    """

    def move_priority(move: chess.Move) -> int:
        score = 0

        # Prefer capturing valuable pieces with less valuable pieces.
        if board.is_capture(move):
            victim = board.piece_at(move.to_square)

            # En passant captures land on an empty square.
            if board.is_en_passant(move):
                victim_value = PIECE_VALUES[chess.PAWN]
            elif victim is not None:
                victim_value = PIECE_VALUES[victim.piece_type]
            else:
                victim_value = 0

            attacker = board.piece_at(move.from_square)

            attacker_value = (
                PIECE_VALUES[attacker.piece_type]
                if attacker is not None
                else 0
            )

            score += 10_000 + victim_value - attacker_value

        # Promotions are valuable, particularly promotion to a queen.
        if move.promotion is not None:
            score += 8_000 + PIECE_VALUES[move.promotion]

        return score

    return sorted(
        moves,
        key=move_priority,
        reverse=True,
    )


# --------------------------------------------------
# Minimax with alpha-beta pruning
# --------------------------------------------------

def minimax(
    board: chess.Board,
    depth: int,
    alpha: float,
    beta: float,
    ai_color: chess.Color,
    ply: int = 0,
) -> int:
    """
    Search possible positions using minimax.

    The AI maximizes its evaluation.
    The opponent minimizes the AI's evaluation.

    Alpha-beta pruning skips branches that cannot
    improve the current decision.
    """

    # Handle checkmate and draw positions.
    outcome = board.outcome()

    if outcome is not None:
        if outcome.winner is None:
            return 0

        if outcome.winner == ai_color:
            return MATE_SCORE - ply

        return -MATE_SCORE + ply

    # Stop searching when the requested depth is reached.
    if depth == 0:
        return evaluate_position(board, ai_color)

    moves = order_moves(
        board,
        list(board.legal_moves),
    )

    maximizing = board.turn == ai_color

    if maximizing:
        best_score = -float("inf")

        for move in moves:
            board.push(move)

            try:
                score = minimax(
                    board,
                    depth - 1,
                    alpha,
                    beta,
                    ai_color,
                    ply + 1,
                )
            finally:
                board.pop()

            best_score = max(best_score, score)
            alpha = max(alpha, best_score)

            # The opponent has a better alternative already.
            if beta <= alpha:
                break

        return int(best_score)

    best_score = float("inf")

    for move in moves:
        board.push(move)

        try:
            score = minimax(
                board,
                depth - 1,
                alpha,
                beta,
                ai_color,
                ply + 1,
            )
        finally:
            board.pop()

        best_score = min(best_score, score)
        beta = min(beta, best_score)

        # The AI has a better alternative already.
        if beta <= alpha:
            break

    return int(best_score)


# --------------------------------------------------
# Public AI interface
# --------------------------------------------------

def choose_move(
    board: chess.Board,
    ai_color: chess.Color = chess.BLACK,
    depth: int = 3,
) -> Optional[chess.Move]:
    """
    Choose a legal move for the AI.

    Parameters:
        board:
            The current python-chess board.

        ai_color:
            The color controlled by the AI.

        depth:
            Number of half-moves searched ahead.

    Returns:
        The selected legal move, or None if the game
        has already ended or there are no legal moves.
    """

    if depth < 1:
        raise ValueError("Search depth must be at least 1.")

    if board.turn != ai_color:
        raise ValueError(
            "It is not the AI's turn to move."
        )

    if board.outcome() is not None:
        return None

    moves = order_moves(
        board,
        list(board.legal_moves),
    )

    if not moves:
        return None

    best_move = None
    best_score = -float("inf")

    alpha = -float("inf")
    beta = float("inf")

    for move in moves:
        board.push(move)

        try:
            score = minimax(
                board,
                depth - 1,
                alpha,
                beta,
                ai_color,
                ply=1,
            )
        finally:
            board.pop()

        if score > best_score:
            best_score = score
            best_move = move

        alpha = max(alpha, best_score)

    return best_move