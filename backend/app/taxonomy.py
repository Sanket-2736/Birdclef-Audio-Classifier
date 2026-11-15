"""
Taxonomy management for bird/animal species.
Builds from existing species_mapping.json with fallback to taxonomy.csv.
"""

from pathlib import Path
import json
import csv


BASE_DIR = Path(__file__).resolve().parent.parent
SPECIES_MAPPING_PATH = BASE_DIR / "models" / "species_mapping.json"
TAXONOMY_CSV_PATH = BASE_DIR / "taxonomy.csv"
TAXONOMY_JSON_PATH = BASE_DIR / "app" / "data" / "taxonomy.json"


def build_taxonomy():
    """
    Build complete taxonomy mapping from existing data sources.
    
    Returns
    -------
    taxonomy : dict
        {code: {common_name, scientific_name, taxon, ...}}
    """
    
    # Load from species_mapping.json (already has taxonomy)
    with open(SPECIES_MAPPING_PATH, "r", encoding="utf-8") as f:
        species_map = json.load(f)
    
    # Load taxonomy.csv for any additional entries or verification
    csv_data = {}
    if TAXONOMY_CSV_PATH.exists():
        with open(TAXONOMY_CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                csv_data[row["primary_label"]] = {
                    "scientific_name": row["scientific_name"],
                    "common_name": row["common_name"],
                    "taxon": row["class_name"],
                }
    
    # Build consolidated taxonomy
    taxonomy = {}
    
    for code, info in species_map.items():
        # Extract taxon from species_mapping (already in class_name field)
        taxon = info.get("class_name", "Unknown")
        
        taxonomy[code] = {
            "code": code,
            "common_name": info.get("common_name", "Unknown"),
            "scientific_name": info.get("scientific_name", "Unknown"),
            "taxon": taxon,
            "class_index": info.get("class_index", -1),
        }
    
    return taxonomy


def load_or_build_taxonomy():
    """
    Load taxonomy from JSON if it exists, otherwise build and cache it.
    
    Returns
    -------
    taxonomy : dict
    """
    
    if TAXONOMY_JSON_PATH.exists():
        with open(TAXONOMY_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # Build it
    taxonomy = build_taxonomy()
    
    # Cache it
    TAXONOMY_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(TAXONOMY_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(taxonomy, f, indent=2)
    
    return taxonomy


def get_taxon(class_code):
    """
    Get taxon (Aves, Insecta, Mammalia, Amphibia, Reptilia) for a class code.
    
    Parameters
    ----------
    class_code : str
        Class code (e.g., "1161364")
    
    Returns
    -------
    taxon : str
        Taxonomic class name
    """
    
    taxonomy = load_or_build_taxonomy()
    return taxonomy.get(class_code, {}).get("taxon", "Unknown")


if __name__ == "__main__":
    taxonomy = build_taxonomy()
    print(f"Taxonomy entries: {len(taxonomy)}")
    
    # Show a few examples
    for i, (code, info) in enumerate(list(taxonomy.items())[:5]):
        print(f"  {code}: {info['common_name']} ({info['taxon']})")
