import sys
import csv
import json
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QSpinBox,
    QComboBox,
    QLineEdit,
    QMessageBox,
    QCheckBox,
    QRadioButton,
    QButtonGroup,
    QInputDialog,
)
from PyQt6.QtCore import Qt, QPointF, QSizeF, QRectF
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtGui import (
    QImage,
    QPainter,
    QPixmap,
    QPdfWriter,
    QPainterPath,
    QFont,
    QFontDatabase,
    QColor,
)
import numpy as np
from PIL import Image

DEMO_CSV_FILE = "demo_data.csv"
DEMO_TEMPLATE_FILE = "demo_template.json"

class CardTemplate:
    def __init__(self, file_path=None):
        if file_path:
            self.load_from_json(file_path)

        self.width = 825  # 2.75" at 300dpi
        self.height = 1125  # 3.75" at 300dpi
        self.bleed = 75  # 0.25" bleed
        self.layers = []
        self.data_fields = []
        self.fonts = {}

    def load_from_json(self, file_path):
        with open(file_path, "r") as f:
            data = json.load(f)

        self.width = data["width"]
        self.height = data["height"]
        self.bleed = data["bleed"]
        self.layers = [
            {
                "path": layer["path"],
                "type": layer["type"],
                "position": layer["position"],
                "order": layer["order"],
            }
            for layer in data["layers"]
        ]
        self.data_fields = data["data_fields"]
        self.fonts = data["fonts"]

    def save_to_json(self, file_path):
        data = {
            "width": self.width,
            "height": self.height,
            "bleed": self.bleed,
            "layers": [
                {
                    "path": layer["path"],
                    "type": layer["type"],
                    "position": layer["position"],
                    "order": layer["order"],
                }
                for layer in self.layers
            ],
            "data_fields": self.data_fields,
            "fonts": self.fonts,
        }
        with open(file_path, "w") as f:
            json.dump(data, f)

    def add_layer(self, path, layer_type, position=(0, 0)):
        self.layers.append(
            {
                "path": path,
                "type": layer_type,  # 'svg', 'png', or 'mask'
                "position": position,
                "order": len(self.layers),  # Add order for reordering
            }
        )
        self.layers = sorted(self.layers, key=lambda x: x["order"])  # Sort layers

    def set_data_fields(self, fields):
        self.data_fields = fields

    def add_font(self, path):
        id = QFontDatabase.addApplicationFont(path)
        if id != -1:
            self.fonts[path] = QFontDatabase.applicationFontFamilies(id)[0]
        else:
            QMessageBox.warning(None, "Warning", "Failed to load font.")

