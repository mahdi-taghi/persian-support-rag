import json
import os
from collections import defaultdict


def load_jsonl(path):
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def analyze_duplicate_urls(data):
    url_map = defaultdict(list)

    for idx, item in enumerate(data):
        url_map[item.get("url", "").strip()].append(idx)

    duplicates = {url: idxs for url, idxs in url_map.items() if len(idxs) > 1}

    print("\n=== Duplicate URL Analysis ===")
    print(f"Total records: {len(data)}")
    print(f"Unique URLs: {len(url_map)}")
    print(f"Duplicate URL count: {len(duplicates)}")

    if duplicates:
        print("\nDuplicate URLs found:")
        for url, idxs in duplicates.items():
            print(f"• {url}  →  {len(idxs)} occurrences")

        with open("duplicate_urls.txt", "w", encoding="utf-8") as f:
            for url, idxs in duplicates.items():
                f.write(f"{url} => {idxs}\n")

        print("\nSaved duplicate URLs to: duplicate_urls.txt")
    else:
        print("\nNo duplicate URLs found.")


def analyze_duplicate_content(data):
    content_map = defaultdict(list)

    for idx, item in enumerate(data):
        content = item.get("content", "").strip()
        if content:
            content_map[content].append(idx)

    duplicates = {txt: idxs for txt, idxs in content_map.items() if len(idxs) > 1}

    print("\n=== Duplicate Content Analysis ===")
    print(f"Total records: {len(data)}")
    print(f"Unique contents: {len(content_map)}")
    print(f"Duplicate content groups: {len(duplicates)}")

    if duplicates:
        print("\nDuplicate content groups found:")
        for txt, idxs in list(duplicates.items())[:20]:  # limit preview
            snippet = txt[:80].replace("\n", " ") + "..."
            print(f"• '{snippet}'  →  {len(idxs)} occurrences")

        with open("duplicate_contents.txt", "w", encoding="utf-8") as f:
            for txt, idxs in duplicates.items():
                snippet = txt[:150].replace("\n", " ")
                f.write(f"{snippet} => {idxs}\n")

        print("\nSaved duplicate content summary to: duplicate_contents.txt")
    else:
        print("\nNo duplicate content found.")


def main():
    print("=== Dataset Analyzer for JSONL (RAG Cleaner) ===\n")

    path = input("Enter path to JSONL dataset file: ").strip()

    if not os.path.exists(path):
        print("❌ File not found. Please check the path.")
        return

    print("\nLoading dataset...")
    data = load_jsonl(path)
    print(f"Loaded {len(data)} records.")

    print(
        """
Choose analysis mode:
1) Find duplicate URLs
2) Find duplicate content
3) Run both analyses
"""
    )

    choice = input("Enter your choice (1/2/3): ").strip()

    if choice == "1":
        analyze_duplicate_urls(data)
    elif choice == "2":
        analyze_duplicate_content(data)
    elif choice == "3":
        analyze_duplicate_urls(data)
        analyze_duplicate_content(data)
    else:
        print("❌ Invalid choice. Exiting.")


if __name__ == "__main__":
    main()
