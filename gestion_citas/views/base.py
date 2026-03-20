from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

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
        return render(request, 'gestion_citas/comun/error_acceso.html', {
            'mensaje': "Tu usuario no tiene un rol asignado."
        })
