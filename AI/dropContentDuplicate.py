import json
import os


def clean_and_merge_duplicates(input_path, output_path):
    content_map = {}
    duplicate_counter = 0

    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            item = json.loads(line)
            content = item.get("content", "").strip()
            url = item.get("url", "").strip()

            if not content:
                continue

            if content not in content_map:
                # اولین بار → فقط همین URL ذخیره شود
                content_map[content] = {
                    "url": url,  # اول URL
                    "content": content,  # بعد content
                }
            else:
                duplicate_counter += 1
                # هیچ URL اضافه‌ای ذخیره نمی‌کنیم

    # نوشتن خروجی
    with open(output_path, "w", encoding="utf-8") as out:
        for data in content_map.values():
            out.write(json.dumps(data, ensure_ascii=False) + "\n")

    print("\n=== Cleaning Complete ===")
    print(f"Unique contents kept: {len(content_map)}")
    print(f"Duplicates removed: {duplicate_counter}")
    print(f"Clean file saved to: {output_path}")


def main():
    print("=== JSONL Duplicate Cleaner (Single URL, Ordered Output) ===\n")

    input_path = input("Enter path to original JSONL file: ").strip()

    if not os.path.exists(input_path):
        print("❌ File not found.")
        return

    output_path = input("Enter path for cleaned output file: ").strip()

    clean_and_merge_duplicates(input_path, output_path)


if __name__ == "__main__":
    main()
