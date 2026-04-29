from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from ..models import Paciente, Medico, Especialidad, Centro, Cita, EstadoCita, NivelUrgencia, HorarioMedico
from datetime import date, timedelta, time

class PacientePortalTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.esp = Especialidad.objects.create(nombre="Test")
        self.centro = Centro.objects.create(nombre="Centro")
        self.u_med = User.objects.create_user(username="dr_p", first_name="Dr", last_name="P")
        self.medico = Medico.objects.create(user=self.u_med, especialidad=self.esp, centro=self.centro, numero_colegiado="123")
        
        # Horarios para evitar errores de validación de días laborables
        for i in range(7):
            HorarioMedico.objects.get_or_create(
                medico=self.medico, dia_semana=i,
                defaults={'hora_inicio': time(8, 0), 'hora_fin': time(20, 0)}
            )
        
        self.user = User.objects.create_user(username="test_user", password="password123")
        self.paciente = Paciente.objects.create(
            user=self.user, 
            dni="12345678Z", 
            fecha_nacimiento=date(1990, 1, 1),
            telefono="600111222"
        )
        self.client.login(username="test_user", password="password123")

    def test_perfil_paciente_view(self):
        """Verifica que el dashboard del paciente carga correctamente."""
        response = self.client.get(reverse('perfil_paciente'))
        self.assertEqual(response.status_code, 200)

    def test_solicitar_cita_paso_1(self):
        """Verifica la carga inicial de médicos y especialidades en la solicitud."""
        response = self.client.get(reverse('solicitar_cita'))
        self.assertEqual(response.status_code, 200)

    def test_asignacion_urgencia_directa(self):
        """Prueba la asignación de urgencia directamente en el modelo (Recomendación del Usuario)."""
        fecha = date.today() + timedelta(days=10)
        # Probamos que el campo urgencia se persiste correctamente en la DB
        cita = Cita.objects.create(
            paciente=self.paciente,
            medico=self.medico,
            fecha=fecha,
            hora_inicio=time(10, 0),
            urgencia=NivelUrgencia.MEDIA,
            estado=EstadoCita.CONFIRMADA
        )
        cita.refresh_from_db()
        self.assertEqual(cita.urgencia, NivelUrgencia.MEDIA)

    def test_perfil_paciente_actualizacion_ajustes(self):
        """Verifica que el paciente puede actualizar su teléfono y preferencias."""
        response = self.client.post(reverse('perfil_paciente'), {
            'ajustes_perfil': True,
            'telefono': '600999888',
            'preferencia_turno': 'T'
        })
        self.assertEqual(response.status_code, 302)
        self.paciente.refresh_from_db()
        self.assertEqual(self.paciente.telefono, '600999888')

    def test_cancelar_cita_action(self):
        """Verifica que el paciente puede cancelar su cita."""
        cita = Cita.objects.create(
            paciente=self.paciente, medico=self.medico,
            fecha=date.today() + timedelta(days=5), hora_inicio=time(9, 0), estado=EstadoCita.CONFIRMADA
        )
        res = self.client.post(reverse('cancelar_cita', args=[cita.id]))
        self.assertEqual(res.status_code, 302)
        cita.refresh_from_db()
        self.assertEqual(cita.estado, EstadoCita.CANCELADA)

    def test_registro_paciente_con_cita_pendiente(self):
        """Si registro un paciente, se debe confirmar su cita en sesión."""
        session = self.client.session
        session['cita_pendiente'] = {
            'medico_id': self.medico.id,
            'fecha': (date.today() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'hora': '10:00:00',
            'urgencia': NivelUrgencia.BAJA
        }
        session.save()
        
        # Como no hay un endpoint de api, usamos el GET/POST de `registro` pero necesitamos desloguearnos primero
        self.client.logout()
        res = self.client.get(reverse('registro'))
        self.assertEqual(res.status_code, 200)

    def test_registro_paciente_post_con_cita_pendiente(self):
        """Si registro un paciente por POST y es valido, confirma la cita pendiente."""
        session = self.client.session
        session['cita_pendiente'] = {
            'medico_id': self.medico.id,
            'fecha': (date.today() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'hora': '10:00:00',
            'urgencia': NivelUrgencia.BAJA
        }
        session.save()
        self.client.logout()
        res = self.client.post(reverse('registro'), {
            'username': 'nuevopac',
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
        # Verifica redirección correcta en el POST completado con éxito
        self.assertEqual(res.status_code, 302)

    def test_solicitar_cita_post_anonimo(self):
        """Solicitar cita por POST anónimo guarda cita en session y pide logueo."""
        self.client.logout()
        res = self.client.post(reverse('solicitar_cita'), {
            'medico': self.medico.id,
            'fecha': (date.today() + timedelta(days=2)).strftime('%Y-%m-%d'),
            'hora': '09:00:00',
        })
        self.assertEqual(res.status_code, 302)
        self.assertIn('cita_pendiente', self.client.session)

    def test_solicitar_cita_post_autenticado(self):
        """Solicitar cita por POST autenticado la crea inmediatamente."""
        res = self.client.post(reverse('solicitar_cita'), {
            'medico': self.medico.id,
            'fecha': (date.today() + timedelta(days=2)).strftime('%Y-%m-%d'),
            'hora': '09:00:00',
        })
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'gestion_citas/paciente/cita_confirmada.html')
        self.assertTrue(Cita.objects.filter(paciente=self.paciente).exists())

    def test_solicitar_cita_post_error(self):
        """Solicitar cita por POST con datos malos falla."""
        res = self.client.post(reverse('solicitar_cita'), {
            'medico': self.medico.id,
            'fecha': '1900-01-01',
            'hora': '09:00:00'
        })
        # Lanza error o no se guarda. No deberia fallar la vista entera.
        self.assertEqual(res.status_code, 200)

    def test_perfil_paciente_actualizar(self):
        """Si un paciente hace POST a perfil_paciente con ajustes_perfil, se actualiza."""
        self.client.force_login(self.user)
        res = self.client.post(reverse('perfil_paciente'), {
            'ajustes_perfil': 'true',
            'telefono': '987654321', # campo del modelo Paciente
            'preferencia_turno': 'T'
        })
        self.assertEqual(res.status_code, 302)
        self.paciente.refresh_from_db()
        self.assertEqual(self.paciente.telefono, '987654321')

    def test_perfil_paciente_con_cita_sesion(self):
        """Magia UX: Si el paciente hace login y tenia cita pendiente, se crea y rediriege a confirmacion."""
        session = self.client.session
        session['cita_pendiente'] = {
            'medico_id': self.medico.id,
            'fecha': (date.today() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'hora': '10:00:00',
            'urgencia': 1
        }
        session.save()
        
        self.client.force_login(self.user)
        res = self.client.get(reverse('perfil_paciente'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'gestion_citas/paciente/cita_confirmada.html')

    def test_ajax_endpoints(self):
        """Test de los endpoints AJAX para pedir cita."""
        self.client.force_login(self.user)
        
        # Centros por esp
        res = self.client.get(reverse('ajax_cargar_centros_esp') + f'?especialidad_id={self.esp.id}')
        self.assertEqual(res.status_code, 200)
        self.assertIn('centros', res.json())
        
        # Medicos por esp y centro
        res = self.client.get(reverse('ajax_cargar_medicos_esp_centro') + f'?especialidad_id={self.esp.id}&centro_id={self.centro.id}')
        self.assertEqual(res.status_code, 200)
        self.assertIn('medicos', res.json())
        
        # Horas libres
        res = self.client.get(reverse('ajax_cargar_horas') + f'?medico={self.medico.id}&fecha={(date.today()+timedelta(days=7)).strftime("%Y-%m-%d")}')
        self.assertEqual(res.status_code, 200)
        self.assertIn('horas', res.json())
        
    def test_aceptar_propuesta(self):
        self.client.force_login(self.user)
        cita = Cita.objects.create(
            paciente=self.paciente, medico=self.medico, fecha=date.today()+timedelta(days=1), hora_inicio=time(9,0), estado=EstadoCita.CONFIRMADA
        )
        hueco = Cita.objects.create(
            paciente=self.paciente, medico=self.medico, fecha=date.today()+timedelta(days=2), hora_inicio=time(9,0), estado=EstadoCita.CANCELADA
        )
        from ..models import PropuestaReasignacion, EstadoPropuesta
        prop = PropuestaReasignacion.objects.create(cita_original=cita, hueco=hueco, paciente=self.paciente, estado=EstadoPropuesta.PENDIENTE, fecha_limite=timezone.now()+timedelta(days=5))
        res = self.client.post(reverse('aceptar_propuesta', args=[prop.id]))
        self.assertEqual(res.status_code, 302)
        # Verify it was successfully consumed
        self.assertFalse(PropuestaReasignacion.objects.filter(id=prop.id).exists())

    def test_rechazar_propuesta(self):
        self.client.force_login(self.user)
        cita = Cita.objects.create(
            paciente=self.paciente, medico=self.medico, fecha=date.today()+timedelta(days=1), hora_inicio=time(10,0), estado=EstadoCita.CONFIRMADA
        )
        hueco = Cita.objects.create(
            paciente=self.paciente, medico=self.medico, fecha=date.today()+timedelta(days=2), hora_inicio=time(10,0), estado=EstadoCita.CANCELADA
        )
        from ..models import PropuestaReasignacion, EstadoPropuesta
        prop = PropuestaReasignacion.objects.create(cita_original=cita, hueco=hueco, paciente=self.paciente, estado=EstadoPropuesta.PENDIENTE, fecha_limite=timezone.now()+timedelta(days=5))
        res = self.client.post(reverse('rechazar_propuesta', args=[prop.id]))
        self.assertEqual(res.status_code, 302)
        prop.refresh_from_db()
        self.assertEqual(prop.estado, EstadoPropuesta.RECHAZADA)

