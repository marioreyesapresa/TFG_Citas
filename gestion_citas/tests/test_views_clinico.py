from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from ..models import Medico, Especialidad, Centro, Cita, EstadoCita, Paciente, ConsultaMedica
from datetime import date, timedelta, time

class ClinicoViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.esp = Especialidad.objects.create(nombre="TestEsp")
        self.centro = Centro.objects.create(nombre="Centro Sur")
        self.u_med = User.objects.create_user(username="dr_test", password="password123")
        self.medico = Medico.objects.create(user=self.u_med, especialidad=self.esp, centro=self.centro, numero_colegiado="COL-001")
        
        for i in range(7):
            from ..models import HorarioMedico
            HorarioMedico.objects.create(
                medico=self.medico, dia_semana=i, 
                hora_inicio=time(8, 0), hora_fin=time(20, 0)
            )
        
        self.u_pac = User.objects.create_user(username="pac_test", password="password123")
        self.paciente = Paciente.objects.create(user=self.u_pac, dni="12345678Z", fecha_nacimiento=date(1990, 1, 1), telefono="600111222")

        self.cita = Cita.objects.create(
            paciente=self.paciente, medico=self.medico, 
            fecha=date.today(), hora_inicio=time(9, 0), estado=EstadoCita.CONFIRMADA
        )
        
    def test_crear_consulta_acceso_denegado_paciente(self):
        """Un paciente no debe poder acceder a la vista médica."""
        self.client.login(username="pac_test", password="password123")
        res = self.client.get(reverse('crear_consulta', args=[self.cita.id]))
        self.assertEqual(res.status_code, 302) # Redirect to su dashboard

    def test_perfil_medico_acceso_denegado(self):
        u_error = User.objects.create_user("dummy", password="123")
        self.client.force_login(u_error)
        res = self.client.get(reverse('perfil_medico'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'gestion_citas/comun/error_acceso.html')

    def test_crear_consulta_get_view(self):
        """Verifica que el médico carga la vista de crear consulta 200 OK."""
        self.client.login(username="dr_test", password="password123")
        res = self.client.get(reverse('crear_consulta', args=[self.cita.id]))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'gestion_citas/clinico/crear_consulta.html')

    def test_crear_consulta_post_valid_data(self):
        """Registra una consulta exitosamente."""
        self.client.login(username="dr_test", password="password123")
        
        data = {
            'motivo_consulta': 'Dolor de cabeza',
            'diagnostico_principal': 'Migraña',
            'recetas-TOTAL_FORMS': '0', 
            'recetas-INITIAL_FORMS': '0',
            'recetas-MIN_NUM_FORMS': '0',
            'recetas-MAX_NUM_FORMS': '1000',
        }
        res = self.client.post(reverse('crear_consulta', args=[self.cita.id]), data)
        self.assertEqual(res.status_code, 302) # Redirect perfil medico
        
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.estado, EstadoCita.ATENDIDA)
        self.assertTrue(ConsultaMedica.objects.filter(cita=self.cita).exists())

    def test_consulta_cita_cancelada_rechazada(self):
        """No se debe poder crear consulta sobre una cita cancelada."""
        self.cita.estado = EstadoCita.CANCELADA
        self.cita.save()
        self.client.login(username="dr_test", password="password123")
        res = self.client.get(reverse('crear_consulta', args=[self.cita.id]))
        self.assertEqual(res.status_code, 302) # Redirect con error
        
    def test_ver_historial_paciente_medico(self):
        """Un médico puede ver el historial de un paciente."""
        self.client.login(username="dr_test", password="password123")
        res = self.client.get(reverse('historial_paciente_medico', args=[self.paciente.user.id]))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'gestion_citas/clinico/historial_clinico.html')
        
    def test_ver_historial_paciente_propio(self):
        """Un paciente puede ver su propio historial, omitiendo el ID."""
        self.client.login(username="pac_test", password="password123")
        res = self.client.get(reverse('historial_paciente'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'gestion_citas/paciente/historial_paciente.html')

    def test_descargar_informe_pdf(self):
        """Verifica la descarga del PDF si tiene permisos."""
        consulta = ConsultaMedica.objects.create(
            cita=self.cita, motivo_consulta="A", diagnostico_principal="B"
        )
        self.client.login(username="dr_test", password="password123")
        res = self.client.get(reverse('descargar_informe_pdf', args=[consulta.id]))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'application/pdf')
        
    def test_validar_receta_publica(self):
        """Verifica la vista pública de validación de receta."""
        consulta = ConsultaMedica.objects.create(
            cita=self.cita, motivo_consulta="A", diagnostico_principal="B"
        )
        # La vista es pública, no requiere login
        res = self.client.get(reverse('validar_receta_publica', args=[consulta.token_verificacion]))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'gestion_citas/clinico/validar_receta_publica.html')
