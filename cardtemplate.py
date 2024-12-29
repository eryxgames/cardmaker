import json

class CardTemplate:
    def __init__(self, data):
        self.width = data.get("width", 640)
        self.height = data.get("height", 920)
        self.bleed = data.get("bleed", 0)
        self.layers = data.get("layers", [])
        self.text_fields = data.get("text_fields", {})
        # Get data fields from text_fields keys and placeholder content_fields
        self.data_fields = list(self.text_fields.keys())
        self.fonts = data.get("fonts", {})
        self.card_image_path = data.get("card_image_path", "")
        self.layer_overrides = data.get("layer_overrides", {})
        
        # Add any content_fields from placeholder layers to data_fields
        for layer in self.layers:
            if layer.get("placeholder") and layer.get("content_field"):
                if layer["content_field"] not in self.data_fields:
                    self.data_fields.append(layer["content_field"])

    def set_card_image_path(self, path):
        self.card_image_path = path

    @classmethod
    def load_from_json(cls, file_path):
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            return cls(data)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Failed to load template: {e}")
            return None

    def update(self, data):
        """Update template with new data"""
        self.width = data.get("width", self.width)
        self.height = data.get("height", self.height)
        self.bleed = data.get("bleed", self.bleed)
        self.layers = data.get("layers", self.layers)
        self.fonts = data.get("fonts", self.fonts)
        self.card_image_path = data.get("card_image_path", self.card_image_path)
        self.text_fields = data.get("text_fields", self.text_fields)
        self.layer_overrides = data.get("layer_overrides", self.layer_overrides)
        
        # Update data_fields from text_fields and placeholder layers
        self.data_fields = list(self.text_fields.keys())
        for layer in self.layers:
            if layer.get("placeholder") and layer.get("content_field"):
                if layer["content_field"] not in self.data_fields:
                    self.data_fields.append(layer["content_field"])

    def save_to_json(self, file_path):
        """Save template to JSON file"""
        data = {
            "width": self.width,
            "height": self.height,
            "bleed": self.bleed,
            "layers": self.layers,
            "text_fields": self.text_fields,
            "fonts": self.fonts,
            "layer_overrides": self.layer_overrides,
            "card_image_path": self.card_image_path
        }
        try:
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Failed to save template: {e}")

    def get_text_field_properties(self, field_name):
        """Get text field properties with defaults"""
        default_props = {
            "position": [0, 0],
            "font": "Arial",
            "size": 12,
            "color": "#000000",
            "alignment": "center"
        }
        if field_name in self.text_fields:
            return {**default_props, **self.text_fields[field_name]}
        return default_props

    def get_layer_by_content_field(self, content_field):
        """Find layer that uses specific content field"""
        for layer in self.layers:
            if layer.get("placeholder") and layer.get("content_field") == content_field:
                return layer
        return None

    def get_placeholder_fields(self):
        """Get list of content fields used by placeholder layers"""
        fields = []
        for layer in self.layers:
            if layer.get("placeholder") and layer.get("content_field"):
                fields.append(layer.get("content_field"))
        return fields


    def update_layer_position(self, layer_id, x, y):
        """Update position for a layer"""
        for layer in self.layers:
            if layer.get("id") == layer_id:
                layer["position"] = [x, y]
                break
        
        # Update placeholder layers if applicable
        for layer in self.placeholder_layers:
            if layer.get("id") == layer_id:
                layer["position"] = [x, y]
                break

    def get_layer_position(self, layer_id):
        """Get position for a layer"""
        for layer in self.layers:
            if layer.get("id") == layer_id:
                return layer.get("position", [0, 0])
        return [0, 0]

    def get_placeholder_content_field(self, layer_id):
        """Get content field name for a placeholder layer"""
        for layer in self.placeholder_layers:
            if layer.get("id") == layer_id:
                return layer.get("content_field")
        return None

    def set_placeholder_content_field(self, layer_id, field_name):
        """Set content field for a placeholder layer"""
        for layer in self.layers:
            if layer.get("id") == layer_id:
                layer["content_field"] = field_name
                break
        
        for layer in self.placeholder_layers:
            if layer.get("id") == layer_id:
                layer["content_field"] = field_name
                break

    def get_layer_by_id(self, layer_id):
        """Get layer by its ID"""
        for layer in self.layers:
            if layer.get("id") == layer_id:
                return layer
        return None

    def update_text_field_properties(self, field_name, properties):
        """Update properties for a text field"""
        if field_name in self.text_fields:
            self.text_fields[field_name].update(properties)
        else:
            self.text_fields[field_name] = properties

    def get_layer_size(self, layer_id):
        """Get size for a layer"""
        layer = self.get_layer_by_id(layer_id)
        if layer:
            return layer.get("size", {"width": 0, "height": 0})
        return {"width": 0, "height": 0}

    def set_layer_size(self, layer_id, width, height):
        """Set size for a layer"""
        layer = self.get_layer_by_id(layer_id)
        if layer:
            layer["size"] = {"width": width, "height": height}