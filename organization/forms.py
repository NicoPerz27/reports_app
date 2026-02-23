from django import forms
from .models import Group, Publisher
from accounts.models import User

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Grupo 1 - Centro'})
        }
        labels = {
            'name': 'Nombre del Grupo'
        }

class PublisherForm(forms.ModelForm):
    class Meta:
        model = Publisher
        fields = ['first_name', 'last_name', 'group', 'gender', 'spiritual_hope', 'date_of_birth', 'baptism_date', 
                  'is_regular_pioneer', 'is_special_pioneer', 'is_missionary', 'is_elder', 'is_ministerial_servant', 'active']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'group': forms.Select(attrs={'class': 'form-select'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'spiritual_hope': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'baptism_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_regular_pioneer': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_special_pioneer': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_missionary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_elder': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_ministerial_servant': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'first_name': 'Nombre(s)',
            'last_name': 'Apellido(s)',
            'group': 'Grupo Asignado',
            'gender': 'Sexo',
            'spiritual_hope': 'Esperanza',
            'date_of_birth': 'Fecha de Nacimiento',
            'baptism_date': 'Fecha de Bautismo',
            'is_regular_pioneer': 'Precursor Regular',
            'is_special_pioneer': 'Precursor Especial',
            'is_missionary': 'Misionero',
            'is_elder': 'Anciano',
            'is_ministerial_servant': 'Siervo Ministerial',
            'active': 'Activo'
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and hasattr(user, 'congregation') and user.congregation:
            self.fields['group'].queryset = Group.objects.filter(congregation=user.congregation)
        elif user and user.role == User.Role.GROUP_ADMIN:
             self.fields['group'].queryset = user.managed_groups.all()
             # If only one group, select it by default
             if self.fields['group'].queryset.count() == 1:
                 self.fields['group'].initial = self.fields['group'].queryset.first()
