import os
import django
from django.test.utils import setup_test_environment
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
setup_test_environment()

from django.test import Client
from gestion_citas.tests.test_views_paciente import PacientePortalTests

class DummyTest(PacientePortalTests):
    def test_print_errors(self):
        res = self.client.post('/registro/', {
            'username': 'nuevo_pac',
            'password': 'password123',
            'confirm_password': 'password123',
            'first_name': 'Nuevo',
            'last_name': 'Pac',
            'email': 'n@p.com',
            'dni': '87654321X',
            'telefono': '600000000',
            'fecha_nacimiento': '1990-01-01',
            'preferencia_turno': 'M'
        })
        if res.status_code == 200:
            print("ERRORS:", res.context['form'].errors)

