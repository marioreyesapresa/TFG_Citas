import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from .models import Cita, EstadoCita, PropuestaReasignacion, Turno, EstadoPropuesta, ConfiguracionReasignacion, Notificacion

logger = logging.getLogger(__name__)

def _mask_email(email):
    """Enmascara un email para propósitos de logging."""
    if not email:
        return ""
    try:
        local, domain = email.split("@", 1)
    except ValueError:
        return "***"
    masked_local = local[0] + "***" + local[-1] if len(local) > 2 else "*" * len(local)
    return f"{masked_local}@{domain}"

# Tiempo límite para responder a una propuesta (horas)
HORAS_TTL = 24 

def determinar_turno(hora):
    """Determina si una hora pertenece al turno de mañana o tarde."""
    if hora.hour < 15:
        return Turno.MANANA
    return Turno.TARDE

def iniciar_reasignacion(cita_cancelada):
    """
    Inicia el proceso de reasignación inteligente para un hueco liberado.
    Evalúa candidatos mediante un algoritmo de scoring paramétrico.
    """
    logger.info(f"Iniciando motor de reasignación para hueco: {cita_cancelada.fecha} {cita_cancelada.hora_inicio}")

    # Control de profundidad de cascada (Circuit Breaker)
    if cita_cancelada.nivel_cascada >= 5:
        logger.warning(f"Límite de cascada alcanzado para hueco {cita_cancelada.id}. Abortando reevaluación.")
        return

    # Cargar configuración de pesos
    config = ConfiguracionReasignacion.objects.first()
    if not config:
        peso_urgencia = 15.0
        peso_turno = 10.0
        peso_antiguedad = 0.1
    else:
        peso_urgencia = config.peso_urgencia
        peso_turno = config.prioridad_turno
        peso_antiguedad = config.peso_antiguedad

    # Evitar procesar huecos pasados
    if cita_cancelada.fecha < datetime.today().date():
        return

    medico = cita_cancelada.medico
    fecha_hueco = cita_cancelada.fecha
    hora_hueco = cita_cancelada.hora_inicio
    turno_hueco = determinar_turno(hora_hueco)

    # Buscar candidatos potenciales (pacientes con citas futuras con el mismo médico)
    candidatos = Cita.objects.filter(
        medico=medico,
        fecha__gt=fecha_hueco, 
        estado__in=[EstadoCita.PENDIENTE, EstadoCita.CONFIRMADA]
    ).select_related('paciente')

    mejor_candidato = None
    mejor_puntuacion = -1000 

    # Evaluación de candidatos
    for candidato in candidatos:
        puntuacion = 0
        paciente = candidato.paciente
        
        # Criterio A: Preferencia de Turno
        if paciente.preferencia_turno == turno_hueco:
            puntuacion += peso_turno
        else:
            puntuacion -= (peso_turno / 2)

        # Criterio B: Urgencia Médica
        puntuacion += (candidato.urgencia * peso_urgencia)

        # Criterio C: Antigüedad de la cita original (distancia temporal)
        dias_diferencia = (candidato.fecha - fecha_hueco).days
        puntuacion += (dias_diferencia * peso_antiguedad) 

        # Restricción: No asignar si ya tiene otra cita el mismo día
        tiene_cita_ese_dia = Cita.objects.filter(
            paciente=paciente, 
            fecha=fecha_hueco
        ).exclude(estado=EstadoCita.CANCELADA).exists()

        if tiene_cita_ese_dia:
            continue

        # Restricción: No repetir ofertas para el mismo hueco
        ya_se_le_ofrecio_este_hueco = PropuestaReasignacion.objects.filter(
            paciente=paciente,
            hueco=cita_cancelada
        ).exists()

        if ya_se_le_ofrecio_este_hueco:
            continue

        # Restricción: Un paciente solo puede tener una propuesta activa
        ya_tiene_propuesta_activa = PropuestaReasignacion.objects.filter(
            paciente=paciente,
            estado=EstadoPropuesta.PENDIENTE
        ).exists()

        if ya_tiene_propuesta_activa:
            continue

        # Selección del mejor candidato basado en el score calculado
        if puntuacion > mejor_puntuacion:
            mejor_puntuacion = puntuacion
            mejor_candidato = candidato

    # Ejecución de la propuesta
    if mejor_candidato:
        propuesta = PropuestaReasignacion.objects.create(
            cita_original=mejor_candidato,
            paciente=mejor_candidato.paciente,
            hueco=cita_cancelada,
            fecha_limite=timezone.now() + timedelta(hours=HORAS_TTL)
        )
        
        # BLOQUEO DE HUECO (Evita que otros pacientes se "cuelen" mientras el candidato decide)
        cita_cancelada.estado = EstadoCita.EN_ESPERA
        cita_cancelada.save()
        
        # Opcional: Podrías querer marcar la cita_original como PENDIENTE de cambio
        # Pero según tu petición, simplemente las nuevas propuestas son las que gestionan el flujo.

        # CREAR NOTIFICACIÓN PERSISTENTE (Novedad V25)
        mensaje_notificacion = f"¡Buenas noticias! Se ha liberado un hueco con el Dr/a. {medico.user.last_name} para el día {fecha_hueco.strftime('%d/%m/%Y')} a las {hora_hueco.strftime('%H:%M')}. ¿Quieres adelantar tu cita?"

        Notificacion.objects.create(
            paciente=mejor_candidato.paciente,
            propuesta=propuesta,
            mensaje=mensaje_notificacion
        )
        
        # Envío de notificación por correo electrónico
        email_destino = mejor_candidato.paciente.user.email
        if email_destino:
            dominio = getattr(settings, "SITE_BASE_URL", "http://127.0.0.1:8000")
            
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
            text_content = f"Hola {mejor_candidato.paciente.user.first_name},\n\n{mensaje_notificacion}\n\nAcceda a {dominio} para gestionarla."
            
            correo = EmailMultiAlternatives(
                subject='Nueva propuesta de adelanto de cita disponible',
                body=text_content,
                from_email='noreply@tfg-citas.com',
                to=[email_destino]
            )
            correo.attach_alternative(html_content, "text/html")
            
            try:
                correo.send(fail_silently=False)
                logger.info(f"Email de propuesta enviado a {_mask_email(email_destino)}")
            except Exception as e:
                logger.error(f"Error al enviar email a {_mask_email(email_destino)}: {e}")
        
        logger.info(f"Propuesta generada con éxito para el paciente {mejor_candidato.paciente.id}")
    else:
        logger.info("No se han encontrado candidatos aptos para el hueco libre.")