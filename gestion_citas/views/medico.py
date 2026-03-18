from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from ..models import Cita, Medico

@login_required
def perfil_medico(request):
    try:
        medico = request.user.medico 
        citas = Cita.objects.filter(medico=medico).order_by('fecha', 'hora_inicio')
        return render(request, 'gestion_citas/medico/perfil_medico.html', {
            'citas': citas,
            'medico': medico 
        })
    except Medico.DoesNotExist:
        return render(request, 'gestion_citas/comun/error_acceso.html', {
            'mensaje': "Acceso denegado. No tienes perfil médico."
        })
