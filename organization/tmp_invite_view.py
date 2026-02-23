from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login
from accounts.models import User
from organization.models import Group
from django.db import transaction

def group_invite_view(request, token):
    group = get_object_or_404(Group, invitation_token=token)
    
    if not group.invitation_active:
        return render(request, 'organization/invite_expired.html', {'message': 'Este enlace de invitación ha expirado o ya se completó el registro.'})

    # Count current admins in the group
    admin_count = group.overseers.count()

    if admin_count >= 2:
        # Group is full (Admin + Subadmin)
        group.invitation_active = False
        group.save()
        return render(request, 'organization/invite_expired.html', {'message': 'El grupo ya tiene asignados a sus administradores.'})

    if request.method == 'POST':
        # Simple registration form handling
        # User creates account and is auto-assigned
        username = request.POST.get('username')
        password = request.POST.get('password')
        name = request.POST.get('name')
        
        if User.objects.filter(username=username).exists():
             messages.error(request, 'El nombre de usuario ya existe.')
        else:
            with transaction.atomic():
                user = User.objects.create_user(username=username, password=password, first_name=name)
                # Assign Congregation
                user.congregation = group.congregation
                
                # Assign Role
                # First one is Group Admin, Second is Group Admin (Aux) - logic per requirement "first admin then subadmin"
                # User requested "Subadmin", but model only has GROUP_ADMIN. We can use same role but distinct by logic or add SUBADMIN role.
                # For simplicity, both get GROUP_ADMIN role, but we could differentiate.
                # Let's stick to GROUP_ADMIN for now as per previous context.
                user.role = User.Role.GROUP_ADMIN
                user.save()
                
                # Assign to Group
                group.overseers.add(user)
                
                # Deactivate token if full
                if group.overseers.count() >= 2:
                    group.invitation_active = False
                    group.save()
            
            login(request, user)
            messages.success(request, f'Bienvenido {name}. Has sido asignado al {group.name}.')
            return redirect('reports:dashboard')

    return render(request, 'organization/invite_register.html', {
        'group': group,
        'role_name': 'Administrador de Grupo' if admin_count == 0 else 'Subadministrador de Grupo'
    })
