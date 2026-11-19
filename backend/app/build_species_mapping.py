
from pathlib import Path
import csv
import json


print("[DEBUG] Initializing species mapping script...")

BASE_DIR = Path(__file__).resolve().parent.parent

CLASSES_FILE = BASE_DIR / "models" / "classes.json"
TAXONOMY_FILE = BASE_DIR / "taxonomy.csv"

OUTPUT_CSV = BASE_DIR / "models" / "species_mapping.csv"
OUTPUT_JSON = BASE_DIR / "models" / "species_mapping.json"

print(f"[DEBUG] Base directory: {BASE_DIR}")
print(f"[DEBUG] Classes file: {CLASSES_FILE}")
print(f"[DEBUG] Taxonomy file: {TAXONOMY_FILE}")
print(f"[DEBUG] Output CSV: {OUTPUT_CSV}")
print(f"[DEBUG] Output JSON: {OUTPUT_JSON}")


def load_classes():
    print("\n[DEBUG] load_classes() called")
    print(f"[DEBUG] Checking classes file: {CLASSES_FILE}")

    if not CLASSES_FILE.exists():
        print("[ERROR] classes.json does not exist!")
    else:
        print("[DEBUG] classes.json found successfully.")

    print("[DEBUG] Loading classes from JSON...")

    with open(CLASSES_FILE, "r", encoding="utf-8") as f:
        classes = json.load(f)

    print("[SUCCESS] Classes loaded successfully.")
    print(f"[DEBUG] Total classes loaded: {len(classes)}")

    if classes:
        print(f"[DEBUG] First class: {classes[0]}")
        print(f"[DEBUG] Last class: {classes[-1]}")

    return classes


def load_taxonomy():
    print("\n[DEBUG] load_taxonomy() called")
    print(f"[DEBUG] Checking taxonomy file: {TAXONOMY_FILE}")

    if not TAXONOMY_FILE.exists():
        print("[ERROR] taxonomy.csv does not exist!")
    else:
        print("[DEBUG] taxonomy.csv found successfully.")

    print("[DEBUG] Reading taxonomy CSV...")

    with open(TAXONOMY_FILE, "r", encoding="utf-8", newline="") as f:
        taxonomy = list(csv.DictReader(f))

    print("[SUCCESS] Taxonomy loaded successfully.")
    print(f"[DEBUG] Total taxonomy rows: {len(taxonomy)}")

    if taxonomy:
        print(f"[DEBUG] Available CSV columns: {list(taxonomy[0].keys())}")
        print(f"[DEBUG] First taxonomy row: {taxonomy[0]}")

    return taxonomy


def main():
    print("\n" + "=" * 60)
    print("[DEBUG] SPECIES MAPPING PROCESS STARTED")
    print("=" * 60)

    print("\n[DEBUG] Step 1: Loading input files...")

    classes = load_classes()
    taxonomy = load_taxonomy()

    print("\n[DEBUG] Input loading summary:")
    print(f"Target classes: {len(classes)}")
    print(f"Taxonomy rows: {len(taxonomy)}")

    print("\n[DEBUG] Step 2: Validating input data...")

    if len(classes) != 234:
        print("[ERROR] Incorrect number of target classes!")
        print(f"[ERROR] Expected: 234 | Found: {len(classes)}")

        raise ValueError(
            f"Expected 234 classes, found {len(classes)}"
        )

    print("[SUCCESS] Target class count validation passed.")

    if not taxonomy:
        print("[ERROR] taxonomy.csv contains no records!")

        raise ValueError("taxonomy.csv is empty")

    print("[SUCCESS] Taxonomy data validation passed.")

    print("\n[DEBUG] Step 3: Building taxonomy lookup dictionary...")

    taxonomy_by_label = {}

    for row_index, row in enumerate(taxonomy):

        label = row.get("primary_label", "").strip()

        if label:
            taxonomy_by_label[label] = row

            if row_index < 5:
                print(f"[DEBUG] Added taxonomy label: {label}")

        else:
            print(
                f"[WARNING] Empty primary_label found "
                f"at taxonomy row {row_index + 1}"
            )

    print("[SUCCESS] Taxonomy lookup dictionary created.")
    print(f"[DEBUG] Unique taxonomy labels: {len(taxonomy_by_label)}")

    print("\n[DEBUG] Step 4: Mapping target classes...")

    mapping = {}
    missing = []

    for class_index, label in enumerate(classes):

        row = taxonomy_by_label.get(label)

        if row is None:

            print(
                f"[WARNING] No taxonomy match found "
                f"for class {class_index}: {label}"
            )

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

        if class_index < 5:
            print(
                f"[DEBUG] Mapped class {class_index}: {label} "
                f"-> {mapping[label]['common_name']}"
            )

    print("\n[SUCCESS] Class mapping loop completed.")

    print(f"[DEBUG] Total mapped entries: {len(mapping)}")
    print(f"[DEBUG] Total missing entries: {len(missing)}")

    if missing:
        print("\n[WARNING] Missing taxonomy entries:")

        for label in missing:
            print("  -", label)

    else:
        print("[SUCCESS] All target classes have taxonomy entries.")

    # ---------------------------------------------------------
    # Write CSV
    # ---------------------------------------------------------

    print("\n[DEBUG] Step 5: Generating CSV output...")
    print(f"[DEBUG] Writing CSV to: {OUTPUT_CSV}")

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

        print("[DEBUG] Writing CSV header...")
        writer.writeheader()

        for row_index, label in enumerate(classes):

            writer.writerow(mapping[label])

            if row_index < 5:
                print(f"[DEBUG] CSV row written: {label}")

    print("[SUCCESS] CSV file generated successfully.")

    # ---------------------------------------------------------
    # Write JSON
    # ---------------------------------------------------------

    print("\n[DEBUG] Step 6: Generating JSON output...")
    print(f"[DEBUG] Writing JSON to: {OUTPUT_JSON}")

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

    print("[SUCCESS] JSON file generated successfully.")

    # ---------------------------------------------------------
    # Final Summary
    # ---------------------------------------------------------

    print("\n" + "=" * 60)
    print("[SUCCESS] SPECIES MAPPING PROCESS COMPLETED")
    print("=" * 60)

    print("\nGenerated:")
    print(f"  {OUTPUT_CSV}")
    print(f"  {OUTPUT_JSON}")

    print(f"\nMapped classes: {len(mapping)}")
    print(f"Missing classes: {len(missing)}")

    if not missing:
        print("\n✓ All 234 classes mapped successfully.")

    print("\n[DEBUG] Final output verification:")

    print(
        f"[DEBUG] CSV exists: {OUTPUT_CSV.exists()}"
    )

    print(
        f"[DEBUG] JSON exists: {OUTPUT_JSON.exists()}"
    )

    print("[DEBUG] Script execution finished.")


if __name__ == "__main__":
    print("[DEBUG] Running script as main module...")
    main()
