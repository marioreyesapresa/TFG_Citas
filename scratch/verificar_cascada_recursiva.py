
import os
import django
from datetime import date, timedelta
from django.utils import timezone

from gestion_citas.models import (
    Cita, Medico, Paciente, Especialidad, Centro, 
    EstadoCita, NivelUrgencia, PropuestaReasignacion, EstadoPropuesta
)
from django.contrib.auth.models import User
from gestion_citas.algoritmo_reasignacion import iniciar_reasignacion
from gestion_citas.views.acciones_motor import aceptar_propuesta
from django.test import RequestFactory

def run_test():
    print("\n" + "="*60)
    print("🧪 PRUEBA DE REACCIÓN EN CADENA: SALTO RECURSIVO (TFG)")
    print("="*60)
    
    # 1. Limpieza
    User.objects.filter(username__startswith="test_").delete()
    
    # 2. Entorno
    esp = Especialidad.objects.create(nombre="TestEsp")
    centro = Centro.objects.create(nombre="TestCentro")
    u_med = User.objects.create_user(username="test_medico", last_name="Cascada")
    medico = Medico.objects.create(user=u_med, especialidad=esp, centro=centro, numero_colegiado="123")
    
    # Horarios (Lun, Mar, Mie, Jue)
    from gestion_citas.models import HorarioMedico
    for i in range(5):
        HorarioMedico.objects.create(medico=medico, dia_semana=i, hora_inicio="08:00", hora_fin="20:00")
    
    hoy = date.today()
    dias = [hoy + timedelta(days=i) for i in range(1, 10)]
    
    # Paciente A (Próximo)
    ua = User.objects.create_user(username="test_paciente_a", first_name="Paciente", last_name="A")
    pa = Paciente.objects.create(user=ua, telefono="601")
    # Paciente B (Más tarde)
    ub = User.objects.create_user(username="test_paciente_b", first_name="Paciente", last_name="B")
    pb = Paciente.objects.create(user=ub, telefono="602")
    
    # 3. Escenario
    # Hueco 0 (Cancelado)
    u0 = User.objects.create_user(username="test_paciente_0")
    p0 = Paciente.objects.create(user=u0, telefono="000")
    h0 = Cita.objects.create(paciente=p0, medico=medico, fecha=dias[0], hora_inicio="10:00", estado=EstadoCita.CONFIRMADA)
    
    # Cita Paciente A (en dias[1]) - ALTA URGENCIA
    cita_a = Cita.objects.create(paciente=pa, medico=medico, fecha=dias[1], hora_inicio="10:30", urgencia=NivelUrgencia.ALTA, estado=EstadoCita.CONFIRMADA)
    # Cita Paciente B (en dias[2]) - MEDIA URGENCIA
    cita_b = Cita.objects.create(paciente=pb, medico=medico, fecha=dias[2], hora_inicio="11:00", urgencia=NivelUrgencia.MEDIA, estado=EstadoCita.CONFIRMADA)
    
    print(f"📍 Estado Inicial:")
    print(f"   - Hueco Lunes: {dias[0]}")
    print(f"   - Paciente A: {dias[1]}")
    print(f"   - Paciente B: {dias[2]}")

    # 4. PASO 1: Cancelación Lunes -> Propuesta a A
    print("\n[PASO 1] Cancelando Lunes...")
    h0.estado = EstadoCita.CANCELADA
    h0.save()
    
    prop_a = PropuestaReasignacion.objects.filter(hueco=h0, paciente=pa, estado=EstadoPropuesta.PENDIENTE).first()
    if not prop_a:
        print("❌ Error: No se generó propuesta para A")
        return
    print("✅ Propuesta 1 generada para Paciente A.")

    # 5. PASO 2: A ACEPTA -> A se mueve a Lunes, Hueco dias[1] queda libre (Nivel 1)
    print("\n[PASO 2] Paciente A ACEPTA el salto...")
    # Emulamos la vista
    factory = RequestFactory()
    request = factory.post('/fake-path/')
    request.user = ua
    
    from gestion_citas.views.acciones_motor import aceptar_propuesta
    aceptar_propuesta(request, prop_a.id)
    
    # Verificamos que A se movió
    cita_a.refresh_from_db()
    print(f"   - Paciente A ahora está el: {cita_a.fecha} (Nivel Cascada: {cita_a.nivel_cascada})")
    
    # IMPORTANTE: ¿Se ha generado un nuevo hueco filtrado en dias[1]?
    h1 = Cita.objects.filter(fecha=dias[1], estado=EstadoCita.CANCELADA, nivel_cascada=1).first()
    if h1:
        print(f"✅ REACCIÓN EN CADENA: Se ha liberado la posición de A ({dias[1]}) con Nivel 1.")
    else:
        print("❌ Error: No se detectó la liberación del hueco de A.")
        return

    # 6. PASO 3: El motor debería haber ofrecido h1 al Paciente B automáticamente
    prop_b = PropuestaReasignacion.objects.filter(hueco=h1, paciente=pb, estado=EstadoPropuesta.PENDIENTE).first()
    if prop_b:
        print(f"🚀 EXITO TOTAL: El Paciente B ya tiene una propuesta para ocupar el hueco que dejó A!")
        print(f"   Propuesta para B el día: {prop_b.hueco.fecha} a las {prop_b.hueco.hora_inicio}")
    else:
        print("❌ Error: El motor no se disparó para el hueco abandonado por A.")

    print("\n" + "="*60)
    print("🏁 PRUEBA DE REACCIÓN EN CADENA FINALIZADA")
    print("="*60)

run_test()
