"""Turns square clicks into chess moves. No pygame: purely game logic.

The UI calls click(square) for every square the user presses. This class
decides whether that click selects a piece, plays a move, switches the
selection, or starts a pawn promotion.
"""

from __future__ import annotations

from typing import Iterable, List, Optional, Set

import chess

from chessmind.game.game_state import GameState


class MoveInput:
    def __init__(
        self,
        game: GameState,
        controlled_colors: Iterable[chess.Color] = (chess.WHITE, chess.BLACK),
    ) -> None:
        self.game = game
        # Which colours a human may move. Both for now; Milestone 4 restricts this.
        self.controlled_colors = frozenset(controlled_colors)
        self.selected: Optional[chess.Square] = None
        self.targets: Set[chess.Square] = set()
        self.pending_promotion: List[chess.Move] = []

    @property
    def is_choosing_promotion(self) -> bool:
        return bool(self.pending_promotion)

    def clear(self) -> None:
        self.selected = None
        self.targets = set()
        self.pending_promotion = []

    def click(self, square: chess.Square) -> Optional[chess.Move]:
        """Handle a click on a square. Returns the move if one was played."""
        if (
            self.is_choosing_promotion
            or self.game.is_game_over
            or self.game.turn not in self.controlled_colors
        ):
            return None

        if self.selected is not None and square in self.targets:
            candidates = [
                move for move in self.game.legal_moves_from(self.selected)
                if move.to_square == square
            ]
            if len(candidates) > 1:  # queen/rook/bishop/knight variants
                self.pending_promotion = candidates
                return None
            move = candidates[0]
            self.game.make_move(move)
            self.clear()
            return move

        piece = self.game.board.piece_at(square)
        if piece is not None and piece.color == self.game.turn:
            self.selected = square
            self.targets = {m.to_square for m in self.game.legal_moves_from(square)}
        else:
            self.clear()
        return None

    def choose_promotion(self, piece_type: chess.PieceType) -> Optional[chess.Move]:
        """Finish a pending promotion. Returns None if nothing matches."""
        for move in self.pending_promotion:
            if move.promotion == piece_type:
                self.game.make_move(move)
                self.clear()
                return move
        return None

    def cancel_promotion(self) -> None:
        """Dismiss the promotion choice but keep the piece selected."""
        self.pending_promotion = []