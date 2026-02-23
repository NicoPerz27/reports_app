
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    Custom user model for the S-21-S system.
    Supports multi-tenancy via Congregation link.
    """
    class Role(models.TextChoices):
        CONG_ADMIN = 'CONG_ADMIN', 'Administrador de Congregación'
        GROUP_ADMIN = 'GROUP_ADMIN', 'Administrador de Grupo'
        VIEWER = 'VIEWER', 'Visualizador'

    role = models.CharField(
        max_length=20, 
        choices=Role.choices, 
        default=Role.GROUP_ADMIN,
        help_text="Nivel de acceso del usuario."
    )
    
    congregation = models.ForeignKey(
        'organization.Congregation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        help_text="Congregación a la que pertenece este usuario."
    )
    
    groups_managed = models.ManyToManyField('organization.Group', blank=True, related_name='managers', verbose_name="Grupos Administrados (Solo Group Admin)")

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

# Signal to auto-assign permissions
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from organization.models import Group, Publisher

@receiver(post_save, sender=User)
def assign_role_permissions(sender, instance, created, **kwargs):
    """
    Auto-assigns Django Admin permissions based on the S-21-S Role.
    """
    if instance.role == User.Role.CONG_ADMIN:
        # Get permissions for Group and Publisher
        content_type_group = ContentType.objects.get_for_model(Group)
        content_type_pub = ContentType.objects.get_for_model(Publisher)
        
        perms = Permission.objects.filter(
            content_type__in=[content_type_group, content_type_pub],
            codename__in=['add_group', 'change_group', 'view_group', 
                          'add_publisher', 'change_publisher', 'view_publisher']
        )
        instance.user_permissions.add(*perms)
        # Ensure staff status
        if not instance.is_staff:
            instance.is_staff = True
            instance.save()
            
    elif instance.role == User.Role.GROUP_ADMIN:
        # Group admins usually don't need Django Admin access, but if they do:
        # They only need to change/view publishers, not groups.
        # For now, likely handled via custom dashboard, so no strict admin perms needed unless requested.
        pass
