import datetime
from datetime import datetime, timedelta
from django.utils import timezone
from .models import Cita, EstadoCita, PropuestaReasignacion, Turno, EstadoPropuesta

# TIEMPO LÍMITE PARA RESPONDER (Requisito R8)
HORAS_TTL = 24 

def determinar_turno(hora):
    """Devuelve 'M' si es antes de las 15:00, 'T' si es después."""
    if hora.hour < 15:
        return Turno.MANANA
    return Turno.TARDE

def iniciar_reasignacion(cita_cancelada):
    """
    Algoritmo Determinista de Reasignación (TFG).
    Se ejecuta automáticamente cuando una cita pasa a estado 'CANCELADA'.
    """
    print(f"\n🚀 MOTOR: Iniciando reasignación para el hueco del {cita_cancelada.fecha} a las {cita_cancelada.hora_inicio}")

    # --- PROTECCIÓN PARA PRUEBAS Y MUNDO REAL ---
    # Si el hueco liberado es de una fecha que ya pasó, el motor no debe actuar.
    if cita_cancelada.fecha < datetime.today().date():
        print("🤷 MOTOR: El hueco liberado es de una fecha pasada. No se puede reasignar a nadie en el pasado.")
        return

    # 1. IDENTIFICAR EL HUECO LIBRE
    medico = cita_cancelada.medico
    fecha_hueco = cita_cancelada.fecha
    hora_hueco = cita_cancelada.hora_inicio
    turno_hueco = determinar_turno(hora_hueco)

    # 2. BUSCAR CANDIDATOS (Requisito R4)
    # Buscamos citas CONFIRMADAS o PENDIENTES que sean POSTERIORES al hueco libre.
    candidatos = Cita.objects.filter(
        medico=medico,
        fecha__gt=fecha_hueco, 
        estado__in=[EstadoCita.PENDIENTE, EstadoCita.CONFIRMADA]
    ).select_related('paciente')

    print(f"🔍 MOTOR: Encontrados {candidatos.count()} candidatos iniciales (citas futuras).")

    mejor_candidato = None
    mejor_puntuacion = -1

    # 3. EVALUACIÓN Y PUNTUACIÓN (Requisito R5)
    for candidato in candidatos:
        puntuacion = 0
        paciente = candidato.paciente
        
        # --- REGLA A: Preferencia de Turno ---
        if paciente.preferencia_turno == turno_hueco:
            puntuacion += 10
        else:
            puntuacion -= 5

        # --- REGLA B: Urgencia Médica (Prioridad absoluta) ---
        puntuacion += (candidato.urgencia * 15)

        # --- REGLA C: Distancia temporal (Optimización) ---
        dias_diferencia = (candidato.fecha - fecha_hueco).days
        puntuacion += (dias_diferencia * 0.1) 

        # --- REGLA D: Restricción Dura (Inmutabilidad diaria) ---
        # No ofrecer el hueco si el paciente YA tiene otra cita ese mismo día (R14)
        # Excluimos las canceladas porque no cuentan como ocupación.
        tiene_cita_ese_dia = Cita.objects.filter(
            paciente=paciente, 
            fecha=fecha_hueco
        ).exclude(estado=EstadoCita.CANCELADA).exists()

        if tiene_cita_ese_dia:
            print(f"   ❌ Descartado {paciente}: Ya tiene cita el {fecha_hueco}")
            continue

        # --- REGLA E: Evitar saturación de propuestas (NUEVA) ---
        # Si el paciente ya tiene una propuesta pendiente de respuesta, no le enviamos otra.
        ya_tiene_propuesta = PropuestaReasignacion.objects.filter(
            cita_original__paciente=paciente,
            estado=EstadoPropuesta.PENDIENTE
        ).exists()

        if ya_tiene_propuesta:
            print(f"   ❌ Descartado {paciente}: Ya tiene una propuesta esperando respuesta.")
            continue

        print(f"   ✅ Candidato: {paciente} | Urgencia: {candidato.get_urgencia_display()} | Puntos: {puntuacion}")

        # 4. SELECCIÓN DEL MEJOR
        if puntuacion > mejor_puntuacion:
            mejor_puntuacion = puntuacion
            mejor_candidato = candidato

    # 5. GENERACIÓN DE LA PROPUESTA (Resultado)
    if mejor_candidato:
        print(f"🏆 GANADOR: {mejor_candidato.paciente} (Cita original: {mejor_candidato.fecha})")
        
        # Crear la propuesta con TTL (Time To Live)
        PropuestaReasignacion.objects.create(
            cita_original=mejor_candidato,
            paciente=mejor_candidato.paciente,
            hueco=cita_cancelada,
            fecha_limite=timezone.now() + timedelta(hours=HORAS_TTL)
        )
        print("📨 MOTOR: Propuesta enviada y guardada en base de datos.")
    else:
        print("🤷 MOTOR: No se encontraron candidatos aptos para este hueco.")