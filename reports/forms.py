from django import forms
from .models import MonthlyReport

class MonthlyReportForm(forms.ModelForm):
    class Meta:
        model = MonthlyReport
        fields = ['participation', 'bible_studies', 'auxiliary_pioneer', 'hours', 'remarks']
        widgets = {
            'participation': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'bible_studies': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'auxiliary_pioneer': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'hours': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'participation': 'Participó en el ministerio',
            'bible_studies': 'Cursos Bíblicos',
            'auxiliary_pioneer': 'Precursor Auxiliar',
            'hours': 'Horas',
            'remarks': 'Notas / Observaciones'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optional: Add validation logic here if needed beyond model cleaning
