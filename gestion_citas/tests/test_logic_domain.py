from django.test import TestCase
from datetime import date, timedelta, time
from django.contrib.auth.models import User
from ..models import Especialidad, Centro, Medico, HorarioMedico, Paciente, Cita, EstadoCita
from ..logic import buscar_huecos_disponibles

class LogicBuscarHuecosTests(TestCase):
    def setUp(self):
        self.esp = Especialidad.objects.create(nombre="Cardiologia")
        self.centro = Centro.objects.create(nombre="Centro Sur")
        self.u_med = User.objects.create_user(username="m1")
        self.medico = Medico.objects.create(user=self.u_med, especialidad=self.esp, centro=self.centro, numero_colegiado="COL-001")
        
        # Horario: Lunes a viernes de 09:00 a 11:00
        for i in range(5):
            HorarioMedico.objects.create(
                medico=self.medico, dia_semana=i, 
                hora_inicio=time(9, 0), hora_fin=time(11, 0)
            )
            
        self.u_pac = User.objects.create_user(username="p1")
        self.paciente = Paciente.objects.create(user=self.u_pac, dni="12345678Z", fecha_nacimiento=date(1990, 1, 1), telefono="600111222")

    def test_fechas_invalidas(self):
        """Si la fecha de inicio es mayor, retorna vacío."""
        res = buscar_huecos_disponibles("Cardiologia", date.today(), date.today() - timedelta(days=1))
        self.assertEqual(res, [])

    def test_especialidad_no_existe(self):
        """Retorna vacío si la especialidad no existe o está mal escrita."""
        res = buscar_huecos_disponibles("Inexistente", date.today(), date.today() + timedelta(days=1))
        self.assertEqual(res, [])
        res = buscar_huecos_disponibles(999, date.today(), date.today() + timedelta(days=1))
        self.assertEqual(res, [])

    def test_medico_sin_especialidad(self):
        """Retorna vacío si no hay médicos en la especialidad."""
        Especialidad.objects.create(nombre="Vacio")
        res = buscar_huecos_disponibles("Vacio", date.today(), date.today() + timedelta(days=1))
        self.assertEqual(res, [])

    def test_huecos_libres_y_ocupados(self):
        """Busca huecos y resta las citas ocupadas."""
        lunes = date.today()
        while lunes.weekday() != 0:
            lunes += timedelta(days=1)
        lunes += timedelta(days=7) # Garantizar futuro

        # Ocupamos el primer hueco
        Cita.objects.create(
            medico=self.medico, paciente=self.paciente, 
            fecha=lunes, hora_inicio=time(9, 0), estado=EstadoCita.CONFIRMADA
        )
        
        # Cita cancelada (no debe restar hueco)
        Cita.objects.create(
            medico=self.medico, paciente=self.paciente, 
            fecha=lunes, hora_inicio=time(9, 30), estado=EstadoCita.CANCELADA
        )

        res = buscar_huecos_disponibles(self.esp.id, lunes, lunes) # Test INT
        horarios = [h['hora_inicio'] for h in res]
        
        # 9:00 está ocupada, no debe estar
        self.assertNotIn(time(9, 0), horarios)
        
        # 9:30 está cancelada, sí debe estar disponible
        self.assertIn(time(9, 30), horarios)
        
        # Debe haber al menos un hueco
        self.assertTrue(len(res) > 0)
