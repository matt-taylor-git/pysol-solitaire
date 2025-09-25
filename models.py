from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING
from PySide6.QtCore import QPointF, QRectF, QPropertyAnimation, QEasingCurve

if TYPE_CHECKING:
    from card import CardItem, PlaceholderItem
    from PySide6.QtCore import QParallelAnimationGroup


@dataclass
class Pile:
    kind: str  # "tableau" | "foundation" | "stock" | "waste"
    index: int
    anchor: QPointF
    placeholder: "PlaceholderItem"  # Forward ref to avoid circular
    spacing_y: float = 0.0

    cards: List["CardItem"] = None  # Forward ref

    def __post_init__(self):
        if self.cards is None:
            self.cards = []

    def rect(self) -> QRectF:
        return self.placeholder.rect().translated(self.anchor)

    def add_cards(self, cards: List["CardItem"]):
        for c in cards:
            self.cards.append(c)
            c.current_pile = self

    def remove_cards_from(self, card: "CardItem") -> List["CardItem"]:
        # Remove 'card' and everything above it in this pile
        if card not in self.cards:
            return []
        idx = self.cards.index(card)
        group = self.cards[idx:]
        self.cards = self.cards[:idx]
        for c in group:
            c.current_pile = None
        return group

    def top_card(self) -> Optional["CardItem"]:
        return self.cards[-1] if self.cards else None

    def layout_cards(self, animate=False, anim_group: Optional["QParallelAnimationGroup"] = None):
        # Position cards starting from anchor; tableau uses spacing_y
        for i, c in enumerate(self.cards):
            target = self.anchor + QPointF(0, i * self.spacing_y)
            if animate and anim_group is not None:
                a = QPropertyAnimation(c, b"pos")
                a.setDuration(220)
                a.setEasingCurve(QEasingCurve.InOutQuad)
                a.setEndValue(target)
                anim_group.addAnimation(a)
            else:
                c.setPos(target)

        # Update z ordering within pile
        base = 50 + self.index * 10
        for i, c in enumerate(self.cards):
            c.setZValue(base + i)

    def contains_point(self, p: QPointF) -> bool:
        return self.rect().contains(p)
