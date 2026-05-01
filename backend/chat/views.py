from time import perf_counter

from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import MessageSerializer
from .services.ai_service import ask_ai
from .services.chat_logging_service import save_chat_log


class UserMessageAPI(APIView):

    def post(self, request):
        request_received_at = timezone.now()
        start_time = perf_counter()

        serializer = MessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_message = serializer.validated_data["message"]
        chat_history = request.data.get("chat_history", [])

        ai_result = ask_ai(user_message, chat_history)
        response_generated_at = timezone.now()
        processing_time_ms = int((perf_counter() - start_time) * 1000)

        log_metadata = {
            "chat_history_count": len(chat_history),
            "client_ip": request.META.get("REMOTE_ADDR"),
            "user_agent": request.META.get("HTTP_USER_AGENT"),
        }
        if ai_result.get("monitoring"):
            log_metadata["monitoring"] = ai_result["monitoring"]

        save_chat_log(
            user_message=user_message,
            ai_response=ai_result["response"],
            handoff_required=ai_result["handoff_required"],
            handoff_reason=ai_result.get("handoff_reason"),
            request_received_at=request_received_at,
            response_generated_at=response_generated_at,
            processing_time_ms=processing_time_ms,
            metadata=log_metadata,
        )

        return Response(
            {
                "question": user_message,
                "answer": ai_result["response"],
                "handoff_required": ai_result["handoff_required"],
                "handoff_reason": ai_result.get("handoff_reason"),
                "processing_time_ms": processing_time_ms,
            }
        )
