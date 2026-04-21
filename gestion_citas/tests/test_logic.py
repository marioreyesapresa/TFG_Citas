from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta, time
from django.contrib.auth.models import User
from unittest.mock import patch
from ..models import (
    Cita, Medico, Paciente, Especialidad, Centro, 
    EstadoCita, NivelUrgencia, PropuestaReasignacion, 
    EstadoPropuesta, HorarioMedico, ConfiguracionReasignacion, Notificacion, Turno
)
from ..algoritmo_reasignacion import iniciar_reasignacion, determinar_turno, _mask_email

class ReasignacionLogicaTests(TestCase):
    def setUp(self):
        # Entorno base
        self.esp = Especialidad.objects.create(nombre="TestEsp")
        self.centro = Centro.objects.create(nombre="TestCentro")
        self.u_med = User.objects.create_user(username="test_med")
        self.medico = Medico.objects.create(user=self.u_med, especialidad=self.esp, centro=self.centro)
        
        # Horarios
        for i in range(7):
            HorarioMedico.objects.get_or_create(
                medico=self.medico, dia_semana=i,
                defaults={'hora_inicio': time(8, 0), 'hora_fin': time(20, 0)}
            )
        
        # Configuración
        self.config = ConfiguracionReasignacion.objects.create(
            peso_urgencia=100.0, prioridad_turno=1.0, peso_antiguedad=0.0
        )
        
        # Pacientes
        self.pa = Paciente.objects.create(user=User.objects.create_user(username="pa", email="pa@test.com"), preferencia_turno='M')
        self.pb = Paciente.objects.create(user=User.objects.create_user(username="pb", email="pb@test.com"), preferencia_turno='T')

    def test_mask_email_edge_cases(self):
        """Cubre líneas 15, 18-19 de _mask_email."""
        self.assertEqual(_mask_email(""), "")
        self.assertEqual(_mask_email(None), "")
        self.assertEqual(_mask_email("email_sin_arroba"), "***")
        self.assertEqual(_mask_email("a@b.com"), "*@b.com")

    def test_determinar_turno_utilidad(self):
        """Verifica la lógica de negocio de división de mañana/tarde."""
        self.assertEqual(determinar_turno(time(10, 0)), Turno.MANANA)
        self.assertEqual(determinar_turno(time(16, 0)), Turno.TARDE)

    def test_iniciar_reasignacion_pasado_directo(self):
        """Cubre líneas 60-61 (Iniciando reasignación para fecha pasada)."""
        ayer = date.today() - timedelta(days=1)
        # Creamos hueco directamente en el pasado
        hueco_pasado = Cita.objects.create(
            paciente=self.pa, medico=self.medico, fecha=ayer, 
            hora_inicio=time(9, 0), estado=EstadoCita.CANCELADA
        )
        # La función debe retornar None casi inmediatamente
        resultado = iniciar_reasignacion(hueco_pasado)
        self.assertIsNone(resultado)

    def test_ranking_scoring_multifactorial(self):
        """Prueba que el scoring prioriza la urgencia correctamente."""
        manana = date.today() + timedelta(days=2)
        sesemana = date.today() + timedelta(days=7)
        
        hueco = Cita.objects.create(
            paciente=self.pa, medico=self.medico, fecha=manana, 
            hora_inicio=time(9, 0), estado=EstadoCita.CANCELADA
        )
        
        # PA: Baja -> Score: 1 + 1*100 = 101
        Cita.objects.create(
            paciente=self.pa, medico=self.medico, fecha=sesemana, 
            hora_inicio=time(9, 0), urgencia=NivelUrgencia.BAJA, estado=EstadoCita.CONFIRMADA
        )
        
        # PB: Alta -> Score: 0 + 3*100 = 300
        Cita.objects.create(
            paciente=self.pb, medico=self.medico, fecha=sesemana, 
            hora_inicio=time(16, 0), urgencia=NivelUrgencia.ALTA, estado=EstadoCita.CONFIRMADA
        )
        
        iniciar_reasignacion(hueco)
        propuesta = PropuestaReasignacion.objects.get(hueco=hueco)
        self.assertEqual(propuesta.paciente, self.pb)

    def test_regla_d_mismo_dia(self):
        """Candidato descartado si ya tiene cita ese mismo día (Línea 107-108)."""
        manana = date.today() + timedelta(days=2)
        futuro = date.today() + timedelta(days=10)
        
        hueco = Cita.objects.create(
            paciente=self.pa, medico=self.medico, fecha=manana, 
            hora_inicio=time(9, 0), estado=EstadoCita.CANCELADA
        )
        # Ya tiene cita ese día
        Cita.objects.create(
            paciente=self.pa, medico=self.medico, fecha=manana, 
            hora_inicio=time(10, 0), estado=EstadoCita.CONFIRMADA
        )
        # Cita a adelantar
        Cita.objects.create(
            paciente=self.pa, medico=self.medico, fecha=futuro, 
            hora_inicio=time(9, 0), estado=EstadoCita.CONFIRMADA
        )
        
        iniciar_reasignacion(hueco)
        self.assertFalse(PropuestaReasignacion.objects.filter(hueco=hueco).exists())

    def test_regla_e_propuesta_activa(self):
        """Candidato descartado si ya tiene una propuesta pendiente (Línea 128-129)."""
        manana = date.today() + timedelta(days=2)
        
        cita_futura = Cita.objects.create(
            paciente=self.pa, medico=self.medico, fecha=manana + timedelta(days=5), 
            hora_inicio=time(9, 0), estado=EstadoCita.CONFIRMADA
        )
        
        # HUECO DUMMY para la propuesta previa (creamos como CONFIRMADA, actualizamos sin disparar motor)
        hueco_dummy = Cita.objects.create(
            paciente=self.pb, medico=self.medico, fecha=manana + timedelta(days=1),
            hora_inicio=time(8, 0), estado=EstadoCita.CONFIRMADA
        )
        Cita.objects.filter(pk=hueco_dummy.pk).update(estado=EstadoCita.CANCELADA)
        
        PropuestaReasignacion.objects.create(
            paciente=self.pa, hueco=hueco_dummy, cita_original=cita_futura,
            estado=EstadoPropuesta.PENDIENTE, fecha_limite=timezone.now() + timedelta(hours=24)
        )
        
        # Hueco real que vamos a pasar manualmente al motor
        hueco_real = Cita.objects.create(
            paciente=self.pa, medico=self.medico, fecha=manana, 
            hora_inicio=time(9, 0), estado=EstadoCita.CONFIRMADA
        )
        Cita.objects.filter(pk=hueco_real.pk).update(estado=EstadoCita.CANCELADA)
        iniciar_reasignacion(hueco_real)
        
        # El motor debe ignorar a PA porque ya tiene la propuesta activa en hueco_dummy
        self.assertFalse(PropuestaReasignacion.objects.filter(hueco=hueco_real).exists())

    def test_candidato_sin_email(self):
        """Cubre la línea 200 (Paciente sin email)."""
        manana = date.today() + timedelta(days=2)
        hueco = Cita.objects.create(
            paciente=self.pa, medico=self.medico, fecha=manana, 
            hora_inicio=time(9, 0), estado=EstadoCita.CANCELADA
        )
        
        # Paciente sin email
        self.pb.user.email = ""
        self.pb.user.save()
        
        Cita.objects.create(
            paciente=self.pb, medico=self.medico, fecha=manana + timedelta(days=10), 
            hora_inicio=time(9, 0), estado=EstadoCita.CONFIRMADA
        )
        
        iniciar_reasignacion(hueco)
        self.assertTrue(PropuestaReasignacion.objects.filter(hueco=hueco, paciente=self.pb).exists())

    def test_motor_circuit_breaker_profundidad(self):
        """Protección contra cascadas infinitas."""
        manana = date.today() + timedelta(days=2)
        hueco = Cita.objects.create(
            paciente=self.pa, medico=self.medico, fecha=manana, 
            hora_inicio=time(9, 0), estado=EstadoCita.CANCELADA, nivel_cascada=5
        )
        Cita.objects.create(
            paciente=self.pa, medico=self.medico, fecha=manana + timedelta(days=5), 
            hora_inicio=time(9, 0), estado=EstadoCita.CONFIRMADA
        )
        iniciar_reasignacion(hueco)
        self.assertFalse(PropuestaReasignacion.objects.filter(hueco=hueco).exists())

    @patch('django.core.mail.EmailMultiAlternatives.send')
    def test_fallo_envio_email(self, mock_send):
        """Cubre fallo SMTP (Líneas 194-197)."""
        mock_send.side_effect = Exception("SMTP Error")
        manana = date.today() + timedelta(days=2)
        hueco = Cita.objects.create(
            paciente=self.pa, medico=self.medico, fecha=manana, 
            hora_inicio=time(9, 0), estado=EstadoCita.CANCELADA
        )
        Cita.objects.create(
            paciente=self.pa, medico=self.medico, fecha=manana + timedelta(days=5), 
            hora_inicio=time(9, 0), estado=EstadoCita.CONFIRMADA
        )
        iniciar_reasignacion(hueco)
        self.assertTrue(PropuestaReasignacion.objects.filter(hueco=hueco).exists())
