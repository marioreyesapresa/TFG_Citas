import re
from django import forms
from ..models import Paciente

class PacienteForm(forms.ModelForm):
    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        patron = r'^[6789]\d{8}$'
        if not re.match(patron, telefono):
            raise forms.ValidationError("Introduce un número de teléfono español válido (9 dígitos y empezar por 6, 7, 8 o 9).")
        return telefono
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
