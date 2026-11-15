import csv
import json

species_info = {}
with open('backend/taxonomy.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        code = row['primary_label']
        sci_name = row['scientific_name']
        species_info[code] = {
            'common_name': row['common_name'],
            'scientific_name': sci_name,
            'taxon': row['class_name'],
            'wikipedia_url': f"https://en.wikipedia.org/wiki/{sci_name.replace(' ', '_')}",
            'xeno_canto_search': f"https://www.xeno-canto.org/?query={'+'.join(sci_name.split())}",
            'image_url': ''
        }

# Write to frontend
with open('frontend/src/data/species_info.json', 'w', encoding='utf-8') as f:
    json.dump(species_info, f, indent=2)

print(f"Generated species_info.json with {len(species_info)} species")
