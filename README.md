# PySol - Klondike Solitaire

A complete implementation of the classic Klondike Solitaire card game using Python and PySide6 for the GUI.

## Features

- Full Klondike Solitaire gameplay
- Drag-and-drop card movements
- Game rules enforcement (valid moves only)
- Responsive layout that adapts to window size
- Smooth animations for visual feedback
- Stock cycling functionality
- Auto-flipping of face-down cards in tableau

## Requirements

- Python 3.8+
- PySide6

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/matt-taylor-git/pysol-solitaire.git
   cd pysol-solitaire
   ```

2. Create a virtual environment:
   ```bash
   python -m venv pysol_venv
   ```

3. Activate the virtual environment:
   - Windows: `pysol_venv\Scripts\activate`
   - macOS/Linux: `source pysol_venv/bin/activate`

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Game

With the virtual environment activated:
```bash
python main.py
```

## How to Play

Klondike Solitaire rules:
- Build foundations up from Ace to King, same suit
- Build tableau down, alternating colors
- Turn over face-down cards by clearing piles above them
- Use stock pile to draw cards in need of moves
- Win by successfully moving all cards to foundations

## Controls

- **Drag and drop** cards with mouse
- Click stock to draw cards
- Use buttons for New Game, Undo, Hint, Settings

## Project Structure

- `main.py` - Application entry point
- `window.py` - Qt main window and UI
- `controller.py` - Game logic and state management
- `card.py` - Card graphics and interaction
- `models.py` - Data structures (Pile class)
- `constants.py` - Game configuration and timing constants

## Assets

Card images from the [SVG-cards-1.3 project](https://github.com/h3rald/cards) by Alessandro Cocco (Open source).

## License

This project is open source. Card assets are courtesy of the SVG-cards library.
