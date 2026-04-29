from django.test import TestCase
from django.contrib.auth.models import User
from ..forms.registro import UserRegistrationForm
from ..forms.paciente import PacienteForm
from ..models import Paciente, Turno
from datetime import date, timedelta

class FormularioTests(TestCase):
    def test_registro_paciente_form_valid(self):
        """Verifica que el formulario de registro funciona con datos reales y válidos."""
        data = {
            'username': 'juanito90',
            'first_name': 'Juan',
            'last_name': 'Pérez García',
            'email': 'juan@example.com',
            'password': 'password12345',
            'telefono': '611222333',
            'dni': '12345678Z', # DNI válido (12345678 % 23 = 14 -> Z)
            'fecha_nacimiento': date(1990, 1, 1), # Mayor de edad
            'preferencia_turno': Turno.MANANA
        }
        form = UserRegistrationForm(data=data)
        if not form.is_valid():
             print(f"DEBUG: Errores del formulario: {form.errors}")
        self.assertTrue(form.is_valid())

    def test_registro_paciente_form_dni_invalido(self):
        """Verifica que el formulario rechaza un DNI con letra incorrecta."""
        data = {
            'username': 'juanito90',
            'first_name': 'Juan',
            'last_name': 'Pérez García',
            'email': 'juan@example.com',
            'password': 'password12345',
            'telefono': '611222333',
            'dni': '12345678A', # Letra A es incorrecta para este número
            'fecha_nacimiento': date(1990, 1, 1),
            'preferencia_turno': Turno.MANANA
        }
        form = UserRegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('dni', form.errors)

    def test_registro_paciente_form_dni_blanco(self):
        """Verifica que el formulario rechaza envío si el DNI está en blanco."""
        data = {
            'username': 'juanito290',
            'first_name': 'Juan',
            'last_name': 'Pérez García',
            'email': 'juan2@example.com',
            'password': 'password12345',
            'telefono': '611222333',
            'dni': '', 
            'fecha_nacimiento': date(1990, 1, 1),
            'preferencia_turno': Turno.MANANA
        }
        form = UserRegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('dni', form.errors)

    def test_registro_paciente_form_menor_edad(self):
        """Verifica que el formulario rechaza el registro si el paciente no acepta que es mayor de edad o es menor."""
        data = {
            'username': 'juanito90',
            'first_name': 'Juan',
            'last_name': 'Pérez García',
            'email': 'juan@example.com',
            'password': 'password12345',
            'telefono': '611222333',
            'dni': '54362315Q', 
            'fecha_nacimiento': date.today() - timedelta(days=365*10), # 10 años
            'preferencia_turno': Turno.MANANA
        }
        form = UserRegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('fecha_nacimiento', form.errors)

    def test_ajustes_paciente_form(self):
        """Verifica el formulario de actualización de perfil."""
        user = User.objects.create_user(username="test_adj")
        paciente = Paciente.objects.create(
            user=user, 
            dni="54362315Q", 
            telefono="622333444", 
            fecha_nacimiento=date(1985, 5, 5)
        )
        data = {
            'telefono': '633444555',
            'preferencia_turno': 'T'
        }
        form = PacienteForm(data=data, instance=paciente)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(paciente.telefono, '633444555')
