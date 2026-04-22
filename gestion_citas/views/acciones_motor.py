from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db import transaction
from ..models import Cita, EstadoCita, PropuestaReasignacion, EstadoPropuesta, Notificacion

@login_required
@require_POST
@transaction.atomic
def aceptar_propuesta(request, propuesta_id):
    if not hasattr(request.user, 'paciente'):
        # Si es admin o médico, redirigimos al dashboard
        return redirect('dashboard')
        
    propuesta = get_object_or_404(PropuestaReasignacion, id=propuesta_id, cita_original__paciente=request.user.paciente)
    if propuesta.estado == EstadoPropuesta.PENDIENTE and propuesta.fecha_limite > timezone.now():
        cita = propuesta.cita_original
        
        # --- REACCIÓN EN CADENA: Detectar Hueco Abandonado ---
        fecha_vieja = cita.fecha
        hora_vieja = cita.hora_inicio
        # El nivel de profundidad hereda del hueco que se ocupa + 1
        nuevo_nivel_cascada = propuesta.hueco.nivel_cascada + 1
        
        # Movemos al paciente al nuevo hueco
        cita.fecha = propuesta.hueco.fecha
        cita.hora_inicio = propuesta.hueco.hora_inicio
        # El paciente 'hereda' el nivel de cascada del hueco al que salta
        cita.nivel_cascada = propuesta.hueco.nivel_cascada 
        cita.save() 
        
        # Marcamos propuesta como aceptada
        propuesta.estado = EstadoPropuesta.ACEPTADA
        propuesta.save()

        # CONSUMO DEL HUECO: El registro 'CANCELADA' del hueco que acabamos de ocupar
        # debe eliminarse para evitar duplicidades en el motor.
        propuesta.hueco.delete()

        # LIBERACIÓN DEL HUECO VIEJO: Generamos un 'Hueco Fantasma' en la posición abandonada
        # para que el motor busque al siguiente candidato (Siguiente nivel de cascada)
        Cita.objects.create(
            paciente=cita.paciente,
            medico=cita.medico,
            especialidad=cita.especialidad,
            centro=cita.centro,
            fecha=fecha_vieja,
            hora_inicio=hora_vieja,
            estado=EstadoCita.CANCELADA, # Marcado como libre
            nivel_cascada=nuevo_nivel_cascada # Incrementamos profundidad basado en la cadena
        )
    return redirect('perfil_paciente')

@login_required
@require_POST
def rechazar_propuesta(request, propuesta_id):
    if not hasattr(request.user, 'paciente'):
        return redirect('dashboard')
        
    propuesta = get_object_or_404(PropuestaReasignacion, id=propuesta_id, cita_original__paciente=request.user.paciente)
    if propuesta.estado == EstadoPropuesta.PENDIENTE:

        propuesta.estado = EstadoPropuesta.RECHAZADA
        propuesta.save()
        
        # EL NÚCLEO DEL TFG: REEVALUACIÓN EN CASCADA
        # Al rechazar, el hueco queda libre. Relanzamos el motor para que elija al siguiente candidato idóneo
        # respetando los pesos globales sin caer en Infinite Loops (gracias a Regla E).
        from ..algoritmo_reasignacion import iniciar_reasignacion
        iniciar_reasignacion(propuesta.hueco)

    return redirect('perfil_paciente')

@login_required
@require_POST
def eliminar_notificacion(request, notificacion_id):
    notificacion = get_object_or_404(Notificacion, id=notificacion_id, paciente=request.user.paciente)
    notificacion.delete()
    return redirect('perfil_paciente')