class CardMaker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.template = CardTemplate(DEMO_TEMPLATE_FILE)
        self.card_data = []
        self.undo_stack = []
        self.redo_stack = []
        self.demo_data_loaded = False
        self.initUI()

    def initUI(self):
        self.setWindowTitle("CardMaker")
        self.setGeometry(100, 100, 1200, 800)

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout()
        main_widget.setLayout(layout)

        # Left panel for controls
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)

        # Template controls
        template_group = QWidget()
        template_layout = QVBoxLayout()
        template_group.setLayout(template_layout)

        # Add template buttons
        load_template_btn = QPushButton("Load Template")
        load_template_btn.clicked.connect(self.load_template)
        template_layout.addWidget(load_template_btn)

        add_layer_btn = QPushButton("Add Layer")
        add_layer_btn.clicked.connect(self.add_layer)
        template_layout.addWidget(add_layer_btn)

        # Card size controls
        size_group = QWidget()
        size_layout = QHBoxLayout()
        size_group.setLayout(size_layout)

        self.width_spin = QSpinBox()
        self.width_spin.setRange(100, 3000)
        self.width_spin.setValue(self.template.width)
        self.width_spin.valueChanged.connect(self.update_card_size)

        self.height_spin = QSpinBox()
        self.height_spin.setRange(100, 3000)
        self.height_spin.setValue(self.template.height)
        self.height_spin.valueChanged.connect(self.update_card_size)

        size_layout.addWidget(QLabel("Width:"))
        size_layout.addWidget(self.width_spin)
        size_layout.addWidget(QLabel("Height:"))
        size_layout.addWidget(self.height_spin)

        template_layout.addWidget(size_group)

        # Data controls
        data_group = QWidget()
        data_layout = QVBoxLayout()
        data_group.setLayout(data_layout)

        load_data_btn = QPushButton("Import Data (CSV/Excel)")
        load_data_btn.clicked.connect(self.load_data)
        data_layout.addWidget(load_data_btn)

        self.data_table = QTableWidget()
        data_layout.addWidget(self.data_table)

        # Demo data checkbox
        demo_data_checkbox = QCheckBox("Use Demo Data")
        demo_data_checkbox.setChecked(True)
        demo_data_checkbox.stateChanged.connect(self.toggle_demo_data)
        data_layout.addWidget(demo_data_checkbox)

        # Data field controls
        data_fields_group = QWidget()
        data_fields_layout = QVBoxLayout()
        data_fields_group.setLayout(data_fields_layout)

        self.data_fields_combo = QComboBox()
        self.data_fields_combo.addItems(self.template.data_fields)
        data_fields_layout.addWidget(self.data_fields_combo)

        add_data_field_btn = QPushButton("Add Data Field")
        add_data_field_btn.clicked.connect(self.add_data_field)
        data_fields_layout.addWidget(add_data_field_btn)

        remove_data_field_btn = QPushButton("Remove Data Field")
        remove_data_field_btn.clicked.connect(self.remove_data_field)
        data_fields_layout.addWidget(remove_data_field_btn)

        data_layout.addWidget(data_fields_group)

        left_layout.addWidget(template_group)
        left_layout.addWidget(data_group)

        # Export controls
        export_group = QWidget()
        export_layout = QVBoxLayout()
        export_group.setLayout(export_layout)

        export_png_btn = QPushButton("Export PNG")
        export_png_btn.clicked.connect(self.export_png)
        export_layout.addWidget(export_png_btn)

        export_pdf_btn = QPushButton("Export PDF (with bleeds)")
        export_pdf_btn.clicked.connect(self.export_pdf)
        export_layout.addWidget(export_pdf_btn)

        left_layout.addWidget(export_group)

        # Right panel for card preview
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.preview_label)

        # Add panels to main layout
        layout.addWidget(left_panel, 1)
        layout.addWidget(right_panel, 2)

        self.update_preview()

    def toggle_demo_data(self, state):
        if state == Qt.CheckState.Checked:
            self.load_demo_data()
        else:
            self.card_data = []

        self.update_data_table()
        self.update_preview()

    def load_demo_data(self):
        if not self.demo_data_loaded:
            df = pd.read_csv(DEMO_CSV_FILE)
            self.card_data = df.to_dict("records")
            self.demo_data_loaded = True

    def load_template(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Load Template", "", "JSON files (*.json);;SVG files (*.svg)"
        )
        if file_name:
            if file_name.endswith(".json"):
                self.template.load_from_json(file_name)
            elif file_name.endswith(".svg"):
                self.template.add_layer(file_name, "svg")
            self.update_layers_table()
            self.update_preview()

    def add_layer(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Add Layer", "", "Image files (*.png *.svg)"
        )
        if file_name:
            layer_type = "svg" if file_name.lower().endswith(".svg") else "png"
            self.template.add_layer(file_name, layer_type)
            self.update_layers_table()
            self.update_preview()

    def load_data(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Import Data", "", "CSV files (*.csv);;Excel files (*.xlsx)"
        )
        if file_name:
            if file_name.lower().endswith(".csv"):
                df = pd.read_csv(file_name)
            else:
                df = pd.read_excel(file_name)

            self.card_data = df.to_dict("records")
            self.demo_data_loaded = False
            self.update_data_table()
            self.update_preview()

    def update_data_table(self):
        if not self.card_data:
            return

        self.data_table.setRowCount(len(self.card_data))
        self.data_table.setColumnCount(len(self.card_data[0]))
        self.data_table.setHorizontalHeaderLabels(self.card_data[0].keys())

        for i, card in enumerate(self.card_data):
            for j, (key, value) in enumerate(card.items()):
                self.data_table.setItem(i, j, QTableWidgetItem(str(value)))

    def update_card_size(self):
        self.template.width = self.width_spin.value()
        self.template.height = self.height_spin.value()
        self.update_preview()

    def render_card(self, card_data=None, include_bleed=False, font="Default"):
        width = self.template.width
        height = self.template.height

        if include_bleed:
            width += 2 * self.template.bleed
            height += 2 * self.template.bleed

        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw layers
        for layer in self.template.layers:
            if layer["type"] == "svg":
                renderer = QSvgRenderer(layer["path"])
                renderer.render(painter)
            elif layer["type"] == "png":
                pixmap = QPixmap(layer["path"])
                painter.drawPixmap(
                    QPointF(layer["position"][0], layer["position"][1]),
                    pixmap,
                )

        # Draw card data if provided
        if card_data:
            font_id = self.template.fonts.get(font, QFont("Default"))
            font = QFont(font_id)
            font.setPointSize(24)  # Change font size

            painter.setFont(font)
            painter.setPen(QColor("black"))

            text_rect = QRectF(
                self.template.bleed,
                self.template.bleed,
                width - 2 * self.template.bleed,
                height - 2 * self.template.bleed,
            )
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "\n".join(str(value) for value in card_data.values()))

        painter.end()
        return image

    def update_preview(self):
        image = self.render_card(self.card_data[0] if self.card_data else None)
        pixmap = QPixmap.fromImage(image)
        scaled_pixmap = pixmap.scaled(
            self.preview_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.preview_label.setPixmap(scaled_pixmap)

    def export_png(self):
        if not self.card_data:
            return

        dir_name = QFileDialog.getExistingDirectory(
            self, "Select Export Directory"
        )
        if dir_name:
            for i, card in enumerate(self.card_data):
                image = self.render_card(card)
                image.save(f"{dir_name}/card_{i+1}.png")

    def export_pdf(self):
        if not self.card_data:
            return

        file_name, _ = QFileDialog.getSaveFileName(
            self, "Export PDF", "", "PDF files (*.pdf)"
        )
        if file_name:
            writer = QPdfWriter(file_name)
            writer.setPageSize(QPdfWriter.PageSize.Custom)
            writer.setPageSizeMM(QSizeF(self.template.width + 2 * self.template.bleed, self.template.height + 2 * self.template.bleed))

            painter = QPainter(writer)
            for card in self.card_data:
                image = self.render_card(card, include_bleed=True)
                painter.drawImage(QPointF(0, 0), image)
                writer.newPage()
            painter.end()

    # Undo and redo methods
    def undo(self):
        if self.undo_stack:
            action = self.undo_stack.pop()
            self.redo_stack.append(action)
            action.undo(self)

            self.update_preview()

    def redo(self):
        if self.redo_stack:
            action = self.redo_stack.pop()
            self.undo_stack.append(action)
            action.redo(self)

            self.update_preview()

    # Define base Action class for undo/redo
    class Action:
        def undo(self, card_maker):
            pass

        def redo(self, card_maker):
            pass

    # Define specific actions for undo/redo
    class AddLayerAction(Action):
        def __init__(self, card_maker, path, layer_type, position):
            self.card_maker = card_maker
            self.path = path
            self.layer_type = layer_type
            self.position = position

        def undo(self, card_maker):
            card_maker.template.layers.remove(
                next(
                    (layer for layer in card_maker.template.layers if layer["path"] == self.path),
                    None,
                )
            )
            card_maker.update_layers_table()
            card_maker.update_preview()

        def redo(self, card_maker):
            card_maker.template.add_layer(self.path, self.layer_type, self.position)
            card_maker.update_layers_table()
            card_maker.update_preview()

    # ... (add other actions like SetDataFieldsAction, AddFontAction, etc.)

    # Update methods to use actions for undo/redo
    def add_layer(self):
        # ... (add_layer method remains the same)

        file_name, _ = QFileDialog.getOpenFileName(
            self, "Add Layer", "", "Image files (*.png *.svg)"
        )
        if file_name:
            layer_type = "svg" if file_name.lower().endswith(".svg") else "png"
            position = (0, 0)  # Default position

            action = self.AddLayerAction(self, file_name, layer_type, position)
            self.undo_stack.append(action)

    # ... (update other methods to use actions for undo/redo)

    def add_data_field(self):
        field_name, ok = QInputDialog.getText(
            self, "Add Data Field", "Enter the new data field name:"
        )
        if ok and field_name:
            self.template.data_fields.append(field_name)
            self.data_fields_combo.addItem(field_name)
            self.update_data_table()

    def remove_data_field(self):
        selected_field = self.data_fields_combo.currentText()
        if selected_field:
            self.template.data_fields.remove(selected_field)
            self.data_fields_combo.removeItem(self.data_fields_combo.findText(selected_field))
            self.update_data_table()

    def update_layers_table(self):
        self.layers_table.setRowCount(len(self.template.layers))
        self.layers_table.setColumnCount(4)
        self.layers_table.setHorizontalHeaderLabels(
            ["Path", "Type", "Position X", "Position Y", "Order"]
        )

        for i, layer in enumerate(self.template.layers):
            for j, (key, value) in enumerate(layer.items()):
                item = QTableWidgetItem(str(value))
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
                self.layers_table.setItem(i, j, item)

    def move_layer_up(self):
        selected_row = self.layers_table.currentRow()
        if selected_row > 0:
            self.template.layers[selected_row - 1], self.template.layers[selected_row] = (
                self.template.layers[selected_row],
                self.template.layers[selected_row - 1],
            )
            self.update_layers_table()
            self.update_preview()

    def move_layer_down(self):
        selected_row = self.layers_table.currentRow()
        if selected_row < len(self.template.layers) - 1:
            self.template.layers[selected_row + 1], self.template.layers[selected_row] = (
                self.template.layers[selected_row],
                self.template.layers[selected_row + 1],
            )
            self.update_layers_table()
            self.update_preview()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = CardMaker()
    ex.show()
    sys.exit(app.exec())
