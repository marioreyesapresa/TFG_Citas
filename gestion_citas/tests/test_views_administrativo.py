from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from ..models import Paciente, Medico, Especialidad, Centro, Cita, EstadoCita, PropuestaReasignacion, EstadoPropuesta
from datetime import date, time, timedelta

class AdministrativoViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.u_admin = User.objects.create_superuser(username="admin_test", password="123")
        
        self.esp = Especialidad.objects.create(nombre="EspTest")
        self.centro = Centro.objects.create(nombre="CentroTest")
        self.u_med = User.objects.create_user(username="med_test", password="123")
        self.medico = Medico.objects.create(user=self.u_med, especialidad=self.esp, centro=self.centro, numero_colegiado="123")
        
        from ..models import HorarioMedico
        for i in range(7):
            HorarioMedico.objects.create(medico=self.medico, dia_semana=i, hora_inicio=time(8, 0), hora_fin=time(20, 0))
            
        self.u_pac = User.objects.create_user(username="pac_test", password="123")
        self.paciente = Paciente.objects.create(user=self.u_pac, dni="11", telefono="600111222")
        
        self.dia_fijado = date.today() + timedelta(days=5)
        self.cita = Cita.objects.create(
            paciente=self.paciente, medico=self.medico, fecha=self.dia_fijado, hora_inicio=time(9,0), estado=EstadoCita.CONFIRMADA
        )
        
        self.prop_activa = PropuestaReasignacion.objects.create(
            cita_original=self.cita, paciente=self.paciente, estado=EstadoPropuesta.PENDIENTE, fecha_limite=date.today() + timedelta(days=1)
        )
        
    def test_acceso_denegado_paciente(self):
        self.client.login(username="pac_test", password="123")
        res = self.client.get(reverse('perfil_administrativo'))
        self.assertRedirects(res, reverse('dashboard'), fetch_redirect_response=False)
        
    def test_perfil_admin_ok(self):
        self.client.login(username="admin_test", password="123")
        res = self.client.get(reverse('perfil_administrativo'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'gestion_citas/admin/perfil_administrativo.html')
        self.assertIn(self.cita, res.context['citas'])
        self.assertIn(self.prop_activa, res.context['propuestas'])
        
    def test_perfil_admin_filtros(self):
        self.client.login(username="admin_test", password="123")
        
        # Filtro por médico
        res_med = self.client.get(reverse('perfil_administrativo') + f"?medico={self.medico.id}")
        self.assertEqual(res_med.status_code, 200)
        self.assertEqual(res_med.context['filtro_medico'], self.medico.id)
        
        # Filtro por fecha específica
        fecha_str = self.dia_fijado.strftime('%Y-%m-%d')
        res_fecha = self.client.get(reverse('perfil_administrativo') + f"?fecha={fecha_str}")
        self.assertEqual(res_fecha.status_code, 200)
        self.assertEqual(res_fecha.context['filtro_fecha'], fecha_str)
