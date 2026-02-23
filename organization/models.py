
import uuid
from django.db import models
from django.conf import settings

class Congregation(models.Model):
    """
    Represents a congregation. 
    Users and Groups belong to one congregation.
    """
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return self.name

class Group(models.Model):
    """
    Represents a specific congregation field service group.
    """
    congregation = models.ForeignKey(
        Congregation, 
        on_delete=models.CASCADE, 
        related_name='groups',
        null=True, # Allow null for migration, enforce later
        help_text="The congregation this group belongs to."
    )
    name = models.CharField(max_length=100, help_text="Name of the group (e.g., 'Group 1', 'Downtown Group').")
    overseers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='managed_groups',
        blank=True,
        help_text="Users who have admin access to this group."
    )
    
    # Invitation System
    invitation_token = models.UUIDField(default=uuid.uuid4, editable=False, null=True, blank=True, unique=True)
    invitation_active = models.BooleanField(default=True, help_text="If Invite Link is active.")

    def __str__(self):
        return f"{self.name} ({self.congregation.name if self.congregation else 'No Cong'})"

class Publisher(models.Model):
    """
    Represents a publisher in the congregation.
    """
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    
    group = models.ForeignKey(
        Group, 
        on_delete=models.CASCADE, 
        related_name='publishers',
        help_text="The group this publisher belongs to."
    )
    
    # Service bio data
    date_of_birth = models.DateField(null=True, blank=True)
    baptism_date = models.DateField(null=True, blank=True)
    
    class Gender(models.TextChoices):
        MALE = 'MALE', 'Hombre'
        FEMALE = 'FEMALE', 'Mujer'

    gender = models.CharField(max_length=10, choices=Gender.choices, default=Gender.MALE)

    class Hope(models.TextChoices):
        OTHER_SHEEP = 'OTHER_SHEEP', 'Otras Ovejas'
        ANOINTED = 'ANOINTED', 'Ungido'

    spiritual_hope = models.CharField(max_length=15, choices=Hope.choices, default=Hope.OTHER_SHEEP)

    # Privileges
    is_elder = models.BooleanField(default=False, verbose_name="Anciano")
    is_ministerial_servant = models.BooleanField(default=False, verbose_name="Siervo Ministerial")
    is_regular_pioneer = models.BooleanField(
        default=False, 
        help_text="Check if the publisher is a Regular Pioneer.",
        verbose_name="Precursor Regular"
    )
    is_special_pioneer = models.BooleanField(default=False, verbose_name="Precursor Especial")
    is_missionary = models.BooleanField(default=False, verbose_name="Misionero")
    
    # Security for self-reporting
    uuid = models.UUIDField(
        default=uuid.uuid4, 
        editable=False, 
        unique=True,
        help_text="Unique identifier for generating public access links."
    )
    
    active = models.BooleanField(default=True, help_text="Uncheck if publisher moves or becomes inactive.")

    class Meta:
        ordering = ['last_name', 'first_name']

    def clean(self):
        from django.core.exceptions import ValidationError
        
        # 1. Elder vs Ministerial Servant (Mutually Exclusive)
        if self.is_elder and self.is_ministerial_servant:
            raise ValidationError("No puede ser Anciano y Siervo Ministerial al mismo tiempo.")

        # 2. Pioneer Status (Mutually Exclusive)
        pioneer_types = [self.is_regular_pioneer, self.is_special_pioneer, self.is_missionary]
        if sum(pioneer_types) > 1:
            raise ValidationError("Solo puede tener un tipo de precursorado (Regular, Especial o Misionero).")

        # 3. Gender Restrictions
        if self.gender == self.Gender.FEMALE:
            if self.is_elder or self.is_ministerial_servant:
                 raise ValidationError("Una mujer no puede ser Anciano ni Siervo Ministerial.")
        
    def save(self, *args, **kwargs):
        self.full_clean() # Enforce validation on save
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"
