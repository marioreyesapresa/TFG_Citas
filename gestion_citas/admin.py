from django.contrib import admin
from django.contrib.auth.models import User
from django import forms 
from django.db import models 
from django.db.models import Q  

from .models import (
    Administrativo, Centro, Cita, Especialidad, 
    HorarioMedico, Medico, Paciente
)

# ================================================================
# 1. CONFIGURACIÓN DE INLINES (Gestión centralizada)
# ================================================================

class HorarioMedicoInline(admin.TabularInline):
    model = HorarioMedico
    extra = 5  # 5 filas para rellenar Lunes a Viernes de golpe
    
    # Forzamos los pasos de 30 minutos (1800 segundos)
    formfield_overrides = {
        models.TimeField: {
            'widget': forms.TimeInput(attrs={'type': 'time', 'step': '1800'})
        },
    }

# ================================================================
# 2. CONFIGURACIÓN DE PERFILES
# ================================================================

class MedicoAdmin(admin.ModelAdmin):
    inlines = [HorarioMedicoInline] # <--- AQUÍ está la magia
    list_display = ('user', 'especialidad', 'centro', 'numero_colegiado')

    # Lógica inteligente para mostrar el usuario correcto en el desplegable
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        field = form.base_fields.get('user')
        if field:
            if obj:
                # Si editamos, mostramos libres + el propio usuario
                field.queryset = User.objects.filter(
                    Q(paciente__isnull=True, medico__isnull=True, administrativo__isnull=True, is_superuser=False) |
                    Q(pk=obj.user.pk)
                )
            else:
                # Si creamos, solo mostramos libres
                field.queryset = User.objects.filter(
                    paciente__isnull=True,
                    medico__isnull=True,
                    administrativo__isnull=True,
                    is_superuser=False
                )
        return form
    
class PacienteAdmin(admin.ModelAdmin):
    list_display = ('user', 'telefono', 'preferencia_turno')

    def formfield_for_foreignkey(self, db_field, request, obj=None, **kwargs):
        if db_field.name == "user":
            kwargs["queryset"] = User.objects.filter(
                paciente__isnull=True,
                medico__isnull=True,
                administrativo__isnull=True,
                is_superuser=False
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class AdministrativoAdmin(admin.ModelAdmin): 
    list_display = ('user', 'centro')

    def formfield_for_foreignkey(self, db_field, request, obj=None, **kwargs):
        if db_field.name == "user":
            kwargs["queryset"] = User.objects.filter(
                paciente__isnull=True,
                medico__isnull=True,
                administrativo__isnull=True,
                is_superuser=False
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# ================================================================
# 3. CONFIGURACIÓN DE CITAS
# ================================================================

class CitaAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'medico', 'fecha', 'hora_inicio', 'estado')
    list_filter = ('estado', 'fecha', 'medico')
    
    formfield_overrides = {
        models.TimeField: {
            'widget': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'step': '1800'})
        },
    }

# ================================================================
# 4. REGISTRO DE MODELOS
# ================================================================

admin.site.register(Medico, MedicoAdmin) 
admin.site.register(Paciente, PacienteAdmin)
admin.site.register(Administrativo, AdministrativoAdmin) 

admin.site.register(Centro)
admin.site.register(Especialidad)
admin.site.register(Cita, CitaAdmin)

# --- LIMPIEZA DEL MENÚ ---
# Hemos eliminado/comentado la línea de abajo porque ya gestionamos 
# los horarios dentro de la ficha del Médico. ¡Más limpio!
# admin.site.register(HorarioMedico) 

# Personalización del título
admin.site.site_header = "Administración de Gestión de Citas Médicas"
admin.site.site_title = "Portal de Citas"
admin.site.index_title = "Panel de Control del Hospital"