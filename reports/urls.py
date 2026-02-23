
from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('', views.dashboard_view, name='dashboard'),
    path('download/<int:publisher_id>/', views.download_pdf_view, name='download_pdf'),
    path('report/edit/<int:publisher_id>/<int:year>/<int:month>/', views.report_edit_view, name='report_edit'),
    path('group/<int:group_id>/bulk/', views.bulk_report_view, name='bulk_report'),
    path('group/<int:group_id>/scan/', views.scan_group_report_view, name='scan_report'),
]
