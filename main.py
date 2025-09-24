import sys

from PySide6.QtWidgets import QApplication

from window import SolitaireWindow


# -------------------------------
# App bootstrap
# -------------------------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SolitaireWindow()
    window.show()
    sys.exit(app.exec())
