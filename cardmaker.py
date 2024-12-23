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
    QDoubleSpinBox,
    QListWidget,
    QListWidgetItem,
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

# Load template data from JSON file
with open("demo_template.json", "r") as f:
    template_data = json.load(f)

DEMO_CSV_FILE = "demo_data.csv"
DEMO_TEMPLATE_FILE = "demo_template.json"
PDF_PAGE_SIZES = {
    "A4": QPdfWriter.PageSize.A4,
    "A3": QPdfWriter.PageSize.A3,
    "B4": QPdfWriter.PageSize.B4,
    "B3": QPdfWriter.PageSize.B3,
    "Custom": None,
}

class CardTemplate:
    def __init__(self, file_path=None):
        if file_path:
            self.load_from_json(file_path)

        self.width = template_data["width"]
        self.height = template_data["height"]
        self.bleed = template_data["bleed"]
        self.layers = []
        self.data_fields = template_data["data_fields"]
        self.fonts = {}
        self.data_field_positions = {field: (0, 0) for field in self.data_fields}  # X, Y
        self.card_image_path = ""
        self.card_image = None

    def load_from_json(self, file_path):
        try:
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
            self.data_field_positions = {field: tuple(data["data_field_positions"].get(field, (0, 0))) for field in self.data_fields}
            self.card_image_path = data.get("card_image_path", "")
            if self.card_image_path:
                self.card_image = QPixmap(self.card_image_path)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            QMessageBox.warning(None, "Error", f"Failed to load template: {e}")

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
            "data_field_positions": {field: list(pos) for field, pos in self.data_field_positions.items()},
            "card_image_path": self.card_image_path,
        }
        try:
            with open(file_path, "w") as f:
                json.dump(data, f)
        except IOError as e:
            QMessageBox.warning(None, "Error", f"Failed to save template: {e}")

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

    def set_data_field_position(self, field, x, y):
        self.data_field_positions[field] = (x, y)

    def set_card_image_path(self, path):
        self.card_image_path = path
        if path:
            self.card_image = QPixmap(path)

    def get_card_image(self):
        return self.card_image

