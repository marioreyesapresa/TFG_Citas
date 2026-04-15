from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'gestion_citas/comun/index.html')

@login_required
def dashboard_redirect(request):
    user = request.user
    if user.is_superuser or hasattr(user, 'administrativo'):
        return redirect('perfil_administrativo')
    elif hasattr(user, 'medico'):
        return redirect('perfil_medico')
    elif hasattr(user, 'paciente'):
        return redirect('perfil_paciente')
    else:
        return render(request, 'gestion_citas/comun/error_acceso.html', {
            'mensaje': "Tu usuario no tiene un rol asignado."
        })
