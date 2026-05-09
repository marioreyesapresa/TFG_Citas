from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db import transaction
from django.contrib.auth import logout
from ..models import Cita, EstadoCita, PropuestaReasignacion, EstadoPropuesta, Notificacion

@login_required
@transaction.atomic
def aceptar_propuesta(request, token):
    """
    Gestiona la aceptación de una propuesta de adelanto de cita mediante token UUID.
    """
    if not hasattr(request.user, 'paciente'):
        return redirect('dashboard')
        
    # Buscamos la propuesta por token único para validar la arquitectura One-Click
    propuesta = PropuestaReasignacion.objects.filter(token_respuesta=token).first()
    
    if not propuesta:
        return redirect('dashboard')

    # SEGURIDAD INTELIGENTE: Si el usuario logueado no es el dueño de la propuesta
    if propuesta.paciente.user != request.user:
        logout(request)
        return redirect(f'/login/?next={request.path}')
    if propuesta.estado == EstadoPropuesta.PENDIENTE and propuesta.fecha_limite > timezone.now():
        cita = propuesta.cita_original
        
        # Guardamos los datos de la cita actual que va a ser liberada
        fecha_vieja = cita.fecha
        hora_vieja = cita.hora_inicio
        nuevo_nivel_cascada = propuesta.hueco.nivel_cascada + 1
        
        # Actualizamos la cita del paciente con el nuevo hueco
        cita.fecha = propuesta.hueco.fecha
        cita.hora_inicio = propuesta.hueco.hora_inicio
        cita.nivel_cascada = propuesta.hueco.nivel_cascada 
        cita.save() 
        
        propuesta.estado = EstadoPropuesta.ACEPTADA
        propuesta.save()

        # CONSUMO DEL HUECO
        propuesta.hueco.delete()

        # LIBERACIÓN DEL HUECO VIEJO: Efecto Cascada
        Cita.objects.create(
            paciente=cita.paciente,
            medico=cita.medico,
            especialidad=cita.especialidad,
            centro=cita.centro,
            fecha=fecha_vieja,
            hora_inicio=hora_vieja,
            estado=EstadoCita.CANCELADA,
            nivel_cascada=nuevo_nivel_cascada
        )
        
    return redirect('perfil_paciente')

@login_required
def rechazar_propuesta(request, token):
    """
    Gestiona el rechazo de una propuesta de adelanto mediante token UUID.
    """
    if not hasattr(request.user, 'paciente'):
        return redirect('dashboard')

    propuesta = PropuestaReasignacion.objects.filter(token_respuesta=token).first()
    
    if not propuesta:
        return redirect('dashboard')

    # SEGURIDAD INTELIGENTE
    if propuesta.paciente.user != request.user:
        logout(request)
        return redirect(f'/login/?next={request.path}')
    if propuesta.estado == EstadoPropuesta.PENDIENTE:
        propuesta.estado = EstadoPropuesta.RECHAZADA
        propuesta.save()
        
        # REEVALUACIÓN EN CASCADA (Liberamos el hueco 'R' a 'X' para que el motor busque al siguiente)
        if propuesta.hueco:
            propuesta.hueco.estado = EstadoCita.CANCELADA
            propuesta.hueco.save()
            from ..algoritmo_reasignacion import iniciar_reasignacion
            iniciar_reasignacion(propuesta.hueco)

    return redirect('perfil_paciente')

@login_required
@require_POST
def eliminar_notificacion(request, notificacion_id):
    """
    Elimina una notificación del panel del paciente.
    """
    notificacion = get_object_or_404(Notificacion, id=notificacion_id, paciente=request.user.paciente)
    notificacion.delete()
    return redirect('perfil_paciente')
