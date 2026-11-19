from pathlib import Path
import json


BASE_DIR = Path(__file__).resolve().parent.parent

MAPPING_FILE = BASE_DIR / "models" / "species_mapping.json"


with open(MAPPING_FILE, "r", encoding="utf-8") as f:
    SPECIES_MAP = json.load(f)


def get_species_info(class_code):
    return SPECIES_MAP.get(
        class_code,
        {
            "class_index": -1,
            "class_code": class_code,
            "common_name": "Unknown",
            "scientific_name": "Unknown",
            "class_name": "Unknown",
        },
    )