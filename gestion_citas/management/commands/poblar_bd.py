import random
from datetime import timedelta, date, datetime, time
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
import unicodedata
from django.core.exceptions import ValidationError

from gestion_citas.models import (
    Centro, Especialidad, Medico, Paciente, 
    HorarioMedico, Cita, EstadoCita, DURACION_CITA, 
    ConfiguracionReasignacion, Turno, NivelUrgencia,
    Notificacion, PropuestaReasignacion
)

class Command(BaseCommand):
    help = 'Puebla la base de datos con 15 Médicos, 30 Pacientes y 150 Citas de prueba'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("=== INICIANDO BORRADO DE BASE DE DATOS LOCAL ==="))
        
        # 1. LIMPIEZA
        Cita.objects.all().delete()
        PropuestaReasignacion.objects.all().delete()
        Notificacion.objects.all().delete()
        HorarioMedico.objects.all().delete()
        Medico.objects.all().delete()
        Paciente.objects.all().delete()
        Especialidad.objects.all().delete()
        Centro.objects.all().delete()
        ConfiguracionReasignacion.objects.all().delete()

        # Borrar todos los usuarios que no sean superuser
        User.objects.filter(is_superuser=False).delete()
        
        self.stdout.write(self.style.SUCCESS("Base de datos limpia."))

        # 2. CONFIGURACIÓN REASIGNACIÓN
        ConfiguracionReasignacion.objects.create(
            peso_urgencia=15.0,
            peso_antiguedad=0.1,
            prioridad_turno=10.0
        )
        self.stdout.write(self.style.SUCCESS("✓ Configuración de Reasignación creada."))

        # 3. ENTIDADES BASE (Centros y Especialidades)
        centros_nombres = ['Hospital Central', 'Clínica Norte']
        centros = [Centro.objects.create(nombre=n) for n in centros_nombres]

        especialidades_nombres = ['Pediatría', 'Dermatología', 'Medicina General']
        especialidades = [Especialidad.objects.create(nombre=n) for n in especialidades_nombres]
        # Nombres y apellidos comunes y reales (Al menos 45 para evitar repeticiones)
        NOMBRES_COMUNES = [
            'Laura', 'Marta', 'María', 'Lucía', 'Paula', 'Carmen', 'Ana', 'Daniela', 'Carla', 'Sara', 'Elena', 'Alba', 'Noelia',
            'Alejandro', 'David', 'Daniel', 'Pablo', 'Javier', 'Álvaro', 'Carlos', 'Hugo', 'Manuel', 'Mario', 'Diego', 'Jorge', 'Adrián',
            'Sofía', 'Valeria', 'Julia', 'Irene', 'Natalia', 'Raquel', 'Rosa', 'Teresa', 'Beatriz', 'Silvia', 'Patricia', 'Mónica', 
            'Victoria', 'Rocío', 'Pilar', 'Blanca', 'Clara', 'Celia', 'Marcos', 'Iván', 'Sergio', 'Miguel', 'Juan', 'Antonio', 
            'José', 'Francisco', 'Alberto', 'Rafael', 'Pedro', 'Luis', 'Fernando', 'Rubén', 'Víctor', 'Roberto', 'Raúl', 'Oscar', 'Ramón'
        ]
        
        APELLIDOS_COMUNES = [
            'García', 'Rodríguez', 'González', 'Fernández', 'López', 'Martínez', 'Sánchez', 'Pérez', 'Gómez', 'Martín', 
            'Jiménez', 'Ruiz', 'Hernández', 'Díaz', 'Moreno', 'Muñoz', 'Álvarez', 'Romero', 'Alonso', 'Gutiérrez'
        ]

        # Evitar repetir nombres barajando y sacando uno a uno
        random.shuffle(NOMBRES_COMUNES)

        # 4. MÉDICOS (15 médicos con turnos divididos: Mañana y Tarde)
        medicos = []
        # Crear usuarios para médicos
        start_date = timezone.now().date()
        
        for i in range(1, 16):
            nombre = NOMBRES_COMUNES.pop()
            apellido = f"{random.choice(APELLIDOS_COMUNES)} {random.choice(APELLIDOS_COMUNES)}"
            clean_nombre = unicodedata.normalize('NFD', nombre).encode('ascii', 'ignore').decode('utf-8').lower().replace(' ', '')
            
            u = User.objects.create_user(
                username=f'medico_{clean_nombre}',
                password='password123',
                first_name=nombre,
                last_name=apellido
            )
            
            # Asignación pseudoalematoria balanceada
            centro = centros[i % len(centros)]
            especialidad = especialidades[i % len(especialidades)]
            
            medico = Medico.objects.create(
                user=u,
                numero_colegiado=f'COL-{10000+i}',
                especialidad=especialidad,
                centro=centro
            )
            medicos.append(medico)

            # Asignar Horario laboral: (M: 08:00-14:00, T: 15:00-21:00)
            es_turno_manana = (i % 2 == 0)
            hora_inicio = time(8, 0) if es_turno_manana else time(15, 0)
            hora_fin = time(14, 0) if es_turno_manana else time(21, 0)
            
            # Asignar a trabajar de Lunes(0) a Viernes(4) o de Miércoles(2) a Domingo(6)
            dias_trabajo = range(0, 5) if i % 3 != 0 else range(2, 7)
            for dia in dias_trabajo:
                HorarioMedico.objects.create(
                    medico=medico,
                    dia_semana=dia,
                    hora_inicio=hora_inicio,
                    hora_fin=hora_fin
                )
        
        self.stdout.write(self.style.SUCCESS(f"✓ {len(medicos)} Médicos y sus horarios creados."))

        # 5. PACIENTES (30 pacientes)
        pacientes = []
        turnos_choice = [Turno.MANANA, Turno.TARDE]
        for i in range(1, 31):
            nombre_p = NOMBRES_COMUNES.pop()
            apellido_p = f"{random.choice(APELLIDOS_COMUNES)} {random.choice(APELLIDOS_COMUNES)}"
            clean_nombre_p = unicodedata.normalize('NFD', nombre_p).encode('ascii', 'ignore').decode('utf-8').lower().replace(' ', '')

            u = User.objects.create_user(
                username=f'paciente_{clean_nombre_p}',
                password='password123',
                email=f'tfgcitas+paciente{i}@gmail.com', # Todo llega a tfgcitas@gmail.com
                first_name=nombre_p,
                last_name=apellido_p
            )
            paciente = Paciente.objects.create(
                user=u,
                telefono=f'600100{i:03d}',
                preferencia_turno=random.choice(turnos_choice)
            )
            pacientes.append(paciente)
            
        self.stdout.write(self.style.SUCCESS(f"✓ {len(pacientes)} Pacientes creados."))

        # 6. GENERAR 150 CITAS VALIDAS
        self.stdout.write("Generando 150 citas (Puede tardar unos segundos)...")
        citas_creadas = 0
        intentos = 0
        estados_citas = [EstadoCita.CONFIRMADA] * 90 

        slots_ocupados_medico = set()
        slots_ocupados_paciente = set()

        # Generar fechas objetivo: Desde hoy hasta 15 días en el futuro
        fechas_disponibles = [start_date + timedelta(days=x) for x in range(0, 15)]

        while citas_creadas < 150 and intentos < 2000:
            intentos += 1
            medico = random.choice(medicos)
            paciente = random.choice(pacientes)
            fecha = random.choice(fechas_disponibles)
            
            # Buscar horario de ese médico en ese día
            dia_semana = fecha.weekday()
            horario = HorarioMedico.objects.filter(medico=medico, dia_semana=dia_semana).first()
            if not horario:
                continue

            # Generar lista de horas posibles desde inicio hasta fin -30min
            dt_dummy = datetime.combine(fecha, horario.hora_inicio)
            dt_fin = datetime.combine(fecha, horario.hora_fin)
            colas_horas = []
            
            while dt_dummy < dt_fin:
                colas_horas.append(dt_dummy.time())
                dt_dummy += timedelta(minutes=DURACION_CITA)

            if not colas_horas:
                continue
                
            hora_inicio_cita = random.choice(colas_horas)
            
            # Validaciones R14 (Unicidad para evitar AssertionError del clean())
            llave_medico = (medico.id, fecha, hora_inicio_cita)
            llave_paciente = (paciente.id, fecha, hora_inicio_cita)
            
            # Inmutabilidad Diaria Fuerte
            llave_diaria_paciente = (paciente.id, fecha)
            citas_hoy_paciente = sum(1 for p, f, _ in slots_ocupados_paciente if p == paciente.id and f == fecha)

            if llave_medico in slots_ocupados_medico or llave_paciente in slots_ocupados_paciente or citas_hoy_paciente > 0:
                continue

            # Todo correcto, instanciar usando save() sin activar motor (desactivaremos trigger fake)
            urgencia = random.choice([NivelUrgencia.BAJA, NivelUrgencia.MEDIA, NivelUrgencia.ALTA])
            estado = random.choice(estados_citas)

            # Inyectar
            cita = Cita(
                paciente=paciente,
                medico=medico,
                especialidad=medico.especialidad,
                centro=medico.centro,
                fecha=fecha,
                hora_inicio=hora_inicio_cita,
                urgencia=urgencia,
                estado=estado
            )
            
            # Ignoramos full_clean por ahora para inyección masiva segura, 
            # o si usamos save() asume estado nuevo (no anterior cancelado), no disparará motor
            try:
                cita.save()
                slots_ocupados_medico.add(llave_medico)
                slots_ocupados_paciente.add(llave_paciente)
                citas_creadas += 1
            except Exception as e:
                pass # Ignoramos falls raros de validación cruzada y probamos el siguiente loop

        self.stdout.write(self.style.SUCCESS(f"✓ {citas_creadas} Citas inyectadas (Confirmadas/Pendientes)."))

        # 7. INYECCIÓN DELIBERADA DE CANCELACIONES PARA PRUEBAS DEL MOTOR
        # Tomaremos unas 10 citas futuras existentes confirmadas y forzaremos la cancelación (lo que arrancará tu motor via post_save)
        citas_futuras_a_cancelar = Cita.objects.filter(
            fecha__gt=start_date, 
            estado=EstadoCita.CONFIRMADA
        )[:10]

        canceladas_count = 0
        for cita_c in citas_futuras_a_cancelar:
            cita_c.estado = EstadoCita.CANCELADA
            # Esto ejecutará `algoritmo_reasignacion.py` automáticamente imprimiendo logs
            cita_c.save() 
            canceladas_count += 1
            
        self.stdout.write(self.style.SUCCESS(f"✓ {canceladas_count} Citas forzadas a CANCELADA para arrancar motor."))
        self.stdout.write(self.style.SUCCESS("=== POBLACIÓN FINALIZADA CON ÉXITO ==="))
