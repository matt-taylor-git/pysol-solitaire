from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGraphicsView,
    QGraphicsScene,
)
from PySide6.QtGui import (
    QColor,
    QPalette,
    QIcon,
)
from PySide6.QtCore import (
    Qt,
    QSize,
)


class SolitaireWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Klondike Solitaire")
        self.setGeometry(100, 100, 1200, 900)

        # Felt green background (slight gradient via palette + scene transparency)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#0e6d45"))
        self.setAutoFillBackground(True)
        self.setPalette(palette)

        # Main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(6)

        # Top bar
        self._create_top_bar(main_layout)

        # Game view and scene
        self.game_view = QGraphicsView()
        self.game_scene = QGraphicsScene()
        self.game_view.setScene(self.game_scene)
        self.game_view.setFrameStyle(QGraphicsView.NoFrame)
        self.game_view.setStyleSheet("background: transparent;")
        self.game_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.game_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        main_layout.addWidget(self.game_view, 1)

        # Controller (needs to be before bottom bar for button connections)
        from controller import GameController  # Import here to avoid circular
        self.controller = GameController(self)
        self._initial_game_started = False

        # Bottom bar
        self._create_bottom_bar(main_layout)

        # Clickable stock area: intercept mouse presses on scene
        self.game_scene.mousePressEvent = self._scene_mouse_press_wrapper(self.game_scene.mousePressEvent)

    def showEvent(self, event):
        super().showEvent(event)
        if not self._initial_game_started:
            self.controller.new_game()
            self._initial_game_started = True

    def _create_top_bar(self, parent_layout):
        top_bar_widget = QWidget()
        top_bar_layout = QHBoxLayout(top_bar_widget)
        top_bar_layout.setContentsMargins(0, 0, 0, 0)

        label_style = "QLabel { color: white; font-size: 18px; }"

        self.time_label = QLabel("Time: 00:00")
        self.time_label.setStyleSheet(label_style)
        self.score_label = QLabel("Score: 0")
        self.score_label.setStyleSheet(label_style)
        self.moves_label = QLabel("Moves: 0")
        self.moves_label.setStyleSheet(label_style)

        top_bar_layout.addWidget(self.time_label)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.score_label)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.moves_label)

        parent_layout.addWidget(top_bar_widget)

    def _create_bottom_bar(self, parent_layout):
        bottom_bar_widget = QWidget()
        bottom_bar_layout = QHBoxLayout(bottom_bar_widget)
        bottom_bar_layout.setContentsMargins(0, 0, 0, 0)
        bottom_bar_layout.setSpacing(10)

        button_style = """
            QPushButton {
                background-color: rgba(255, 255, 255, 0.12);
                color: white;
                font-size: 16px;
                padding: 10px;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                icon-size: 60px;
                min-width: 64px;
                min-height: 64px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-color: rgba(255, 255, 255, 0.5);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.3);
                border-color: rgba(255, 255, 255, 0.7);
            }
        """

        undo_button = QPushButton()
        hint_button = QPushButton()
        new_game_button = QPushButton()
        draw_stock_button = QPushButton()

        icons_dir = Path(__file__).resolve().parent / "assets" / "icons"

        def configure_button(button, icon_name, tooltip):
            button.setStyleSheet(button_style)
            button.setIcon(QIcon(str(icons_dir / icon_name)))
            button.setIconSize(QSize(60, 60))
            button.setToolTip(tooltip)
            button.setAccessibleName(tooltip)

        configure_button(new_game_button, "new-game.png", "New Game")
        configure_button(undo_button, "undo.png", "Undo")
        configure_button(hint_button, "hint.png", "Hint")
        configure_button(draw_stock_button, "draw-stock.png", "Draw or Recycle Stock")

        bottom_bar_layout.addWidget(new_game_button)
        bottom_bar_layout.addWidget(undo_button)
        bottom_bar_layout.addWidget(hint_button)
        bottom_bar_layout.addStretch()
        bottom_bar_layout.addWidget(draw_stock_button)

        parent_layout.addWidget(bottom_bar_widget)

        new_game_button.clicked.connect(self.controller.new_game)
        undo_button.clicked.connect(self.controller.on_undo_clicked)
        hint_button.clicked.connect(self.controller.on_hint_clicked)
        draw_stock_button.clicked.connect(self.controller.on_stock_clicked)

    def _scene_mouse_press_wrapper(self, original_handler):
        # Wrap the scene's mousePressEvent to detect clicks on stock placeholder
        def handler(event):
            if self.controller.stock and self.controller.stock.placeholder.sceneBoundingRect().contains(event.scenePos()):
                self.controller.on_stock_clicked()
                event.accept()
                return
            # Otherwise, default handling (will bubble to items for drag)
            return original_handler(event)
        return handler
