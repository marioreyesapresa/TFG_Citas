from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from ..models import Paciente, Medico, Administrativo, Especialidad, Centro
from datetime import date

class BaseViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.esp = Especialidad.objects.create(nombre="EspTest")
        self.centro = Centro.objects.create(nombre="CentroTest")
        
        self.u_admin = User.objects.create_superuser(username="admin_test", password="123")
        self.u_med = User.objects.create_user(username="med_test", password="123")
        self.medico = Medico.objects.create(user=self.u_med, especialidad=self.esp, centro=self.centro)
        
        self.u_pac = User.objects.create_user(username="pac_test", password="123")
        self.paciente = Paciente.objects.create(user=self.u_pac, dni="11")
        
        self.u_no_role = User.objects.create_user(username="none_test", password="123")
    
    def test_index_anonimo(self):
        res = self.client.get(reverse('index'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'gestion_citas/comun/index.html')

    def test_index_autenticado(self):
        self.client.login(username="pac_test", password="123")
        res = self.client.get(reverse('index'))
        self.assertRedirects(res, reverse('dashboard'), fetch_redirect_response=False)

    def test_dashboard_admin(self):
        self.client.login(username="admin_test", password="123")
        res = self.client.get(reverse('dashboard'))
        self.assertRedirects(res, reverse('perfil_administrativo'))

    def test_dashboard_medico(self):
        self.client.login(username="med_test", password="123")
        res = self.client.get(reverse('dashboard'))
        self.assertRedirects(res, reverse('perfil_medico'))
        
    def test_dashboard_paciente(self):
        self.client.login(username="pac_test", password="123")
        res = self.client.get(reverse('dashboard'))
        self.assertRedirects(res, reverse('perfil_paciente'))
        
    def test_dashboard_no_role(self):
        self.client.login(username="none_test", password="123")
        res = self.client.get(reverse('dashboard'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'gestion_citas/comun/error_acceso.html')
