import json
import re
import html
import hashlib


def advanced_text_cleaning(text):
    """پاکسازی پیشرفته متن"""
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
        "",
        text,
    )

    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    english_digits = "0123456789"
    translation_table = str.maketrans(persian_digits, english_digits)
    text = text.translate(translation_table)

    arabic_digits = "٠١٢٣٤٥٦٧٨٩"
    translation_table = str.maketrans(arabic_digits, english_digits)
    text = text.translate(translation_table)

    text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([.,!?؟،])", r"\1", text)
    text = re.sub(r"([.,!?؟،])\s+", r"\1 ", text)
    text = re.sub(r"\.{4,}", "...", text)
    text = text.strip()

    return text


def remove_noise_words(text):
    """حذف کلمات اضافی"""
    noise_patterns = [
        r"\bبستن\b",
        r"\bکلیک کنید\b",
        r"\bمشاهده\s*(?:بیشتر|کمتر)?\b",
        r"\bبرای\s+(?:مشاهده|دیدن)\b",
        r"\bاینجا\s+کلیک\s+کنید\b",
        r"\bادامه\s+مطلب\b",
        r"\bبیشتر\s+بخوانید\b",
        r"\bدسکتاپ\s+موبایل\b",
    ]

    for pattern in noise_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_chunk_start(text):
    """پاکسازی ابتدای چانک"""
    # حذف نقطه، شماره، پرانتز از ابتدا
    text = re.sub(r"^[\d\s.،؛:)(\]]+", "", text).strip()

    # حذف کلمات اضافی
    noise_words = [
        "دسکتاپ",
        "موبایل",
        "راهنمای",
        "راهنما",
        "نحوه",
        "آموزش",
        "صرافی تبدیل",
        "خانه",
        "اطلاعیه‌ها",
    ]

    for word in noise_words:
        if text.startswith(word):
            text = text[len(word) :].strip()

    return text.strip()


def generate_smart_title(text, max_length=45):
    """تولید عنوان کوتاه و معنادار"""
    text = clean_chunk_start(text)

    if not text:
        return "محتوای عمومی"

    # اولین جمله کامل (20-70 کاراکتر)
    match = re.search(r"^([^.!?،؛]{20,70}[.!?،؛])", text)
    if match:
        title = match.group(1).strip()
        title = re.sub(r"[.!?،؛]+$", "", title)
    else:
        # 6 کلمه اول
        words = text.split()[:6]
        title = " ".join(words)

    if len(title) > max_length:
        title = title[:max_length].rsplit(" ", 1)[0].strip() + "..."

    return title if title else "محتوای عمومی"


def extract_section_from_url(url):
    """استخراج بخش از URL"""
    if not url or url.strip() == "":
        return "عمومی"

    url_lower = url.lower()

    if "/help/" in url_lower or "/guide/" in url_lower:
        return "راهنما"
    elif "/trade/" in url_lower or "/trading/" in url_lower:
        return "معاملات"
    elif "/account/" in url_lower or "/profile/" in url_lower:
        return "حساب کاربری"
    elif "/verification/" in url_lower or "/kyc/" in url_lower:
        return "احراز هویت"
    elif (
        "/wallet/" in url_lower or "/deposit/" in url_lower or "/withdraw/" in url_lower
    ):
        return "کیف پول"
    elif "/order/" in url_lower:
        return "سفارش‌گذاری"
    else:
        return "عمومی"


def is_valid_chunk(text, min_length=300, max_length=650):
    """بررسی اعتبار چانک برای embedding"""
    text = text.strip()

    # طول مناسب
    if len(text) < min_length or len(text) > max_length:
        return False

    # پاکسازی ابتدا
    cleaned = clean_chunk_start(text)
    if len(cleaned) < min_length * 0.85:
        return False

    # حداقل 3 جمله کامل
    sentences = re.findall(r"[.!?؟]", text)
    if len(sentences) < 3:
        return False

    # نسبت اعداد کمتر از 40%
    digits = len(re.findall(r"\d", text))
    if digits > len(text) * 0.4:
        return False

    # حداقل 25 کلمه یونیک
    words = re.findall(r"[\u0600-\u06FF\w]+", text)
    unique_words = set(words)
    if len(unique_words) < 25:
        return False

    return True


