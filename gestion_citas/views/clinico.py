from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import get_template
from io import BytesIO
from xhtml2pdf import pisa
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
    # Si el usuario es paciente, solo ve las suyas
    if hasattr(request.user, 'paciente'):
        consultas = ConsultaMedica.objects.filter(cita__paciente=request.user.paciente).order_by('-fecha_creacion')
        return render(request, 'gestion_citas/paciente/historial_paciente.html', {'consultas': consultas})
    
    # Si es médico o administrativo, puede ver las de un paciente específico
    elif hasattr(request.user, 'medico') or hasattr(request.user, 'administrativo'):
        consultas = ConsultaMedica.objects.filter(cita__paciente_id=paciente_id).order_by('-fecha_creacion')
        return render(request, 'gestion_citas/clinico/historial_clinico.html', {'consultas': consultas})
    
    return redirect('dashboard')

@login_required
def descargar_informe_pdf(request, consulta_id):
    consulta = get_object_or_404(ConsultaMedica, id=consulta_id)
    
    # Seguridad básica: solo el médico de la cita, el propio paciente o el admin
    es_su_cita = hasattr(request.user, 'paciente') and consulta.cita.paciente == request.user.paciente
    es_su_medico = hasattr(request.user, 'medico') and consulta.cita.medico == request.user.medico
    es_admin = request.user.is_staff or hasattr(request.user, 'administrativo')
    
    if not (es_su_cita or es_su_medico or es_admin):
        messages.error(request, "No tienes permiso para descargar este informe.")
        return redirect('dashboard')

    template = get_template('gestion_citas/clinico/informe_pdf.html')
    html = template.render({'consulta': consulta})
    result = BytesIO()
    
    # Generar el PDF
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        filename = f"informe_{consulta.cita.paciente.user.last_name}_{consulta.id}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    return HttpResponse("Error al generar el informe PDF", status=400)
