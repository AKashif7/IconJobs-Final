from django.urls import path
from django.shortcuts import redirect
from . import views

urlpatterns = [
    path('inbox/', views.inbox, name='inbox'),
    path('inbox/<int:conversation_id>/', views.inbox, name='inbox_conversation'),
    path('', lambda req: redirect('inbox'), name='conversations_list'),
    path('<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),

    path('api/start/', views.start_conversation, name='start_conversation'),
    path('api/<int:conversation_id>/messages/', views.get_conversation_messages, name='get_conversation_messages'),
    path('api/message/send/', views.send_message, name='send_message'),
    path('api/message/read/', views.mark_message_read, name='mark_message_read'),
    path('api/<int:conversation_id>/typing/', views.set_typing_indicator, name='set_typing_indicator'),
    path('api/<int:conversation_id>/typing/get/', views.get_typing_indicators, name='get_typing_indicators'),
    path('api/unread/', views.get_unread_count, name='get_unread_count'),
    path('api/online/', views.get_online_status, name='get_online_status'),
    path('api/ping/', views.ping, name='ping'),
]