def smart_chunk_for_embedding(text, target_length=500, overlap=40):
    """چانک‌بندی بهینه برای embedding"""
    # تقسیم به جملات
    sentences = re.split(r"([.!?؟]\s+)", text)

    # ترکیب جملات با علائم
    combined = []
    for i in range(0, len(sentences) - 1, 2):
        sentence = sentences[i]
        punctuation = sentences[i + 1] if i + 1 < len(sentences) else ""
        combined.append((sentence + punctuation).strip())

    if len(sentences) % 2 == 1:
        combined.append(sentences[-1].strip())

    chunks = []
    current_chunk = ""

    for sentence in combined:
        if not sentence:
            continue

        # اگر اضافه کردن جمله از target_length بگذرد
        potential_chunk = (
            (current_chunk + " " + sentence).strip() if current_chunk else sentence
        )

        if len(potential_chunk) > target_length and current_chunk:
            # ذخیره چانک فعلی
            if is_valid_chunk(current_chunk):
                chunks.append(current_chunk.strip())

                # overlap: فقط آخرین جمله (حداکثر overlap کاراکتر)
                last_sentences = []
                temp_length = 0

                for s in reversed(combined[max(0, len(chunks) - 3) :]):
                    if temp_length + len(s) <= overlap:
                        last_sentences.insert(0, s)
                        temp_length += len(s)
                    else:
                        break

                current_chunk = (
                    (" ".join(last_sentences) + " " + sentence).strip()
                    if last_sentences
                    else sentence
                )
            else:
                current_chunk = sentence
        else:
            current_chunk = potential_chunk

    # چانک آخر
    if current_chunk and is_valid_chunk(current_chunk):
        chunks.append(current_chunk.strip())

    return chunks


def deduplicate_chunks(chunks_with_metadata, similarity_threshold=0.7):
    """حذف چانک‌های تکراری با similarity check"""
    unique_chunks = []
    seen_hashes = set()

    for item in chunks_with_metadata:
        chunk_text = item["chunk"]

        # hash کل متن
        full_hash = hashlib.md5(chunk_text.encode("utf-8")).hexdigest()

        # hash از 150 کاراکتر اول و آخر
        start_hash = hashlib.md5(chunk_text[:150].encode("utf-8")).hexdigest()
        end_hash = hashlib.md5(chunk_text[-150:].encode("utf-8")).hexdigest()

        combined_hash = f"{start_hash}_{end_hash}"

        if full_hash not in seen_hashes and combined_hash not in seen_hashes:
            seen_hashes.add(full_hash)
            seen_hashes.add(combined_hash)
            unique_chunks.append(item)

    return unique_chunks


def process_jsonl(input_file, output_file):
    """پردازش فایل JSONL"""
    total_records = 0
    total_chunks = 0
    skipped_records = 0
    all_chunks = []

    with open(input_file, "r", encoding="utf-8") as infile:
        for line in infile:
            try:
                record = json.loads(line)
                total_records += 1

                content = record.get("content", "")

                if not content.strip():
                    skipped_records += 1
                    continue

                cleaned = advanced_text_cleaning(content)
                cleaned = remove_noise_words(cleaned)

                chunks = smart_chunk_for_embedding(
                    cleaned, target_length=500, overlap=40
                )

                if not chunks:
                    skipped_records += 1
                    continue

                for idx, chunk in enumerate(chunks):
                    # پاکسازی نهایی
                    chunk = clean_chunk_start(chunk)

                    if not is_valid_chunk(chunk):
                        continue

                    chunk_title = generate_smart_title(chunk)
                    section = extract_section_from_url(record.get("source", ""))

                    metadata = {
                        "section": section,
                        "chunk_title": chunk_title,
                        "chunk_index": idx,
                        "chunk_length": len(chunk),
                    }

                    output_record = {"chunk": chunk, "metadata": metadata}
                    all_chunks.append(output_record)
                    total_chunks += 1

            except json.JSONDecodeError as e:
                print(f"خطا در خواندن JSON: {e}")
                skipped_records += 1
                continue
            except Exception as e:
                print(f"خطای غیرمنتظره: {e}")
                skipped_records += 1
                continue

    print(f"حذف چانک‌های تکراری...")
    unique_chunks = deduplicate_chunks(all_chunks)
    duplicates_removed = total_chunks - len(unique_chunks)

    with open(output_file, "w", encoding="utf-8") as outfile:
        for record in unique_chunks:
            outfile.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"\n{'='*50}")
    print(f"پردازش کامل شد!")
    print(f"{'='*50}")
    print(f"تعداد رکوردهای خوانده شده: {total_records}")
    print(f"تعداد چانک‌های تولید شده: {total_chunks}")
    print(f"تعداد چانک‌های تکراری حذف شده: {duplicates_removed}")
    print(f"تعداد چانک‌های نهایی: {len(unique_chunks)}")
    print(f"تعداد رکوردهای رد شده: {skipped_records}")
    print(
        f"میانگین چانک به ازای هر رکورد: {len(unique_chunks)/max(total_records-skipped_records, 1):.2f}"
    )

    # آمار طول چانک‌ها
    lengths = [item["metadata"]["chunk_length"] for item in unique_chunks]
    if lengths:
        print(f"میانگین طول چانک: {sum(lengths)/len(lengths):.0f} کاراکتر")
        print(f"کوتاه‌ترین چانک: {min(lengths)} کاراکتر")
        print(f"بلندترین چانک: {max(lengths)} کاراکتر")

    print(f"{'='*50}\n")


if __name__ == "__main__":
    input_file = "/Users/mahditaghi/Desktop/project/chatbot-as/Data/tabdeal_help_dropduplicated_and_clean.jsonl"
    output_file = "tabdeal_chunks.jsonl"

    print("شروع پردازش...")
    process_jsonl(input_file, output_file)
    print(f"چانک‌ها در فایل '{output_file}' ذخیره شدند.")
