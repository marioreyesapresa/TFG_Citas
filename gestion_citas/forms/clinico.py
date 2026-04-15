from django import forms
from ..models import ConsultaMedica, Receta

class ConsultaForm(forms.ModelForm):
    class Meta:
        model = ConsultaMedica
        fields = [
            'motivo_consulta', 'antecedentes_alergias', 'descripcion_problema', 
            'exploracion_medica', 'pruebas_solicitadas', 'diagnostico_principal', 
            'tratamiento_pautas', 'observaciones'
        ]
        widgets = {
            'motivo_consulta': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Cefalea intensa'}),
            'antecedentes_alergias': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'RAM, antecedentes familiares...'}),
            'descripcion_problema': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Narrativa del episodio...'}),
            'exploracion_medica': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'TA, FC, Tª... Hallazgos exploración.'}),
            'pruebas_solicitadas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Rx Tórax, Analítica, ECO...'}),
            'diagnostico_principal': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Diagnóstico definitivo o presuntivo'}),
            'tratamiento_pautas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Tratamiento, derivaciones, reposo...'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Información para control interno...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Valores por defecto para ahorrar tiempo al médico
        self.fields['antecedentes_alergias'].initial = "No se refieren RAM (Reacciones Adversas a Medicamentos)."
        self.fields['exploracion_medica'].initial = "Buen estado general. Consciente, orientado y colaborador."
        self.fields['descripcion_problema'].initial = "El paciente refiere..."
        
        # Obligatorio en Formulario (aunque opcional en BD por migración)
        self.fields['diagnostico_principal'].required = True


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
