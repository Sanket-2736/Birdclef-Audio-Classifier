from pathlib import Path
import csv
import json


BASE_DIR = Path(__file__).resolve().parent.parent

CLASSES_FILE = BASE_DIR / "models" / "classes.json"
TAXONOMY_FILE = BASE_DIR / "taxonomy.csv"

OUTPUT_CSV = BASE_DIR / "models" / "species_mapping.csv"
OUTPUT_JSON = BASE_DIR / "models" / "species_mapping.json"


def load_classes():
    with open(CLASSES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_taxonomy():
    with open(TAXONOMY_FILE, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main():
    classes = load_classes()
    taxonomy = load_taxonomy()

    print(f"Target classes: {len(classes)}")
    print(f"Taxonomy rows:  {len(taxonomy)}")

    if len(classes) != 234:
        raise ValueError(
            f"Expected 234 classes, found {len(classes)}"
        )

    if not taxonomy:
        raise ValueError("taxonomy.csv is empty")

    taxonomy_by_label = {}

    for row in taxonomy:
        label = row.get("primary_label", "").strip()

        if label:
            taxonomy_by_label[label] = row

    mapping = {}
    missing = []

    for class_index, label in enumerate(classes):
        row = taxonomy_by_label.get(label)

        if row is None:
            missing.append(label)

            mapping[label] = {
                "class_index": class_index,
                "class_code": label,
                "common_name": "Unknown",
                "scientific_name": "Unknown",
                "class_name": "Unknown",
            }

            continue

        mapping[label] = {
            "class_index": class_index,
            "class_code": label,
            "common_name": (
                row.get("common_name", "").strip()
                or "Unknown"
            ),
            "scientific_name": (
                row.get("scientific_name", "").strip()
                or "Unknown"
            ),
            "class_name": (
                row.get("class_name", "").strip()
                or "Unknown"
            ),
        }

    if missing:
        print("\nWARNING: Missing taxonomy entries:")
        for label in missing:
            print("  -", label)

    # ---------------------------------------------------------
    # Write CSV
    # ---------------------------------------------------------

    with open(
        OUTPUT_CSV,
        "w",
        encoding="utf-8",
        newline=""
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=[
                "class_index",
                "class_code",
                "common_name",
                "scientific_name",
                "class_name",
            ],
        )

        writer.writeheader()

        for label in classes:
            writer.writerow(mapping[label])

    # ---------------------------------------------------------
    # Write JSON
    # ---------------------------------------------------------

    with open(
        OUTPUT_JSON,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            mapping,
            f,
            indent=2,
            ensure_ascii=False,
        )

    print("\nGenerated:")
    print(f"  {OUTPUT_CSV}")
    print(f"  {OUTPUT_JSON}")

    print(f"\nMapped classes: {len(mapping)}")
    print(f"Missing classes: {len(missing)}")

    if not missing:
        print("\n✓ All 234 classes mapped successfully.")


if __name__ == "__main__":
    main()