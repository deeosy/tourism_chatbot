"""
Correct region-attraction mapping errors in the cleaned knowledge base.
"""

import json
from pathlib import Path

INPUT_PATH = Path("data/processed/cleaned_knowledge_base.json")
OUTPUT_JSON = Path("data/processed/corrected_knowledge_base.json")
OUTPUT_TEXT = Path("data/processed/corrected_knowledge_base.txt")

CORRECT_REGIONS = {
    "Cape Coast Castle": "Central Region",
    "Elmina Castle": "Central Region",
    "Kakum National Park": "Central Region",
    "Bonwire Kente Village": "Ashanti Region",
    "Manhyia Palace": "Ashanti Region",
    "Jamestown": "Greater Accra",
    "Labadi Beach": "Greater Accra",
    "Larabanga Mosque": "Northern Region",
    "Mole National Park": "Northern Region",
    "Boti Falls": "Eastern Region",
    "Lake Volta": "Eastern Region",
    "Busua Beach": "Western Region",
    "Nzulezu Stilt Village": "Western Region",
    "Wli Waterfalls": "Volta Region",
    "Mount Afadjato": "Volta Region",
}


def main():
    data = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    chapters = data["chapters"]

    corrections = 0
    skipped = 0
    summary: dict[str, list[str]] = {}

    for ch in chapters:
        attr = ch["attraction"]
        old_region = ch["region"]

        if attr in CORRECT_REGIONS:
            correct = CORRECT_REGIONS[attr]
            if old_region != correct:
                ch["region"] = correct
                corrections += 1
                key = f"{attr}: {old_region} -> {correct}"
                summary.setdefault(attr, []).append(f"  {old_region} -> {correct}")
        else:
            skipped += 1

    data["metadata"]["total_corrections"] = corrections
    data["metadata"]["unique_regions"] = len(set(c["region"] for c in chapters))

    OUTPUT_JSON.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    full_text = "# Ghana Tourism Knowledge Base (Corrected)\n\n"
    for ch in chapters:
        full_text += f"## Region: {ch['region']} | Attraction: {ch['attraction']}\n\n"
        full_text += ch["content"] + "\n\n"
    OUTPUT_TEXT.write_text(full_text, encoding="utf-8")

    print(f"Total corrections applied: {corrections}")
    print(f"Unmapped attractions (left as-is): {skipped}")
    print()
    print("Correction summary:")
    for attr, changes in sorted(summary.items()):
        print(f"\n{attr}:")
        for c in sorted(set(changes)):
            print(c)


if __name__ == "__main__":
    main()
