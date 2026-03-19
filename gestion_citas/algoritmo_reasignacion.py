import datetime
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.mail import send_mail
from .models import Cita, EstadoCita, PropuestaReasignacion, Turno, EstadoPropuesta, ConfiguracionReasignacion, Notificacion

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

    # 0. CARGAR CONFIGURACIÓN DINÁMICA
    config = ConfiguracionReasignacion.objects.first()
    if not config:
        # Fallback por seguridad si no hay config en DB
        peso_urgencia = 15.0
        peso_turno = 10.0
        peso_antiguedad = 0.1
        print("⚠️ MOTOR: No hay configuración global. Usando valores por defecto.")
    else:
        peso_urgencia = config.peso_urgencia
        peso_turno = config.prioridad_turno
        peso_antiguedad = config.peso_antiguedad
        print(f"⚙️ MOTOR: Configuración cargada -> Urgencia:{peso_urgencia}, Turno:{peso_turno}, Antigüedad:{peso_antiguedad}")

    # --- PROTECCIÓN PARA PRUEBAS ---
    if cita_cancelada.fecha < datetime.today().date():
        print("🤷 MOTOR: El hueco liberado es del pasado. Abortando.")
        return

    # 1. IDENTIFICAR EL HUECO LIBRE
    medico = cita_cancelada.medico
    fecha_hueco = cita_cancelada.fecha
    hora_hueco = cita_cancelada.hora_inicio
    turno_hueco = determinar_turno(hora_hueco)

    # 2. BUSCAR CANDIDATOS (Requisito R4)
    candidatos = Cita.objects.filter(
        medico=medico,
        fecha__gt=fecha_hueco, 
        estado__in=[EstadoCita.PENDIENTE, EstadoCita.CONFIRMADA]
    ).select_related('paciente')

    print(f"🔍 MOTOR: {candidatos.count()} candidatos futuros encontrados.")

    mejor_candidato = None
    mejor_puntuacion = -1000 # Score inicial bajo

    # 3. EVALUACIÓN Y PUNTUACIÓN (Requisito R5)
    for candidato in candidatos:
        puntuacion = 0
        paciente = candidato.paciente
        
        # --- REGLA A: Preferencia de Turno (Configurable) ---
        if paciente.preferencia_turno == turno_hueco:
            puntuacion += peso_turno
        else:
            puntuacion -= (peso_turno / 2) # Penalización proporcional

        # --- REGLA B: Urgencia Médica (Configurable) ---
        puntuacion += (candidato.urgencia * peso_urgencia)

        # --- REGLA C: Distancia temporal / Antigüedad (Configurable) ---
        # Cuanto más lejos esté la cita original, más "antigüedad" o "ganas de adelantar" tiene.
        dias_diferencia = (candidato.fecha - fecha_hueco).days
        puntuacion += (dias_diferencia * peso_antiguedad) 

        # --- REGLA D: Restricción Dura (Inmutabilidad diaria) ---
        tiene_cita_ese_dia = Cita.objects.filter(
            paciente=paciente, 
            fecha=fecha_hueco
        ).exclude(estado=EstadoCita.CANCELADA).exists()

        if tiene_cita_ese_dia:
            print(f"   ❌ Descartado {paciente}: Ya tiene cita ese día.")
            continue

        # --- REGLA E: Filtros de Propuestas Previas ---
        # 1. No volver a ofrecerle el MISMO hueco si ya se le ofreció antes (Rechazada, Expirada...)
        ya_se_le_ofrecio_este_hueco = PropuestaReasignacion.objects.filter(
            paciente=paciente,
            hueco=cita_cancelada
        ).exists()

        if ya_se_le_ofrecio_este_hueco:
            print(f"   ❌ Descartado {paciente}: Ya se le ofreció este hueco (y lo rechazó o expiró).")
            continue

        # 2. No abrumar al paciente si ya tiene OTRA propuesta diferente todavía pendiente de que la responda.
        ya_tiene_propuesta_activa = PropuestaReasignacion.objects.filter(
            paciente=paciente,
            estado=EstadoPropuesta.PENDIENTE
        ).exists()

        if ya_tiene_propuesta_activa:
            print(f"   ❌ Descartado {paciente}: Ya tiene otra propuesta activa pendiente de responder.")
            continue

        print(f"   ✅ Candidato: {paciente} | Score: {puntuacion:.2f}")

        # 4. SELECCIÓN DEL MEJOR
        if puntuacion > mejor_puntuacion:
            mejor_puntuacion = puntuacion
            mejor_candidato = candidato

    # 5. GENERACIÓN DE LA PROPUESTA Y NOTIFICACIÓN
    if mejor_candidato:
        print(f"🏆 GANADOR: {mejor_candidato.paciente} (Score: {mejor_puntuacion:.2f})")
        
        # Crear la propuesta
        propuesta = PropuestaReasignacion.objects.create(
            cita_original=mejor_candidato,
            paciente=mejor_candidato.paciente,
            hueco=cita_cancelada,
            fecha_limite=timezone.now() + timedelta(hours=HORAS_TTL)
        )
        
        # Opcional: Podrías querer marcar la cita_original como PENDIENTE de cambio
        # Pero según tu petición, simplemente las nuevas propuestas son las que gestionan el flujo.

        # CREAR NOTIFICACIÓN PERSISTENTE (Novedad V25)
        mensaje_notificacion = f"¡Buenas noticias! Se ha liberado un hueco con el Dr/a. {medico.user.last_name} para el día {fecha_hueco.strftime('%d/%m/%Y')} a las {hora_hueco.strftime('%H:%M')}. ¿Quieres adelantar tu cita?"

        Notificacion.objects.create(
            paciente=mejor_candidato.paciente,
            propuesta=propuesta,
            mensaje=mensaje_notificacion
        )
        
        # ENVIAR CORREO ELECTRÓNICO EN FORMATO HTML PREMIUM (Requisito R7 y R15)
        email_destino = mejor_candidato.paciente.user.email
        
        if email_destino:
            from django.template.loader import render_to_string
            from django.core.mail import EmailMultiAlternatives
            
            # Dominio para URLs absolutas en el correo (Para DEMO)
            dominio = 'http://127.0.0.1:8000'
            
            contexto = {
                'paciente_nombre': mejor_candidato.paciente.user.first_name,
                'medico_nombre': medico.user.last_name,
                'fecha': fecha_hueco.strftime('%d/%m/%Y'),
                'hora': hora_hueco.strftime('%H:%M'),
                'horas_ttl': HORAS_TTL,
                'propuesta': propuesta,
                'dominio': dominio
            }
            
            html_content = render_to_string('gestion_citas/emails/propuesta_mail.html', contexto)
            text_content = f"Hola {mejor_candidato.paciente.user.first_name},\n\n{mensaje_notificacion}\n\nEntra en {dominio} para gestionarla."
            
            correo = EmailMultiAlternatives(
                subject='✨ Nueva Propuesta de Adelanto de Cita Disponible',
                body=text_content,
                from_email='noreply@tfg-citas.com',
                to=[email_destino]
            )
            correo.attach_alternative(html_content, "text/html")
            correo.send(fail_silently=False)
            
            print(f"📧 EMAIL HTML PREMIUM ENVIADO a {email_destino}")
        else:
            print(f"⚠️ MOTOR: El paciente {mejor_candidato.paciente} no tiene email asociado. Solo se envió notificación web.")

        print("📨 MOTOR: Propuesta y Notificación creadas con éxito.")
    else:
        print("🤷 MOTOR: No hay candidatos aptos.")