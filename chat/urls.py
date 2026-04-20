from django.urls import path
from . import views

urlpatterns = [
    # Conversation list and detail
    path('', views.conversations_list, name='conversations_list'),
    path('<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    
    # AJAX/API endpoints for messaging
    path('api/start/', views.start_conversation, name='start_conversation'),
    path('api/<int:conversation_id>/messages/', views.get_conversation_messages, name='get_conversation_messages'),
    path('api/message/send/', views.send_message, name='send_message'),
    path('api/message/read/', views.mark_message_read, name='mark_message_read'),
    path('api/<int:conversation_id>/typing/', views.set_typing_indicator, name='set_typing_indicator'),
    path('api/<int:conversation_id>/typing/get/', views.get_typing_indicators, name='get_typing_indicators'),
]
