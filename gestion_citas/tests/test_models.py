from django.test import TestCase
from datetime import date, time
from django.contrib.auth.models import User
from ..models import NivelUrgencia, EstadoCita, Turno, Especialidad, Centro, Medico, Paciente, Cita, HorarioMedico, Notificacion, ConfiguracionReasignacion, ConsultaMedica
from django.core.exceptions import ValidationError

class ModelsFullCoverageTests(TestCase):
    def test_especialidad_centro_str(self):
        esp = Especialidad.objects.create(nombre="TestEsp")
        self.assertEqual(str(esp), "TestEsp")
        
        centro = Centro.objects.create(nombre="TestCentro")
        self.assertEqual(str(centro), "TestCentro")
        
    def test_medico_str_and_properties(self):
        u1 = User.objects.create_user(username="m1", first_name="Dr A", last_name="B")
        esp = Especialidad.objects.create(nombre="E")
        c = Centro.objects.create(nombre="C")
        med = Medico.objects.create(user=u1, especialidad=esp, centro=c, numero_colegiado="COL-001")
        
        self.assertEqual(str(med), "Dr/a. B (E)")
        
    def test_paciente_str(self):
        u2 = User.objects.create_user(username="p1", first_name="Pac", last_name="X")
        pac = Paciente.objects.create(user=u2, dni="12345678Z", telefono="600111222")
        self.assertEqual(str(pac), "Pac X")
        
    def test_horariomedico_clean_and_str(self):
        u1 = User.objects.create_user(username="m_hm", first_name="Dr", last_name="C")
        esp = Especialidad.objects.create(nombre="E")
        c = Centro.objects.create(nombre="C")
        med = Medico.objects.create(user=u1, especialidad=esp, centro=c, numero_colegiado="COL-001")
        
        hm = HorarioMedico(medico=med, dia_semana=0, hora_inicio=time(9,0), hora_fin=time(14,0))
        hm.clean() # should pass
        self.assertTrue("Lunes" in str(hm))
        
        # Test validation error start != 0 or 30
        hm_err = HorarioMedico(medico=med, dia_semana=0, hora_inicio=time(9,15), hora_fin=time(14,0))
        with self.assertRaises(ValidationError):
            hm_err.clean()
            
        # Test validation error end != 0 or 30
        hm_err2 = HorarioMedico(medico=med, dia_semana=0, hora_inicio=time(9,0), hora_fin=time(14,15))
        with self.assertRaises(ValidationError):
            hm_err2.clean()
            
        # Test validation error start > end
        hm_err3 = HorarioMedico(medico=med, dia_semana=0, hora_inicio=time(14,0), hora_fin=time(9,0))
        with self.assertRaises(ValidationError):
            hm_err3.clean()
            
    def test_cita_str_y_estados(self):
        u1 = User.objects.create_user(username="m_c", first_name="Dr", last_name="C")
        u2 = User.objects.create_user(username="p_c", first_name="Pac", last_name="X")
        esp = Especialidad.objects.create(nombre="E")
        c = Centro.objects.create(nombre="C")
        med = Medico.objects.create(user=u1, especialidad=esp, centro=c, numero_colegiado="COL-001")
        pac = Paciente.objects.create(user=u2, dni="11111111H", telefono="600111222")
        
        lunes = date.today()
        from datetime import timedelta
        while lunes.weekday() != 0:
            lunes += timedelta(days=1)
        lunes += timedelta(days=7) # Garantizar futuro
        
        HorarioMedico.objects.create(medico=med, dia_semana=0, hora_inicio=time(9,0), hora_fin=time(14,0))
        
        cita = Cita.objects.create(paciente=pac, medico=med, fecha=lunes, hora_inicio=time(9,0))
        self.assertTrue(str(cita).startswith("Cita: Pac X "))
        
    def test_admin_config(self):
        conf = ConfiguracionReasignacion.objects.create(peso_urgencia=15.0)
        self.assertEqual(str(conf), "Configuración Global del Motor")
        
    def test_notificacion(self):
        u2 = User.objects.create_user(username="p_n", first_name="Pac", last_name="X")
        pac = Paciente.objects.create(user=u2, dni="22222222J", telefono="600111222")
        n = Notificacion.objects.create(paciente=pac, mensaje="M")
        self.assertEqual(str(n), "Notificación para Pac X: No leída")
