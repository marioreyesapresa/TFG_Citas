from django.test import TestCase, RequestFactory
from django.utils import timezone
from datetime import date, timedelta
from django.contrib.auth.models import User
from .models import (
    Cita, Medico, Paciente, Especialidad, Centro, 
    EstadoCita, NivelUrgencia, PropuestaReasignacion, 
    EstadoPropuesta, HorarioMedico, ConfiguracionReasignacion
)
from .algoritmo_reasignacion import iniciar_reasignacion
from .views.acciones_motor import aceptar_propuesta

class ReasignacionMotorTests(TestCase):
    def setUp(self):
        # 1. Entorno básico
        self.esp = Especialidad.objects.create(nombre="Cardiología")
        self.centro = Centro.objects.create(nombre="Centro Test")
        
        # Médico
        self.u_med = User.objects.create_user(username="dr_test", last_name="Martínez")
        self.medico = Medico.objects.create(
            user=self.u_med, especialidad=self.esp, centro=self.centro, numero_colegiado="12345"
        )
        
        # Horarios para hoy y los próximos 10 días
        hoy = date.today()
        for i in range(11):
            HorarioMedico.objects.create(
                medico=self.medico, dia_semana=(hoy + timedelta(days=i)).weekday(),
                hora_inicio="08:00", hora_fin="20:00"
            )
        
        # Pacientes
        self.u_pa = User.objects.create_user(username="paciente_a")
        self.pa = Paciente.objects.create(user=self.u_pa, telefono="601", preferencia_turno='M')
        
        self.u_pb = User.objects.create_user(username="paciente_b")
        self.pb = Paciente.objects.create(user=self.u_pb, telefono="602", preferencia_turno='M')

        # Configuración del motor
        ConfiguracionReasignacion.objects.create(
            peso_urgencia=15.0, prioridad_turno=10.0, peso_antiguedad=0.1
        )

    def test_scoring_prioriza_urgencia_alta(self):
        """El motor debe elegir al paciente con urgencia ALTA aunque su cita esté más cerca."""
        manana = date.today() + timedelta(days=1)
        semana_prox = date.today() + timedelta(days=7)
        
        # Hueco libre (manana)
        hueco = Cita.objects.create(
            paciente=self.pa, medico=self.medico, fecha=manana, hora_inicio="10:00", estado=EstadoCita.CANCELADA
        )
        
        # Candidato A (Urgencia MEDIA, cita en 7 días)
        Cita.objects.create(
            paciente=self.pa, medico=self.medico, fecha=semana_prox, hora_inicio="10:00",
            urgencia=NivelUrgencia.MEDIA, estado=EstadoCita.CONFIRMADA
        )
        # Candidato B (Urgencia ALTA, cita en 8 días)
        Cita.objects.create(
            paciente=self.pb, medico=self.medico, fecha=semana_prox + timedelta(days=1), hora_inicio="10:00",
            urgencia=NivelUrgencia.ALTA, estado=EstadoCita.CONFIRMADA
        )
        
        # Disparamos motor
        iniciar_reasignacion(hueco)
        
        propuesta = PropuestaReasignacion.objects.get(hueco=hueco)
        self.assertEqual(propuesta.paciente, self.pb)
        print("✅ Test Scoring: Prioridad ALTA verificada.")

    def test_regla_d_evita_colision_mismo_dia(self):
        """No se debe ofrecer un hueco si el paciente ya tiene otra cita ese día."""
        manana = date.today() + timedelta(days=1)
        # Cita fantasma del paciente A el mismo día del hueco
        Cita.objects.create(
            paciente=self.pa, medico=self.medico, fecha=manana, hora_inicio="16:00", estado=EstadoCita.CONFIRMADA
        )
        
        hueco = Cita.objects.create(
            paciente=self.pb, medico=self.medico, fecha=manana, hora_inicio="09:00", estado=EstadoCita.CANCELADA
        )
        
        # Paciente A tiene cita futura que podría adelantar
        Cita.objects.create(
            paciente=self.pa, medico=self.medico, fecha=manana + timedelta(days=5), hora_inicio="10:00",
            estado=EstadoCita.CONFIRMADA
        )
        
        iniciar_reasignacion(hueco)
        
        # El paciente A debería ser descartado por la Regla D, por lo que no habría propuesta
        # (ya que no hay más candidatos en este test)
        self.assertFalse(PropuestaReasignacion.objects.filter(paciente=self.pa).exists())
        print("✅ Test Regla D: Colisión misma fecha evitada.")

    def test_reaccion_en_cadena_funcional(self):
        """Verifica que al aceptar una propuesta, se libera el hueco y se ofrece al siguiente."""
        hoy = date.today()
        d1 = hoy + timedelta(days=1) # Hueco
        d2 = hoy + timedelta(days=2) # Cita A cada vez más cerca
        d3 = hoy + timedelta(days=3) # Cita B
        
        h1 = Cita.objects.create(paciente=self.pa, medico=self.medico, fecha=d1, hora_inicio="09:00", estado=EstadoCita.CANCELADA)
        c_a = Cita.objects.create(paciente=self.pa, medico=self.medico, fecha=d2, hora_inicio="09:00", estado=EstadoCita.CONFIRMADA)
        c_b = Cita.objects.create(paciente=self.pb, medico=self.medico, fecha=d3, hora_inicio="09:00", estado=EstadoCita.CONFIRMADA)
        
        # 1. Propuesta para A
        iniciar_reasignacion(h1)
        prop_a = PropuestaReasignacion.objects.get(paciente=self.pa, hueco=h1)
        
        # 2. A Acepta (Simulamos vista)
        factory = RequestFactory()
        request = factory.post('/fake/')
        request.user = self.u_pa
        aceptar_propuesta(request, prop_a.id)
        
        # 3. Verificar que A se movió y se generó hueco en d2
        c_a.refresh_from_db()
        self.assertEqual(c_a.fecha, d1)
        
        # Debe existir un nuevo hueco libre en d2 con Nivel 1
        h2 = Cita.objects.get(fecha=d2, estado=EstadoCita.CANCELADA)
        self.assertEqual(h2.nivel_cascada, 1)
        
        # 4. Verificar que B tiene propuesta para d2 (Reacción en cadena)
        self.assertTrue(PropuestaReasignacion.objects.filter(paciente=self.pb, hueco=h2).exists())
        print("✅ Test Reacción en Cadena: Salto recursivo verificado.")

    def test_circuit_breaker_limite_5(self):
        """El motor debe detenerse al alcanzar el nivel de cascada 5."""
        manana = date.today() + timedelta(days=1)
        
        # Creamos un hueco directamente con nivel 5
        h5 = Cita.objects.create(
            paciente=self.pa, medico=self.medico, fecha=manana, hora_inicio="12:00", 
            estado=EstadoCita.CANCELADA, nivel_cascada=5
        )
        
        # Candidato apto
        Cita.objects.create(
            paciente=self.pb, medico=self.medico, fecha=manana + timedelta(days=5), 
            hora_inicio="12:00", estado=EstadoCita.CONFIRMADA
        )
        
        iniciar_reasignacion(h5)
        
        # No debería haber ninguna propuesta debido al Circuit Breaker
        self.assertFalse(PropuestaReasignacion.objects.filter(hueco=h5).exists())
        print("✅ Test Circuit Breaker: Límite de nivel 5 respetado.")
