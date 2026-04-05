from django import forms
from ..models import ConsultaMedica, Receta

class ConsultaForm(forms.ModelForm):
    class Meta:
        model = ConsultaMedica
        fields = ['motivo_consulta', 'diagnostico', 'observaciones']
        widgets = {
            'motivo_consulta': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Dolor de garganta'}),
            'diagnostico': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Diagnóstico médico...'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Notas adicionales...'}),
        }

class RecetaForm(forms.ModelForm):
    class Meta:
        model = Receta
        fields = ['medicamento', 'posologia', 'duracion']
        widgets = {
            'medicamento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del fármaco'}),
            'posologia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 1 cada 8 horas'}),
            'duracion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 7 días'}),
        }

RecetaFormSet = forms.inlineformset_factory(
    ConsultaMedica, Receta, form=RecetaForm, extra=1, can_delete=True
)
