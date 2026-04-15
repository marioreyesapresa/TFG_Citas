import random
import uuid
import unicodedata
from datetime import timedelta, date, datetime, time
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction

from gestion_citas.models import (
    Centro, Especialidad, Medico, Paciente, 
    HorarioMedico, Cita, EstadoCita, DURACION_CITA, 
    Turno, NivelUrgencia, ConsultaMedica, Receta
)

class Command(BaseCommand):
    help = 'Seeder Pro v2.1: Puebla la base de datos con volumen profesional para demostración (TFG)'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("=== INICIANDO ESCALAMIENTO MASIVO DE DATOS (PRO v2.1) ==="))
        
        # 1. LIMPIEZA TOTAL
        with transaction.atomic():
            Receta.objects.all().delete()
            ConsultaMedica.objects.all().delete()
            Cita.objects.all().delete()
            HorarioMedico.objects.all().delete()
            Medico.objects.all().delete()
            Paciente.objects.all().delete()
            Especialidad.objects.all().delete()
            Centro.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
        
        self.stdout.write(self.style.SUCCESS("Base de datos reseteada."))

        # 2. CATÁLOGO DE CENTROS (10)
        centros_data = [
            'Hospital Universitario Central', 'Clínica Santa María', 'Centro Médico Quirúrgico', 
            'Hospital del Norte', 'Hospital del Sur', 'Clínica San José', 
            'Policlínica Metropolitana', 'Centro de Salud Integral', 
            'Hospital de la Esperanza', 'Clínica de Rehabilitación Avanzada'
        ]
        centros = [Centro.objects.create(nombre=n) for n in centros_data]

        # 3. CATÁLOGO DE ESPECIALIDADES (15)
        especialidades_data = [
            'Cardiología', 'Traumatología', 'Dermatología', 'Neurología', 'Oftalmología', 
            'Pediatría', 'Psiquiatría', 'Ginecología', 'Oncología', 'Urología', 
            'Neumología', 'Endocrinología', 'Gastroenterología', 'Otorrinolaringología', 'Medicina Interna'
        ]
        especialidades = [Especialidad.objects.create(nombre=n) for n in especialidades_data]

        # 4. BANCO DE NOMBRES
        NOMBRES = ['Laura', 'Marta', 'Lucía', 'Paula', 'Ana', 'Elena', 'Alba', 'Sofía', 'Julia', 'Irene', 'Alejandro', 'David', 'Daniel', 'Pablo', 'Javier', 'Álvaro', 'Carlos', 'Manuel', 'Diego', 'Jorge', 'Adrián', 'Hugo', 'Iván', 'Sergio', 'Miguel', 'Juan', 'Luis', 'Víctor', 'Raúl', 'Oscar']
        APELLIDOS = ['García', 'Rodríguez', 'González', 'Fernández', 'López', 'Martínez', 'Sánchez', 'Pérez', 'Gómez', 'Martín', 'Jiménez', 'Ruiz', 'Hernández', 'Díaz', 'Moreno', 'Muñoz', 'Álvarez', 'Romero', 'Alonso', 'Gutiérrez']

        def generate_dni():
            nums = "".join([str(random.randint(0, 9)) for _ in range(8)])
            letras = "TRWAGMYFPDXBNJZSQVHLCKE"
            return f"{nums}{letras[int(nums) % 23]}"

        # 5. GENERACIÓN DE MÉDICOS (30)
        medicos = []
        for i in range(30):
            nom = random.choice(NOMBRES)
            ape = f"{random.choice(APELLIDOS)} {random.choice(APELLIDOS)}"
            u = User.objects.create_user(username=f"medico_{i}", password='password123', first_name=nom, last_name=ape)
            medico = Medico.objects.create(user=u, numero_colegiado=f"COL-{20000+i}", especialidad=random.choice(especialidades), centro=random.choice(centros))
            medicos.append(medico)
            for dia in range(5):
                HorarioMedico.objects.create(medico=medico, dia_semana=dia, hora_inicio=time(8,0), hora_fin=time(14,0))

        # 6. GENERACIÓN DE PACIENTES (100)
        pacientes = []
        for i in range(100):
            nom = random.choice(NOMBRES)
            ape = f"{random.choice(APELLIDOS)} {random.choice(APELLIDOS)}"
            u = User.objects.create_user(username=f"paciente_{i}", password='password123', first_name=nom, last_name=ape)
            pacientes.append(Paciente.objects.create(user=u, dni=generate_dni(), telefono=f"6{random.randint(10000000, 99999999)}"))

        # 7. GENERACIÓN DE CITAS (250+)
        self.stdout.write("Generando citas...")
        hoy = timezone.now().date()
        citas_creadas = []
        
        for i in range(270):
            # Para evitar el error de "citas en el pasado", creamos todas para HOY o FUTURO
            # y luego "bajamos" las que interesen al pasado mediante .update()
            medico = random.choice(medicos)
            paciente = random.choice(pacientes)
            
            # Buscamos un hueco válido para este médico (L-V, 8-14)
            fecha_futura = hoy + timedelta(days=random.randint(0, 60))
            if fecha_futura.weekday() > 4: fecha_futura -= timedelta(days=2) # Evitar findes
            
            hora = time(random.choice(range(8, 14)), random.choice([0, 30]))
            
            if Cita.objects.filter(medico=medico, fecha=fecha_futura, hora_inicio=hora).exists(): continue
            
            cita = Cita.objects.create(
                paciente=paciente, medico=medico, especialidad=medico.especialidad, 
                centro=medico.centro, fecha=fecha_futura, hora_inicio=hora,
                urgencia=random.choice(NivelUrgencia.values), estado=EstadoCita.CONFIRMADA
            )
            citas_creadas.append(cita)

        # 8. "VIAJE EN EL TIEMPO" PARA INFORMES CLÍNICOS (30 Atendidas)
        self.stdout.write("Simulando 30 consultas atendidas (Viaje en el tiempo)...")
        citas_para_atender = citas_creadas[:30]
        DATOS_CLINICOS = [
            ("Faringoamigdalitis", "Dolor al tragar", "Ibuprofeno 600mg", "Amoxicilina"),
            ("Esguince", "Dolor tras caída", "Vendaje y frío", "Enantyum"),
            ("Control HT", "Revisión tensión", "Seguir dieta", "Enalapril")
        ]

        for cita in citas_para_atender:
            fecha_pasada = hoy - timedelta(days=random.randint(1, 15))
            if fecha_pasada.weekday() > 4: fecha_pasada -= timedelta(days=2)
            
            # Bypass de validaciones mediante update()
            Cita.objects.filter(id=cita.id).update(fecha=fecha_pasada, estado=EstadoCita.ATENDIDA)
            cita.refresh_from_db()
            
            motivo, desc, plan, med = random.choice(DATOS_CLINICOS)
            consulta = ConsultaMedica.objects.create(
                cita=cita, motivo_consulta=motivo, 
                descripcion_problema=f"{desc}. Evolución favorable.",
                diagnostico_principal=f"Paciente con {motivo.lower()}.",
                tratamiento_pautas=plan
            )
            Receta.objects.create(consulta=consulta, medicamento=med, posologia="1 cada 8h", duracion="1 semana")

        self.stdout.write(self.style.SUCCESS("=== POBLACIÓN FINALIZADA CON ÉXITO ==="))
