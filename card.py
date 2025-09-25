from typing import List, Optional, Tuple, TYPE_CHECKING

from PySide6.QtWidgets import QGraphicsObject, QGraphicsRectItem, QGraphicsDropShadowEffect
from PySide6.QtGui import (
    QColor,
    QPen,
    QBrush,
    QPainter,
    QLinearGradient,
    QTransform,
)
from PySide6.QtCore import (
    Qt,
    QRectF,
    QPointF,
    Signal,
)
from PySide6.QtSvg import QSvgRenderer
from models import Pile

if TYPE_CHECKING:
    from controller import GameController


class PlaceholderItem(QGraphicsRectItem):
    def __init__(self, rect: QRectF):
        super().__init__(rect)
        from constants import PLACEHOLDER_PEN, PLACEHOLDER_BRUSH, SELECTION_HALO_PEN
        self.setPen(PLACEHOLDER_PEN)
        self.setBrush(PLACEHOLDER_BRUSH)
        self.setZValue(0)

    def set_highlighted(self, on: bool):
        from constants import SELECTION_HALO_PEN, PLACEHOLDER_PEN
        self.setPen(SELECTION_HALO_PEN if on else PLACEHOLDER_PEN)


class CardItem(QGraphicsObject):
    """
    QGraphicsObject-based card so we can animate 'pos' and custom paint the back with gradients.
    """
    # Emitted when a drag finishes: (card, dropScenePos, startPositions)
    dragReleased = Signal(object, QPointF, list)

    def __init__(self, suit: str, rank: str, front_svg: str, controller: "GameController", face_up=False):
        super().__init__()
        self.suit = suit
        self.rank = rank
        self.front_svg_path = front_svg
        self.controller = controller

        # Rendering
        self.svg_renderer = QSvgRenderer(self.front_svg_path)
        # Default size; controller will scale this after view is available
        self.w = 90.0
        self.h = self.w * 1.45  # CARD_ASPECT

        # State
        self._face_up = face_up
        self.current_pile: Optional["Pile"] = None
        self._dragging = False
        self._drag_group: List[CardItem] = [self]
        self._drag_offset = QPointF(0, 0)
        self._group_offsets: List[QPointF] = [QPointF(0, 0)]
        self._start_positions: List[QPointF] = []

        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.setFlag(QGraphicsObject.ItemIsFocusable, True)
        self.setZValue(10)  # cards above placeholders

        # Subtle shadow to lift cards
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.setGraphicsEffect(shadow)

        # cached back design recalculated when size changes
        self._back_cache_size: Tuple[int, int] = (0, 0)
        self._back_pixmap = None

    @property
    def color(self) -> str:
        return "red" if self.suit in ("hearts", "diamonds") else "black"

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self.w, self.h)

    def set_size(self, w: float):
        new_w = max(30.0, min(w, 240.0))
        if abs(new_w - self.w) < 0.1:
            return
        self.prepareGeometryChange()
        from constants import CARD_ASPECT
        self.w = new_w
        self.h = self.w * CARD_ASPECT
        self._back_cache_size = (0, 0)  # invalidate
        self.update()

    def is_face_up(self) -> bool:
        return self._face_up

    def set_face_up(self, face_up: bool):
        if self._face_up == face_up:
            return
        self._face_up = face_up
        self.update()

    def paint(self, painter: QPainter, option, widget=None):
        # Antialiasing for smooth edges
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Rounded card shape mask
        r = 12.0
        rect = self.boundingRect()
        # Draw drop-shadow handled by effect; draw white edge
        painter.setPen(QPen(QColor(255, 255, 255), 1.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect.adjusted(0.75, 0.75, -0.75, -0.75), r, r)

        if self._face_up:
            # Render the SvG front
            # Many card SvGs have their own backgrounds; scale to rect
            self.svg_renderer.render(painter, rect.adjusted(2, 2, -2, -2))
        else:
            # Programmatic gradient back
            pm = self._ensure_back_pixmap(int(rect.width()), int(rect.height()))
            painter.drawPixmap(rect.topLeft(), pm)

    def _ensure_back_pixmap(self, w: int, h: int):
        if self._back_pixmap and self._back_cache_size == (w, h):
            return self._back_pixmap

        from PySide6.QtGui import QPixmap, QPainterPath

        pm = QPixmap(w, h)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing, True)

        rr = 12.0
        card_rect = QRectF(0, 0, w, h)
        path = QPainterPath()
        path.addRoundedRect(card_rect.adjusted(1, 1, -1, -1), rr, rr)
        p.setClipPath(path)

        # Deep royal blue gradient background
        grad = QLinearGradient(0, 0, w, h)
        grad.setColorAt(0.0, QColor("#0A1F44"))
        grad.setColorAt(0.5, QColor("#123C8A"))
        grad.setColorAt(1.0, QColor("#0A1F44"))
        p.fillRect(card_rect, grad)

        # Subtle diagonal pattern
        stripe = QLinearGradient(0, 0, 18, 18)
        stripe.setColorAt(0.0, QColor(255, 255, 255, 18))
        stripe.setColorAt(0.5, QColor(255, 255, 255, 6))
        stripe.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.save()
        p.setTransform(QTransform().rotate(35), True)
        for x in range(-h, w + h, 18):
            p.fillRect(QRectF(x, -h, 8, h * 3), stripe)
        p.restore()

        # Inner border
        inner = card_rect.adjusted(6, 6, -6, -6)
        p.setPen(QPen(QColor(255, 255, 255, 180), 2))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(inner, rr - 3, rr - 3)

        # Center motif: simple diamond
        motif_rect = QRectF(0, 0, w * 0.28, h * 0.18)
        motif_rect.moveCenter(card_rect.center())
        motif_path = QPainterPath()
        cx, cy = motif_rect.center().x(), motif_rect.center().y()
        dx, dy = motif_rect.width() / 2, motif_rect.height() / 2
        motif_path.moveTo(cx, cy - dy)
        motif_path.lineTo(cx + dx, cy)
        motif_path.lineTo(cx, cy + dy)
        motif_path.lineTo(cx - dx, cy)
        motif_path.closeSubpath()
        p.setBrush(QColor(255, 255, 255, 180))
        p.setPen(QPen(QColor(255, 255, 255, 220), 2))
        p.drawPath(motif_path)

        p.end()
        self._back_pixmap = pm
        self._back_cache_size = (w, h)
        return pm

    # ---------------- Dragging ----------------

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return super().mousePressEvent(event)

        # Only allow dragging if controller says it's ok
        group = self.controller.get_draggable_group_for(self)
        if not group:
            return

        self._dragging = True
        self._drag_group = group
        self._drag_offset = event.scenePos() - self.pos()
        self._start_positions = [c.pos() for c in group]
        top_pos = self.pos()
        self._group_offsets = [c.pos() - top_pos for c in group]

        # Bring group to front
        base_z = 1000.0
        for i, c in enumerate(group):
            c.setZValue(base_z + i)

        # Visual feedback
        for c in group:
            c.setOpacity(0.92)

        # Highlight valid piles (UI hint; rules loose in Phase 1)
        self.controller.highlight_drop_targets(True)

        event.accept()

    def mouseMoveEvent(self, event):
        if not self._dragging:
            return super().mouseMoveEvent(event)

        new_pos = event.scenePos() - self._drag_offset
        # Move the top (anchor) card
        self.setPos(new_pos)
        # Move the rest maintaining offsets
        for i in range(1, len(self._drag_group)):
            c = self._drag_group[i]
            c.setPos(new_pos + self._group_offsets[i])
        event.accept()

    def mouseReleaseEvent(self, event):
        if not self._dragging:
            return super().mouseReleaseEvent(event)

        self._dragging = False
        self.controller.highlight_drop_targets(False)

        # Reset visual feedback
        for c in self._drag_group:
            c.setOpacity(1.0)

        # Delegate drop resolution to controller
        self.dragReleased.emit(self, event.scenePos(), self._start_positions)
        # Controller will animate cards to proper pile or revert
        event.accept()
