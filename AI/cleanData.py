import json
import os
import re


def clean_content(text):
    if not text:
        return ""

    # حذف فهرست مطالب / سرفصل‌های انتهایی
    patterns = [
        r"فهرست مطالب.*$",
        r"مطالب مرتبط.*$",
        r"سوالات متداول.*$",
    ]

    for p in patterns:
        text = re.sub(p, "", text, flags=re.DOTALL)

    # حذف کلمات تکراری مثل "بستن"
    text = re.sub(r"(بستن\s*){2,}", "بستن ", text)

    # حذف فاصله‌ها و خطوط خالی اضافی
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    return text.strip()


def clean_dataset(input_path, output_path):
    cleaned = 0
    skipped = 0

    with open(input_path, "r", encoding="utf-8") as f, open(
        output_path, "w", encoding="utf-8"
    ) as out:

        for line in f:
            if not line.strip():
                continue

            item = json.loads(line)

            url = item.get("url", "").strip()
            content = item.get("content", "")

            cleaned_content = clean_content(content)

            if not cleaned_content:
                skipped += 1
                continue

            new_record = {"url": url, "content": cleaned_content}

            out.write(json.dumps(new_record, ensure_ascii=False) + "\n")
            cleaned += 1

    print("\n=== Cleaning Complete ===")
    print("Records processed:", cleaned)
    print("Records skipped:", skipped)
    print("Saved to:", output_path)


def main():
    print("=== JSONL Dataset Cleaner (No Truncate) ===\n")

    input_path = input("Enter dataset path: ").strip()

    if not os.path.exists(input_path):
        print("❌ File not found")
        return

    output_path = input("Enter output path: ").strip()

    clean_dataset(input_path, output_path)


if __name__ == "__main__":
    main()
