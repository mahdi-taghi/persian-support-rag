import json
import os
from typing import List, Dict, Any
from openai import OpenAI
import chromadb
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv
from tqdm import tqdm

# بارگذاری متغیرهای محیطی
load_dotenv()

# تنظیمات
INPUT_CHUNKS_FILE = "/Users/mahditaghi/Desktop/project/chatbot-as/tabdeal_chunks.jsonl"
OUTPUT_JSONL = "embedded_chunks.jsonl"
CHROMA_DB_PATH = "./chroma_db"
COLLECTION_NAME = "binance_help_docs"
EMBEDDING_MODEL = "text-embedding-3-small"
BATCH_SIZE = 50
CHROMA_BATCH_SIZE = 50

# ========== توابع Embedding ==========


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def get_embeddings_batch(client: OpenAI, texts: List[str]) -> List[List[float]]:
    """دریافت embedding برای چندین متن به صورت batch"""
    try:
        response = client.embeddings.create(
            input=texts,
            model=EMBEDDING_MODEL,
            encoding_format="float",
        )
        return [item.embedding for item in response.data]
    except Exception as e:
        print(f"\n❌ خطا در دریافت batch embedding: {e}")
        raise


def embed_chunks_batch(
    client: OpenAI, chunks: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Embedding چانک‌ها به صورت batch"""
    embedded_chunks = []
    failed_batches = []

    print(f"\n🔄 شروع embedding {len(chunks)} چانک با batch size {BATCH_SIZE}...")
    total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"📊 تعداد API calls مورد نیاز: {total_batches}")

    for i in tqdm(range(0, len(chunks), BATCH_SIZE), desc="Embedding Progress"):
        batch = chunks[i : i + BATCH_SIZE]

        try:
            texts = [chunk["text"] for chunk in batch]
            embeddings = get_embeddings_batch(client, texts)

            for chunk, embedding in zip(batch, embeddings):
                chunk["embedding"] = embedding
                embedded_chunks.append(chunk)

        except Exception as e:
            print(f"\n⚠️ Batch {i//BATCH_SIZE + 1} ناموفق بود: {e}")
            failed_batches.append((i, batch))
            continue

    # تلاش مجدد برای batch های ناموفق
    if failed_batches:
        print(f"\n🔄 تلاش مجدد برای {len(failed_batches)} batch ناموفق...")
        for batch_idx, batch in failed_batches:
            for chunk in batch:
                try:
                    embedding = get_embeddings_batch(client, [chunk["text"]])[0]
                    chunk["embedding"] = embedding
                    embedded_chunks.append(chunk)
                except Exception as e:
                    print(f"\n⚠️ چانک {chunk.get('id', 'unknown')} رد شد: {e}")
                    continue

    success_rate = len(embedded_chunks) / len(chunks) * 100
    print(
        f"\n✅ {len(embedded_chunks)}/{len(chunks)} چانک embed شد ({success_rate:.1f}%)"
    )

    return embedded_chunks


# ========== توابع ذخیره‌سازی ==========


def save_to_jsonl(chunks: List[Dict[str, Any]], output_file: str):
    """ذخیره چانک‌ها در فایل JSONL"""
    with open(output_file, "w", encoding="utf-8") as f:
        for chunk in chunks:
            json.dump(chunk, f, ensure_ascii=False)
            f.write("\n")

    print(f"✅ {len(chunks)} چانک در {output_file} ذخیره شد")


def save_to_chromadb(chunks: List[Dict[str, Any]], db_path: str, collection_name: str):
    """ذخیره چانک‌ها در ChromaDB"""
    print(f"\n🔄 ذخیره‌سازی در ChromaDB...")

    client = chromadb.PersistentClient(path=db_path)

    try:
        client.delete_collection(collection_name)
        print(f"🗑️  Collection قبلی حذف شد")
    except:
        pass

    collection = client.create_collection(
        name=collection_name,
        metadata={"description": "Binance Help Documents Embeddings"},
    )

    print(f"📦 ذخیره‌سازی {len(chunks)} چانک با batch size {CHROMA_BATCH_SIZE}...")

    for i in tqdm(range(0, len(chunks), CHROMA_BATCH_SIZE), desc="ChromaDB Insert"):
        batch = chunks[i : i + CHROMA_BATCH_SIZE]

        ids = [chunk["id"] for chunk in batch]
        documents = [chunk["text"] for chunk in batch]
        embeddings = [chunk["embedding"] for chunk in batch]
        metadatas = [chunk["metadata"] for chunk in batch]

        collection.add(
            ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas
        )

    print(f"✅ {len(chunks)} چانک در ChromaDB ذخیره شد")
    print(f"📁 مسیر دیتابیس: {db_path}")
    print(f"📦 نام Collection: {collection_name}")


# ========== تابع اصلی ==========


def embed_and_store(
    input_file: str, output_jsonl: str, chroma_db_path: str, collection_name: str
):
    """خواندن چانک‌ها، embedding و ذخیره‌سازی"""

    api_key = os.getenv("METIS_API_KEY")
    if not api_key:
        raise ValueError("❌ METIS_API_KEY در فایل .env تنظیم نشده است!")

    if not os.path.exists(".env"):
        print("⚠️  هشدار: فایل .env یافت نشد!")

    openai_client = OpenAI(api_key=api_key, base_url="https://api.metisai.ir/openai/v1")

    print("=" * 60)
    print("🚀 شروع پردازش Embedding")
    print("=" * 60)

    # خواندن فایل چانک‌ها با استخراج صحیح متن
    print(f"\n📥 خواندن فایل: {input_file}")
    chunks = []
    with open(input_file, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if line:
                try:
                    data = json.loads(line)

                    # 🔧 استخراج متن از کلید "chunk"
                    text = data.get("chunk", "").strip()

                    if not text:
                        print(f"⚠️ خط {idx+1}: متن خالی است")
                        continue

                    # ساخت ساختار استاندارد
                    chunk = {
                        "id": data.get("id", f"chunk_{idx}"),
                        "text": text,
                        "metadata": data.get("metadata", {}),
                        "embedding": None,
                    }

                    chunks.append(chunk)

                except json.JSONDecodeError as e:
                    print(f"⚠️ خط {idx+1} معیوب: {e}")

    print(f"✅ {len(chunks)} چانک خوانده شد")

    if not chunks:
        print("❌ هیچ چانکی خوانده نشد!")
        return

    # نمایش نمونه اولین چانک
    print(f"\n📄 نمونه اولین چانک:")
    print(f"   - ID: {chunks[0].get('id', 'N/A')}")
    print(f"   - طول متن: {len(chunks[0].get('text', ''))} کاراکتر")
    print(f"   - متادیتا: {chunks[0].get('metadata', {})}")

    # محاسبه آمار
    avg_length = sum(len(c.get("text", "")) for c in chunks) / len(chunks)
    print(f"\n📊 آمار چانک‌ها:")
    print(f"   - تعداد کل: {len(chunks)}")
    print(f"   - میانگین طول: {avg_length:.0f} کاراکتر")
    print(f"   - Batch size: {BATCH_SIZE}")
    print(f"   - تعداد API calls: {(len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE}")

    # Embedding
    embedded_chunks = embed_chunks_batch(openai_client, chunks)

    if not embedded_chunks:
        print("❌ هیچ چانکی embed نشد!")
        return

    print(f"\n✅ {len(embedded_chunks)} چانک با موفقیت embed شد")
    print(f"📊 ابعاد embedding: {len(embedded_chunks[0]['embedding'])}")

    # ذخیره‌سازی
    print("\n" + "=" * 60)
    print("💾 ذخیره‌سازی نتایج")
    print("=" * 60)

    save_to_jsonl(embedded_chunks, output_jsonl)
    save_to_chromadb(embedded_chunks, chroma_db_path, collection_name)

    # گزارش نهایی
    print("\n" + "=" * 60)
    print("🎉 پردازش با موفقیت تکمیل شد!")
    print("=" * 60)
    print(f"📊 خلاصه:")
    print(f"   - چانک‌های ورودی: {len(chunks)}")
    print(f"   - چانک‌های embed شده: {len(embedded_chunks)}")
    print(f"   - نرخ موفقیت: {len(embedded_chunks)/len(chunks)*100:.1f}%")
    print(f"   - API calls واقعی: ~{(len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE}")
    print(f"\n📁 فایل‌های خروجی:")
    print(f"   - JSONL: {output_jsonl}")
    print(f"   - ChromaDB: {chroma_db_path}")


# ========== اجرای برنامه ==========

if __name__ == "__main__":
    try:
        embed_and_store(
            INPUT_CHUNKS_FILE, OUTPUT_JSONL, CHROMA_DB_PATH, COLLECTION_NAME
        )
    except FileNotFoundError:
        print(f"❌ فایل {INPUT_CHUNKS_FILE} پیدا نشد!")
    except Exception as e:
        print(f"\n❌ خطای کلی: {e}")
        import traceback

        traceback.print_exc()
