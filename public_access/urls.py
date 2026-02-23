
from django.urls import path
from . import views

app_name = 'public_access'

urlpatterns = [
    path('report/<uuid:publisher_uuid>/', views.publisher_report_view, name='publisher_report'),
]
