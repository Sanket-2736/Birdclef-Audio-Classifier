"""
Generate species_info.json from taxonomy.csv for proper Wikipedia and Xeno-canto links.
"""

import csv
import json
from pathlib import Path
from urllib.parse import quote

# Paths
BACKEND_DIR = Path(__file__).parent.parent
TAXONOMY_CSV = BACKEND_DIR / "taxonomy.csv"
OUTPUT_JSON = BACKEND_DIR.parent / "frontend_fixed" / "frontend - Copy" / "src" / "data" / "species_info.json"

def generate_species_info():
    """Generate species_info.json from taxonomy.csv"""
    
    species_info = {}
    
    with open(TAXONOMY_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Extract fields from CSV
            primary_label = row['primary_label'].strip()
            scientific_name = row['scientific_name'].strip()
            common_name = row['common_name'].strip()
            class_name = row['class_name'].strip()
            
            # Generate Wikipedia URL from scientific name
            # Replace spaces with underscores and URL encode
            wiki_title = scientific_name.replace(' ', '_')
            wikipedia_url = f"https://en.wikipedia.org/wiki/{wiki_title}"
            
            # Generate Xeno-canto search URL
            xeno_canto_search = f"https://www.xeno-canto.org/?query={quote(scientific_name)}"
            
            # Create entry
            species_info[primary_label] = {
                "common_name": common_name,
                "scientific_name": scientific_name,
                "taxon": class_name,
                "wikipedia_url": wikipedia_url,
                "xeno_canto_search": xeno_canto_search,
                "image_url": ""
            }
    
    # Write JSON
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(species_info, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Generated {len(species_info)} species entries")
    print(f"✓ Saved to: {OUTPUT_JSON}")
    
    # Print some examples
    print("\nExample entries:")
    for i, (code, info) in enumerate(list(species_info.items())[:3]):
        print(f"\n  {code}:")
        print(f"    Common: {info['common_name']}")
        print(f"    Scientific: {info['scientific_name']}")
        print(f"    Wikipedia: {info['wikipedia_url']}")

if __name__ == "__main__":
    generate_species_info()
