
from django.contrib import admin
from .models import ServiceYear, MonthlyReport

@admin.register(ServiceYear)
class ServiceYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_current')
    list_filter = ('is_current',)

@admin.register(MonthlyReport)
class MonthlyReportAdmin(admin.ModelAdmin):
    list_display = ('publisher', 'month', 'status', 'participation', 'hours')
    list_filter = ('month', 'status', 'publisher__group')
    search_fields = ('publisher__last_name', 'publisher__first_name')
    date_hierarchy = 'month'
