from django.db import models


class ChatLog(models.Model):
    user_message = models.TextField()
    ai_response = models.TextField()
    handoff_required = models.BooleanField(default=False)
    handoff_reason = models.TextField(null=True, blank=True)
    request_received_at = models.DateTimeField()
    response_generated_at = models.DateTimeField()
    processing_time_ms = models.PositiveIntegerField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"ChatLog #{self.id} ({self.created_at.isoformat()})"
