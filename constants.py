import os

from PySide6.QtGui import QColor, QPen, QBrush
from PySide6.QtCore import Qt

SUITS = ["clubs", "diamonds", "hearts", "spades"]
RANKS = ["ace"] + [str(n) for n in range(2, 11)] + ["jack", "queen", "king"]

CARD_ASPECT = 1.45  # height/width
TOP_MARGIN = 20
SIDE_MARGIN = 20
PILE_GAP_X = 18
PILE_GAP_Y = 26
PLACEHOLDER_RADIUS = 10

PLACEHOLDER_PEN = QPen(QColor(255, 255, 255, 160), 2, Qt.SolidLine)
PLACEHOLDER_BRUSH = QBrush(QColor(255, 255, 255, 30))
SELECTION_HALO_PEN = QPen(QColor(255, 255, 0, 200), 3, Qt.SolidLine)

SVG_BASE_DIR = "SVG-cards-1.3"


def svg_path_for(suit: str, rank: str) -> str:
    # Files like "ace_of_spades.svg", "10_of_hearts.svg"
    return os.path.join(SVG_BASE_DIR, f"{rank}_of_{suit}.svg")
