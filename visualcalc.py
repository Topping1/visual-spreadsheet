import sys
import math
import ast
import xml.etree.ElementTree as ET
from html import escape

from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QPen, QBrush, QPainter, QPainterPath, QColor
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsScene, QToolBar, QAction,
    QFileDialog, QInputDialog, QLineEdit, QMessageBox, QColorDialog,
    QGraphicsItem, QGraphicsRectItem, QGraphicsLineItem, QGraphicsTextItem,
    QGraphicsView
)

# ---------------------------
# Custom QGraphicsView to handle Ctrl+MouseWheel zoom
# ---------------------------
class ZoomableGraphicsView(QGraphicsView):
    def wheelEvent(self, event):
        """Override wheelEvent to zoom if Ctrl is held; else default scroll."""
        if event.modifiers() & Qt.ControlModifier:
            # Zoom in/out
            if event.angleDelta().y() > 0:  # wheel up
                scale_factor = 1.25
            else:  # wheel down
                scale_factor = 0.8
            self.scale(scale_factor, scale_factor)
        else:
            super().wheelEvent(event)

# ---------------------------
# IF helper function
# ---------------------------
def IF(condition, val_if_true, val_if_false):
    return val_if_true if condition else val_if_false

# ---------------------------
# AST Transformer: Convert '^' to '**'
# ---------------------------
class XorToPow(ast.NodeTransformer):
    def visit_BinOp(self, node):
        self.generic_visit(node)
        if isinstance(node.op, ast.BitXor):
            node.op = ast.Pow()
        return node

# ---------------------------
# Helper functions for formulas
# ---------------------------
def get_dependencies(expr):
    try:
        tree = ast.parse(expr, mode='eval')
    except Exception:
        return set()
    return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}

def evaluate_element(element, computed, stack, element_dict):
    if element.name in computed:
        return computed[element.name]
    if element.name in stack:
        raise Exception("Circular dependency detected for element: " + element.name)
    stack.add(element.name)

    content = element.content
    try:
        # If it's purely numeric, parse as float:
        result = float(content)
    except Exception:
        # Otherwise, treat it as a formula
        deps = get_dependencies(content)
        env = {}
        for dep in deps:
            if dep in ("math", "IF"):
                continue
            if dep in element_dict:
                env[dep] = evaluate_element(element_dict[dep], computed, stack, element_dict)
            else:
                raise Exception(f"Unknown variable: {dep}")

        try:
            tree = ast.parse(content, mode='eval')
            tree = XorToPow().visit(tree)
            ast.fix_missing_locations(tree)
            globals_dict = {
                "__builtins__": {},
                "math": math,
                "IF": IF
            }
            result = eval(compile(tree, filename="<ast>", mode="eval"), globals_dict, env)
        except Exception as e:
            raise Exception(f"Error evaluating formula: {e}")

    computed[element.name] = result
    stack.remove(element.name)
    return result

def recalc_all(element_dict):
    computed = {}
    for name, element in element_dict.items():
        try:
            val = evaluate_element(element, computed, set(), element_dict)
            element.raw_result = val
            element.result = val  # Will be re‐formatted if needed
        except Exception as e:
            element.raw_result = None
            element.result = str(e)
        element.update_display()

