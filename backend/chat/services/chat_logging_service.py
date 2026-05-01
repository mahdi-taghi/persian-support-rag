from chat.models import ChatLog


def save_chat_log(
    *,
    user_message,
    ai_response,
    handoff_required,
    handoff_reason,
    request_received_at,
    response_generated_at,
    processing_time_ms,
    metadata=None,
):
    return ChatLog.objects.create(
        user_message=user_message,
        ai_response=ai_response,
        handoff_required=handoff_required,
        handoff_reason=handoff_reason,
        request_received_at=request_received_at,
        response_generated_at=response_generated_at,
        processing_time_ms=processing_time_ms,
        metadata=metadata or {},
    )
