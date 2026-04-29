from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # 1. LANDING / LOGIN / LOGOUT
    path('', views.index, name='index'),
    path('login/', auth_views.LoginView.as_view(template_name='gestion_citas/comun/login.html'), name='login'),
    path('registro/', views.registro_paciente, name='registro'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # 2. DASHBOARD (Distribuidor de roles)
    path('dashboard/', views.dashboard_redirect, name='dashboard'),

    # 3. RUTAS DE MÉDICO
    path('perfil-medico/', views.perfil_medico, name='perfil_medico'),

    # 4. RUTAS DE PACIENTE
    path('solicitar-cita/', views.solicitar_cita, name='solicitar_cita'),
    path('perfil-paciente/', views.perfil_paciente, name='perfil_paciente'), 
    path('cancelar-cita/<int:cita_id>/', views.cancelar_cita, name='cancelar_cita'),
    # Rutas para el Motor de Reasignación
    path('propuesta/aceptar/<int:propuesta_id>/', views.aceptar_propuesta, name='aceptar_propuesta'),
    path('propuesta/rechazar/<int:propuesta_id>/', views.rechazar_propuesta, name='rechazar_propuesta'),
   
    # 5. UTILIDADES (AJAX)
    path('ajax/cargar-horas/', views.cargar_horas_libres, name='ajax_cargar_horas'),
    path('ajax/cargar-centros-esp/', views.cargar_centros_por_especialidad, name='ajax_cargar_centros_esp'),
    path('ajax/cargar-medicos-esp-centro/', views.cargar_medicos_por_especialidad_y_centro, name='ajax_cargar_medicos_esp_centro'),
    path('notificacion/eliminar/<int:notificacion_id>/', views.eliminar_notificacion, name='eliminar_notificacion'),

    # 6. RUTA PROPIA DEL ADMINISTRATIVO 
   path('perfil-administrativo/', views.perfil_administrativo, name='perfil_administrativo'),

    # 7. MÓDULO CLÍNICO (EPIC 4)
    path('medico/consulta/<int:cita_id>/', views.crear_consulta, name='crear_consulta'),
    path('paciente/historial/', views.ver_historial_paciente, name='historial_paciente'),
    path('medico/historial/<int:paciente_id>/', views.ver_historial_paciente, name='historial_paciente_medico'),
    path('clinico/descargar-pdf/<int:consulta_id>/', views.descargar_informe_pdf, name='descargar_informe_pdf'),
    path('validar/receta/<uuid:token>/', views.validar_receta_publica, name='validar_receta_publica'),

]