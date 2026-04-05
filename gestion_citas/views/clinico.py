from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import Cita, ConsultaMedica, Receta, EstadoCita
from ..forms import ConsultaForm, RecetaFormSet

@login_required
def crear_consulta(request, cita_id):
    # Verificamos que el usuario tiene perfil médico
    if not hasattr(request.user, 'medico'):
        return redirect('dashboard')
    
    cita = get_object_or_404(Cita, id=cita_id, medico=request.user.medico)
    
    # Si ya tiene una consulta asociada, redirigimos a verla (o podemos dar error)
    if hasattr(cita, 'consulta_medica'):
        messages.info(request, "Esta cita ya tiene un registro clínico asociado.")
        return redirect('perfil_medico')

    if request.method == 'POST':
        form = ConsultaForm(request.POST)
        formset = RecetaFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            consulta = form.save(commit=False)
            consulta.cita = cita
            consulta.save()
            
            # Guardamos las recetas del formset
            instances = formset.save(commit=False)
            for instance in instances:
                instance.consulta = consulta
                instance.save()
            
            messages.success(request, "¡Consulta registrada con éxito!")
            return redirect('perfil_medico')
    else:
        form = ConsultaForm()
        formset = RecetaFormSet()

    return render(request, 'gestion_citas/clinico/crear_consulta.html', {
        'form': form,
        'formset': formset,
        'cita': cita
    })

@login_required
def ver_historial_paciente(request, paciente_id=None):
    # Lógica para ver el historial clínico (Epic 4.2)
    # Por ahora, una vista simple que lista consultas
    if hasattr(request.user, 'paciente'):
        consultas = ConsultaMedica.objects.filter(cita__paciente=request.user.paciente).order_by('-fecha_creacion')
        return render(request, 'gestion_citas/clinico/historial_clinico.html', {'consultas': consultas})
    
    elif hasattr(request.user, 'medico'):
        # Si es médico, ve las de un paciente concreto
        consultas = ConsultaMedica.objects.filter(cita__paciente_id=paciente_id).order_by('-fecha_creacion')
        return render(request, 'gestion_citas/clinico/historial_clinico.html', {'consultas': consultas})
    
    return redirect('dashboard')
