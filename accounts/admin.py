
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib import messages
from .models import User

@admin.action(description="Cambiar contraseña a los usuarios seleccionados")
def update_passwords_action(modeladmin, request, queryset):
    if request.POST.get('apply'):
        new_pass = request.POST.get('new_password')
        if new_pass:
            for user in queryset:
                user.set_password(new_pass)
                user.save()
            modeladmin.message_user(request, f"Se actualizó la contraseña de {queryset.count()} usuario(s) exitosamente.")
            return HttpResponseRedirect(request.get_full_path())
        else:
            modeladmin.message_user(request, "La contraseña no puede estar vacía.", level=messages.ERROR)
            return HttpResponseRedirect(request.get_full_path())

    context = {
        'queryset': queryset,
        'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
        'title': 'Designe nueva contraseña',
    }
    return render(request, 'admin/change_password_action.html', context)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Custom user admin to manage the custom User model.
    """
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'congregation', 'is_staff')
    list_filter = ('role', 'congregation', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    
    fieldsets = UserAdmin.fieldsets + (
        ('S-21-S Custom Fields', {'fields': ('role', 'congregation')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('S-21-S Custom Fields', {'fields': ('role', 'congregation')}),
    )

    actions = [update_passwords_action]
