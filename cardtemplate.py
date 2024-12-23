import json

class CardTemplate:
    def __init__(self, data):
        self.width = data.get("width", 825)  # Default width if not provided
        self.height = data.get("height", 1125)  # Default height if not provided
        self.bleed = data.get("bleed", 0)  # Default bleed if not provided
        self.layers = data.get("layers", [])  # Default empty list if not provided
        self.data_fields = data.get("data_fields", [])  # Default empty list if not provided
        self.fonts = data.get("fonts", {})  # Default empty dictionary if not provided
        self.data_field_positions = data.get("data_field_positions", {})  # Default empty dictionary if not provided
        self.card_image_path = data.get("card_image_path", "")  # Default empty string if not provided

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
        self.width = data.get("width", self.width)
        self.height = data.get("height", self.height)
        self.bleed = data.get("bleed", self.bleed)
        self.layers = data.get("layers", self.layers)
        self.data_fields = data.get("data_fields", self.data_fields)
        self.fonts = data.get("fonts", self.fonts)
        self.data_field_positions = data.get("data_field_positions", self.data_field_positions)
        self.card_image_path = data.get("card_image_path", self.card_image_path)

    def save_to_json(self, file_path):
        data = {
            "width": self.width,
            "height": self.height,
            "bleed": self.bleed,
            "layers": self.layers,
            "data_fields": self.data_fields,
            "fonts": self.fonts,
            "data_field_positions": self.data_field_positions,
            "card_image_path": self.card_image_path,
        }
        try:
            with open(file_path, "w") as f:
                json.dump(data, f)
        except IOError as e:
            print(f"Failed to save template: {e}")
