from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Group, Publisher
from .forms import GroupForm, PublisherForm
from accounts.models import User
from django.db import transaction
from django.contrib.auth import login

# --- INVITATION SYSTEM ---

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

# --- GROUP MANAGEMENT ---

@login_required
def group_create_view(request):
    if request.user.role != User.Role.CONG_ADMIN and not request.user.is_superuser:
        return render(request, '403.html', status=403)

    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            if request.user.congregation:
                group.congregation = request.user.congregation
            group.save()
            messages.success(request, f'Grupo "{group.name}" creado correctamente.')
            return redirect('reports:dashboard')
    else:
        form = GroupForm()

    return render(request, 'organization/group_form.html', {'form': form, 'title': 'Crear Nuevo Grupo'})

@login_required
def group_edit_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    
    # Permission check
    if request.user.role != User.Role.CONG_ADMIN and not request.user.is_superuser:
        return render(request, '403.html', status=403)
    if request.user.congregation and group.congregation != request.user.congregation:
        return render(request, '403.html', status=403)

    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, f'Grupo "{group.name}" actualizado.')
            return redirect('reports:dashboard')
    else:
        form = GroupForm(instance=group)

    return render(request, 'organization/group_form.html', {'form': form, 'title': f'Editar {group.name}'})

# --- PUBLISHER MANAGEMENT ---

@login_required
def publisher_create_view(request):
    # Allow Cong Admin or Group Admin to create? Usually Cong Admin.
    # Requirement says "Cong Admin creates groups", "Group Admin manages publishers".
    # Let's allow both to add publishers, but scoped.
    
    if request.method == 'POST':
        form = PublisherForm(request.POST, user=request.user)
        if form.is_valid():
            publisher = form.save(commit=False)
            
            # Security verification: Ensure the selected group belongs to user (if Group Admin)
            if request.user.role == User.Role.GROUP_ADMIN:
                if publisher.group not in request.user.managed_groups.all():
                     messages.error(request, "No tienes permiso para agregar publicadores a este grupo.")
                     return render(request, 'organization/publisher_form.html', {'form': form, 'title': 'Registrar Publicador'})
            
            publisher.save()
            messages.success(request, f'Publicador "{publisher}" registrado.')
            return redirect('reports:dashboard')
    else:
        form = PublisherForm(user=request.user)

    return render(request, 'organization/publisher_form.html', {'form': form, 'title': 'Registrar Publicador'})

@login_required
def publisher_edit_view(request, publisher_id):
    publisher = get_object_or_404(Publisher, id=publisher_id)
    
    # Permission Check
    has_access = False
    if request.user.is_superuser:
        has_access = True
    elif request.user.role == User.Role.CONG_ADMIN and request.user.congregation == publisher.group.congregation:
        has_access = True
    elif publisher.group in request.user.managed_groups.all():
        has_access = True
        
    if not has_access:
        return render(request, '403.html', status=403)

    if request.method == 'POST':
        form = PublisherForm(request.POST, instance=publisher, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Datos de "{publisher}" actualizados.')
            return redirect('reports:dashboard')
    else:
        form = PublisherForm(instance=publisher, user=request.user)

    return render(request, 'organization/publisher_form.html', {'form': form, 'title': 'Editar Publicador'})
