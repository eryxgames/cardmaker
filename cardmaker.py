import sys
import csv
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QPushButton,
    QLabel,
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
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
)
from PyQt6.QtCore import Qt, QSize, QRectF, QSizeF, QPointF, QMarginsF

from PyQt6.QtGui import (
    QImage,
    QPainter,
    QPixmap,
    QPdfWriter,
    QPainterPath,
    QFont,
    QFontDatabase,
    QColor,
    QPageSize,
)
from PyQt6.QtSvg import QSvgRenderer
import numpy as np
from PIL import Image
import json
from cardtemplate import CardTemplate  # Import the CardTemplate class

DEMO_CSV_FILE = "demo_data.csv"
DEMO_TEMPLATE_FILE = "demo_template.json"
PDF_PAGE_SIZES = {
    "A4": QPageSize.PageSizeId.A4,
    "A3": QPageSize.PageSizeId.A3,
    "B4": QPageSize.PageSizeId.B4,
    "B3": QPageSize.PageSizeId.B3,
    "Custom": None,
}

class CardMaker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CardMaker")
        self.setGeometry(100, 100, 1200, 800)  # Increased size to accommodate card preview

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        # Template selection and loading
        template_group = QWidget()
        template_layout = QVBoxLayout()
        template_group.setLayout(template_layout)

        # Load template button
        load_template_btn = QPushButton("Load Template")
        load_template_btn.clicked.connect(self.load_template)
        template_layout.addWidget(load_template_btn)

        # Card size controls
        size_group = QWidget()
        size_layout = QHBoxLayout()
        size_group.setLayout(size_layout)

        self.width_spin = QSpinBox()
        self.width_spin.setRange(100, 3000)
        self.width_spin.setValue(825)
        size_layout.addWidget(QLabel("Width:"))
        size_layout.addWidget(self.width_spin)

        self.height_spin = QSpinBox()
        self.height_spin.setRange(100, 3000)
        self.height_spin.setValue(1125)
        size_layout.addWidget(QLabel("Height:"))
        size_layout.addWidget(self.height_spin)

        template_layout.addWidget(size_group)

        # Data fields control
        data_fields_group = QWidget()
        data_fields_layout = QVBoxLayout()
        data_fields_group.setLayout(data_fields_layout)

        # Data field combo box
        self.data_fields_combo = QComboBox()
        data_fields_layout.addWidget(QLabel("Data Fields:"))
        data_fields_layout.addWidget(self.data_fields_combo)

        # Add data field button
        add_data_field_btn = QPushButton("Add Data Field")
        add_data_field_btn.clicked.connect(self.add_data_field)
        data_fields_layout.addWidget(add_data_field_btn)

        # Remove data field button
        remove_data_field_btn = QPushButton("Remove Data Field")
        remove_data_field_btn.clicked.connect(self.remove_data_field)
        data_fields_layout.addWidget(remove_data_field_btn)

        layout.addWidget(template_group)
        layout.addWidget(data_fields_group)

        # Layers control
        layers_group = QWidget()
        layers_layout = QVBoxLayout()
        layers_group.setLayout(layers_layout)

        # Layers table
        self.layers_table = QTableWidget()
        self.layers_table.setColumnCount(5)
        self.layers_table.setHorizontalHeaderLabels(
            ["Path", "Type", "Position X", "Position Y", "Order", "Visible"]
        )
        layers_layout.addWidget(self.layers_table)

        # Add layer button
        add_layer_btn = QPushButton("Add Layer")
        add_layer_btn.clicked.connect(self.add_layer)
        layers_layout.addWidget(add_layer_btn)

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

        layers_layout.addWidget(move_layer_group)

        layout.addWidget(layers_group)

        # Card data control
        card_data_group = QWidget()
        card_data_layout = QVBoxLayout()
        card_data_group.setLayout(card_data_layout)

        # Load card data button
        load_card_data_btn = QPushButton("Load Card Data")
        load_card_data_btn.clicked.connect(self.load_card_data)
        card_data_layout.addWidget(load_card_data_btn)

        # Card data table
        self.card_data_table = QTableWidget()
        self.card_data_table.setColumnCount(1)
        self.card_data_table.setHorizontalHeaderLabels(["Card Data"])
        card_data_layout.addWidget(self.card_data_table)

        layout.addWidget(card_data_group)

        # Card preview
        preview_group = QWidget()
        preview_layout = QHBoxLayout()
        preview_group.setLayout(preview_layout)

        # Card preview label
        self.card_preview_label = QLabel()
        self.card_preview_label.setFixedSize(600, 800)  # Set fixed size for card preview
        preview_layout.addWidget(self.card_preview_label)

        # Card properties label
        self.card_properties_label = QLabel()
        self.card_properties_label.setTextFormat(Qt.TextFormat.RichText)
        preview_layout.addWidget(self.card_properties_label)

        layout.addWidget(preview_group)

        # PDF page size controls
        pdf_page_size_group = QWidget()
        pdf_page_size_layout = QHBoxLayout()
        pdf_page_size_group.setLayout(pdf_page_size_layout)

        # PDF page size combo box
        self.pdf_page_size_combo = QComboBox()
        self.pdf_page_size_combo.addItems(list(PDF_PAGE_SIZES.keys()))
        pdf_page_size_layout.addWidget(QLabel("PDF Page Size:"))
        pdf_page_size_layout.addWidget(self.pdf_page_size_combo)

        # Custom PDF page size controls
        custom_pdf_page_size_group = QWidget()
        custom_pdf_page_size_layout = QHBoxLayout()
        custom_pdf_page_size_group.setLayout(custom_pdf_page_size_layout)

        self.custom_pdf_width_spin = QDoubleSpinBox()
        self.custom_pdf_width_spin.setRange(100, 3000)
        self.custom_pdf_width_spin.setValue(825)
        custom_pdf_page_size_layout.addWidget(QLabel("Width:"))
        custom_pdf_page_size_layout.addWidget(self.custom_pdf_width_spin)

        self.custom_pdf_height_spin = QDoubleSpinBox()
        self.custom_pdf_height_spin.setRange(100, 3000)
        self.custom_pdf_height_spin.setValue(1125)
        custom_pdf_page_size_layout.addWidget(QLabel("Height:"))
        custom_pdf_page_size_layout.addWidget(self.custom_pdf_height_spin)

        pdf_page_size_layout.addWidget(custom_pdf_page_size_group)

        layout.addWidget(pdf_page_size_group)

        # Buttons for card preview, PDF export, etc.
        buttons_group = QWidget()
        buttons_layout = QHBoxLayout()
        buttons_group.setLayout(buttons_layout)

        # Preview card button
        preview_card_btn = QPushButton("Preview Card")
        preview_card_btn.clicked.connect(self.update_card_preview)
        buttons_layout.addWidget(preview_card_btn)

        # Export PDF button
        export_pdf_btn = QPushButton("Export PDF")
        export_pdf_btn.clicked.connect(self.export_pdf)
        buttons_layout.addWidget(export_pdf_btn)

        layout.addWidget(buttons_group)

        # Initialize template and demo data
        self.template = CardTemplate({})  # Initialize an empty CardTemplate object with default values
        self.demo_data_loaded = False
        self.card_data = []
        self.current_card_index = 0

        # Ensure the template is initialized before calling update_layers_table
        self.update_layers_table()

    def toggle_demo_data(self, state):
        if state == Qt.CheckState.Checked:
            self.load_demo_data()
        else:
            self.card_data = []

    def load_demo_data(self):
        if not self.demo_data_loaded:
            df = pd.read_csv(DEMO_CSV_FILE)
            self.card_data = df.to_dict("records")
            self.demo_data_loaded = True

    def load_template(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Load Template", "", "JSON files (*.json);;SVG files (*.svg)"
        )
        if not file_name:
            return

        try:
            with open(file_name, "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            QMessageBox.warning(None, "Error", f"Failed to load template: {e}")
            return

        if not all(key in data for key in ("width", "height", "bleed", "layers", "data_fields", "fonts", "data_field_positions", "card_image_path")):
            QMessageBox.warning(None, "Error", "Invalid template format")
            return

        if not self.template:
            self.template = CardTemplate(data)
        else:
            self.template.update(data)  # Update the existing template with the new data

#        self.template = CardTemplate(data)
        self.update_layers_table()
        self.update_data_table()
        self.update_preview()

    def load_card_data(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Load Card Data", "", "CSV files (*.csv)"
        )
        if not file_name:
            return

        try:
            df = pd.read_csv(file_name)
            self.card_data = df.to_dict("records")
            self.update_card_data_table()
            self.update_card_preview()
        except (FileNotFoundError, pd.errors.ParserError) as e:
            QMessageBox.warning(None, "Error", f"Failed to load card data: {e}")

    def update_card_data_table(self):
        if not self.card_data:
            return

        self.card_data_table.setRowCount(len(self.card_data))

        for i, card in enumerate(self.card_data):
            item = QTableWidgetItem(json.dumps(card, indent=4))
            item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEditable)
            self.card_data_table.setItem(i, 0, item)

    def update_card_preview(self):
        if not self.template or not self.card_data:
            return

        card_data = self.card_data[self.current_card_index]
        image = self.render_card(card_data, include_bleed=False, data_field_position=None, font="Default")
        pixmap = QPixmap.fromImage(image)
        scaled_pixmap = pixmap.scaled(
            self.card_preview_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.card_preview_label.setPixmap(scaled_pixmap)

        # Update card properties label
        properties_text = "<br>".join(f"<b>{key}:</b> {value}" for key, value in card_data.items())
        self.card_properties_label.setText(f"<div style='white-space: pre-wrap;'>Properties:<br>{properties_text}</div>")

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

    def update_layers_table(self):
        if not self.template:
            return

        self.layers_table.setRowCount(len(self.template.layers))

        for i, layer in enumerate(self.template.layers):
            for j, (key, value) in enumerate(layer.items()):
                item = QTableWidgetItem(str(value))
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
                self.layers_table.setItem(i, j, item)

    def update_preview(self):
        if not self.template or not self.card_data:
            return

        card_data = self.card_data[self.current_card_index]
        image = self.render_card(card_data, include_bleed=False, data_field_position=None, font="Default")
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
        if not dir_name:
            return

        for i, card in enumerate(self.card_data):
            image = self.render_card(card)
            image.save(f"{dir_name}/card_{i+1}.png")

    def export_pdf(self):
        if not self.card_data:
            return

        file_name, _ = QFileDialog.getSaveFileName(
            self, "Export PDF", "", "PDF files (*.pdf)"
        )
        if not file_name:
            return

        writer = QPdfWriter(file_name)
        page_size = self.get_pdf_page_size()
        writer.setPageSize(page_size)

        # Convert template dimensions from units to millimeters if necessary
        width_mm = self.template.width + 2 * self.template.bleed
        height_mm = self.template.height + 2 * self.template.bleed

        # Set page margins to zero
        margins = QMarginsF(0, 0, 0, 0)
        writer.setPageMargins(margins)

        painter = QPainter(writer)
        for card in self.card_data:
            image = self.render_card(card, include_bleed=True)
            painter.drawImage(QPointF(0, 0), image)
            if card != self.card_data[-1]:  # Don't add a new page after the last card
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

    def add_layer(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Add Layer", "", "Image files (*.png *.svg)"
        )
        if not file_name:
            return

        layer_type = "svg" if file_name.lower().endswith(".svg") else "png"
        position = (0, 0)  # Default position
        order = len(self.template.layers)  # Add order for new layer

        self.template.layers.append(
            {
                "path": file_name,
                "type": layer_type,
                "position": position,
                "order": order,
            }
        )
        self.update_layers_table()
        self.update_preview()

    def load_card_image(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Load Card Image", "", "Image files (*.png *.jpg *.jpeg)"
        )
        if not file_name:
            return

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
            return QPageSize(QSizeF(
                self.custom_pdf_width_spin.value(),
                self.custom_pdf_height_spin.value()
            ))
        else:
            return QPageSize(PDF_PAGE_SIZES[page_size])

    def render_card(
        self,
        card_data=None,
        include_bleed=False,
        data_field_position=None,
        font="Default",
    ):
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

    def __del__(self):
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = CardMaker()
    ex.show()
    sys.exit(app.exec())
