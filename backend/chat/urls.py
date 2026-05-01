from django.urls import path
from .views import UserMessageAPI

urlpatterns = [
    path("message/", UserMessageAPI.as_view(), name="user_message"),
]
