from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.http import require_POST
from ..models import PropuestaReasignacion, EstadoPropuesta, Notificacion

@login_required
def aceptar_propuesta(request, propuesta_id):
    if not hasattr(request.user, 'paciente'):
        # Si es admin o médico, redirigimos al dashboard
        return redirect('dashboard')
        
    propuesta = get_object_or_404(PropuestaReasignacion, id=propuesta_id, cita_original__paciente=request.user.paciente)
    if propuesta.estado == EstadoPropuesta.PENDIENTE and propuesta.fecha_limite > timezone.now():
        cita = propuesta.cita_original
        cita.fecha = propuesta.hueco.fecha
        cita.hora_inicio = propuesta.hueco.hora_inicio
        cita.save() 
        propuesta.estado = EstadoPropuesta.ACEPTADA
        propuesta.save()
    return redirect('perfil_paciente')

@login_required
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
