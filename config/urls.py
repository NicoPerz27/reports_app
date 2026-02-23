
"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')), # Login/Logout/Password reset
    path('org/', include('organization.urls')),             # Custom Management Views
    path('', include('reports.urls')),      # Dashboard at /dashboard/ and root
    path('', include('public_access.urls')), # /report/uuid/
]
