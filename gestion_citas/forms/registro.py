import re
from django import forms
from django.contrib.auth.models import User
from ..models import Paciente, Turno

class UserRegistrationForm(forms.ModelForm):
    # Campos de User
    username = forms.CharField(label='Nombre de usuario', min_length=4, required=True, widget=forms.TextInput(attrs={'placeholder': 'Mínimo 4 caracteres'}))
    first_name = forms.CharField(
        label='Nombre', 
        max_length=150, 
        min_length=2,
        required=True, 
        widget=forms.TextInput(attrs={
            'placeholder': 'Tu nombre',
            'pattern': r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$',
            'title': 'El nombre solo puede contener letras y espacios.'
        })
    )
    last_name = forms.CharField(
        label='Apellidos', 
        max_length=150, 
        min_length=2,
        required=True, 
        widget=forms.TextInput(attrs={
            'placeholder': 'Tus apellidos',
            'pattern': r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$',
            'title': 'Los apellidos solo pueden contener letras y espacios.'
        })
    )
    email = forms.EmailField(label='Correo electrónico', required=True, widget=forms.EmailInput(attrs={'placeholder': 'tu@email.com'}))
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput(attrs={'placeholder': 'Mínimo 8 caracteres'}), required=True)
    
    # Campos de Paciente
    dni = forms.CharField(
        label='DNI', 
        max_length=9, 
        min_length=9, 
        required=True, 
        widget=forms.TextInput(attrs={
            'placeholder': '12345678X',
            'pattern': r'^\d{8}[a-zA-Z]$',
            'title': 'El DNI debe tener 8 números y una letra.'
        })
    )
    telefono = forms.CharField(
        label='Teléfono', 
        max_length=9, 
        min_length=9, 
        required=True, 
        widget=forms.TextInput(attrs={
            'placeholder': '600000000',
            'pattern': r'^[6789]\d{8}$',
            'title': 'Introduce un teléfono español válido (9 dígitos empezando por 6, 7, 8 o 9).'
        })
    )
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

    def clean_first_name(self):
        nombre = self.cleaned_data.get('first_name')
        if len(nombre) < 2:
            raise forms.ValidationError("El nombre debe tener al menos 2 caracteres.")
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', nombre):
            raise forms.ValidationError("El nombre solo puede contener letras y espacios.")
        return nombre

    def clean_last_name(self):
        apellidos = self.cleaned_data.get('last_name')
        if len(apellidos) < 2:
            raise forms.ValidationError("Los apellidos deben tener al menos 2 caracteres.")
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', apellidos):
            raise forms.ValidationError("Los apellidos solo pueden contener letras y espacios.")
        return apellidos

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if len(username) < 4:
            raise forms.ValidationError("El nombre de usuario debe tener al menos 4 caracteres.")
        if not username.isalnum():
            raise forms.ValidationError("El nombre de usuario solo debe contener caracteres alfanuméricos.")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        return username

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 8:
            raise forms.ValidationError("La contraseña debe tener al menos 8 caracteres.")
        return password

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        # Patrón: 9 dígitos, empieza por 6, 7, 8 o 9
        patron = r'^[6789]\d{8}$'
        if not re.match(patron, telefono):
            raise forms.ValidationError("Introduce un número de teléfono español válido (9 dígitos y empieza por 6, 7, 8 o 9).")
        return telefono

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get('fecha_nacimiento')
        # Validación de mayoría de edad (18 años)
        hoy = forms.fields.datetime.date.today()
        edad = hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
        
        if fecha > hoy:
            raise forms.ValidationError("La fecha de nacimiento no puede ser en el futuro.")
        if fecha.year < 1900:
            raise forms.ValidationError("El año de nacimiento debe ser posterior a 1900.")
        if edad < 18:
            raise forms.ValidationError("Debes ser mayor de 18 años para registrarte en la plataforma.")
        return fecha

    def clean_dni(self):
        dni = self.cleaned_data.get('dni').upper()
        
        # 1. Validar formato básico (8 números + 1 letra)
        if not re.match(r'^\d{8}[TRWAGMYFPDXBNJZSQVHLCKE]$', dni):
            raise forms.ValidationError("El formato del DNI no es válido (8 números y 1 letra).")
        
        # 2. Validar Algoritmo Oficial (Módulo 23)
        letras = "TRWAGMYFPDXBNJZSQVHLCKE"
        numero = int(dni[:8])
        letra = dni[8]
        if letras[numero % 23] != letra:
            raise forms.ValidationError(f"La letra del DNI es incorrecta para el número {numero}.")

        # 3. Validar duplicados
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