# ---------------------------
# Graphics item for an element (cell)
# ---------------------------
class VisualElementItem(QGraphicsRectItem):
    def __init__(self, name, content, rect, description="", brush_color=Qt.white):
        super().__init__(rect)
        self.name = name
        self.content = content
        self.description = description
        self.result = ""
        self.raw_result = None
        self.setFlags(QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemSendsGeometryChanges)

        # Use the passed-in background color
        self.setBrush(QBrush(brush_color))
        self.setPen(QPen(Qt.black))

        # We'll display four lines in HTML:
        # 1) <b>Name</b>
        # 2) Desc
        # 3) = content (styled somewhat "pretty")
        # 4) Result
        self.text_item = QGraphicsTextItem(self)
        self.text_item.setPos(rect.x() + 5, rect.y() + 5)
        self.update_display()
        self.setAcceptHoverEvents(True)

    def update_background(self, brush_color):
        """Change the brush color (called from MainWindow when user picks a new color)."""
        self.setBrush(QBrush(brush_color))

    def update_display(self):
        """Update the displayed text and tooltip of the element, escaping HTML.
           Apply a bit of styling to formula line for a 'latex-like' feel.
        """
        esc_name = escape(self.name)
        esc_desc = escape(self.description)
        esc_content = escape(self.content)
        esc_result = escape(str(self.result))

        # Minimal "pretty" styling for formula line: italic, colored
        # (Not real LaTeX, but a small improvement)
        pretty_formula = f"<span style='font-family:\"Times\"; font-style:italic; color:#005000;'>{esc_content}</span>"

        # Tooltip is plain text
        tip = (f"Name: {self.name}\n"
               f"Description: {self.description}\n"
               f"Content: {self.content}\n"
               f"Result: {self.result}")
        self.setToolTip(tip)

        # HTML for the item
        html = (f"<b>{esc_name}</b><br>"
                f"Desc: {esc_desc}<br>"
                f"= {pretty_formula}<br>"
                f"Result: {esc_result}")
        self.text_item.setHtml(html)

    def mouseDoubleClickEvent(self, event):
        new_content, ok = QInputDialog.getText(
            None, "Edit Element Content",
            "Enter formula or numeric value:",
            text=self.content
        )
        if ok:
            self.content = new_content

        new_desc, ok = QInputDialog.getText(
            None, "Edit Element Description",
            "Enter description:",
            text=self.description
        )
        if ok:
            self.description = new_desc

        self.update_display()
        if self.scene() and hasattr(self.scene(), 'parent'):
            self.scene().parent.recalculate_all()

        super().mouseDoubleClickEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            if self.scene() and hasattr(self.scene(), 'parent'):
                self.scene().parent.update_connections()
        return super().itemChange(change, value)

# ---------------------------
# Graphics item for a connection (arrowed line)
# ---------------------------
class ConnectionLine(QGraphicsLineItem):
    def __init__(self, source, target):
        super().__init__()
        self.source = source
        self.target = target
        self.setPen(QPen(Qt.blue, 2, Qt.SolidLine))
        self.setZValue(-1)
        self.update_position()

    def update_position(self):
        """Set the line from the center of the source to the center of the target."""
        if self.source and self.target:
            s_center = self.source.sceneBoundingRect().center()
            t_center = self.target.sceneBoundingRect().center()
            self.setLine(s_center.x(), s_center.y(), t_center.x(), t_center.y())

    def paint(self, painter, option, widget):
        line = self.line()
        painter.setPen(self.pen())
        painter.drawLine(line)

        mid = QPointF((line.x1() + line.x2()) / 2, (line.y1() + line.y2()) / 2)
        angle = math.atan2(line.dy(), line.dx())
        arrow_size = 15

        tip = mid
        base_center = tip - QPointF(math.cos(angle), math.sin(angle)) * arrow_size
        left = base_center + QPointF(math.cos(angle + math.pi/2), math.sin(angle + math.pi/2)) * (arrow_size / 2)
        right = base_center + QPointF(math.cos(angle - math.pi/2), math.sin(angle - math.pi/2)) * (arrow_size / 2)

        path = QPainterPath()
        path.moveTo(tip)
        path.lineTo(left)
        path.lineTo(right)
        path.closeSubpath()

        painter.setBrush(QBrush(self.pen().color()))
        painter.drawPath(path)

