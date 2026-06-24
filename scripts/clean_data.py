"""
Clean the Ghana Tourism RAG Master Knowledge Base PDF.
Extracts text, removes boilerplate, normalizes whitespace,
and outputs structured clean data.
"""

import re
import json
from pathlib import Path
from pypdf import PdfReader

PDF_PATH = Path("data/raw/Ghana_Tourism_RAG_Master_Knowledge_Base_100plus_Pages.pdf")
OUTPUT_JSON = Path("data/processed/cleaned_knowledge_base.json")
OUTPUT_TEXT = Path("data/processed/cleaned_knowledge_base.txt")

BOILERPLATE = (
    "Ghana is one of West Africa's most visited destinations due to its blend of "
    "culture, heritage, wildlife, beaches, festivals, cuisine, and hospitality. "
)


def extract_all_text(pdf_path: Path) -> list[str]:
    reader = PdfReader(pdf_path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        pages.append(text)
    return pages


def clean_page_text(text: str) -> str:
    lines = text.split("\n")

    cleaned_lines = []
    for line in lines:
        line = line.strip()

        if not line:
            continue

        if re.match(r"^Chapter \d+:", line):
            cleaned_lines.append(f"\n## {line}")
            continue

        if line.startswith("Region:"):
            cleaned_lines.append(f"**{line}**")
            continue

        if line.startswith("Attraction Focus:"):
            cleaned_lines.append(f"**{line}**")
            continue

        if BOILERPLATE in line:
            remaining = line.replace(BOILERPLATE, "").strip()
            if remaining:
                cleaned_lines.append(remaining)
            continue

        if re.match(
            r"^(The\s+\w+\s+Region|The\s+\w+\s+region)\s+contributes\s+significantly",
            line,
        ):
            remaining = re.sub(
                r"^The\s+\w+(\s+\w+)?\s+[Rr]egion\s+contributes\s+significantly\s+to\s+"
                r"the\s+tourism\s+ecosystem\s+through\s+.*?\.",
                "",
                line,
            ).strip()
            if remaining:
                cleaned_lines.append(remaining)
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def normalize_whitespace(text: str) -> str:
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\u2018|\u2019", "'", text)
    text = re.sub(r"\u201c|\u201d", '"', text)
    text = re.sub(r"\u2013|\u2014", "-", text)
    return text.strip()


def parse_chapters(text: str) -> list[dict]:
    chapters = []
    blocks = re.split(r"\n## Chapter \d+:", text)

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        region_match = re.search(r"\*\*Region:\s*(.+?)\*\*", block)
        attraction_match = re.search(r"\*\*Attraction Focus:\s*(.+?)\*\*", block)

        region = region_match.group(1).strip() if region_match else "Unknown"
        attraction = (
            attraction_match.group(1).strip() if attraction_match else "Unknown"
        )

        content = block
        if region_match:
            content = content.replace(region_match.group(0), "", 1)
        if attraction_match:
            content = content.replace(attraction_match.group(0), "", 1)

        content = content.strip()
        content = re.sub(r"\*\*", "", content)

        chapters.append(
            {
                "region": region,
                "attraction": attraction,
                "content": content,
            }
        )

    return chapters


def main():
    print(f"Reading PDF: {PDF_PATH}")
    pages = extract_all_text(PDF_PATH)
    print(f"  Extracted {len(pages)} pages")

    print("Cleaning text...")
    all_clean = []
    for i, page_text in enumerate(pages):
        cleaned = clean_page_text(page_text)
        all_clean.append(cleaned)

    full_text = "\n\n".join(all_clean)
    full_text = normalize_whitespace(full_text)

    print("Parsing chapters...")
    chapters = parse_chapters(full_text)
    print(f"  Found {len(chapters)} chapters")

    stats = {
        "total_pages": len(pages),
        "total_chapters": len(chapters),
        "unique_regions": len(set(c["region"] for c in chapters)),
        "unique_attractions": len(set(c["attraction"] for c in chapters)),
    }
    print(f"  Stats: {stats}")

    output = {
        "metadata": stats,
        "chapters": chapters,
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(
        json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"  Saved JSON: {OUTPUT_JSON}")

    full_text_clean = "# Ghana Tourism Knowledge Base (Cleaned)\n\n"
    for ch in chapters:
        full_text_clean += (
            f"## Region: {ch['region']} | Attraction: {ch['attraction']}\n\n"
        )
        full_text_clean += ch["content"] + "\n\n"

    OUTPUT_TEXT.write_text(full_text_clean, encoding="utf-8")
    print(f"  Saved text: {OUTPUT_TEXT}")

    print("\nData quality issues found:")
    issues = []
    for ch in chapters:
        if ch["attraction"] == "Cape Coast Castle" and ch["region"] != "Central Region":
            issues.append(
                f"  - Cape Coast Castle listed under {ch['region']}, should be Central Region"
            )
        if ch["attraction"] == "Wli Waterfalls" and ch["region"] not in (
            "Volta Region",
        ):
            issues.append(
                f"  - Wli Waterfalls listed under {ch['region']}, should be Volta Region"
            )
        if ch["attraction"] == "Labadi Beach" and ch["region"] != "Greater Accra":
            issues.append(
                f"  - Labadi Beach listed under {ch['region']}, should be Greater Accra"
            )
        if (
            ch["attraction"] == "Nzulezu Stilt Village"
            and ch["region"] != "Western Region"
        ):
            issues.append(
                f"  - Nzulezu Stilt Village listed under {ch['region']}, should be Western Region"
            )

    for issue in sorted(set(issues)):
        print(issue)

    print(f"\nDone! Total chapters: {len(chapters)}")


if __name__ == "__main__":
    main()
