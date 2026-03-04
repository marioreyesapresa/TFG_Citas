from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
# Importamos los modelos necesarios para el motor
from .models import Cita, Medico, Paciente, EstadoCita, PropuestaReasignacion, EstadoPropuesta 
from django.http import JsonResponse
from django.core.exceptions import ValidationError 

from datetime import datetime, timedelta, date 
from django.db.models import Q 
from django.utils import timezone 

# ---------------------------------------------------------
# 1. EL CEREBRO: VISTA DE REDIRECCIÓN (Dashboard)
# ---------------------------------------------------------
@login_required
def dashboard_redirect(request):
    user = request.user
    if user.is_superuser:
        return redirect('/admin/') 
    elif hasattr(user, 'administrativo'):
        return redirect('perfil_administrativo')
    elif hasattr(user, 'medico'):
        return redirect('perfil_medico')
    elif hasattr(user, 'paciente'):
        return redirect('perfil_paciente')
    else:
        return render(request, 'gestion_citas/error_acceso.html', {
            'mensaje': "Tu usuario no tiene un rol asignado."
        })

# ---------------------------------------------------------
# 2. VISTA MÉDICO: VER AGENDA
# ---------------------------------------------------------
@login_required
def perfil_medico(request):
    try:
        medico = request.user.medico 
        citas = Cita.objects.filter(medico=medico).order_by('fecha', 'hora_inicio')
        return render(request, 'gestion_citas/perfil_medico.html', {
            'citas': citas,
            'medico': medico 
        })
    except Medico.DoesNotExist:
        return render(request, 'gestion_citas/error_acceso.html', {
            'mensaje': "Acceso denegado. No tienes perfil médico."
        })

# ---------------------------------------------------------
# 3. VISTA PACIENTE: PERFIL (HISTORIAL Y REASIGNACIÓN)
# ---------------------------------------------------------
@login_required
def perfil_paciente(request):
    if not hasattr(request.user, 'paciente'):
        return redirect('dashboard')
    
    paciente = request.user.paciente
    citas = Cita.objects.filter(
        paciente=paciente
    ).order_by('-fecha', '-hora_inicio')

    # --- LÓGICA DEL MOTOR DE REASIGNACIÓN (R8) ---
    ahora = timezone.now()
    # 1. Caducamos las propuestas que han superado el tiempo límite
    PropuestaReasignacion.objects.filter(
        estado=EstadoPropuesta.PENDIENTE,
        fecha_limite__lt=ahora
    ).update(estado=EstadoPropuesta.EXPIRADA)

    # 2. Buscamos si hay una propuesta pendiente para este paciente
    propuesta_activa = PropuestaReasignacion.objects.filter(
        cita_original__paciente=paciente,
        estado=EstadoPropuesta.PENDIENTE,
        fecha_limite__gt=ahora
    ).first()

    return render(request, 'gestion_citas/perfil_paciente.html', {
        'citas': citas,
        'propuesta': propuesta_activa
    })

@login_required
def cancelar_cita(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id, paciente=request.user.paciente)
    if cita.estado != EstadoCita.CANCELADA:
        cita.estado = EstadoCita.CANCELADA
        cita.save() # Al guardar, el modelo disparará el algoritmo
    return redirect('perfil_paciente')

# ---------------------------------------------------------
# 4. ACCIONES DEL MOTOR (Aceptar / Rechazar)
# ---------------------------------------------------------
@login_required
def aceptar_propuesta(request, propuesta_id):
    propuesta = get_object_or_404(PropuestaReasignacion, id=propuesta_id, cita_original__paciente=request.user.paciente)
    if propuesta.estado == EstadoPropuesta.PENDIENTE and propuesta.fecha_limite > timezone.now():
        cita = propuesta.cita_original
        cita.fecha = propuesta.fecha_oferta
        cita.hora_inicio = propuesta.hora_oferta
        cita.save() 
        propuesta.estado = EstadoPropuesta.ACEPTADA
        propuesta.save()
    return redirect('perfil_paciente')

