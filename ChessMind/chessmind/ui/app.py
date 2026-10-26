"""Main application window (Milestone 3: mouse play, human vs human)."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from typing import Optional, Tuple

import chess
import pygame

from chessmind.ai.engine import choose_move
from chessmind.game.game_state import GameState
from chessmind.game.move_input import MoveInput
from chessmind.ui import theme
from chessmind.ui.board_view import BoardView
from chessmind.ui.widgets import Button, PromotionDialog

MOVES_SHOWN = 14
GAME_OVER_COLOR = (240, 190, 80)


class App:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("ChessMind AI")
        self.screen = pygame.display.set_mode((theme.WINDOW_WIDTH, theme.WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()

        # Run AI calculations outside the Pygame event loop.
        self.ai_executor = ThreadPoolExecutor(max_workers=1)
        self.ai_future: Optional[Future] = None
        self.ai_position_fen: Optional[str] = None
        self.ai_error: Optional[str] = None

        self.board_view = BoardView(theme.SQUARE_SIZE, (0, 0))
        self.dialog = PromotionDialog(theme.BOARD_SIZE, theme.SQUARE_SIZE)
        self.title_font = pygame.font.SysFont("arial", 28, bold=True)
        self.text_font = pygame.font.SysFont("arial", 20)
        self.small_font = pygame.font.SysFont("arial", 16)

        panel_x = theme.BOARD_SIZE + 20
        self.new_game_button = Button("New Game", pygame.Rect(panel_x, 100, 110, 36))
        self.undo_button = Button("Undo", pygame.Rect(panel_x + 120, 100, 110, 36))

        self.drag_square: Optional[chess.Square] = None
        self.use_game(GameState())

    def use_game(self, game: GameState) -> None:
        """Attach a game and restrict human input to White."""
        self.game = game

        self.input = MoveInput(
            game,
            controlled_colors=(chess.WHITE,),
        )

        self.drag_square = None

    def update_ai(self) -> None:
        """Schedule and apply AI moves without blocking Pygame."""

        # Do not calculate a move after the game has ended.
        if self.game.is_game_over:
            return

        # The AI controls Black only.
        if self.game.turn != chess.BLACK:
            return

        # Do not start another calculation if an error occurred.
        if self.ai_error is not None:
            return

        # Start a calculation if one is not already running.
        if self.ai_future is None:
            # Give the worker its own board copy. The AI's search must
            # not modify the board currently used by the GUI.
            board_snapshot = self.game.board.copy(stack=True)

            self.ai_position_fen = board_snapshot.fen()

            self.ai_future = self.ai_executor.submit(
                choose_move,
                board_snapshot,
                chess.BLACK,
                2,
            )

        # Wait for the background calculation without blocking the UI.
        if not self.ai_future.done():
            return

        future = self.ai_future
        expected_fen = self.ai_position_fen

        # Clear the pending task before handling its result.
        self.ai_future = None
        self.ai_position_fen = None

        try:
            move = future.result()
        except Exception as exc:
            self.ai_error = str(exc)
            print(f"ChessMind AI error: {exc}")
            return

        # A reset or undo may have changed the game while the AI was
        # calculating. Never apply a move for an outdated position.
        if self.game.board.fen() != expected_fen:
            return

        # Recheck the game state and turn before applying the move.
        if self.game.is_game_over:
            return

        if self.game.turn != chess.BLACK:
            return

        if move is None:
            return

        # Validate the AI's move against the actual game board.
        if move not in self.game.board.legal_moves:
            self.ai_error = f"AI returned an illegal move: {move.uci()}"
            print(f"ChessMind AI error: {self.ai_error}")
            return

        self.game.make_move(move)

    # ---- main loop -----------------------------------------------------

    def run(self) -> None:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    else:
                        self.handle_key(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.on_mouse_down(event.pos)
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.on_mouse_up(event.pos)
            # Update the AI without blocking the Pygame event loop.
            self.update_ai()

            self.draw()
            pygame.display.flip()
            self.clock.tick(theme.FPS)
        pygame.quit()

    # ---- input handling ------------------------------------------------

    def handle_key(self, key: int) -> None:
        if key == pygame.K_n:
            self.new_game()
        elif key == pygame.K_u:
            self.undo()

    def new_game(self) -> None:
        """Reset the game and invalidate any pending AI result."""

        if self.ai_future is not None:
            self.ai_future.cancel()

        self.ai_future = None
        self.ai_position_fen = None
        self.ai_error = None

        self.game.reset()
        self.input.clear()
        self.drag_square = None

    def undo(self) -> None:
        """Undo the most recent human move and AI reply."""

        # Invalidate any AI calculation already in progress.
        if self.ai_future is not None:
            self.ai_future.cancel()

        self.ai_future = None
        self.ai_position_fen = None
        self.ai_error = None

        # Undo the most recent move.
        if self.game.undo():
            # If that move was Black's, it is now Black's turn again.
            # Undo the corresponding White move too.
            if self.game.turn == chess.BLACK:
                self.game.undo()

        self.input.clear()
        self.drag_square = None

    def on_mouse_down(self, pos: Tuple[int, int]) -> None:
        # 1. A promotion choice is waiting: the click answers it.
        if self.input.is_choosing_promotion:
            piece_type = self.dialog.choice_at(pos)
            if piece_type is None:
                self.input.cancel_promotion()
            else:
                self.input.choose_promotion(piece_type)
            return
        # 2. Buttons.
        if self.new_game_button.contains(pos):
            self.new_game()
            return
        if self.undo_button.contains(pos):
            self.undo()
            return
        # 3. The board.
        square = self.board_view.pixel_to_square(pos)
        if square is None:
            return
        move = self.input.click(square)
        if move is None and self.input.selected == square:
            self.drag_square = square  # a piece was picked up: it may be dragged

    def on_mouse_up(self, pos: Tuple[int, int]) -> None:
        if self.drag_square is None:
            return
        origin = self.drag_square
        self.drag_square = None
        square = self.board_view.pixel_to_square(pos)
        if square is not None and square != origin and square in self.input.targets:
            self.input.click(square)
        # Otherwise the piece snaps back and stays selected (click-click still works).

    # ---- drawing -------------------------------------------------------

    def draw(self) -> None:
        mouse_pos = pygame.mouse.get_pos()
        self.screen.fill(theme.PANEL_BG)
        self.board_view.draw(
            self.screen,
            self.game,
            selected=self.input.selected,
            targets=self.input.targets,
            drag_square=self.drag_square,
            drag_pos=mouse_pos if self.drag_square is not None else None,
        )
        if self.input.is_choosing_promotion:
            self.dialog.draw(self.screen, self.board_view, self.game.turn, mouse_pos)
        self.draw_panel(mouse_pos)

    def _text(self, text: str, font: pygame.font.Font, color, x: int, y: int) -> int:
        """Draw text and return the y position for the next line."""
        image = font.render(text, True, color)
        self.screen.blit(image, (x, y))
        return y + image.get_height() + 6

    def draw_panel(self, mouse_pos: Tuple[int, int]) -> None:
        x = theme.BOARD_SIZE + 20
        y = self._text("ChessMind AI", self.title_font, theme.TEXT_COLOR, x, 20)

        game_over = self.game.is_game_over
        text_x = x
        if not game_over:  # a disc showing whose turn it is
            disc = theme.WHITE_PIECE_FILL if self.game.turn == chess.WHITE else theme.BLACK_PIECE_FILL
            pygame.draw.circle(self.screen, disc, (x + 9, y + 15), 9)
            pygame.draw.circle(self.screen, theme.MUTED_TEXT, (x + 9, y + 15), 9, 2)
            text_x = x + 26
        status_color = GAME_OVER_COLOR if game_over else theme.ACCENT
        self._text(self.game.status_text(), self.text_font, status_color, text_x, y + 4)

        self.new_game_button.draw(self.screen, self.small_font, mouse_pos)
        self.undo_button.draw(self.screen, self.small_font, mouse_pos,
                              enabled=self.game.ply_count > 0)

        y = self._text("Moves", self.text_font, theme.MUTED_TEXT, x, 152)
        for line in self.game.move_list_text()[-MOVES_SHOWN:]:
            y = self._text(line, self.small_font, theme.TEXT_COLOR, x, y)

        help_lines = [
        "Play as White against the AI",
        "Click or drag a piece to move",
        "N new game   U undo   ESC quit",
    ]
        y = theme.WINDOW_HEIGHT - 25 * len(help_lines) - 10
        for line in help_lines:
            y = self._text(line, self.small_font, theme.MUTED_TEXT, x, y)