import re
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

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        # Patrón: 9 dígitos, empieza por 6, 7, 8 o 9
        patron = r'^[6789]\d{8}$'
        if not re.match(patron, telefono):
            raise forms.ValidationError("Introduce un número de teléfono español válido (9 dígitos y empezar por 6, 7, 8 o 9).")
        return telefono

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get('fecha_nacimiento')
        if fecha > forms.fields.datetime.date.today():
            raise forms.ValidationError("La fecha de nacimiento no puede ser en el futuro.")
        if fecha.year < 1900:
            raise forms.ValidationError("El año de nacimiento debe ser posterior a 1900.")
        return fecha

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
