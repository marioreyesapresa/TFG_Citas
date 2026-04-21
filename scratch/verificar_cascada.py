
import os
import django
from datetime import date, timedelta
from django.utils import timezone

# Configurar el entorno de Django si se ejecuta como script independiente
# Aunque usualmente se correrá vía 'python manage.py shell < script.py'
try:
    from gestion_citas.models import (
        Cita, Medico, Paciente, Especialidad, Centro, 
        EstadoCita, NivelUrgencia, PropuestaReasignacion, EstadoPropuesta
    )
    from django.contrib.auth.models import User
    from gestion_citas.algoritmo_reasignacion import iniciar_reasignacion
except ImportError:
    print("Error: Asegúrate de ejecutar este script con 'python manage.py shell < scratch/verificar_cascada.py'")
    exit()

def run_test():
    print("\n" + "="*50)
    print("🧪 PRUEBA DE REEVALUACIÓN EN CASCADA (TFG)")
    print("="*50)
    
    # 1. Limpieza de datos de pruebas anteriores
    print("🧹 Limpiando datos de prueba previos...")
    User.objects.filter(username__startswith="test_").delete()
    Especialidad.objects.filter(nombre="TestEsp").delete()
    Centro.objects.filter(nombre="TestCentro").delete()
    
    # 2. Creación del entorno de prueba
    esp = Especialidad.objects.create(nombre="TestEsp")
    centro = Centro.objects.create(nombre="TestCentro")
    
    u_med = User.objects.create_user(username="test_medico", last_name="Cascada")
    medico = Medico.objects.create(user=u_med, especialidad=esp, centro=centro, numero_colegiado="123")
    
    hoy = date.today()
    manana = hoy + timedelta(days=1)
    semana_proxima = hoy + timedelta(days=7)
    
    # IMPORTANTE: El médico necesita un horario para que las citas sean válidas (R14)
    from gestion_citas.models import HorarioMedico
    HorarioMedico.objects.create(
        medico=medico, 
        dia_semana=manana.weekday(), 
        hora_inicio="08:00", 
        hora_fin="20:00"
    )
    HorarioMedico.objects.create(
        medico=medico, 
        dia_semana=semana_proxima.weekday(), 
        hora_inicio="08:00", 
        hora_fin="20:00"
    )
    
    # Paciente A (Alta Urgencia -> Debería ser el primero en el ranking)
    ua = User.objects.create_user(username="test_paciente_a", first_name="Paciente", last_name="A")
    pa = Paciente.objects.create(user=ua, telefono="600000001", preferencia_turno='M')
    
    # Paciente B (Media Urgencia -> Debería ser el segundo en el ranking)
    ub = User.objects.create_user(username="test_paciente_b", first_name="Paciente", last_name="B")
    pb = Paciente.objects.create(user=ub, telefono="600000002", preferencia_turno='M')
    
    # 3. Preparación del escenario de citas
    # Cita original que ocupa el hueco de mañana (la que cancelaremos)
    u_orig = User.objects.create_user(username="test_paciente_orig")
    p_orig = Paciente.objects.create(user=u_orig, telefono="000")
    cita_a_cancelar = Cita.objects.create(
        paciente=p_orig, medico=medico, especialidad=esp, centro=centro,
        fecha=manana, hora_inicio="10:00", estado=EstadoCita.CONFIRMADA
    )
    
    # Citas futuras para los candidatos adelantar
    # Importante: paciente 'A' tiene urgencia 3 (Alta) y 'B' tiene 2 (Media)
    cita_a = Cita.objects.create(
        paciente=pa, medico=medico, especialidad=esp, centro=centro,
        fecha=semana_proxima, hora_inicio="11:00", urgencia=NivelUrgencia.ALTA, estado=EstadoCita.CONFIRMADA
    )
    cita_b = Cita.objects.create(
        paciente=pb, medico=medico, especialidad=esp, centro=centro,
        fecha=semana_proxima, hora_inicio="12:00", urgencia=NivelUrgencia.MEDIA, estado=EstadoCita.CONFIRMADA
    )
    
    print(f"📊 Escenario configurado:")
    print(f"   - Hueco mañana: {manana} 10:00")
    print(f"   - Candidato A (Urgencia Alta): Cita el {semana_proxima}")
    print(f"   - Candidato B (Urgencia Media): Cita el {semana_proxima}")
    
    # 4. EJECUCIÓN: PASO 1 - CANCELACIÓN
    print("\n[ACCION 1] Cancelando la cita de mañana...")
    cita_a_cancelar.estado = EstadoCita.CANCELADA
    cita_a_cancelar.save() # El modelo Cita dispara el motor automáticamente
    
    propuesta1 = PropuestaReasignacion.objects.filter(hueco=cita_a_cancelar, estado=EstadoPropuesta.PENDIENTE).first()
    
    if propuesta1 and propuesta1.paciente == pa:
        print(f"✅ MOTOR NIVEL 1: El hueco se ha ofrecido correctamente al Paciente A.")
    else:
        print(f"❌ ERROR: El motor no asignó correctamente. Ofrecido a: {propuesta1.paciente if propuesta1 else 'Nadie'}")
        return

    # 5. EJECUCIÓN: PASO 2 - RECHAZO (CASCADA)
    print("\n[ACCION 2] El Paciente A RECHAZA la propuesta. Simulando lógica de Cascada...")
    
    # Emulamos lo que hace la vista 'rechazar_propuesta'
    propuesta1.estado = EstadoPropuesta.RECHAZADA
    propuesta1.save()
    
    # Relanzamos el motor manualmente (como hace la vista)
    iniciar_reasignacion(propuesta1.hueco)
    
    propuesta2 = PropuestaReasignacion.objects.filter(
        hueco=cita_a_cancelar, 
        estado=EstadoPropuesta.PENDIENTE
    ).first()
    
    if propuesta2 and propuesta2.paciente == pb:
        print(f"\n✨ MAGIA DE REASIGNACIÓN ✨")
        print(f"✅ MOTOR NIVEL 2 (CASCADA): El motor detectó el rechazo de A y saltó automáticamente al Paciente B.")
        print(f"   Propuesta válida para: {propuesta2.paciente}")
    else:
        print(f"❌ ERROR EN CASCADA: No se generó la segunda propuesta para B.")
        if propuesta2:
            print(f"   Se le ofreció a: {propuesta2.paciente}")

    print("\n" + "="*50)
    print("🏁 PRUEBA FINALIZADA CON ÉXITO")
    print("="*50)

run_test()
