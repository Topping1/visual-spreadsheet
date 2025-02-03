import sys
import math
import ast
import xml.etree.ElementTree as ET

from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QPen, QBrush, QPainter, QPainterPath
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsScene, QGraphicsView,
    QGraphicsRectItem, QGraphicsLineItem, QGraphicsTextItem,
    QGraphicsItem, QToolBar, QAction, QFileDialog, QInputDialog
)

# ---------------------------
# IF helper function
# ---------------------------
def IF(condition, val_if_true, val_if_false):
    """Return val_if_true if condition is True, otherwise val_if_false."""
    return val_if_true if condition else val_if_false

# ---------------------------
# AST Transformer: Convert '^' to '**'
# ---------------------------
class XorToPow(ast.NodeTransformer):
    def visit_BinOp(self, node):
        self.generic_visit(node)
        # Convert bitwise XOR (^) into exponentiation (**)
        if isinstance(node.op, ast.BitXor):
            node.op = ast.Pow()
        return node

# ---------------------------
# Helper functions for formulas
# ---------------------------
def get_dependencies(expr):
    """
    Parse a Python expression (given as a string) and return a set
    of all variable names referenced. (These will be interpreted as names
    of other elements.)
    """
    try:
        tree = ast.parse(expr, mode='eval')
    except Exception:
        return set()
    return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}

def evaluate_element(element, computed, stack, element_dict):
    """
    Recursively evaluate the element’s content.
    
    If the content is a number, simply return it (as float). Otherwise,
    treat it as a Python expression. Variable names in the expression
    are looked up in element_dict. The 'computed' dict caches already
    computed results. 'stack' is used to detect circular dependencies.
    """
    if element.name in computed:
        return computed[element.name]
    if element.name in stack:
        raise Exception("Circular dependency detected for element: " + element.name)
    stack.add(element.name)

    content = element.content
    try:
        # Try to convert to a number first.
        result = float(content)
    except Exception:
        # Otherwise, treat it as a formula.
        deps = get_dependencies(content)
        env = {}
        for dep in deps:
            # Skip 'math' and 'IF' because they are provided in our globals_dict
            # and are not "elements" in the diagram.
            if dep in ("math", "IF"):
                continue

            if dep in element_dict:
                env[dep] = evaluate_element(element_dict[dep], computed, stack, element_dict)
            else:
                raise Exception(f"Unknown variable: {dep}")

        try:
            # Parse the expression and transform '^' to '**'
            tree = ast.parse(content, mode='eval')
            tree = XorToPow().visit(tree)
            ast.fix_missing_locations(tree)

            # We allow math functions & IF by adding them to globals.
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
    """
    Iterate through all elements (a dict mapping name -> element)
    and update their result by evaluating their content.
    """
    computed = {}
    for name, element in element_dict.items():
        try:
            val = evaluate_element(element, computed, set(), element_dict)
            element.result = val
        except Exception as e:
            element.result = str(e)
        element.update_display()

# ---------------------------
# Graphics item for an element (cell)
# ---------------------------
class VisualElementItem(QGraphicsRectItem):
    def __init__(self, name, content, rect):
        super().__init__(rect)
        self.name = name
        self.content = content  # A string – either a number or a Python expression.
        self.result = ""
        self.setFlags(QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemSendsGeometryChanges)
        self.setBrush(QBrush(Qt.white))
        self.setPen(QPen(Qt.black))

        # Use a QGraphicsTextItem to display three lines:
        # 1. Name (in bold)
        # 2. Content (prefixed with "= ")
        # 3. Result (prefixed with "Result: ")
        self.text_item = QGraphicsTextItem(self)
        self.text_item.setPos(rect.x() + 5, rect.y() + 5)
        self.update_display()
        self.setAcceptHoverEvents(True)

    def update_display(self):
        """Update the displayed text and tooltip of the element."""
        tip = f"Name: {self.name}\nContent: {self.content}\nResult: {self.result}"
        self.setToolTip(tip)
        html = f"<b>{self.name}</b><br>= {self.content}<br>Result: {self.result}"
        self.text_item.setHtml(html)

    def mouseDoubleClickEvent(self, event):
        new_content, ok = QInputDialog.getText(None, "Edit Element", "Enter content:", text=self.content)
        if ok:
            self.content = new_content
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
        self.source = source   # The element providing the value.
        self.target = target   # The element that uses the value.
        self.setPen(QPen(Qt.blue, 2, Qt.SolidLine))
        self.setZValue(-1)     # Draw behind the elements.
        self.update_position()

    def update_position(self):
        """Set the line from the center of the source to the center of the target."""
        if self.source and self.target:
            source_center = self.source.sceneBoundingRect().center()
            target_center = self.target.sceneBoundingRect().center()
            self.setLine(source_center.x(), source_center.y(), target_center.x(), target_center.y())

    def paint(self, painter, option, widget):
        line = self.line()
        painter.setPen(self.pen())
        painter.drawLine(line)
        
        # Compute the midpoint of the line.
        mid = QPointF((line.x1() + line.x2()) / 2, (line.y1() + line.y2()) / 2)
        
        # Compute the angle of the line.
        angle = math.atan2(line.dy(), line.dx())
        arrow_size = 15
        
        # Compute the base center of the arrow (shifted backward from the tip along the line direction).
        tip = mid
        base_center = tip - QPointF(math.cos(angle), math.sin(angle)) * arrow_size
        
        # Determine the left and right corners of the arrow base.
        left = base_center + QPointF(math.cos(angle + math.pi/2), math.sin(angle + math.pi/2)) * (arrow_size / 2)
        right = base_center + QPointF(math.cos(angle - math.pi/2), math.sin(angle - math.pi/2)) * (arrow_size / 2)
        
        # Create the arrowhead as a closed triangle.
        arrow_head = QPainterPath()
        arrow_head.moveTo(tip)
        arrow_head.lineTo(left)
        arrow_head.lineTo(right)
        arrow_head.closeSubpath()
        
        painter.setBrush(QBrush(self.pen().color()))
        painter.drawPath(arrow_head)

