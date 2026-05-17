import os
import sys
import django
import random
from datetime import time, timedelta, datetime

# Configurar el entorno de Django dinámicamente
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from gestion_citas.models import (
    Medico, HorarioMedico, Cita, Paciente, Especialidad, 
    Centro, EstadoCita, NivelUrgencia
)

def crear_medicos_horario_partido():
    print("=== INICIANDO CREACIÓN DE MÉDICOS CON HORARIO PARTIDO ===")
    
    # 1. Verificar prerrequisitos en la Base de Datos
    especialidades = list(Especialidad.objects.all())
    centros = list(Centro.objects.all())
    pacientes = list(Paciente.objects.all())
    
    if not especialidades or not centros:
        print("Error: Se necesitan especialidades y centros en la base de datos para asignar a los nuevos médicos.")
        return
    if not pacientes:
        print("Error: Se necesitan pacientes registrados para poder asignarles las citas de prueba.")
        return

    # Banco de datos para generar nombres realistas
    NOMBRES = ['Patricia', 'Guillermo', 'Beatriz', 'Fernando', 'Alicia', 'Roberto', 'Clara', 'Ricardo', 'Victoria', 'Alberto']
    APELLIDOS = ['Ortega', 'Molina', 'Castro', 'Serrano', 'Delgado', 'Morales', 'Marín', 'Navarro', 'Soler', 'Vidal']
    
    # Días de la semana para citas de prueba
    hoy = datetime.now().date()
    
    # Función auxiliar para encontrar los siguientes 4 días laborables futuros a partir de 'hoy + 7 días'
    def obtener_dias_laborables_futuros(desde_fecha, cantidad):
        dias = []
        fecha_actual = desde_fecha + timedelta(days=7)
        while len(dias) < cantidad:
            if fecha_actual.weekday() < 5: # 0-4 son Lunes a Viernes
                dias.append(fecha_actual)
            fecha_actual += timedelta(days=1)
        return dias

    dias_citas = obtener_dias_laborables_futuros(hoy, 4)

    # 2. Creación de los 10 médicos
    medicos_creados = []
    for i in range(10):
        username = f"medico_partido_{i}"
        
        # Evitar crear duplicados si el script se ejecuta más de una vez
        user = User.objects.filter(username=username).first()
        if user:
            medico = Medico.objects.filter(user=user).first()
            if medico:
                print(f"El médico {username} ya existe. Saltando creación de perfil.")
                medicos_creados.append(medico)
                continue
        
        nom = NOMBRES[i % len(NOMBRES)]
        ape = f"{APELLIDOS[i % len(APELLIDOS)]} {APELLIDOS[(i+1) % len(APELLIDOS)]}"
        
        # Crear usuario
        user = User.objects.create_user(
            username=username,
            password='password123',
            first_name=nom,
            last_name=ape
        )
        
        # Crear perfil Medico
        medico = Medico.objects.create(
            user=user,
            numero_colegiado=f"COL-3500{i}",
            especialidad=random.choice(especialidades),
            centro=random.choice(centros)
        )
        medicos_creados.append(medico)
        print(f"-> Creado Dr/a. {ape} ({medico.especialidad}) en {medico.centro}")

        # 3. Asignar el HORARIO PARTIDO (Lunes a Viernes)
        # Mañana: 09:00 - 13:00  |  Tarde: 16:00 - 20:00
        for dia in range(5):
            # Turno de mañana
            HorarioMedico.objects.create(
                medico=medico,
                dia_semana=dia,
                hora_inicio=time(9, 0),
                hora_fin=time(13, 0)
            )
            # Turno de tarde
            HorarioMedico.objects.create(
                medico=medico,
                dia_semana=dia,
                hora_inicio=time(16, 0),
                hora_fin=time(20, 0)
            )
        print("   Horario partido asignado (L-V: 09:00-13:00 y 16:00-20:00).")

    # 4. Asignar 4 citas de prueba a cada uno de los 10 médicos nuevos
    # Dos citas por la mañana y dos por la tarde, en diferentes días laborables
    horas_propuestas = [
        time(9, 30),   # Mañana 1
        time(11, 0),   # Mañana 2
        time(16, 30),  # Tarde 1
        time(18, 0)    # Tarde 2
    ]

    print("\nGenerando citas de prueba respetando la integridad existente...")
    for medico in medicos_creados:
        citas_medico_actual = Cita.objects.filter(medico=medico).count()
        if citas_medico_actual >= 4:
            print(f"Dr/a. {medico.user.last_name} ya tiene {citas_medico_actual} citas asignadas. Saltando.")
            continue
            
        citas_nuevas_creadas = 0
        for index, hora in enumerate(horas_propuestas):
            fecha_cita = dias_citas[index]
            
            # Buscar un paciente aleatorio que no tenga solapamientos a esta hora/fecha
            paciente_elegido = None
            intentos = 0
            
            while paciente_elegido is None and intentos < 100:
                candidato = random.choice(pacientes)
                intentos += 1
                
                # Regla de integridad: El paciente no debe estar ocupado a esa hora exacta
                ocupado = Cita.objects.filter(
                    paciente=candidato,
                    fecha=fecha_cita,
                    hora_inicio=hora
                ).exclude(estado=EstadoCita.CANCELADA).exists()
                
                if not ocupado:
                    paciente_elegido = candidato
            
            if not paciente_elegido:
                print(f"   [Aviso] No se encontró un paciente libre para la fecha {fecha_cita} a las {hora}. Cita omitida.")
                continue

            # Crear la cita de forma segura utilizando validación completa (.full_clean())
            try:
                nueva_cita = Cita(
                    paciente=paciente_elegido,
                    medico=medico,
                    especialidad=medico.especialidad,
                    centro=medico.centro,
                    fecha=fecha_cita,
                    hora_inicio=hora,
                    urgencia=random.choice(NivelUrgencia.values),
                    estado=EstadoCita.CONFIRMADA
                )
                nueva_cita.full_clean()
                nueva_cita.save()
                citas_nuevas_creadas += 1
            except Exception as e:
                print(f"   [Error] Falló la validación al crear cita: {e}")
                
        print(f"-> Creadas {citas_nuevas_creadas} citas de prueba exitosamente para Dr/a. {medico.user.last_name}")

    print("\n=== PROCESO COMPLETADO CON ÉXITO Y SIN AFECTAR DATOS EXISTENTES ===")

if __name__ == "__main__":
    crear_medicos_horario_partido()
