"""Milestone 1 smoke test.

Run with:  python scripts/check_setup.py
Checks that Python, python-chess, pygame and NumPy are installed and working.
"""

import os
import sys

# Make pygame run without opening a real window, and hide its banner.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")


def check_python() -> str:
    v = sys.version_info
    if v < (3, 10):
        raise RuntimeError(f"Python 3.10+ required, found {v.major}.{v.minor}")
    in_venv = sys.prefix != sys.base_prefix
    note = "venv active" if in_venv else "WARNING: venv not active"
    return f"Python {v.major}.{v.minor}.{v.micro} ({note})"


def check_chess() -> str:
    import chess

    board = chess.Board()
    move_count = board.legal_moves.count()
    if move_count != 20:
        raise RuntimeError(f"Expected 20 opening moves, got {move_count}")

    # Fool's mate: the fastest possible checkmate.
    for san in ["f3", "e5", "g4", "Qh4"]:
        board.push_san(san)
    if not board.is_checkmate():
        raise RuntimeError("Fool's mate was not detected as checkmate")

    return f"python-chess {chess.__version__} (20 opening moves, checkmate detected)"


def check_pygame() -> str:
    import pygame

    pygame.init()
    screen = pygame.display.set_mode((100, 100))
    screen.fill((255, 255, 255))
    pygame.quit()
    return f"pygame {pygame.version.ver} (headless window created)"


def check_numpy() -> str:
    import numpy as np

    total = int(np.array([1, 2, 3]).sum())
    if total != 6:
        raise RuntimeError("NumPy arithmetic failed")
    return f"NumPy {np.__version__}"


def main() -> int:
    print("ChessMind AI - setup check")
    checks = [check_python, check_chess, check_pygame, check_numpy]
    failures = 0
    for check in checks:
        try:
            print(f"[ OK ] {check()}")
        except Exception as error:  # report any problem, keep checking the rest
            failures += 1
            print(f"[FAIL] {check.__name__}: {error}")
    print("All checks passed." if failures == 0 else f"{failures} check(s) failed.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())