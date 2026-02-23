
from django import forms
from reports.models import MonthlyReport
from django.utils.translation import gettext_lazy as _

class PublicReportForm(forms.ModelForm):
    """
    Form for publishers to submit their monthly report.
    Simplified fields, hiding internal status.
    """
    class Meta:
        model = MonthlyReport
        fields = ['participation', 'bible_studies', 'auxiliary_pioneer', 'hours', 'remarks']
        widgets = {
            'remarks': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'participation': forms.CheckboxInput(attrs={'class': 'form-check-input', 'style': 'width: 25px; height: 25px;'}),
            'bible_studies': forms.NumberInput(attrs={'class': 'form-control'}),
            'hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'auxiliary_pioneer': forms.CheckboxInput(attrs={'class': 'form-check-input', 'style': 'width: 25px; height: 25px;'}),
        }
        labels = {
            'participation': _('Participé en el ministerio'),
            'bible_studies': _('Estudios Bíblicos'),
            'auxiliary_pioneer': _('Precursor Auxiliar'),
            'hours': _('Horas'),
            'remarks': _('Notas / Comentarios'),
        }
        help_texts = {
            'participation': _('Marque si participó en cualquier rasgo del ministerio este mes.'),
        }
