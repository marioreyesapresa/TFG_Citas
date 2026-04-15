from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from datetime import datetime, timedelta
import logging

from django.contrib.auth import login
from ..models import Cita, Medico, Paciente, Especialidad, Centro, EstadoCita, PropuestaReasignacion, EstadoPropuesta, Notificacion
from ..forms import PacienteForm
from ..forms.registro import UserRegistrationForm

logger = logging.getLogger(__name__)

@login_required
def perfil_paciente(request):
    if not hasattr(request.user, 'paciente'):
        return redirect('dashboard')
    
    paciente = request.user.paciente
 
    # --- MAGIA UX: Confirmación automática tras Login/Registro ---
    cita_pendiente = request.session.get('cita_pendiente')
    if cita_pendiente:
        try:
            medico = Medico.objects.get(id=cita_pendiente['medico_id'])
            nueva_cita = Cita.objects.create(
                paciente=paciente,
                medico=medico,
                especialidad=medico.especialidad,
                centro=medico.centro,
                fecha=cita_pendiente['fecha'],
                hora_inicio=cita_pendiente['hora'],
                estado=EstadoCita.CONFIRMADA
            )
            messages.success(request, f"¡Hola {request.user.first_name}! Tu sesión se ha iniciado y hemos confirmado la cita que habías seleccionado.")
            return render(request, 'gestion_citas/paciente/cita_confirmada.html', {'cita': nueva_cita})
        except Exception as e:
            logger.error(f"Error al asignar cita pendiente tras login: {e}")
            messages.warning(request, "Tu sesión se ha iniciado, pero no pudimos confirmar automáticamente tu cita seleccionada. Por favor, inténtalo de nuevo desde la búsqueda.")
        finally:
            request.session.pop('cita_pendiente', None)

    # Manejo del Formulario de Ajustes (vía Modal)
    if request.method == 'POST' and 'ajustes_perfil' in request.POST:
        form = PacienteForm(request.POST, instance=paciente)
        if form.is_valid():
            form.save()
            messages.success(request, "¡Perfil actualizado con éxito!")
            return redirect('perfil_paciente')
    else:
        form = PacienteForm(instance=paciente)
    
    citas = Cita.objects.filter(
        paciente=paciente
    ).select_related('medico__user', 'centro', 'consulta_medica').order_by('fecha', 'hora_inicio')

    ahora = timezone.now()
    PropuestaReasignacion.objects.filter(
        estado=EstadoPropuesta.PENDIENTE,
        fecha_limite__lt=ahora
    ).update(estado=EstadoPropuesta.EXPIRADA)

    notificaciones_no_leidas = Notificacion.objects.filter(paciente=paciente, leida=False).order_by('-fecha_creacion')
    notificaciones_no_leidas.update(leida=True)

    propuesta_activa = PropuestaReasignacion.objects.filter(
        cita_original__paciente=paciente,
        estado=EstadoPropuesta.PENDIENTE,
        fecha_limite__gt=ahora
    ).first()

    notificaciones = Notificacion.objects.filter(paciente=paciente).order_by('-fecha_creacion')[:5]

    return render(request, 'gestion_citas/paciente/perfil_paciente.html', {
        'citas': citas,
        'propuesta': propuesta_activa,
        'notificaciones': notificaciones,
        'form': form # Pasamos el formulario para el Modal
    })

def registro_paciente(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            
            # MAGIA UX: ¿Había una cita pendiente en la sesión?
            cita_pendiente = request.session.get('cita_pendiente')
            if cita_pendiente:
                try:
                    medico = Medico.objects.get(id=cita_pendiente['medico_id'])
                    nueva_cita = Cita.objects.create(
                        paciente=user.paciente,
                        medico=medico,
                        especialidad=medico.especialidad,
                        centro=medico.centro,
                        fecha=cita_pendiente['fecha'],
                        hora_inicio=cita_pendiente['hora'],
                        estado=EstadoCita.CONFIRMADA
                    )
                    messages.success(request, f"¡Bienvenido/a {user.first_name}! Tu cuenta ha sido creada y tu cita ha sido confirmada.")
                    return render(request, 'gestion_citas/paciente/cita_confirmada.html', {'cita': nueva_cita})
                except Exception as e:
                    logger.error(f"Error al asignar cita pendiente tras registro: {e}")
                    messages.warning(request, "Tu cuenta ha sido creada, pero no pudimos confirmar automáticamente la cita seleccionada. Por favor, solicítala de nuevo.")
                finally:
                    request.session.pop('cita_pendiente', None)
            
            messages.success(request, f"¡Bienvenido/a {user.first_name}! Tu cuenta ha sido creada con éxito.")
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'gestion_citas/comun/registro.html', {'form': form})

