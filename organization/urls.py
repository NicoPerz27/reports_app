from django.urls import path
from . import views

app_name = 'organization'

urlpatterns = [
    # Groups
    path('group/add/', views.group_create_view, name='group_create'),
    path('group/<int:group_id>/edit/', views.group_edit_view, name='group_edit'),
    
    # Publishers
    path('publisher/add/', views.publisher_create_view, name='publisher_create'),
    path('publisher/<int:publisher_id>/edit/', views.publisher_edit_view, name='publisher_edit'),
    
    # Invitation
    path('invite/<uuid:token>/', views.group_invite_view, name='group_invite'),
]
