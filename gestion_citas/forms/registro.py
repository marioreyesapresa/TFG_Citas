from django import forms
from django.contrib.auth.models import User
from ..models import Paciente, Turno

class UserRegistrationForm(forms.ModelForm):
    # Campos de User
    first_name = forms.CharField(label='Nombre', max_length=150, required=True, widget=forms.TextInput(attrs={'placeholder': 'Tu nombre'}))
    last_name = forms.CharField(label='Apellidos', max_length=150, required=True, widget=forms.TextInput(attrs={'placeholder': 'Tus apellidos'}))
    email = forms.EmailField(label='Correo electrónico', required=True, widget=forms.EmailInput(attrs={'placeholder': 'tu@email.com'}))
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput(attrs={'placeholder': 'Mínimo 8 caracteres'}), required=True)
    
    # Campos de Paciente
    dni = forms.CharField(label='DNI', max_length=9, min_length=9, required=True, widget=forms.TextInput(attrs={'placeholder': '12345678X'}))
    telefono = forms.CharField(label='Teléfono', max_length=15, required=True, widget=forms.TextInput(attrs={'placeholder': '600000000'}))
    fecha_nacimiento = forms.DateField(
        label='Fecha de Nacimiento', 
        required=True, 
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    preferencia_turno = forms.ChoiceField(
        label='Preferencia de Horario',
        choices=Turno.choices,
        initial=Turno.MANANA,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']
        help_texts = {
            'username': None, # Ocultar el help text por defecto de Django
        }

    def clean_dni(self):
        dni = self.cleaned_data.get('dni')
        if Paciente.objects.filter(dni=dni).exists():
            raise forms.ValidationError("Este DNI ya está registrado en el sistema.")
        return dni

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            # Crear el perfil de paciente automáticamente
            Paciente.objects.create(
                user=user,
                dni=self.cleaned_data['dni'],
                telefono=self.cleaned_data['telefono'],
                fecha_nacimiento=self.cleaned_data['fecha_nacimiento'],
                preferencia_turno=self.cleaned_data['preferencia_turno']
            )
        return user
