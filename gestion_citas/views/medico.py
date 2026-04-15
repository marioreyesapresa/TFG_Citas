from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from ..models import Cita, Medico, EstadoCita

@login_required
def perfil_medico(request):
    try:
        medico = request.user.medico 
        
        # Todas las citas confirmadas/pendientes (Hoy + Futuro)
        citas_pendientes = Cita.objects.filter(
            medico=medico, 
            estado=EstadoCita.CONFIRMADA,
            fecha__gte=timezone.localdate()
        ).select_related('paciente__user').order_by('fecha', 'hora_inicio')
        
        # Historial de citas ya atendidas
        citas_atendidas = Cita.objects.filter(
            medico=medico, 
            estado=EstadoCita.ATENDIDA
        ).select_related('paciente__user', 'consulta_medica').order_by('-fecha', '-hora_inicio')

        return render(request, 'gestion_citas/medico/perfil_medico.html', {
            'citas_pendientes': citas_pendientes,
            'citas_atendidas': citas_atendidas,
            'medico': medico 
        })
    except Medico.DoesNotExist:
        return render(request, 'gestion_citas/comun/error_acceso.html', {
            'mensaje': "Acceso denegado. No tienes perfil médico."
        })
