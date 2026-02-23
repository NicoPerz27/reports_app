
from django.contrib import admin
from .models import Group, Publisher, Congregation

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'congregation')
    search_fields = ('name',)
    filter_horizontal = ('overseers',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'congregation') and request.user.congregation:
            return qs.filter(congregation=request.user.congregation)
        return qs.none()

    def save_model(self, request, obj, form, change):
        if not obj.congregation and hasattr(request.user, 'congregation') and request.user.congregation:
            obj.congregation = request.user.congregation
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        # Allow if user is Cong Admin
        if hasattr(request.user, 'role') and request.user.role == 'CONG_ADMIN': # Checking string or enum
            return True
        # Also rely on standard permissions
        return super().has_add_permission(request)

@admin.register(Congregation)
class CongregationAdmin(admin.ModelAdmin):
    list_display = ('name', 'city')


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'group', 'is_regular_pioneer', 'active')
    list_filter = ('group', 'is_regular_pioneer', 'active')
    search_fields = ('last_name', 'first_name')
    readonly_fields = ('uuid',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'congregation') and request.user.congregation:
            return qs.filter(group__congregation=request.user.congregation)
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "group" and not request.user.is_superuser:
             if hasattr(request.user, 'congregation') and request.user.congregation:
                kwargs["queryset"] = Group.objects.filter(congregation=request.user.congregation)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
