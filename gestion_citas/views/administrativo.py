from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import date
from ..models import Cita, Medico, PropuestaReasignacion, EstadoPropuesta

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
    propuestas_activas = PropuestaReasignacion.objects.filter(
        estado=EstadoPropuesta.PENDIENTE,
        fecha_limite__gt=timezone.now()
    ).order_by('-fecha_creacion')

    return render(request, 'gestion_citas/admin/perfil_administrativo.html', {
        'citas': citas,
        'medicos': medicos,
        'filtro_fecha': fecha_filtro,
        'filtro_medico': int(medico_id) if medico_id else None,
        'propuestas': propuestas_activas
    })
