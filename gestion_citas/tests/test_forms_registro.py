from django.test import TestCase
from ..forms.registro import UserRegistrationForm

class RegistroFormTest(TestCase):
    def test_registro_form_valido(self):
        data = {
            'username': 'juanito',
            'first_name': 'Juan',
            'last_name': 'Perez',
            'email': 'juan@email.com',
            'password': 'password123',
            'dni': '12345678Z',
            'telefono': '600000000',
            'fecha_nacimiento': '1990-01-01',
            'preferencia_turno': 'M'
        }
        form = UserRegistrationForm(data=data)
        self.assertTrue(form.is_valid())
        
    def test_registro_form_invalido_dni(self):
        data = {
            'username': 'juanito',
            'first_name': 'J', # invalido
            'last_name': 'P', # invalido
            'email': 'juan@email.com',
            'password': 'pass', # invalido
            'dni': '12345678A', # invalido (letra A mala)
            'telefono': '500000000', # invalido (empieza en 5)
            'fecha_nacimiento': '2050-01-01', # invalida (futuro)
            'preferencia_turno': 'M'
        }
        form = UserRegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)
        self.assertIn('last_name', form.errors)
        self.assertIn('password', form.errors)
        self.assertIn('dni', form.errors)
        self.assertIn('telefono', form.errors)
        self.assertIn('fecha_nacimiento', form.errors)
    
    def test_clean_username_numerico(self):
        data = {
            'username': 'ju@n', # symbol not allowed
            'first_name': 'Juan',
            'last_name': 'Perez',
            'email': 'juan@email.com',
            'password': 'password123',
            'dni': '12345678Z',
            'telefono': '600000000',
            'fecha_nacimiento': '1990-01-01',
            'preferencia_turno': 'M'
        }
        form = UserRegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