# ---------------------------
# Main application window
# ---------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visual Spreadsheet")
        self.resize(800, 600)

        # Create a very large scene to simulate an "infinite" white canvas.
        self.scene = QGraphicsScene(-5000, -5000, 10000, 10000)
        self.view = QGraphicsView(self.scene)
        # Force full viewport updates to reduce ghosting artifacts.
        self.view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setCentralWidget(self.view)

        # Dictionaries for elements and connections.
        self.elements = {}       # Maps element names to VisualElementItem objects.
        self.connections = []    # List of ConnectionLine objects.
        self.element_counter = 1

        # Build a toolbar with actions.
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

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

        self.scene.parent = self

    def new_canvas(self):
        self.scene.clear()
        self.elements.clear()
        self.connections.clear()
        self.element_counter = 1

    def save_canvas(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Canvas", "", "XML Files (*.xml)")
        if filename:
            root = ET.Element("Canvas")
            for name, element in self.elements.items():
                elem = ET.SubElement(root, "Element")
                elem.set("name", element.name)
                elem.set("content", element.content)
                pos = element.pos()
                elem.set("x", str(pos.x()))
                elem.set("y", str(pos.y()))
            tree = ET.ElementTree(root)
            tree.write(filename)
            print(f"Saved canvas to {filename}")

    def load_canvas(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Canvas", "", "XML Files (*.xml)")
        if filename:
            self.new_canvas()
            tree = ET.parse(filename)
            root = tree.getroot()
            for elem in root.findall("Element"):
                name = elem.get("name")
                content = elem.get("content")
                x = float(elem.get("x"))
                y = float(elem.get("y"))
                rect = QRectF(0, 0, 120, 70)  # Adjusted size for three lines of text.
                ve = VisualElementItem(name, content, rect)
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
        rect = QRectF(0, 0, 120, 70)
        ve = VisualElementItem(name, "0", rect)
        ve.setPos(0, 0)
        self.scene.addItem(ve)
        self.elements[name] = ve
        self.recalculate_all()

    def recalculate_all(self):
        recalc_all(self.elements)
        self.update_all_connections()

    def update_all_connections(self):
        # Remove all existing connection lines.
        for conn in self.connections:
            self.scene.removeItem(conn)
        self.connections.clear()
        # Create new connection lines based on each element's formula dependencies.
        for element in self.elements.values():
            deps = get_dependencies(element.content)
            for dep in deps:
                # Exclude 'math' and 'IF' from dependencies, they are built-ins, not element names.
                if dep in ("math", "IF"):
                    continue
                if dep in self.elements:
                    source = self.elements[dep]
                    target = element
                    cl = ConnectionLine(source, target)
                    self.scene.addItem(cl)
                    self.connections.append(cl)

    def update_connections(self):
        for conn in self.connections:
            conn.update_position()

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
                if conn.source.name in removed_names or conn.target.name in removed_names:
                    self.scene.removeItem(conn)
                    self.connections.remove(conn)
            self.recalculate_all()
        else:
            super().keyPressEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
