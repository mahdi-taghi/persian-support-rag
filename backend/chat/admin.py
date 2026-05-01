from django.contrib import admin

from .models import ChatLog


@admin.register(ChatLog)
class ChatLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created_at",
        "monitor_hint",
        "monitor_path",
        "handoff_required",
        "processing_time_ms",
    )
    search_fields = ("user_message", "ai_response", "handoff_reason")
    list_filter = ("handoff_required", "created_at")

    @admin.display(description="سرنخ کیفیت")
    def monitor_hint(self, obj):
        m = (obj.metadata or {}).get("monitoring") or {}
        return m.get("hint", "—")

    @admin.display(description="مسیر پردازش")
    def monitor_path(self, obj):
        m = (obj.metadata or {}).get("monitoring") or {}
        return m.get("path", "—")