@login_required
def rechazar_propuesta(request, propuesta_id):
    propuesta = get_object_or_404(PropuestaReasignacion, id=propuesta_id, cita_original__paciente=request.user.paciente)
    if propuesta.estado == EstadoPropuesta.PENDIENTE:
        propuesta.estado = EstadoPropuesta.RECHAZADA
        propuesta.save()
    return redirect('perfil_paciente')

# ---------------------------------------------------------
# 5. VISTA PACIENTE: SOLICITAR CITA (Tu lógica de Calendario intacta)
# ---------------------------------------------------------
@login_required
def solicitar_cita(request):
    error_personalizado = None

    if request.method == 'POST':
        medico_id = request.POST.get('medico')
        fecha = request.POST.get('fecha')
        hora = request.POST.get('hora')
        try:
            nueva_cita = Cita(
                paciente=request.user.paciente,
                medico_id=medico_id,
                fecha=fecha,
                hora_inicio=hora,
                estado='C'
            )
            nueva_cita.full_clean() 
            nueva_cita.save()
            return render(request, 'gestion_citas/cita_confirmada.html', {'cita': nueva_cita})
        except ValidationError as e:
            if hasattr(e, 'message_dict'):
                error_personalizado = e.message_dict.get('__all__', e.messages)[0]
            else:
                error_personalizado = e.messages[0]

    # ESTA ES LA PARTE QUE BLOQUEA DÍAS EN EL CALENDARIO
    medicos = Medico.objects.all()
    horarios_json = {m.id: list(m.horarios.values_list('dia_semana', flat=True)) for m in medicos}
    
    resumen_horarios = {}
    for m in medicos:
        textos = [f"{h.get_dia_semana_display()}: {h.hora_inicio.strftime('%H:%M')} - {h.hora_fin.strftime('%H:%M')}" 
                 for h in m.horarios.all().order_by('dia_semana')]
        resumen_horarios[m.id] = textos

    return render(request, 'gestion_citas/solicitar_cita.html', {
        'medicos': medicos,
        'horarios_json': horarios_json,
        'resumen_horarios': resumen_horarios,
        'error_personalizado': error_personalizado 
    })

# ---------------------------------------------------------
# 6. AJAX: CARGAR HORAS LIBRES
# ---------------------------------------------------------
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

    citas_ocupadas = Cita.objects.filter(
        medico=medico, fecha=fecha_obj, estado__in=['P', 'C'] 
    ).values_list('hora_inicio', flat=True)

    citas_ocupadas_limpias = [h.replace(second=0, microsecond=0) for h in citas_ocupadas]
    horas_libres = [h.strftime('%H:%M') for h in horas_posibles if h not in citas_ocupadas_limpias]

    return JsonResponse({'horas': horas_libres})

# ---------------------------------------------------------
# 7. VISTA ADMINISTRATIVO: PERFIL ADMINISTRATIVO
# ---------------------------------------------------------
@login_required
def perfil_administrativo(request):
    if not (request.user.is_superuser or hasattr(request.user, 'administrativo')):
        return redirect('dashboard')

    medico_id = request.GET.get('medico')
    fecha_filtro = request.GET.get('fecha')
    citas = Cita.objects.all().order_by('fecha', 'hora_inicio')

    if medico_id:
        citas = citas.filter(medico_id=medico_id)
    if fecha_filtro:
        citas = citas.filter(fecha=fecha_filtro)
    else:
        citas = citas.filter(fecha__gte=date.today())

    medicos = Medico.objects.all()
    return render(request, 'gestion_citas/perfil_administrativo.html', {
        'citas': citas,
        'medicos': medicos,
        'filtro_fecha': fecha_filtro,
        'filtro_medico': int(medico_id) if medico_id else None
    })