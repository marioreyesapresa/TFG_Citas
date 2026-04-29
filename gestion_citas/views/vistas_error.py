from django.shortcuts import render

def mi_error_csrf(request, reason=""):
    """
    Vista personalizada para manejar fallos de validación CSRF.
    Común cuando se intenta iniciar sesión en múltiples pestañas con distintos usuarios.
    """
    return render(request, 'gestion_citas/comun/csrf_error.html', status=403)
