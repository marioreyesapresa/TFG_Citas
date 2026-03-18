from django import forms
from ..models import Paciente

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ['telefono', 'preferencia_turno']
        widgets = {
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 600123456',
                'style': 'width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #ddd; margin-top: 5px;'
            }),
            'preferencia_turno': forms.Select(attrs={
                'class': 'form-select',
                'style': 'width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #ddd; margin-top: 5px;'
            }),
        }
        labels = {
            'telefono': 'Número de Teléfono',
            'preferencia_turno': 'Preferencia de Horario',
        }