def solicitar_cita(request):
    error_personalizado = None

    if request.method == 'POST':
        medico_id = request.POST.get('medico')
        fecha = request.POST.get('fecha')
        hora = request.POST.get('hora')
        try:
            if not request.user.is_authenticated:
                # MAGIA UX: Guardar en sesión y pedir login/registro
                request.session['cita_pendiente'] = {
                    'medico_id': medico_id,
                    'fecha': fecha,
                    'hora': hora
                }
                messages.info(request, "Para confirmar tu cita, por favor inicia sesión o crea una cuenta.")
                return redirect('login')

            medico = Medico.objects.get(id=medico_id)
            nueva_cita = Cita(
                paciente=request.user.paciente,
                medico=medico,
                especialidad=medico.especialidad,
                centro=medico.centro,
                fecha=fecha,
                hora_inicio=hora,
                estado=EstadoCita.CONFIRMADA
            )
            nueva_cita.full_clean() 
            nueva_cita.save()
            return render(request, 'gestion_citas/paciente/cita_confirmada.html', {'cita': nueva_cita})
        except ValidationError as e:
            if hasattr(e, 'message_dict'):
                error_personalizado = e.message_dict.get('__all__', e.messages)[0]
            else:
                error_personalizado = e.messages[0]
        except Exception as e:
            logger.exception("Error al solicitar cita")
            error_personalizado = "Ha ocurrido un error inesperado al procesar su solicitud. Por favor, inténtelo de nuevo."

    medicos = Medico.objects.all()
    horarios_json = {m.id: list(m.horarios.values_list('dia_semana', flat=True)) for m in medicos}
    
    resumen_horarios = {}
    for m in medicos:
        textos = [f"{h.get_dia_semana_display()}: {h.hora_inicio.strftime('%H:%M')} - {h.hora_fin.strftime('%H:%M')}" 
                 for h in m.horarios.all().order_by('dia_semana')]
        resumen_horarios[m.id] = textos

    return render(request, 'gestion_citas/paciente/solicitar_cita.html', {
        'especialidades': Especialidad.objects.all(),
        'medicos': medicos,
        'horarios_json': horarios_json,
        'resumen_horarios': resumen_horarios,
        'error_personalizado': error_personalizado 
    })

from django.views.decorators.http import require_POST

@login_required
@require_POST
def cancelar_cita(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id, paciente=request.user.paciente)
    if cita.estado != EstadoCita.CANCELADA:
        cita.estado = EstadoCita.CANCELADA
        cita.save()
    return redirect('perfil_paciente')

# Vistas AJAX relacionadas con el paciente/solicitud
def cargar_centros_por_especialidad(request):
    especialidad_id = request.GET.get('especialidad_id')
    if not especialidad_id or especialidad_id == "undefined":
        return JsonResponse({'centros': []})
    centros_ids = Medico.objects.filter(especialidad_id=especialidad_id).values_list('centro_id', flat=True).distinct()
    centros = Centro.objects.filter(id__in=centros_ids)
    resultados = [{'id': c.id, 'nombre': c.nombre} for c in centros]
    return JsonResponse({'centros': resultados})

def cargar_medicos_por_especialidad_y_centro(request):
    especialidad_id = request.GET.get('especialidad_id')
    centro_id = request.GET.get('centro_id')
    if not especialidad_id or not centro_id or especialidad_id == "undefined" or centro_id == "undefined":
        return JsonResponse({'medicos': []})
    medicos = Medico.objects.filter(especialidad_id=especialidad_id, centro_id=centro_id).select_related('user')
    resultados = [{'id': m.id, 'nombre': f"Dr/a. {m.user.first_name} {m.user.last_name}"} for m in medicos]
    return JsonResponse({'medicos': resultados})

def cargar_horas_libres(request):
    medico_id = request.GET.get('medico')
    fecha_str = request.GET.get('fecha')
    if not medico_id or not fecha_str:
        return JsonResponse({'horas': []})
    fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    dia_semana = fecha_obj.weekday()
    medico = Medico.objects.get(id=medico_id)
    horario = medico.horarios.filter(dia_semana=dia_semana).first()
    if not horario:
        return JsonResponse({'horas': []})
    actual_time = horario.hora_inicio.replace(second=0, microsecond=0)
    fin_time = horario.hora_fin.replace(second=0, microsecond=0)
    horas_posibles = []
    actual = datetime.combine(fecha_obj, actual_time)
    fin = datetime.combine(fecha_obj, fin_time)
    while actual < fin:
        horas_posibles.append(actual.time())
        actual += timedelta(minutes=30)
    citas_ocupadas = Cita.objects.filter(medico=medico, fecha=fecha_obj, estado__in=['P', 'C']).values_list('hora_inicio', flat=True)
    citas_ocupadas_limpias = [h.replace(second=0, microsecond=0) for h in citas_ocupadas]
    horas_libres = [h.strftime('%H:%M') for h in horas_posibles if h not in citas_ocupadas_limpias]
    return JsonResponse({'horas': horas_libres})
