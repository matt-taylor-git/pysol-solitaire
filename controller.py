import os
import random
from typing import List, Optional, TYPE_CHECKING

from PySide6.QtWidgets import QGraphicsView, QGraphicsTextItem
from PySide6.QtCore import (
    QObject,
    Signal,
    QPointF,
    QRectF,
    QParallelAnimationGroup,
    QPropertyAnimation,
    QSequentialAnimationGroup,
    QEasingCurve,
    Qt,
)
from PySide6.QtGui import QPainter, QFont

from constants import (
    SUITS, RANKS, CARD_ASPECT, TOP_MARGIN, SIDE_MARGIN, PILE_GAP_X, PILE_GAP_Y,
    svg_path_for
)
from models import Pile
from card import CardItem, PlaceholderItem
from window import SolitaireWindow

if TYPE_CHECKING:
    # Type hints only - these are already imported above for runtime
    pass


class GameController(QObject):
    def __init__(self, window: "SolitaireWindow"):
        super().__init__(window)
        self.window = window
        self.scene = window.game_scene
        self.view = window.game_view

        self.card_width = 100.0
        self.card_height = self.card_width * CARD_ASPECT

        self.tableau: List[Pile] = []
        self.foundations: List[Pile] = []
        self.stock: Optional[Pile] = None
        self.waste: Optional[Pile] = None

        self.all_piles: List[Pile] = []

        self.deck: List[CardItem] = []  # undealt cards
        self._win_animation: Optional[QPropertyAnimation] = None
        self._win_text_item: Optional[QGraphicsTextItem] = None
        self._wire_view_resize()

    def _wire_view_resize(self):
        # Recompute layout when the view resizes
        class _View(self.view.__class__):
            resized = Signal()

            def resizeEvent(self, ev):
                super().resizeEvent(ev)
                self.resized.emit()

        parent_layout = self.window.game_view.parentWidget().layout()
        idx = parent_layout.indexOf(self.view)
        old_view = self.view
        old_view.hide()
        old_view.setParent(None)

        new_view = _View()
        new_view.setScene(self.scene)
        new_view.setFrameStyle(old_view.frameStyle())
        new_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        new_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        new_view.setStyleSheet("background: transparent;")
        new_view.setAttribute(Qt.WA_TranslucentBackground)
        new_view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        new_view.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        new_view.resized.connect(self.relayout_on_resize)

        parent_layout.insertWidget(idx, new_view)
        self.window.game_view = new_view
        self.view = new_view

    # ---------------- Layout ----------------

    def compute_card_size(self):
        vw = max(640, self.view.viewport().width())
        # Space for 7 columns + gaps + margins
        usable = vw - 2 * SIDE_MARGIN - 6 * PILE_GAP_X
        cw = usable / 7.0
        cw = max(60.0, min(cw, 140.0))
        self.card_width = cw
        self.card_height = self.card_width * CARD_ASPECT

    def clear_scene(self):
        # Stop win animation and remove text
        if self._win_animation:
            self._win_animation.stop()
            self._win_animation = None
        if self._win_text_item:
            self.scene.removeItem(self._win_text_item)
            self._win_text_item = None

        # Remove all items except persistent UI
        for item in list(self.scene.items()):
            if isinstance(item, (PlaceholderItem, CardItem)):
                self.scene.removeItem(item)
        self.tableau.clear()
        self.foundations.clear()
        self.stock = None
        self.waste = None
        self.all_piles.clear()
        self.deck.clear()

    def setup_piles(self):
        self.compute_card_size()
        cw, ch = self.card_width, self.card_height
        self.scene.setSceneRect(0, 0, max(900, self.view.width()), max(600, self.view.height()))

        # Columns X positions
        cols_x = [SIDE_MARGIN + i * (cw + PILE_GAP_X) for i in range(7)]
        y_top = TOP_MARGIN + 50  # Some space for top info bar
        y_tableau = y_top + ch + 24

        # Foundations (upper left: 4 piles)
        self.foundations = []
        for i in range(4):
            ph = PlaceholderItem(QRectF(0, 0, cw, ch))
            self.scene.addItem(ph)
            anchor = QPointF(cols_x[i], y_top)
            ph.setPos(anchor)
            self.foundations.append(Pile("foundation", i, anchor, ph, spacing_y=0))

        # Waste and Stock (upper right)
        waste_rect = QRectF(0, 0, cw, ch)
        stock_rect = QRectF(0, 0, cw, ch)

        waste_ph = PlaceholderItem(waste_rect)
        stock_ph = PlaceholderItem(stock_rect)

        self.scene.addItem(waste_ph)
        self.scene.addItem(stock_ph)

        waste_anchor = QPointF(cols_x[5], y_top)
        stock_anchor = QPointF(cols_x[6], y_top)
        waste_ph.setPos(waste_anchor)
        stock_ph.setPos(stock_anchor)

        self.waste = Pile("waste", 0, waste_anchor, waste_ph, spacing_y=0)
        self.stock = Pile("stock", 0, stock_anchor, stock_ph, spacing_y=0)

        # Tableau (7 piles)
        self.tableau = []
        for i in range(7):
            ph = PlaceholderItem(QRectF(0, 0, cw, ch))
            self.scene.addItem(ph)
            anchor = QPointF(cols_x[i], y_tableau)
            ph.setPos(anchor)
            self.tableau.append(Pile("tableau", i, anchor, ph, spacing_y=PILE_GAP_Y))

        self.all_piles = [self.stock, self.waste] + self.foundations + self.tableau

    def relayout_on_resize(self):
        if not self.tableau:
            return
        # Recompute sizes and move piles/cards
        prev_cw = self.card_width
        self.compute_card_size()
        cw, ch = self.card_width, self.card_height

        # Update placeholders and anchors
        cols_x = [SIDE_MARGIN + i * (cw + PILE_GAP_X) for i in range(7)]
        y_top = TOP_MARGIN + 50
        y_tableau = y_top + ch + 24

        # Update stock/waste/foundations
        for i, f in enumerate(self.foundations):
            f.placeholder.setRect(QRectF(0, 0, cw, ch))
            f.anchor = QPointF(cols_x[i], y_top)
            f.placeholder.setPos(f.anchor)

        if self.waste:
            self.waste.placeholder.setRect(QRectF(0, 0, cw, ch))
            self.waste.anchor = QPointF(cols_x[5], y_top)
            self.waste.placeholder.setPos(self.waste.anchor)

        if self.stock:
            self.stock.placeholder.setRect(QRectF(0, 0, cw, ch))
            self.stock.anchor = QPointF(cols_x[6], y_top)
            self.stock.placeholder.setPos(self.stock.anchor)

        for i, t in enumerate(self.tableau):
            t.placeholder.setRect(QRectF(0, 0, cw, ch))
            t.anchor = QPointF(cols_x[i], y_tableau)
            t.placeholder.setPos(t.anchor)

        # Scale cards and re-layout
        for item in self.scene.items():
            if isinstance(item, CardItem):
                item.set_size(cw)

        # Instant reflow for accurate UI
        anim = QParallelAnimationGroup()
        for p in self.all_piles:
            p.layout_cards(animate=False, anim_group=None)

    # ---------------- Deck & Deal ----------------

    def build_deck(self):
        self.deck.clear()
        print("DEBUG: Building deck...")
        for s in SUITS:
            for r in RANKS:
                path = svg_path_for(s, r)
                if not os.path.exists(path):
                    # Skip missing assets defensively
                    continue
                c = CardItem(s, r, path, self, face_up=False)
                c.set_size(self.card_width)
                c.setPos(self.stock.anchor)  # start at stock for deal animation origin
                c.dragReleased.connect(self.on_card_drag_released)
                self.scene.addItem(c)
                self.deck.append(c)

        random.shuffle(self.deck)
        print(f"DEBUG: Deck built with {len(self.deck)} cards.")

    def deal(self):
        """
        Standard Klondike deal:
        - 7 tableau columns
        - Column i gets i+1 cards, only the top one face-up
        - Remainder to stock face-down
        """
        # Start with everything at stock anchor
        for c in self.deck:
            c.setPos(self.stock.anchor)

        anim = QParallelAnimationGroup()

        # Deal to tableau
        idx = 0
        for col in range(7):
            for row in range(col + 1):
                if idx >= len(self.deck):
                    break
                card = self.deck[idx]
                idx += 1
                # Move from deck to tableau[col]
                card.set_face_up(row == col)
                target_pile = self.tableau[col]
                target_pile.add_cards([card])
                card.current_pile = target_pile
        # Animate layout of tableau
        for t in self.tableau:
            t.layout_cards(animate=False, anim_group=None)

        # Remaining cards to stock
        remaining = self.deck[idx:]
        self.deck = []  # clear deck list as cards are now in piles
        if remaining:
            self.stock.add_cards(remaining)
            for card in remaining:
                card.current_pile = self.stock
        self.stock.layout_cards(animate=True, anim_group=anim)

        anim.start(QParallelAnimationGroup.DeleteWhenStopped)
        print("DEBUG: Deal finished.")
        # Log pile counts
        for p in self.all_piles:
            print(f"DEBUG: Pile {p.kind} {p.index} has {len(p.cards)} cards.")



    # ---------------- Interactions ----------------

    def new_game(self):
        # Clear scene, piles, build deck, deal
        print("\nDEBUG: ====================")
        print("DEBUG: Starting new game...")
        print("DEBUG: ====================")
        self.clear_scene()
        self.won = False
        self.setup_piles()
        self.build_deck()
        self.deal()
        print("DEBUG: New game setup complete.")

    def highlight_drop_targets(self, on: bool):
        # Phase 1: allow drops to any pile except stock; foundations accept only single card visually
        for p in self.all_piles:
            if p.kind == "stock":
                p.placeholder.set_highlighted(False)
            else:
                p.placeholder.set_highlighted(on)

    def get_draggable_group_for(self, card: CardItem) -> List[CardItem]:
        """
        Determines which cards can be dragged, based on game rules.
        - top card of waste
        - any face-up card in tableau, along with all face-up cards stacked above it in valid sequence
        - top card of a foundation
        """
        pile = card.current_pile
        if pile is None:
            return []

        if pile.kind == "waste":
            if card is pile.top_card():
                return [card]
            return []

        if pile.kind == "tableau":
            # Build group from this card to top, only if this card is face-up and sequence is valid
            if not card.is_face_up():
                return []
            idx = pile.cards.index(card)
            group = [card]
            for i in range(idx + 1, len(pile.cards)):
                top = group[-1]
                bottom = pile.cards[i]
                # Tableau stack rule: next card must be one rank lower and opposite color
                if bottom.color == top.color:
                    return [] # invalid group
                if RANKS.index(bottom.rank) != RANKS.index(top.rank) - 1:
                    return [] # invalid group
                group.append(bottom)
            return group

        if pile.kind == "foundation":
            if card is pile.top_card():
                return [card]
            return []

        if pile.kind == "stock":
            # Stock cards aren't draggable
            return []

        return []

    def _can_stack_on(self, bottom_card: CardItem, top_pile: Pile) -> bool:
        """ Check if a card can be legally placed on a pile """
        if top_pile.kind == "tableau":
            # Tableau: empty accepts King; otherwise opposite color, rank-1
            if not top_pile.cards:
                return bottom_card.rank == "king"
            else:
                top_card = top_pile.top_card()
                if not top_card: return False
                return (bottom_card.color != top_card.color and
                        RANKS.index(bottom_card.rank) == RANKS.index(top_card.rank) - 1)

        if top_pile.kind == "foundation":
            # Foundation: empty accepts Ace; otherwise same suit, rank+1
            if not top_pile.cards:
                return bottom_card.rank == "ace"
            else:
                top_card = top_pile.top_card()
                if not top_card: return False
                return (bottom_card.suit == top_card.suit and
                        RANKS.index(bottom_card.rank) == RANKS.index(top_card.rank) + 1)
        return False

    def on_card_drag_released(self, card: CardItem, scene_pos: QPointF, start_positions: List[QPointF]):
        """
        Resolve drop target and animate group to destination, or revert.
        Rules are now enforced via _can_stack_on.
        """
        src_pile = card.current_pile
        if src_pile is None:
            return

        # Which cards are we moving?
        group = self.get_draggable_group_for(card)
        if not group:
            # Not actually draggable; revert
            self._animate_revert([card], [card.pos()])
            return

        # Find best target pile under drop point
        target = self._find_target_pile(scene_pos, prefer_tableau=True)

        # Validate drop
        can_drop = target and self._can_stack_on(group[0], target)

        if can_drop:
            # Temporarily detach from source pile
            old_group = src_pile.remove_cards_from(card)
            # Accept drop
            target.add_cards(old_group)
            self._animate_layout([src_pile, target])
            print(f"DEBUG: Accepted drop to {target.kind}, calling check_win")
            self.check_win()
            # Auto-flip new top card of a tableau if it was face-down
            if src_pile.kind == "tableau" and src_pile.top_card() and not src_pile.top_card().is_face_up():
                src_pile.top_card().set_face_up(True)
        else:
            # Revert
            self._animate_revert(group, start_positions)


    def _find_target_pile(self, pt: QPointF, prefer_tableau=True) -> Optional[Pile]:
        candidates = []
        for p in self.all_piles:
            if p.kind == "stock":
                continue
            if p.kind == "tableau":
                # Expanded drop zone for tableau: covers full stack height
                x = p.anchor.x()
                y = p.anchor.y()
                w = self.card_width
                if len(p.cards) == 0:
                    h = self.card_height
                else:
                    h = (len(p.cards) - 1) * p.spacing_y + self.card_height
                drop_rect = QRectF(x, y, w, h)
                if drop_rect.contains(pt):
                    candidates.append(p)
            else:
                # Foundation/waste: standard placeholder rect
                if p.placeholder.sceneBoundingRect().contains(pt):
                    candidates.append(p)
        if not candidates:
            return None
        # If multiple, prefer tableau over foundation/waste
        if prefer_tableau:
            for p in candidates:
                if p.kind == "tableau":
                    return p
        return candidates[0]

    def _animate_layout(self, piles: List[Pile]):
        for p in piles:
            p.layout_cards(animate=False, anim_group=None)

    def _animate_revert(self, cards: List[CardItem], start_positions: List[QPointF]):
        # Instantly revert dragged cards to their original positions
        for c, start in zip(cards, start_positions):
            c.setPos(start)

    def check_win(self):
        if self.won:
            return
        print(f"DEBUG: Check win, foundations: {[len(f.cards) for f in self.foundations]}")
        if all(len(f.cards) == 13 for f in self.foundations):
            print("DEBUG: Win condition met!")
            self.won = True
            self.show_celebration()

    def show_celebration(self):
        self._win_text_item = QGraphicsTextItem("🎉 You Win! 🎉")
        self._win_text_item.setFont(QFont("Arial", 48, QFont.Bold))
        self._win_text_item.setDefaultTextColor(Qt.white)
        self._win_text_item.setZValue(1000)  # On top of everything

        # Center horizontally, position vertically above cards
        scene_rect = self.scene.sceneRect()
        text_rect = self._win_text_item.boundingRect()
        x = scene_rect.center().x() - text_rect.center().x()
        y = TOP_MARGIN  # Position it at the top margin
        self._win_text_item.setPos(x, y)

        self._win_text_item.setScale(1.0)
        self._win_text_item.setOpacity(1.0)
        self.scene.addItem(self._win_text_item)

        # Animate a repeating pulse
        anim_group = QParallelAnimationGroup()
        
        scale_up = QPropertyAnimation(self._win_text_item, b"scale")
        scale_up.setDuration(700)
        scale_up.setStartValue(1.0)
        scale_up.setEndValue(1.1)
        scale_up.setEasingCurve(QEasingCurve.InOutQuad)

        scale_down = QPropertyAnimation(self._win_text_item, b"scale")
        scale_down.setDuration(700)
        scale_down.setStartValue(1.1)
        scale_down.setEndValue(1.0)
        scale_down.setEasingCurve(QEasingCurve.InOutQuad)
        
        seq = QSequentialAnimationGroup()
        seq.addAnimation(scale_up)
        seq.addAnimation(scale_down)
        seq.setLoopCount(-1) # Loop forever
        
        self._win_animation = seq
        self._win_animation.start()

    # ---------------- Button hooks ----------------

    def on_shuffle_clicked(self):
        self.new_game()

    def on_play_clicked(self):
        # Alias for new game in Phase 1
        self.new_game()

    def on_stock_clicked(self):
        # Draw one from stock to waste with flip animation (Phase 1)
        if not self.stock or not self.stock.cards:
            # If stock empty, recycle waste back to stock face-down (Phase 1 UX)
            if self.waste and self.waste.cards:
                moving = list(reversed(self.waste.cards))
                self.waste.cards.clear()
                for c in moving:
                    c.set_face_up(False)
                    c.current_pile = self.stock
                self.stock.add_cards(moving)
                self._animate_layout([self.stock, self.waste])
                self.check_win()
            return

        card = self.stock.cards.pop()  # take top visually
        card.current_pile = self.waste
        # Move to waste
        self.waste.add_cards([card])
        card.set_face_up(True)
        self._animate_layout([self.stock, self.waste])
        self.check_win()

    def on_force_win_clicked(self):
        # Debug: Force fill foundations with full suits
        suits = SUITS[:4]  # clubs, diamonds, hearts, spades
        for i, f in enumerate(self.foundations):
            suit = suits[i]
            # Cards from ace to king
            for r in RANKS:
                path = svg_path_for(suit, r)
                if not os.path.exists(path):
                    continue
                c = CardItem(suit, r, path, self, face_up=True)
                c.set_size(self.card_width)
                c.current_pile = f
                f.add_cards([c])
                self.scene.addItem(c)
            self._animate_layout([f])
        self.check_win()
