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
    QHeaderView,
)
from PyQt6.QtCore import Qt, QSize, QRectF, QSizeF, QPointF, QMarginsF, QEvent

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
    QDrag,
    QDropEvent,
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
        self.setGeometry(100, 100, 1400, 800)  # Increased size to accommodate card preview

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)

        # Left column for controls
        left_column = QWidget()
        left_layout = QVBoxLayout()
        left_column.setLayout(left_layout)

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

        left_layout.addWidget(template_group)
        left_layout.addWidget(data_fields_group)

        # Layers control
        layers_group = QWidget()
        layers_layout = QVBoxLayout()
        layers_group.setLayout(layers_layout)

        # Layers table
        self.layers_table = QTableWidget()
        self.layers_table.setColumnCount(6)
        self.layers_table.setHorizontalHeaderLabels(
            ["Path", "Type", "Position X", "Position Y", "Order", "Visible"]
        )
        self.layers_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.layers_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.layers_table.setDragDropMode(QTableWidget.DragDropMode.InternalMove)
        self.layers_table.setDragEnabled(True)
        self.layers_table.setAcceptDrops(True)
        self.layers_table.viewport().installEventFilter(self)
        layers_layout.addWidget(self.layers_table)

        # Add layer button
        add_layer_btn = QPushButton("Add Layer")
        add_layer_btn.clicked.connect(self.add_layer)
        layers_layout.addWidget(add_layer_btn)

        # Delete layer button
        delete_layer_btn = QPushButton("Delete Layer")
        delete_layer_btn.clicked.connect(self.delete_layer)
        layers_layout.addWidget(delete_layer_btn)

        left_layout.addWidget(layers_group)

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
        self.card_data_table.cellChanged.connect(self.update_card_preview)
        card_data_layout.addWidget(self.card_data_table)

        left_layout.addWidget(card_data_group)

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

        left_layout.addWidget(pdf_page_size_group)

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

        # Export PNG button
        export_png_btn = QPushButton("Export PNG")
        export_png_btn.clicked.connect(self.export_png)
        buttons_layout.addWidget(export_png_btn)

        left_layout.addWidget(buttons_group)

        # Navigation buttons
        nav_buttons_group = QWidget()
        nav_buttons_layout = QHBoxLayout()
        nav_buttons_group.setLayout(nav_buttons_layout)

        # Previous card button
        prev_card_btn = QPushButton("Previous Card")
        prev_card_btn.clicked.connect(self.show_previous_card)
        nav_buttons_layout.addWidget(prev_card_btn)

        # Next card button
        next_card_btn = QPushButton("Next Card")
        next_card_btn.clicked.connect(self.show_next_card)
        nav_buttons_layout.addWidget(next_card_btn)

        left_layout.addWidget(nav_buttons_group)

        # Right column for card preview
        right_column = QWidget()
        right_layout = QVBoxLayout()
        right_column.setLayout(right_layout)

        # Card preview label
        self.card_preview_label = QLabel()
        self.card_preview_label.setFixedSize(600, 800)  # Set fixed size for card preview
        right_layout.addWidget(self.card_preview_label)

        # Card properties label
        self.card_properties_label = QLabel()
        self.card_properties_label.setTextFormat(Qt.TextFormat.RichText)
        right_layout.addWidget(self.card_properties_label)

        main_layout.addWidget(left_column)
        main_layout.addWidget(right_column)

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
            self.update_card_data_table()

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

        self.update_layers_table()
        self.update_card_data_table()
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
        self.card_data_table.setColumnCount(len(self.card_data[0]))
        self.card_data_table.setHorizontalHeaderLabels(self.card_data[0].keys())

        for i, card in enumerate(self.card_data):
            for j, (key, value) in enumerate(card.items()):
                item = QTableWidgetItem(str(value))
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEditable)
                self.card_data_table.setItem(i, j, item)

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

        self.card_data_table.setRowCount(len(self.card_data))
        self.card_data_table.setColumnCount(len(self.card_data[0]))
        self.card_data_table.setHorizontalHeaderLabels(self.card_data[0].keys())

        for i, card in enumerate(self.card_data):
            for j, (key, value) in enumerate(card.items()):
                item = QTableWidgetItem(str(value))
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEditable)
                self.card_data_table.setItem(i, j, item)

    def update_layers_table(self):
        if not self.template:
            return

        self.layers_table.setRowCount(len(self.template.layers) + len(self.template.data_field_positions))

        for i, layer in enumerate(self.template.layers):
            for j, (key, value) in enumerate(layer.items()):
                item = QTableWidgetItem(str(value))
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEditable)
                self.layers_table.setItem(i, j, item)

        for i, (field, position) in enumerate(self.template.data_field_positions.items(), start=len(self.template.layers)):
            item_path = QTableWidgetItem(f"Data Field: {field}")
            item_path.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
            self.layers_table.setItem(i, 0, item_path)

            item_type = QTableWidgetItem("data_field")
            item_type.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
            self.layers_table.setItem(i, 1, item_type)

            item_pos_x = QTableWidgetItem(str(position[0]))
            item_pos_x.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEditable)
            self.layers_table.setItem(i, 2, item_pos_x)

            item_pos_y = QTableWidgetItem(str(position[1]))
            item_pos_y.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEditable)
            self.layers_table.setItem(i, 3, item_pos_y)

            item_order = QTableWidgetItem(str(i))
            item_order.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
            self.layers_table.setItem(i, 4, item_order)

            item_visible = QTableWidgetItem("True")
            item_visible.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
            self.layers_table.setItem(i, 5, item_visible)

    def update_preview(self):
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

    def delete_layer(self):
        selected_row = self.layers_table.currentRow()
        if selected_row >= 0:
            del self.template.layers[selected_row]
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

            # Ensure data_field_positions has the correct keys
            if self.template.data_fields and self.template.data_field_positions:
                for field in self.template.data_fields:
                    if field in self.template.data_field_positions:
                        position = self.template.data_field_positions[field]
                        text_rect = QRectF(
                            position[0],
                            position[1],
                            width - 2 * self.template.bleed,
                            height - 2 * self.template.bleed,
                        )
                        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, str(card_data.get(field, "")))

        painter.end()
        return image

    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.Drop and source is self.layers_table.viewport():
            drop_event = QDropEvent(event)
            if drop_event.source() is self.layers_table:
                selected_items = self.layers_table.selectedItems()
                if selected_items:
                    selected_row = selected_items[0].row()
                    drop_row = self.layers_table.rowAt(drop_event.pos().y())
                    if drop_row != -1 and drop_row != selected_row:
                        self.template.layers[selected_row], self.template.layers[drop_row] = (
                            self.template.layers[drop_row],
                            self.template.layers[selected_row],
                        )
                        self.update_layers_table()
                        self.update_preview()
                        return True
        return super().eventFilter(source, event)

    def __del__(self):
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = CardMaker()
    ex.show()
    sys.exit(app.exec())