class CardMaker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.template = CardTemplate(DEMO_TEMPLATE_FILE)
        self.card_data = []
        self.undo_stack = []
        self.redo_stack = []
        self.demo_data_loaded = False
        self.current_card_index = 0
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

        # Load template button
        load_template_btn = QPushButton("Load Template")
        load_template_btn.clicked.connect(self.load_template)
        template_layout.addWidget(load_template_btn)

        # Add layer button
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

        # Import data button
        load_data_btn = QPushButton("Import Data (CSV/Excel)")
        load_data_btn.clicked.connect(self.load_data)
        data_layout.addWidget(load_data_btn)

        # Data table
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

        # Data field combo box
        self.data_fields_combo = QComboBox()
        self.data_fields_combo.addItems(self.template.data_fields)
        data_fields_layout.addWidget(self.data_fields_combo)

        # Add data field button
        add_data_field_btn = QPushButton("Add Data Field")
        add_data_field_btn.clicked.connect(self.add_data_field)
        data_fields_layout.addWidget(add_data_field_btn)

        # Remove data field button
        remove_data_field_btn = QPushButton("Remove Data Field")
        remove_data_field_btn.clicked.connect(self.remove_data_field)
        data_fields_layout.addWidget(remove_data_field_btn)

        data_layout.addWidget(data_fields_group)

        # Data field position controls
        data_field_position_group = QWidget()
        data_field_position_layout = QHBoxLayout()
        data_field_position_group.setLayout(data_field_position_layout)

        self.data_field_x_spin = QDoubleSpinBox()
        self.data_field_x_spin.setRange(0, self.template.width)
        self.data_field_x_spin.setValue(self.template.data_field_positions[self.template.data_fields[0]][0])
        self.data_field_x_spin.valueChanged.connect(self.update_data_field_position)

        self.data_field_y_spin = QDoubleSpinBox()
        self.data_field_y_spin.setRange(0, self.template.height)
        self.data_field_y_spin.setValue(self.template.data_field_positions[self.template.data_fields[0]][1])
        self.data_field_y_spin.valueChanged.connect(self.update_data_field_position)

        data_field_position_layout.addWidget(QLabel("X:"))
        data_field_position_layout.addWidget(self.data_field_x_spin)
        data_field_position_layout.addWidget(QLabel("Y:"))
        data_field_position_layout.addWidget(self.data_field_y_spin)

        data_layout.addWidget(data_field_position_group)

        # Move layer buttons
        move_layer_group = QWidget()
        move_layer_layout = QHBoxLayout()
        move_layer_group.setLayout(move_layer_layout)

        # Move layer up button
        move_up_btn = QPushButton("Move Up")
        move_up_btn.clicked.connect(self.move_layer_up)
        move_layer_layout.addWidget(move_up_btn)

        # Move layer down button
        move_down_btn = QPushButton("Move Down")
        move_down_btn.clicked.connect(self.move_layer_down)
        move_layer_layout.addWidget(move_down_btn)

        data_layout.addWidget(move_layer_group)

        # Card image controls
        card_image_group = QWidget()
        card_image_layout = QHBoxLayout()
        card_image_group.setLayout(card_image_layout)

        # Load card image button
        load_card_image_btn = QPushButton("Load Card Image")
        load_card_image_btn.clicked.connect(self.load_card_image)
        card_image_layout.addWidget(load_card_image_btn)

        # Card image preview label
        self.card_image_label = QLabel()
        self.card_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_image_layout.addWidget(self.card_image_label)

        data_layout.addWidget(card_image_group)

        # PDF page size controls
        pdf_page_size_group = QWidget()
        pdf_page_size_layout = QHBoxLayout()
        pdf_page_size_group.setLayout(pdf_page_size_layout)

        # PDF page size combo box
        self.pdf_page_size_combo = QComboBox()
        self.pdf_page_size_combo.addItems(list(PDF_PAGE_SIZES.keys()))
        pdf_page_size_layout.addWidget(self.pdf_page_size_combo)

        # Custom PDF page size controls
        custom_pdf_page_size_group = QWidget()
        custom_pdf_page_size_layout = QHBoxLayout()
        custom_pdf_page_size_group.setLayout(custom_pdf_page_size_layout)

        self.custom_pdf_width_spin = QSpinBox()
        self.custom_pdf_width_spin.setRange(100, 3000)
        self.custom_pdf_width_spin.setValue(210)
        custom_pdf_page_size_layout.addWidget(QLabel("Width:"))
        custom_pdf_page_size_layout.addWidget(self.custom_pdf_width_spin)

        self.custom_pdf_height_spin = QSpinBox()
        self.custom_pdf_height_spin.setRange(100, 3000)
        self.custom_pdf_height_spin.setValue(297)
        custom_pdf_page_size_layout.addWidget(QLabel("Height:"))
        custom_pdf_page_size_layout.addWidget(self.custom_pdf_height_spin)

        pdf_page_size_layout.addWidget(custom_pdf_page_size_group)

        data_layout.addWidget(pdf_page_size_group)

        left_layout.addWidget(template_group)
        left_layout.addWidget(data_group)

        # Right panel for card preview and navigation
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)

        # Card preview label
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.preview_label)

        # Card navigation buttons
        card_nav_group = QWidget()
        card_nav_layout = QHBoxLayout()
        card_nav_group.setLayout(card_nav_layout)

        # Previous card button
        prev_card_btn = QPushButton("Previous Card")
        prev_card_btn.clicked.connect(self.show_previous_card)
        card_nav_layout.addWidget(prev_card_btn)

        # Next card button
        next_card_btn = QPushButton("Next Card")
        next_card_btn.clicked.connect(self.show_next_card)
        card_nav_layout.addWidget(next_card_btn)

        right_layout.addWidget(card_nav_group)

        # Layers table
        self.layers_table = QTableWidget()
        self.layers_table.setColumnCount(5)
        self.layers_table.setHorizontalHeaderLabels(
            ["Path", "Type", "Position X", "Position Y", "Order"]
        )
        self.update_layers_table()

        right_layout.addWidget(self.layers_table)

        # Add panels to main layout
        layout.addWidget(left_panel, 1)
        layout.addWidget(right_panel, 2)

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
            position = (0, 0)  # Default position

            action = self.AddLayerAction(self, file_name, layer_type, position)
            self.undo_stack.append(action)

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
                item = QTableWidgetItem(str(value))
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEditable)
                self.data_table.setItem(i, j, item)

    def update_card_size(self):
        self.template.width = self.width_spin.value()
        self.template.height = self.height_spin.value()
        self.update_data_field_position()
        self.update_preview()

    def update_data_field_position(self):
        field = self.template.data_fields[0]
        self.template.set_data_field_position(field, self.data_field_x_spin.value(), self.data_field_y_spin.value())
        self.update_preview()

    def render_card(self, card_data=None, include_bleed=False, data_field_position=None, font="Default"):
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
                data_field_position[0] if data_field_position else self.template.data_field_positions[self.template.data_fields[0]],
                data_field_position[1] if data_field_position else self.template.data_field_positions[self.template.data_fields[0]],
                width - 2 * self.template.bleed,
                height - 2 * self.template.bleed,
            )
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "\n".join(str(value) for value in card_data.values()))

        painter.end()
        return image

    def update_preview(self):
        if not self.card_data:
            return

        card_data = self.card_data[self.current_card_index]
        image = self.render_card(card_data, data_field_position=(self.data_field_x_spin.value(), self.data_field_y_spin.value()))
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
            writer.setPageSize(self.get_pdf_page_size())
            writer.setPageSizeMM(QSizeF(self.template.width + 2 * self.template.bleed, self.template.height + 2 * self.template.bleed))

            painter = QPainter(writer)
            for card in self.card_data:
                image = self.render_card(card, include_bleed=True)
                painter.drawImage(QPointF(0, 0), image)
                writer.newPage()
            painter.end()

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

        for i, layer in enumerate(self.template.layers):
            for j, (key, value) in enumerate(layer.items()):
                item = QTableWidgetItem(str(value))
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
                self.layers_table.setItem(i, j, item)

    def load_card_image(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Load Card Image", "", "Image files (*.png *.jpg *.jpeg)"
        )
        if file_name:
            self.template.set_card_image_path(file_name)
            pixmap = QPixmap(file_name)
            scaled_pixmap = pixmap.scaled(
                self.card_image_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.card_image_label.setPixmap(scaled_pixmap)

    def show_previous_card(self):
        if self.current_card_index > 0:
            self.current_card_index -= 1
            self.update_preview()

    def show_next_card(self):
        if self.current_card_index < len(self.card_data) - 1:
            self.current_card_index += 1
            self.update_preview()

    def get_pdf_page_size(self):
        page_size = self.pdf_page_size_combo.currentText()
        if page_size == "Custom":
            return QSizeF(self.custom_pdf_width_spin.value(), self.custom_pdf_height_spin.value())
        else:
            return PDF_PAGE_SIZES[page_size]

    # ... (other methods remain the same)

    class AddLayerAction:
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = CardMaker()
    ex.show()
    sys.exit(app.exec())
