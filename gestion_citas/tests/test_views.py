from django.test import TestCase, RequestFactory
from django.utils import timezone
from datetime import date, timedelta, time
from django.contrib.auth.models import User
from django.urls import reverse
from ..models import (
    Cita, Medico, Paciente, Especialidad, Centro, 
    EstadoCita, PropuestaReasignacion, EstadoPropuesta, HorarioMedico
)
from ..views.acciones_motor import aceptar_propuesta

class MotorVistasIntegracionTests(TestCase):
    def setUp(self):
        self.esp = Especialidad.objects.create(nombre="Test")
        self.centro = Centro.objects.create(nombre="Centro")
        self.u_med = User.objects.create_user(username="dr")
        self.medico = Medico.objects.create(user=self.u_med, especialidad=self.esp, centro=self.centro, numero_colegiado="123")
        
        for i in range(7):
            HorarioMedico.objects.get_or_create(
                medico=self.medico, dia_semana=i,
                defaults={'hora_inicio': time(8, 0), 'hora_fin': time(20, 0)}
            )
        
        self.u_pa = User.objects.create_user(username="pa")
        self.pa = Paciente.objects.create(user=self.u_pa, dni="12345678Z", telefono="600111222", fecha_nacimiento=date(1990, 1, 1))
        
        self.u_pb = User.objects.create_user(username="pb")
        self.pb = Paciente.objects.create(user=self.u_pb, dni="54362315K", telefono="600333444", fecha_nacimiento=date(1995, 5, 5))
        
        self.factory = RequestFactory()

    def test_aceptar_propuesta_flujo_completo(self):
        """Prueba de integración: Aceptación -> Movimiento -> Consumo de Hueco -> Reacción en Cadena."""
        hoy = date.today()
        d1 = hoy + timedelta(days=1)
        d2 = hoy + timedelta(days=5)
        
        # Hueco libre
        hueco = Cita.objects.create(
            paciente=self.pa, medico=self.medico, fecha=d1, 
            hora_inicio=time(10, 0), estado=EstadoCita.CANCELADA, nivel_cascada=0
        )
        
        # Cita original del paciente B
        cita_b = Cita.objects.create(
            paciente=self.pb, medico=self.medico, fecha=d2, 
            hora_inicio=time(10, 0), estado=EstadoCita.CONFIRMADA, nivel_cascada=0
        )
        
        # Generamos propuesta
        propuesta = PropuestaReasignacion.objects.create(
            paciente=self.pb, hueco=hueco, cita_original=cita_b,
            fecha_limite=timezone.now() + timedelta(hours=24)
        )
        
        request = self.factory.post(reverse('aceptar_propuesta', args=[propuesta.id]))
        request.user = self.u_pb
        
        aceptar_propuesta(request, propuesta.id)
        
        cita_b.refresh_from_db()
        self.assertEqual(cita_b.fecha, d1)
        self.assertFalse(Cita.objects.filter(id=hueco.id).exists())
        
        nuevo_hueco = Cita.objects.get(fecha=d2, hora_inicio=time(10, 0), estado=EstadoCita.CANCELADA)
        self.assertEqual(nuevo_hueco.nivel_cascada, 1)

    def test_rechazar_propuesta_relanza_motor(self):
        """Verifica que rechazar una propuesta deja el hueco disponible para el siguiente."""
        hoy = date.today()
        hueco = Cita.objects.create(
            paciente=self.pa, medico=self.medico, fecha=hoy+timedelta(days=1), 
            hora_inicio=time(9, 0), estado=EstadoCita.CANCELADA
        )
        
        cita_a = Cita.objects.create(
            paciente=self.pa, medico=self.medico, fecha=hoy+timedelta(days=5), 
            hora_inicio=time(9, 0), estado=EstadoCita.CONFIRMADA
        )
        
        propuesta = PropuestaReasignacion.objects.create(
            paciente=self.pa, hueco=hueco, cita_original=cita_a,
            fecha_limite=timezone.now() + timedelta(hours=24)
        )
        
        from ..views.acciones_motor import rechazar_propuesta
        request = self.factory.post(reverse('rechazar_propuesta', args=[propuesta.id]))
        request.user = self.u_pa
        
        rechazar_propuesta(request, propuesta.id)
        
        propuesta.refresh_from_db()
        self.assertEqual(propuesta.estado, EstadoPropuesta.RECHAZADA)
        self.assertTrue(Cita.objects.filter(id=hueco.id).exists())
