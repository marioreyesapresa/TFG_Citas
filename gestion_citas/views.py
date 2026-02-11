from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Cita, Medico, Paciente, EstadoCita 
from django.http import JsonResponse
from django.core.exceptions import ValidationError 

# --- CORRECCIÓN IMPORTANTE AQUÍ ---
# Hemos añadido ', date' para que funcione el filtro de hoy
from datetime import datetime, timedelta, date 
from django.db.models import Q 

# ---------------------------------------------------------
# 1. EL CEREBRO: VISTA DE REDIRECCIÓN (Dashboard)
# ---------------------------------------------------------
@login_required
def dashboard_redirect(request):
    user = request.user
    
    # CASO A: Eres el Superusuario (Técnico) -> Vas al Admin de Django
    if user.is_superuser:
        return redirect('/admin/') 
    
    # CASO B: Eres un Administrativo (Recepcionista) -> Vas al Perfil Administrativo
    elif hasattr(user, 'administrativo'):
        return redirect('perfil_administrativo')
    
    # CASO C: Eres Médico
    elif hasattr(user, 'medico'):
        return redirect('perfil_medico')
    
    # CASO D: Eres Paciente
    elif hasattr(user, 'paciente'):
        return redirect('perfil_paciente')
    
    # Error
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
# 3. VISTA PACIENTE: PERFIL (HISTORIAL Y GESTIÓN)
# ---------------------------------------------------------
@login_required
def perfil_paciente(request):
    if not hasattr(request.user, 'paciente'):
        return redirect('dashboard')
    
    citas = Cita.objects.filter(
        paciente=request.user.paciente
    ).order_by('-fecha', '-hora_inicio')

    return render(request, 'gestion_citas/perfil_paciente.html', {'citas': citas})

@login_required
def cancelar_cita(request, cita_id):
    # Seguridad: Solo cancela si la cita es del usuario logueado
    cita = get_object_or_404(Cita, id=cita_id, paciente=request.user.paciente)
    
    if cita.estado != EstadoCita.CANCELADA:
        cita.estado = EstadoCita.CANCELADA
        cita.save()
    
    return redirect('perfil_paciente')

# ---------------------------------------------------------
# 4. VISTA PACIENTE: SOLICITAR CITA
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
                estado='C' # Nacen confirmadas
            )
            nueva_cita.full_clean() 
            nueva_cita.save()
            return render(request, 'gestion_citas/cita_confirmada.html', {'cita': nueva_cita})
            
        except ValidationError as e:
            if hasattr(e, 'message_dict'):
                error_personalizado = e.message_dict.get('__all__', e.messages)[0]
            else:
                error_personalizado = e.messages[0]

    # Carga de datos
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
# 5. AJAX: CARGAR HORAS LIBRES
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

    # Solo bloqueamos citas Pendientes (P) o Confirmadas (C)
    citas_ocupadas = Cita.objects.filter(
        medico=medico, 
        fecha=fecha_obj, 
        estado__in=['P', 'C'] 
    ).values_list('hora_inicio', flat=True)

    citas_ocupadas_limpias = [h.replace(second=0, microsecond=0) for h in citas_ocupadas]
    horas_libres = [h.strftime('%H:%M') for h in horas_posibles if h not in citas_ocupadas_limpias]

    return JsonResponse({'horas': horas_libres})

# ---------------------------------------------------------
# 6. VISTA ADMINISTRATIVO: PERFIL ADMINISTRATIVO
# ---------------------------------------------------------
@login_required
def perfil_administrativo(request):
    # 1. Seguridad
    if not (request.user.is_superuser or hasattr(request.user, 'administrativo')):
        return redirect('dashboard')

    # 2. Filtros
    medico_id = request.GET.get('medico')
    fecha_filtro = request.GET.get('fecha')

    # 3. Consulta base
    citas = Cita.objects.all().order_by('fecha', 'hora_inicio')

    # 4. Aplicar filtros
    if medico_id:
        citas = citas.filter(medico_id=medico_id)
    
    if fecha_filtro:
        citas = citas.filter(fecha=fecha_filtro)
    else:
        # CORRECCIÓN: Usamos date.today() directamente (gracias al import arreglado)
        citas = citas.filter(fecha__gte=date.today())

    medicos = Medico.objects.all()

    context = {
        'citas': citas,
        'medicos': medicos,
        'filtro_fecha': fecha_filtro,
        'filtro_medico': int(medico_id) if medico_id else None
    }
    return render(request, 'gestion_citas/perfil_administrativo.html', context)