# ---------------------------
# Main application window
# ---------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visual Spreadsheet")
        self.resize(800, 600)

        # Use our ZoomableGraphicsView
        self.scene = QGraphicsScene(-5000, -5000, 10000, 10000)
        self.view = ZoomableGraphicsView(self.scene)
        self.view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setCentralWidget(self.view)

        self.elements = {}
        self.connections = []
        self.element_counter = 1

        # Format and decimals
        self.current_format = "NONE"  # "NONE", "SCI", "FIX"
        self.decimals = 3

        # NEW: Store a global background color for all elements
        self.global_bgcolor = QColor(Qt.white)  # default white

        # Build toolbar
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        # Give the toolbar/toolbuttons a style so each button is "boxed"
        toolbar.setStyleSheet("""
            QToolBar {
                border: 1px solid gray;
            }
            QToolButton {
                border: 1px solid #ccc;
                margin: 2px;
                padding: 4px;
            }
        """)

        new_action = QAction("New", self)
        new_action.triggered.connect(self.new_canvas)
        toolbar.addAction(new_action)

        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_canvas)
        toolbar.addAction(save_action)

        load_action = QAction("Load", self)
        load_action.triggered.connect(self.load_canvas)
        toolbar.addAction(load_action)

        add_element_action = QAction("Add Element", self)
        add_element_action.triggered.connect(self.add_element)
        toolbar.addAction(add_element_action)

        center_action = QAction("Center", self)
        center_action.triggered.connect(self.center_canvas)
        toolbar.addAction(center_action)

        sci_action = QAction("SCI", self)
        sci_action.triggered.connect(self.set_sci_format)
        toolbar.addAction(sci_action)

        fix_action = QAction("FIX", self)
        fix_action.triggered.connect(self.set_fix_format)
        toolbar.addAction(fix_action)

        # Add a small text box for decimals
        self.decimals_box = QLineEdit(self)
        self.decimals_box.setFixedWidth(40)
        self.decimals_box.setPlaceholderText("dec")
        self.decimals_box.setText(str(self.decimals))
        toolbar.addWidget(self.decimals_box)

        # NEW: Add a "BG Color" button for picking background color
        bg_color_action = QAction("BG Color", self)
        bg_color_action.triggered.connect(self.pick_bg_color)
        toolbar.addAction(bg_color_action)

        self.scene.parent = self

    # ---------------------------
    # Canvas management
    # ---------------------------
    def new_canvas(self):
        self.scene.clear()
        self.elements.clear()
        self.connections.clear()
        self.element_counter = 1
        self.current_format = "NONE"
        self.decimals = 3
        self.decimals_box.setText(str(self.decimals))
        self.global_bgcolor = QColor(Qt.white)

    def save_canvas(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Canvas", "", "XML Files (*.xml)")
        if not filename:
            return
        root = ET.Element("Canvas")
        root.set("format", self.current_format)
        root.set("decimals", str(self.decimals))
        # Save global BG color as #RRGGBB
        root.set("bgcolor", self.global_bgcolor.name())

        for name, element in self.elements.items():
            elem = ET.SubElement(root, "Element")
            elem.set("name", element.name)
            elem.set("content", element.content)
            elem.set("description", element.description)
            pos = element.pos()
            elem.set("x", str(pos.x()))
            elem.set("y", str(pos.y()))
        tree = ET.ElementTree(root)
        tree.write(filename)
        print(f"Saved canvas to {filename}")

    def load_canvas(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Canvas", "", "XML Files (*.xml)")
        if not filename:
            return
        self.new_canvas()
        tree = ET.parse(filename)
        root = tree.getroot()
        self.current_format = root.get("format", "NONE")
        self.decimals = int(root.get("decimals", "3"))
        self.decimals_box.setText(str(self.decimals))

        # Load BG color
        bg_hex = root.get("bgcolor", "#ffffff")
        self.global_bgcolor = QColor(bg_hex)

        for elem in root.findall("Element"):
            name = elem.get("name")
            content = elem.get("content")
            description = elem.get("description", "")
            x = float(elem.get("x"))
            y = float(elem.get("y"))
            rect = QRectF(0, 0, 120, 80)
            ve = VisualElementItem(
                name, content, rect,
                description=description,
                brush_color=self.global_bgcolor  # use global BG color
            )
            ve.setPos(x, y)
            self.scene.addItem(ve)
            self.elements[name] = ve
            try:
                num = int(name[1:])
                if num >= self.element_counter:
                    self.element_counter = num + 1
            except Exception:
                pass
        self.recalculate_all()

    def add_element(self):
        name = "E" + str(self.element_counter)
        self.element_counter += 1
        rect = QRectF(0, 0, 120, 80)
        ve = VisualElementItem(
            name, "0", rect,
            description="",
            brush_color=self.global_bgcolor
        )
        ve.setPos(0, 0)
        self.scene.addItem(ve)
        self.elements[name] = ve
        self.recalculate_all()

    def recalculate_all(self):
        recalc_all(self.elements)
        self.update_all_connections()
        self.apply_current_format_to_all()

    def update_all_connections(self):
        for c in self.connections:
            self.scene.removeItem(c)
        self.connections.clear()
        for element in self.elements.values():
            deps = get_dependencies(element.content)
            for dep in deps:
                if dep in ("math", "IF"):
                    continue
                if dep in self.elements:
                    source = self.elements[dep]
                    target = element
                    cl = ConnectionLine(source, target)
                    self.scene.addItem(cl)
                    self.connections.append(cl)

    def update_connections(self):
        for c in self.connections:
            c.update_position()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            removed_names = set()
            for item in self.scene.selectedItems():
                if isinstance(item, VisualElementItem):
                    removed_names.add(item.name)
                    self.scene.removeItem(item)
                    if item.name in self.elements:
                        del self.elements[item.name]
            for conn in self.connections[:]:
                if (conn.source and conn.source.name in removed_names) or \
                   (conn.target and conn.target.name in removed_names):
                    self.scene.removeItem(conn)
                    self.connections.remove(conn)
            self.recalculate_all()
        else:
            super().keyPressEvent(event)

    # ---------------------------
    # "Center" button action
    # ---------------------------
    def center_canvas(self):
        """Center the view on the origin (0, 0)."""
        self.view.centerOn(0, 0)

    # ---------------------------
    # Global background color
    # ---------------------------
    def pick_bg_color(self):
        """Open a color dialog to pick the background color of all elements."""
        color = QColorDialog.getColor(self.global_bgcolor, self, "Select Background Color")
        if not color.isValid():
            return
        self.global_bgcolor = color
        # Update all elements
        for element in self.elements.values():
            element.update_background(self.global_bgcolor)

    # ---------------------------
    # Formatting / decimals
    # ---------------------------
    def set_sci_format(self):
        if not self.read_decimals_box():
            return
        self.current_format = "SCI"
        self.apply_current_format_to_all()

    def set_fix_format(self):
        if not self.read_decimals_box():
            return
        self.current_format = "FIX"
        self.apply_current_format_to_all()

    def read_decimals_box(self):
        text_val = self.decimals_box.text().strip()
        if not text_val:
            QMessageBox.warning(self, "Invalid Input", "Please enter the number of decimals.")
            return False
        try:
            val = int(text_val)
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", f"'{text_val}' is not a valid integer.")
            return False
        self.decimals = val
        return True

    def apply_current_format_to_all(self):
        for element in self.elements.values():
            if isinstance(element.raw_result, (int, float)):
                if self.current_format == "SCI":
                    fmt_str = f".{self.decimals}e"
                    element.result = format(element.raw_result, fmt_str)
                elif self.current_format == "FIX":
                    fmt_str = f".{self.decimals}f"
                    element.result = format(element.raw_result, fmt_str)
                else:
                    element.result = str(element.raw_result)
            elif isinstance(element.raw_result, bool):
                element.result = str(element.raw_result)
            # If it's None or an exception string, leave as-is
            element.update_display()

# ---------------------------
# Entry Point
# ---------------------------
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
