import chromadb
import json
import os
from dotenv import load_dotenv
import numpy as np
from openai import OpenAI
from rank_bm25 import BM25Okapi

from human_handler import should_handoff_to_human
from prompt_guard import PromptGuard
from rag_monitor import monitor_rag_answer, monitor_skipped
from time_tool import TimeTool

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

_metis_openai_base = os.getenv("METIS_OPENAI_BASE_URL")
if not _metis_openai_base:
    raise RuntimeError("METIS_OPENAI_BASE_URL is not set")

openai_client = OpenAI(
    api_key=os.getenv("METIS_API_KEY"),
    base_url=_metis_openai_base.rstrip("/"),
)

BASE_DIR = os.path.dirname(__file__)
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")

client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_collection(name="binance_help_docs")


def tokenize_persian(text):
    return text.split()


def bm25_search(query, all_docs, all_ids, top_k=10):
    tokenized_docs = [tokenize_persian(doc) for doc in all_docs]
    bm25 = BM25Okapi(tokenized_docs)
    tokenized_query = tokenize_persian(query)
    scores = bm25.get_scores(tokenized_query)
    top_indices = np.argsort(scores)[::-1][:top_k]
    return [(all_ids[i], scores[i]) for i in top_indices]


def reciprocal_rank_fusion(semantic_results, bm25_results, k=60):
    scores = {}
    for rank, (doc_id, _) in enumerate(semantic_results, 1):
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)
    for rank, (doc_id, _) in enumerate(bm25_results, 1):
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def get_ai_response(query: str, chat_history: list = None):
    try:
        security_check = PromptGuard.validate_prompt(query, use_llm=True)

        if not security_check["is_safe"]:
            return {
                "response": (
                    "این پیام با سیاست‌های امنیتی سازگار نیست.\n"
                    f"توضیح: {security_check['reason']}\n\n"
                    "لطفاً سوال خود را مستقیم و مرتبط با خدمات بپرسید."
                ),
                "handoff_required": False,
                "handoff_reason": f"Security: {security_check['reason']}",
                "monitoring": monitor_skipped("security_block"),
            }

        if TimeTool.is_time_query(query):
            inferred_args = TimeTool.infer_function_args_from_query(query)
            direct_time_response = TimeTool.handle_function_call(inferred_args)
            return {
                "response": direct_time_response,
                "handoff_required": False,
                "handoff_reason": None,
                "monitoring": monitor_skipped("time_tool"),
            }

        handoff_required, handoff_reason = should_handoff_to_human(query)

        if handoff_required:
            return {
                "response": (
                    "این موضوع به پشتیبانی انسانی واگذار شد. "
                    "کمی صبر کنید تا همکار ما پاسخ بدهد."
                ),
                "handoff_required": True,
                "handoff_reason": handoff_reason,
                "monitoring": monitor_skipped("handoff"),
            }

        all_data = collection.get()
        all_docs = all_data["documents"]
        all_ids = all_data["ids"]

        response = openai_client.embeddings.create(
            input=query,
            model="text-embedding-3-small",
            encoding_format="float",
        )
        query_embedding = response.data[0].embedding

        semantic_results = collection.query(
            query_embeddings=[query_embedding], n_results=10
        )
        semantic_ranked = list(
            zip(semantic_results["ids"][0], semantic_results["distances"][0])
        )

        bm25_ranked = bm25_search(query, all_docs, all_ids, top_k=10)
        hybrid_ranked = reciprocal_rank_fusion(semantic_ranked, bm25_ranked)

        doc_map = {doc_id: doc for doc_id, doc in zip(all_ids, all_docs)}
        context = ""
        for i, (doc_id, _) in enumerate(hybrid_ranked[:3], 1):
            document = doc_map[doc_id]
            context += f"[{i}]\n{document}\n\n"

        system_message = (
            "دستیار پشتیبانی صرافی تبدیل هستی. فقط با تکیه به متن روبه‌رو جواب بده؛ "
            "اگر جواب قطع نیست بگو نمی‌دانی.\n\n"
            f"متن:\n{context}\n"
            "برای سؤال‌های زمان واریز/برداشت می‌توانی از تابع get_transaction_time_info استفاده کنی.\n"
            "پاسخ را فارسی و کوتاه نگه دار."
        )

        messages = [{"role": "system", "content": system_message}]
        if chat_history:
            messages.extend(chat_history)
        messages.append({"role": "user", "content": query})

        llm_response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=[TimeTool.get_function_schema()],
            tool_choice="auto",
            temperature=0.3,
            max_tokens=500,
        )

        response_message = llm_response.choices[0].message

        if response_message.tool_calls:
            tool_call = response_message.tool_calls[0]
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments or "{}")

            if function_name == "get_transaction_time_info":
                if not function_args.get("transaction_type") or not function_args.get(
                    "currency_type"
                ):
                    function_args = TimeTool.infer_function_args_from_query(query)
                function_response = TimeTool.handle_function_call(function_args)
            else:
                function_response = "تابعی برای این نام تعریف نشده."

            messages.append(response_message)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": function_response,
                }
            )

            final_response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.3,
                max_tokens=500,
            )
            final_content = final_response.choices[0].message.content
        else:
            final_content = response_message.content

        monitoring = monitor_rag_answer(
            hybrid_top3=hybrid_ranked[:3],
            semantic_ranked=semantic_ranked,
            context_text=context,
            answer_text=final_content or "",
            openai_client=openai_client,
        )

        return {
            "response": final_content,
            "handoff_required": False,
            "handoff_reason": None,
            "monitoring": monitoring,
        }

    except Exception as e:
        return {
            "response": f"خطای داخلی: {str(e)}",
            "handoff_required": False,
            "handoff_reason": None,
            "monitoring": monitor_skipped("error", str(e)),
        }
