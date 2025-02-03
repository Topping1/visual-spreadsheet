# Visual Spreadsheet

Visual Spreadsheet is a Python desktop application built with PyQt5 that lets you create and manipulate a spreadsheet-like canvas. Each cell (called an “element”) can store either a numeric value or a Python expression (formula). The app automatically computes cell values, tracks dependencies between cells, and draws visual connections between elements, creating an interactive “visual spreadsheet” environment.

---

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Code Overview](#code-overview)
- [Screenshot](#screenshot)
- [License](#license)

---

## Features

- **Dynamic Formulas:** Cells can contain numbers or Python expressions. The script parses expressions and automatically converts the caret operator (`^`) to exponentiation (`**`) using an AST transformer.
- **Dependency Tracking:** When a cell’s value is updated, any cells that depend on its value are recalculated.
- **Interactive UI:** Built using PyQt5, the application supports:
  - Moving and selecting cells on a virtually infinite canvas.
  - Double-clicking cells to edit their contents.
  - Visual connection lines (with arrowheads) to indicate dependencies between cells.
- **File Operations:** 
  - **New Canvas:** Clear the current canvas.
  - **Save/Load:** Save the canvas (cell names, contents, and positions) to an XML file and load it later.
- **Keyboard Shortcuts:** Pressing the Delete key removes selected elements and updates the calculations.

---

## Requirements

- **Python 3.x**
- **PyQt5**  
  Install via pip if necessary:  
  ```sh
  pip install PyQt5
  ```
- Standard Python libraries: `sys`, `math`, `ast`, and `xml.etree.ElementTree`

---

## Installation

1. **Clone the repository:**

   ```sh
   git clone https://github.com/Topping1/visual-spreadsheet.git
   cd visual-spreadsheet
   ```

2. **(Optional) Create and activate a virtual environment:**

   ```sh
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```sh
   pip install PyQt5
   ```

---

## Usage

1. **Run the application:**

   ```sh
   python visualcalc.py
   ```

2. **Interacting with the Visual Spreadsheet:**
   - **Add Element:** Click on the "Add Element" button in the toolbar to create a new cell.
   - **Edit Element:** Double-click any cell to edit its content. You can enter a number or a Python expression (e.g., `E1 + 10` or use functions like `math.sqrt(16)`).
   - **Delete Element:** Select one or more cells and press the `Delete` key.
   - **Save/Load:** Use the "Save" and "Load" toolbar buttons to persist the canvas state in an XML file.
   - **Dynamic Calculations:** The app recalculates and updates cell values automatically when any dependent cell is modified.

---

## Code Overview

- **AST Transformation:**  
  The `XorToPow` class converts caret (`^`) operators in formulas to Python’s exponentiation operator (`**`) to support familiar spreadsheet syntax.
  
- **Expression Evaluation:**  
  The helper functions `get_dependencies` and `evaluate_element` parse and compute cell values. Dependencies among cells are tracked, and circular dependencies are detected.
  
- **Graphics Components:**  
  Custom PyQt5 graphics items (like `VisualElementItem` and `ConnectionLine`) handle the rendering of cells and the connection arrows between them.
  
- **Main Application Window:**  
  The `MainWindow` class sets up the canvas, toolbar, file operations (new, save, load), and overall interaction logic.

---

## Screenshot

![Screenshot](https://github.com/user-attachments/assets/f3dfd33a-58d8-4d2a-854c-c6f12a868a77)

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
