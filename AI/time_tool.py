import re
from typing import Any, Dict, Optional


class TimeTool:

    TIME_DATA = {
        "deposit": {
            "rial": {
                "working_hours": "۰۸:۰۰ تا ۲۳:۰۰",
                "processing_time": "آنی (کمتر از ۱ دقیقه)",
                "days": "همه روزه (حتی تعطیلات)",
            },
            "crypto": {
                "working_hours": "۲۴/۷ (همیشه)",
                "processing_time": "بسته به تأییدات شبکه (معمولاً ۱۰-۳۰ دقیقه)",
                "confirmations": {
                    "bitcoin": "۳ تأییدیه",
                    "ethereum": "۱۲ تأییدیه",
                    "tether": "۱۲ تأییدیه",
                },
            },
        },
        "withdrawal": {
            "rial": {
                "working_hours": "۰۸:۰۰ تا ۲۳:۰۰",
                "processing_time": "حداکثر ۲۴ ساعت کاری",
                "instant_limit": "تا ۵۰ میلیون تومان: آنی",
                "days": "روزهای کاری (شنبه تا چهارشنبه)",
            },
            "crypto": {
                "working_hours": "۲۴/۷ (همیشه)",
                "processing_time": "۱۰ تا ۳۰ دقیقه پس از تأیید",
                "security_check": (
                    "برداشت‌های بالای ۱۰۰ میلیون تومان نیاز به بررسی امنیتی دارند"
                ),
            },
        },
    }

    TIME_QUERY_KEYWORDS = (
        "زمان",
        "ساعت",
        "ساعات",
        "کاری",
        "پردازش",
        "چه موقع",
        "چه زمانی",
        "کی",
        "چقدر طول",
        "برداشت",
        "واریز",
        "تسویه",
        "withdraw",
        "deposit",
    )

    @staticmethod
    def get_function_schema() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_transaction_time_info",
                "description": (
                    "زمان و شرایط واریز یا برداشت ریالی/رمزارز؛ "
                    "ساعات کاری، SLA و محدودیت‌ها."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "transaction_type": {
                            "type": "string",
                            "enum": ["deposit", "withdrawal"],
                            "description": "واریز یا برداشت",
                        },
                        "currency_type": {
                            "type": "string",
                            "enum": ["rial", "crypto"],
                            "description": "ریالی یا رمزارز",
                        },
                        "specific_crypto": {
                            "type": "string",
                            "enum": ["bitcoin", "ethereum", "tether", "general"],
                            "description": "در صورت رمزارز، کدام شبکه",
                        },
                    },
                    "required": ["transaction_type", "currency_type"],
                },
            },
        }

    @classmethod
    def execute(
        cls,
        transaction_type: str,
        currency_type: str,
        specific_crypto: Optional[str] = None,
    ) -> str:
        try:
            data = cls.TIME_DATA.get(transaction_type, {}).get(currency_type, {})
            if not data:
                return "برای این ترکیب چیزی ثبت نشده."

            txn_fa = "واریز" if transaction_type == "deposit" else "برداشت"
            cur_fa = "ریالی" if currency_type == "rial" else "رمزارزی"
            parts = [f"زمان‌بندی {txn_fa} {cur_fa}"]

            if "working_hours" in data:
                parts.append(f"ساعات فعال: {data['working_hours']}")
            if "processing_time" in data:
                parts.append(f"زمان پردازش: {data['processing_time']}")
            if "days" in data:
                parts.append(f"روزها: {data['days']}")
            if "instant_limit" in data:
                parts.append(data["instant_limit"])
            if "security_check" in data:
                parts.append(data["security_check"])

            if currency_type == "crypto" and "confirmations" in data:
                parts.append("تأییدیه شبکه:")
                if specific_crypto and specific_crypto in data["confirmations"]:
                    parts.append(f"— {specific_crypto}: {data['confirmations'][specific_crypto]}")
                else:
                    for crypto, conf in data["confirmations"].items():
                        parts.append(f"— {crypto}: {conf}")

            return "\n".join(parts)
        except Exception as e:
            return f"خطا در خواندن دادهٔ زمانی: {str(e)}"

    @staticmethod
    def is_time_query(query: str) -> bool:
        if not query:
            return False
        q = query.strip().lower()
        return any(k in q for k in TimeTool.TIME_QUERY_KEYWORDS)

    @staticmethod
    def infer_function_args_from_query(query: str) -> Dict[str, Any]:
        q = re.sub(r"\s+", " ", (query or "").strip().lower())
        transaction_type = "withdrawal"
        currency_type = "rial"
        specific_crypto = None

        deps = ("واریز", "شارژ", "deposit", "واریزی")
        wds = ("برداشت", "withdraw", "برداشتی", "تسویه")
        cryptos = (
            "رمزارز",
            "کریپتو",
            "ارز دیجیتال",
            "crypto",
            "btc",
            "eth",
            "usdt",
            "بیت",
            "اتریوم",
            "تتر",
            "بیت کوین",
            "بیتکوین",
            "bitcoin",
            "ethereum",
            "tether",
        )

        if any(x in q for x in deps):
            transaction_type = "deposit"
        elif any(x in q for x in wds):
            transaction_type = "withdrawal"

        if any(x in q for x in cryptos):
            currency_type = "crypto"

        if any(x in q for x in ("btc", "bitcoin", "بیت کوین", "بیتکوین")):
            specific_crypto = "bitcoin"
        elif any(x in q for x in ("eth", "ethereum", "اتریوم")):
            specific_crypto = "ethereum"
        elif any(x in q for x in ("usdt", "tether", "تتر")):
            specific_crypto = "tether"

        return {
            "transaction_type": transaction_type,
            "currency_type": currency_type,
            "specific_crypto": specific_crypto,
        }

    @classmethod
    def handle_function_call(cls, function_args: Dict[str, Any]) -> str:
        return cls.execute(
            transaction_type=function_args.get("transaction_type"),
            currency_type=function_args.get("currency_type"),
            specific_crypto=function_args.get("specific_crypto"),
        )
