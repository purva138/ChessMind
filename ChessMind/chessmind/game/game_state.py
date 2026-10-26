"""Game state: a thin wrapper around python-chess's Board.

python-chess does all rule enforcement. This class adds what the UI and
(later) the AI need: a move log in standard notation, status text, undo,
and the square of a king in check.
"""

from __future__ import annotations

from typing import List, Optional

import chess

_DRAW_REASONS = {
    chess.Termination.STALEMATE: "Stalemate",
    chess.Termination.INSUFFICIENT_MATERIAL: "Insufficient material",
    chess.Termination.SEVENTYFIVE_MOVES: "75-move rule",
    chess.Termination.FIVEFOLD_REPETITION: "Fivefold repetition",
}


class GameState:
    def __init__(self, fen: Optional[str] = None) -> None:
        self._start_fen = fen if fen is not None else chess.STARTING_FEN
        self.board = chess.Board(self._start_fen)
        self._start_turn = self.board.turn
        self._start_fullmove = self.board.fullmove_number
        self._san_log: List[str] = []

    # ---- queries -------------------------------------------------------

    @property
    def turn(self) -> chess.Color:
        return self.board.turn

    @property
    def last_move(self) -> Optional[chess.Move]:
        return self.board.move_stack[-1] if self.board.move_stack else None

    @property
    def ply_count(self) -> int:
        """Number of half-moves played since the game started."""
        return len(self._san_log)

    @property
    def is_game_over(self) -> bool:
        return self.board.outcome() is not None

    def result(self) -> Optional[str]:
        """'1-0', '0-1', '1/2-1/2', or None while the game is running."""
        outcome = self.board.outcome()
        return outcome.result() if outcome is not None else None

    def legal_moves(self) -> List[chess.Move]:
        return list(self.board.legal_moves)

    def legal_moves_from(self, square: chess.Square) -> List[chess.Move]:
        return [m for m in self.board.legal_moves if m.from_square == square]

    def is_legal(self, move: chess.Move) -> bool:
        return move in self.board.legal_moves

    def check_square(self) -> Optional[chess.Square]:
        """Square of the king that is in check, or None."""
        if self.board.is_check():
            return self.board.king(self.board.turn)
        return None

    def status_text(self) -> str:
        outcome = self.board.outcome()
        if outcome is None:
            side = "White" if self.board.turn == chess.WHITE else "Black"
            return f"{side} to move" + (" - check!" if self.board.is_check() else "")
        if outcome.termination == chess.Termination.CHECKMATE:
            winner = "White" if outcome.winner == chess.WHITE else "Black"
            return f"Checkmate - {winner} wins"
        fallback = outcome.termination.name.replace("_", " ").title()
        return f"Draw - {_DRAW_REASONS.get(outcome.termination, fallback)}"

    def move_list_text(self) -> List[str]:
        """Move history as lines like '1. e4 e5' (handles a black-first start)."""
        lines: List[str] = []
        number = self._start_fullmove
        index = 0
        if self._start_turn == chess.BLACK and self._san_log:
            lines.append(f"{number}... {self._san_log[0]}")
            index = 1
            number += 1
        while index < len(self._san_log):
            lines.append(f"{number}. {' '.join(self._san_log[index:index + 2])}")
            index += 2
            number += 1
        return lines

    # ---- actions -------------------------------------------------------

    def make_move(self, move: chess.Move) -> None:
        """Play a move. Raises ValueError (board untouched) if it is illegal."""
        if move not in self.board.legal_moves:
            raise ValueError(f"Illegal move: {move.uci()}")
        self._san_log.append(self.board.san(move))  # SAN must be computed BEFORE pushing
        self.board.push(move)

    def undo(self) -> bool:
        """Take back one half-move. Returns False if there is nothing to undo."""
        if not self.board.move_stack:
            return False
        self.board.pop()
        self._san_log.pop()
        return True

    def reset(self) -> None:
        """Return to the starting position this GameState was created with."""
        self.board.set_fen(self._start_fen)  # also clears the move stack
        self._san_log.clear()