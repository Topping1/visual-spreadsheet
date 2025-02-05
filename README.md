# Visual Spreadsheet

Visual Spreadsheet is a Python desktop application built with PyQt5 that lets you create and manipulate a spreadsheet-like canvas. Each cell (called an “element”) can store either a numeric value or a Python expression (formula). The app automatically computes cell values, tracks dependencies between cells, and draws visual connections between elements, creating an interactive “visual spreadsheet” environment.

---

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Code Overview](#code-overview)
- [Supported functions from Python Math library](#supported-functions-from-python-math-library-from-python-docs)
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

## Supported functions from Python Math library (from [Python Docs](https://docs.python.org/3/library/math.html))

| Function | Description |
| --- | --- |
| **Number-theoretic functions** |  |
| `comb(n, k)` | Number of ways to choose *k* items from *n* items without repetition and without order |
| `factorial(n)` | *n* factorial |
| `gcd(*integers)` | Greatest common divisor of the integer arguments |
| `isqrt(n)` | Integer square root of a nonnegative integer *n* |
| `lcm(*integers)` | Least common multiple of the integer arguments |
| `perm(n, k)` | Number of ways to choose *k* items from *n* items without repetition and with order |
| **Floating point arithmetic** |  |
| `ceil(x)` | Ceiling of *x*, the smallest integer greater than or equal to *x* |
| `fabs(x)` | Absolute value of *x* |
| `floor(x)` | Floor of *x*, the largest integer less than or equal to *x* |
| `fma(x, y, z)` | Fused multiply-add operation: `(x * y) + z` |
| `fmod(x, y)` | Remainder of division `x / y` |
| `modf(x)` | Fractional and integer parts of *x* |
| `remainder(x, y)` | Remainder of *x* with respect to *y* |
| `trunc(x)` | Integer part of *x* |
| **Floating point manipulation functions** |  |
| `copysign(x, y)` | Magnitude (absolute value) of *x* with the sign of *y* |
| `frexp(x)` | Mantissa and exponent of *x* |
| `isclose(a, b, rel_tol, abs_tol)` | Check if the values *a* and *b* are close to each other |
| `isfinite(x)` | Check if *x* is neither an infinity nor a NaN |
| `isinf(x)` | Check if *x* is a positive or negative infinity |
| `isnan(x)` | Check if *x* is a NaN (not a number) |
| `ldexp(x, i)` | `x * (2**i)`, inverse of function `frexp()` |
| `nextafter(x, y, steps)` | Floating-point value *steps* steps after *x* towards *y* |
| `ulp(x)` | Value of the least significant bit of *x* |
| **Power, exponential and logarithmic functions** |  |
| `cbrt(x)` | Cube root of *x* |
| `exp(x)` | *e* raised to the power *x* |
| `exp2(x)` | *2* raised to the power *x* |
| `expm1(x)` | *e* raised to the power *x*, minus 1 |
| `log(x, base)` | Logarithm of *x* to the given base (*e* by default) |
| `log1p(x)` | Natural logarithm of *1+x* (base *e*) |
| `log2(x)` | Base-2 logarithm of *x* |
| `log10(x)` | Base-10 logarithm of *x* |
| `pow(x, y)` | *x* raised to the power *y* |
| `sqrt(x)` | Square root of *x* |
| **Summation and product functions** |  |
| `dist(p, q)` | Euclidean distance between two points *p* and *q* given as an iterable of coordinates |
| `fsum(iterable)` | Sum of values in the input *iterable* |
| `hypot(*coordinates)` | Euclidean norm of an iterable of coordinates |
| `prod(iterable, start)` | Product of elements in the input *iterable* with a *start* value |
| `sumprod(p, q)` | Sum of products from two iterables *p* and *q* |
| **Angular conversion** |  |
| `degrees(x)` | Convert angle *x* from radians to degrees |
| `radians(x)` | Convert angle *x* from degrees to radians |
| **Trigonometric functions** |  |
| `acos(x)` | Arc cosine of *x* |
| `asin(x)` | Arc sine of *x* |
| `atan(x)` | Arc tangent of *x* |
| `atan2(y, x)` | `atan(y / x)` |
| `cos(x)` | Cosine of *x* |
| `sin(x)` | Sine of *x* |
| `tan(x)` | Tangent of *x* |
| **Hyperbolic functions** |  |
| `acosh(x)` | Inverse hyperbolic cosine of *x* |
| `asinh(x)` | Inverse hyperbolic sine of *x* |
| `atanh(x)` | Inverse hyperbolic tangent of *x* |
| `cosh(x)` | Hyperbolic cosine of *x* |
| `sinh(x)` | Hyperbolic sine of *x* |
| `tanh(x)` | Hyperbolic tangent of *x* |
| **Special functions** |  |
| `erf(x)` | [Error function](https://en.wikipedia.org/wiki/Error_function) at *x* |
| `erfc(x)` | [Complementary error function](https://en.wikipedia.org/wiki/Error_function) at *x* |
| `gamma(x)` | [Gamma function](https://en.wikipedia.org/wiki/Gamma_function) at *x* |
| `lgamma(x)` | Natural logarithm of the absolute value of the [Gamma function](https://en.wikipedia.org/wiki/Gamma_function) at *x* |
| **Constants** |  |
| `pi` | *π* = 3.141592… |
| `e` | *e* = 2.718281… |
| `tau` | *τ* = 2*π* = 6.283185… |
| `inf` | Positive infinity |
| `nan` | “Not a number” (NaN) |


---

## Screenshot

![Screenshot](https://github.com/user-attachments/assets/f3dfd33a-58d8-4d2a-854c-c6f12a868a77)

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
