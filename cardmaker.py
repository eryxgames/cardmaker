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
    QInputDialog,
    QDoubleSpinBox,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
    QMessageBox,
    QCheckBox,
    QRadioButton,
    QButtonGroup,
    QInputDialog,
    QHeaderView,
)
from PyQt6.QtCore import Qt, QSizeF, QPointF, QMarginsF, QRectF, QEvent
from PyQt6.QtGui import (
    QImage,
    QPainter,
    QPixmap,
    QPdfWriter,
    QFont,
    QColor,
    QPageSize,
    QDropEvent,
)
from PyQt6.QtSvg import QSvgRenderer
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
        self.setGeometry(100, 100, 1400, 800)

        # Initialize attributes first
        self.demo_data_loaded = False
        self.template = None
        self.card_data = []
        self.current_card_index = 0
        self._image_cache = {}  # Add image caching

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
        template_layout = QHBoxLayout()
        template_group.setLayout(template_layout)

        # Load template button
        load_template_btn = QPushButton("Load Template")
        load_template_btn.clicked.connect(self.load_template)
        template_layout.addWidget(load_template_btn)

        # Save template button
        save_template_btn = QPushButton("Save Template")
        save_template_btn.clicked.connect(self.save_template)
        template_layout.addWidget(save_template_btn)

        # Save template as button
        save_as_template_btn = QPushButton("Save Template As")
        save_as_template_btn.clicked.connect(self.save_as_template)
        template_layout.addWidget(save_as_template_btn)

        left_layout.addWidget(template_group)

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

        left_layout.addWidget(size_group)

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

        left_layout.addWidget(data_fields_group)

        # Layers control
        layers_group = QWidget()
        layers_layout = QVBoxLayout()
        layers_group.setLayout(layers_layout)

        # Layers table
        self.layers_table = QTableWidget()
        self.layers_table.setColumnCount(8)
        self.layers_table.setHorizontalHeaderLabels(
            ["Path", "Type", "Position X", "Position Y", "Order", "Visible", "Actions", "Delete"]
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

        left_layout.addWidget(layers_group)

        # Card data control
        card_data_group = QWidget()
        card_data_layout = QHBoxLayout()
        card_data_group.setLayout(card_data_layout)

        # Load card data button
        load_card_data_btn = QPushButton("Load Card Data")
        load_card_data_btn.clicked.connect(self.load_card_data)
        card_data_layout.addWidget(load_card_data_btn)

        # Save card data button
        save_card_data_btn = QPushButton("Save Card Data")
        save_card_data_btn.clicked.connect(self.save_card_data)
        card_data_layout.addWidget(save_card_data_btn)

        # Save card data as button
        save_as_card_data_btn = QPushButton("Save Card Data As")
        save_as_card_data_btn.clicked.connect(self.save_as_card_data)
        card_data_layout.addWidget(save_as_card_data_btn)

        left_layout.addWidget(card_data_group)

        # Card data table
        self.card_data_table = QTableWidget()
        self.card_data_table.setColumnCount(1)
        self.card_data_table.setHorizontalHeaderLabels(["Card Data"])
        self.card_data_table.cellChanged.connect(self.card_data_table_cell_changed)
        self.card_data_table.cellDoubleClicked.connect(self.open_image_selector)
        left_layout.addWidget(self.card_data_table)

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
        preview_card_btn.clicked.connect(self.open_preview_window)
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

        main_layout.addWidget(left_column)

        # Right column for card preview
        right_column = QWidget()
        right_layout = QVBoxLayout()
        right_column.setLayout(right_layout)

        # Card preview label
        self.card_preview_label = QLabel()
        self.card_preview_label.setFixedSize(600, 800)
        right_layout.addWidget(self.card_preview_label)

        # Card properties label
        self.card_properties_label = QLabel()
        self.card_properties_label.setTextFormat(Qt.TextFormat.RichText)
        right_layout.addWidget(self.card_properties_label)

        # Card resolution and printing resolution info
        resolution_info_label = QLabel()
        resolution_info_label.setTextFormat(Qt.TextFormat.RichText)
        resolution_info_label.setText(
            f"<div style='white-space: pre-wrap;'>"
            f"Resolution: {self.width_spin.value()} x {self.height_spin.value()} pixels<br>"
            f"Printing Resolution: 300 DPI</div>"
        )
        right_layout.addWidget(resolution_info_label)

        main_layout.addWidget(right_column)

        # Initialize template and demo data
        self.template = CardTemplate({})
        self.load_demo_data()

    def card_data_table_cell_changed(self, row, column):
        self.update_card_data_from_table()
        self.update_layers_table()

    def open_image_selector(self, row, column):
        if column == self.card_data_table.columnCount() - 1:  # Assuming the last column is for the image path
            file_name, _ = QFileDialog.getOpenFileName(
                self, "Select Image", "", "Image files (*.png *.jpg *.jpeg)"
            )
            if file_name:
                self.card_data_table.setItem(row, column, QTableWidgetItem(file_name))
                self.update_card_data_from_table()
                self.update_card_preview()
        # Update card preview and layers_table with the new image path
        self.update_card_preview()
        self.update_layers_table()

    def update_layers_table(self, card_data=None):
        """
        Single implementation of update_layers_table with proper error handling
        """
        try:
            if card_data is None:
                if not self.card_data or self.current_card_index >= len(self.card_data):
                    return
                card_data = self.card_data[self.current_card_index]

            self.layers_table.setUpdatesEnabled(False)  # Prevent multiple redraws
            try:
                self.layers_table.setRowCount(0)
                for i, card in enumerate(self.card_data):
                    self._add_layer_row(i, card)
            finally:
                self.layers_table.setUpdatesEnabled(True)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to update layers table: {str(e)}")

    def _add_layer_row(self, row_index, layer):
        """Enhanced layer row with editable properties"""
        self.layers_table.insertRow(row_index)
        
        # Determine if this is a placeholder layer
        is_placeholder = layer.get("placeholder", False)
        layer_id = layer.get("id", "")
        
        # Create items with proper data
        items = [
            QTableWidgetItem(layer_id),  # Layer ID
            QTableWidgetItem(layer.get("type", "")),
            QSpinBox(),  # X position
            QSpinBox(),  # Y position
            QTableWidgetItem(str(row_index)),  # Order
            QCheckBox(),  # Visible
            QComboBox() if is_placeholder else QTableWidgetItem(""),  # Content field selector
        ]
        
        # Configure position spinboxes
        pos = layer.get("position", [0, 0])
        items[2].setRange(-1000, 1000)
        items[2].setValue(pos[0])
        items[2].valueChanged.connect(
            lambda val, layer_id=layer_id: self.update_layer_position(layer_id, val, 'x'))
            
        items[3].setRange(-1000, 1000)
        items[3].setValue(pos[1])
        items[3].valueChanged.connect(
            lambda val, layer_id=layer_id: self.update_layer_position(layer_id, val, 'y'))

        # Configure content field selector for placeholder layers
        if is_placeholder:
            items[6].addItems([col for col in self.card_data[0].keys()])
            items[6].setCurrentText(layer.get("content_field", ""))
            items[6].currentTextChanged.connect(
                lambda text, layer_id=layer_id: self.update_layer_content_field(layer_id, text))

        # Set items in table
        for col, item in enumerate(items):
            if isinstance(item, QTableWidgetItem):
                self.layers_table.setItem(row_index, col, item)
            else:
                self.layers_table.setCellWidget(row_index, col, item)

    def update_layer_position(self, layer_id, value, axis):
        """Update layer position and refresh preview"""
        if self.template:
            current_pos = self.template.get_layer_position(layer_id)
            new_pos = list(current_pos)
            new_pos[0 if axis == 'x' else 1] = value
            self.template.update_layer_position(layer_id, new_pos[0], new_pos[1])
            self.update_preview()

    def update_card_data_from_table(self):
        for row in range(self.card_data_table.rowCount()):
            card_data = {}
            for column in range(self.card_data_table.columnCount()):
                item = self.card_data_table.item(row, column)
                if item:
                    card_data[self.card_data_table.horizontalHeaderItem(column).text()] = item.text()
            self.card_data[row] = card_data
        # Update layers_table with the new card_data
        self.update_layers_table()

    def toggle_demo_data(self, state):
        if state == Qt.CheckState.Checked:
            self.load_demo_data()
        else:
            self.card_data = []

    def load_demo_data(self):
        if not self.demo_data_loaded:
            try:
                # Use pandas with explicit encoding and error handling
                df = pd.read_csv(DEMO_CSV_FILE, encoding='utf-8', on_bad_lines='skip')
                self.card_data = df.to_dict("records")
                if not self.card_data:
                    raise ValueError("No data loaded from CSV file")
                self.demo_data_loaded = True
                self.update_card_data_table()
                print(f"Loaded {len(self.card_data)} cards from demo data")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load demo data: {str(e)}")
                self.card_data = []
                self.demo_data_loaded = False

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

        # Updated required keys check
        required_keys = {"width", "height", "bleed", "layers", "text_fields", "fonts", "card_image_path"}
        if not all(key in data for key in required_keys):
            QMessageBox.warning(None, "Error", f"Invalid template format. Missing one of required keys: {required_keys}")
            return

        if not self.template:
            self.template = CardTemplate(data)
        else:
            self.template.update(data)

        self.update_layers_table()
        self.update_card_data_table()
        self.update_preview()

    def save_template(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Template", "", "JSON files (*.json)"
        )
        if not file_name:
            return

        self.template.save_to_json(file_name)

    def save_as_template(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Template As", "", "JSON files (*.json)"
        )
        if not file_name:
            return

        self.template.save_to_json(file_name)

    def save_card_data(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Card Data", "", "CSV files (*.csv)"
        )
        if not file_name:
            return

        self.update_card_data_from_table()
        df = pd.DataFrame(self.card_data)
        df.to_csv(file_name, index=False)

    def save_as_card_data(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Card Data As", "", "CSV files (*.csv)"
        )
        if not file_name:
            return

        self.update_card_data_from_table()
        df = pd.DataFrame(self.card_data)
        df.to_csv(file_name, index=False)

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

        try:
            card_data = self.card_data[self.current_card_index]
            
            # Render the card
            image = self.render_card(
                card_data,
                include_bleed=False,
                font="Default"
            )
                
            # Convert to pixmap and scale for preview
            pixmap = QPixmap.fromImage(image)
            scaled_pixmap = pixmap.scaled(
                self.card_preview_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.card_preview_label.setPixmap(scaled_pixmap)

            # Update properties label
            properties_text = "<br>".join(f"<b>{key}:</b> {value}" for key, value in card_data.items())
            self.card_properties_label.setText(f"<div style='white-space: pre-wrap;'>Properties:<br>{properties_text}</div>")

            # Update layers table
            self.update_layers_table()

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to update card preview: {str(e)}")

    def update_preview(self):
        if not self.template or not self.card_data:
            return

        card_data = self.card_data[self.current_card_index]
        image = self.render_card(card_data, include_bleed=False, font="Default")
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

    def move_layer_up(self, row):
        if row > 0:
            self.template.layers[row - 1], self.template.layers[row] = (
                self.template.layers[row],
                self.template.layers[row - 1],
            )
            self.update_layers_table()
            self.update_preview()

    def move_layer_down(self, row):
        if row < len(self.template.layers) - 1:
            self.template.layers[row + 1], self.template.layers[row] = (
                self.template.layers[row],
                self.template.layers[row + 1],
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
                "visible": True
            }
        )
        self.update_layers_table()
        self.update_preview()

    def delete_layer(self, row):
        if row >= 0:
            del self.template.layers[row]
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
            self.update_card_preview()

    def show_next_card(self):
        if self.current_card_index < len(self.card_data) - 1:
            self.current_card_index += 1
            self.update_preview()
            self.update_card_preview()

    def get_pdf_page_size(self):
        page_size = self.pdf_page_size_combo.currentText()
        if page_size == "Custom":
            return QPageSize(QSizeF(
                self.custom_pdf_width_spin.value(),
                self.custom_pdf_height_spin.value()
            ))
        else:
            return QPageSize(PDF_PAGE_SIZES[page_size])

    def render_card(self, card_data, include_bleed=False, font="Default"):
        if not card_data:
            return None
            
        width = self.template.width
        height = self.template.height
        
        if include_bleed:
            width += 2 * self.template.bleed
            height += 2 * self.template.bleed
            
        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw static layers and placeholders
        if hasattr(self.template, 'layers'):
            for layer in sorted(self.template.layers, key=lambda x: x.get("order", 0)):
                if layer.get("visible", True):
                    if layer.get("placeholder"):
                        # Handle placeholder layers (illustrations and icons)
                        content_field = layer.get("content_field")
                        if content_field and content_field in card_data:
                            image_path = card_data[content_field]
                            if image_path and image_path.strip():
                                try:
                                    pixmap = QPixmap(image_path)
                                    if not pixmap.isNull():
                                        pos = layer.get("position", [0, 0])
                                        size = layer.get("size", {"width": pixmap.width(), "height": pixmap.height()})
                                        scaled_pixmap = pixmap.scaled(
                                            size["width"], 
                                            size["height"],
                                            Qt.AspectRatioMode.KeepAspectRatio,
                                            Qt.TransformationMode.SmoothTransformation
                                        )
                                        painter.drawPixmap(QPointF(pos[0], pos[1]), scaled_pixmap)
                                except Exception as e:
                                    print(f"Error loading image {image_path}: {e}")
                    else:
                        # Handle static layers (SVG backgrounds, etc.)
                        if layer["type"] == "svg":
                            try:
                                renderer = QSvgRenderer(layer["path"])
                                pos = layer.get("position", [0, 0])
                                svg_rect = QRectF(pos[0], pos[1], width, height)
                                renderer.render(painter, svg_rect)
                            except Exception as e:
                                print(f"Error rendering SVG {layer['path']}: {e}")
                        elif layer["type"] == "png":
                            try:
                                pixmap = QPixmap(layer["path"])
                                if not pixmap.isNull():
                                    pos = layer.get("position", [0, 0])
                                    painter.drawPixmap(QPointF(pos[0], pos[1]), pixmap)
                            except Exception as e:
                                print(f"Error loading PNG {layer['path']}: {e}")

        # Draw text fields
        for field_name, field_props in self.template.text_fields.items():
            if field_name in card_data:
                # Set font
                font = QFont(field_props.get("font", "Arial"))
                font.setPointSize(field_props.get("size", 12))
                painter.setFont(font)
                
                # Set color
                painter.setPen(QColor(field_props.get("color", "#000000")))
                
                # Get position
                pos = field_props.get("position", [0, 0])
                
                # Create text rectangle
                text_rect = QRectF(
                    pos[0],
                    pos[1],
                    field_props.get("max_width", width),
                    height
                )
                
                # Set alignment
                alignment = Qt.AlignmentFlag.AlignCenter
                if field_props.get("alignment") == "left":
                    alignment = Qt.AlignmentFlag.AlignLeft
                elif field_props.get("alignment") == "right":
                    alignment = Qt.AlignmentFlag.AlignRight
                    
                painter.drawText(text_rect, alignment, str(card_data.get(field_name, "")))

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

    def open_preview_window(self):
        if not self.template or not self.card_data:
            return

        preview_window = QMainWindow()
        preview_widget = QWidget()
        preview_layout = QVBoxLayout()
        preview_widget.setLayout(preview_layout)
        preview_window.setCentralWidget(preview_widget)

        preview_label = QLabel()
        preview_label.setFixedSize(600, 800)
        preview_layout.addWidget(preview_label)

        card_data = self.card_data[self.current_card_index]
        image = self.render_card(card_data, include_bleed=False, font="Default")
        pixmap = QPixmap.fromImage(image)
        scaled_pixmap = pixmap.scaled(
            preview_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        preview_label.setPixmap(scaled_pixmap)

        preview_window.show()

    def cleanup(self):
        """Proper cleanup of resources"""
        self._image_cache.clear()
        # Clean up any other resources...

    def __del__(self):
        self.cleanup()

    def load_demo_data(self):
        if not self.demo_data_loaded:
            try:
                # Read CSV with proper encoding
                df = pd.read_csv(DEMO_CSV_FILE, encoding='utf-8')
                self.card_data = df.to_dict("records")
                if not self.card_data:
                    raise ValueError("No data loaded from CSV file")
                self.demo_data_loaded = True
                self.current_card_index = 0
                self.update_card_data_table()
                self.update_card_preview()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load demo data: {str(e)}")
                self.card_data = []
                self.demo_data_loaded = False

    def update_card_data_table(self):
        if not self.card_data:
            return

        # Block signals during update
        self.card_data_table.blockSignals(True)
        try:
            # Clear existing data
            self.card_data_table.setRowCount(0)
            self.card_data_table.setColumnCount(0)

            # Set up table structure
            columns = list(self.card_data[0].keys())
            self.card_data_table.setColumnCount(len(columns))
            self.card_data_table.setHorizontalHeaderLabels(columns)
            self.card_data_table.setRowCount(len(self.card_data))

            # Fill data
            for i, card in enumerate(self.card_data):
                for j, (key, value) in enumerate(card.items()):
                    item = QTableWidgetItem(str(value))
                    self.card_data_table.setItem(i, j, item)

            # Adjust column widths
            self.card_data_table.resizeColumnsToContents()
        finally:
            self.card_data_table.blockSignals(False)

    def update_layers_table(self, card_data=None):  # Make card_data optional
        if not self.template or not self.template.layers:
            return

        self.layers_table.blockSignals(True)
        try:
            self.layers_table.setRowCount(0)
            for i, layer in enumerate(self.template.layers):
                self._add_layer_row(i, layer)
            self.layers_table.resizeColumnsToContents()
        finally:
            self.layers_table.blockSignals(False)

    def _add_layer_row(self, row_index, layer):
        self.layers_table.insertRow(row_index)
        
        # Create items with proper data
        items = [
            QTableWidgetItem(layer.get("path", "")),
            QTableWidgetItem(layer.get("type", "")),
            QTableWidgetItem(str(layer.get("position", (0, 0))[0])),
            QTableWidgetItem(str(layer.get("position", (0, 0))[1])),
            QTableWidgetItem(str(layer.get("order", row_index))),
            QTableWidgetItem(str(layer.get("visible", True)))
        ]
        
        for col, item in enumerate(items):
            self.layers_table.setItem(row_index, col, item)

        # Add action buttons
        self._add_layer_action_buttons(row_index)



    def _add_layer_action_buttons(self, row_index):
        # Create action buttons widget
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(2, 2, 2, 2)

        # Add Up/Down buttons
        up_btn = QPushButton("↑")
        down_btn = QPushButton("↓")
        up_btn.clicked.connect(lambda: self.move_layer_up(row_index))
        down_btn.clicked.connect(lambda: self.move_layer_down(row_index))
        
        actions_layout.addWidget(up_btn)
        actions_layout.addWidget(down_btn)
        
        self.layers_table.setCellWidget(row_index, 6, actions_widget)

        # Add Delete button
        delete_btn = QPushButton("×")
        delete_btn.clicked.connect(lambda: self.delete_layer(row_index))
        self.layers_table.setCellWidget(row_index, 7, delete_btn)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = CardMaker()
    ex.show()
    sys.exit(app.exec())
