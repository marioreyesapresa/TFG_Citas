from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db import transaction
from django.contrib.auth import logout
from ..models import Cita, EstadoCita, PropuestaReasignacion, EstadoPropuesta, Notificacion

from django.contrib.auth import logout

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
        from django.contrib import messages
        messages.error(request, "Lo sentimos, este enlace de adelanto ya no es válido o la propuesta ha expirado.")
        return redirect('dashboard')

    # SEGURIDAD INTELIGENTE: Si el usuario logueado no es el dueño de la propuesta
    if propuesta.paciente.user != request.user:
        from django.contrib import messages
        messages.warning(request, f"Lo sentimos, esta propuesta pertenece a otro paciente. Has sido desconectado automáticamente para que puedas entrar con la cuenta correcta.")
        logout(request)
        return redirect(f'/login/?next={request.path}')
    if propuesta.estado == EstadoPropuesta.PENDIENTE and propuesta.fecha_limite > timezone.now():
        cita = propuesta.cita_original
        
        # Guardamos los datos de la cita actual que va a ser liberada
        fecha_vieja = cita.fecha
        # 1. Guardamos los datos del hueco (destino) antes de borrarlo
        nueva_fecha = propuesta.hueco.fecha
        nueva_hora = propuesta.hueco.hora_inicio
        nuevo_nivel = propuesta.hueco.nivel_cascada
        
        # 2. Guardamos los datos de la cita actual (que quedará libre)
        fecha_vieja = cita.fecha
        hora_vieja = cita.hora_inicio
        nivel_vieja_mejorado = nuevo_nivel + 1

        # 3. Marcamos la propuesta como aceptada
        hueco_a_borrar = propuesta.hueco
        propuesta.estado = EstadoPropuesta.ACEPTADA
        propuesta.save()

        # 4. Movemos la cita del paciente (Usamos .update() para que el cambio sea instantáneo en la BD)
        # IMPORTANTE: Hacemos esto ANTES de borrar el hueco físico. Así, cuando el motor se dispare
        # por el borrado del hueco, ya verá al paciente ocupando este horario y no le mandará duplicados.
        Cita.objects.filter(id=cita.id).update(
            fecha=nueva_fecha,
            hora_inicio=nueva_hora,
            nivel_cascada=nuevo_nivel
        )

        # 5. CONSUMO DEL HUECO (Liberamos el espacio físico para evitar conflictos de validación)
        hueco_a_borrar.delete()

        # 6. LIMPIEZA: Marcamos el resto de propuestas pendientes como rechazadas para que desaparezcan
        PropuestaReasignacion.objects.filter(
            paciente=cita.paciente, 
            estado=EstadoPropuesta.PENDIENTE
        ).exclude(id=propuesta.id).update(estado=EstadoPropuesta.RECHAZADA)

        # 5. LIBERACIÓN DEL HUECO VIEJO: Efecto Cascada (Sin paciente vinculado para evitar confusión)
        hueco_fantasma = Cita.objects.create(
            paciente=None, 
            medico=cita.medico,
            especialidad=cita.especialidad,
            centro=cita.centro,
            fecha=fecha_vieja,
            hora_inicio=hora_vieja,
            estado=EstadoCita.CANCELADA,
            nivel_cascada=nivel_vieja_mejorado
        )

        # 6. DISPARO MANUAL DE LA CASCADA: Nos aseguramos de que el motor busque al siguiente
        from ..algoritmo_reasignacion import iniciar_reasignacion
        iniciar_reasignacion(hueco_fantasma)
        
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
