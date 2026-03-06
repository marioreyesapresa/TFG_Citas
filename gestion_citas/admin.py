from django.contrib import admin
from django.contrib.auth.models import User
from django import forms 
from django.db import models 
from django.db.models import Q  
import json
from django.utils.html import format_html 
from django.utils.safestring import mark_safe 

from .models import (
    Administrativo, Centro, Cita, Especialidad, 
    HorarioMedico, Medico, Paciente, PropuestaReasignacion, GestionHorario,
    Notificacion, ConfiguracionReasignacion
)

# ================================================================
# 1. CONFIGURACIÓN DE PERFILES
# ================================================================

class MedicoAdmin(admin.ModelAdmin):
    # El médico normal ya NO tiene horarios aquí. Pantalla súper limpia.
    list_display = ('user', 'especialidad', 'centro', 'numero_colegiado')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        field = form.base_fields.get('user')
        if field:
            if obj:
                field.queryset = User.objects.filter(
                    Q(paciente__isnull=True, medico__isnull=True, administrativo__isnull=True, is_superuser=False) |
                    Q(pk=obj.user.pk)
                )
            else:
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
                paciente__isnull=True, medico__isnull=True, administrativo__isnull=True, is_superuser=False
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class AdministrativoAdmin(admin.ModelAdmin): 
    list_display = ('user', 'centro')

    def formfield_for_foreignkey(self, db_field, request, obj=None, **kwargs):
        if db_field.name == "user":
            kwargs["queryset"] = User.objects.filter(
                paciente__isnull=True, medico__isnull=True, administrativo__isnull=True, is_superuser=False
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# ================================================================
# 2. EL MENÚ EXCLUSIVO DE HORARIOS (Tú idea hecha realidad)
# ================================================================

class HorarioMedicoInline(admin.TabularInline):
    model = HorarioMedico
    extra = 0 # Sin filas fantasma
    fields = ('dia_semana', 'hora_inicio', 'hora_fin')
    ordering = ('dia_semana',)
class GestionHorarioAdmin(admin.ModelAdmin):
    list_display = ('medico_info', 'horario_semanal')
    search_fields = ('user__last_name', 'user__first_name', 'especialidad__nombre')
    
    # Aquí cargamos el "creador de horarios"
    inlines = [HorarioMedicoInline]
    
    # OCULTAMOS TODOS LOS DATOS DEL MÉDICO. ¡Pantalla 100% enfocada en horarios!
    exclude = ('user', 'especialidad', 'centro', 'numero_colegiado')
    
    def has_add_permission(self, request):
        return False

    # --- DISEÑO VISUAL DE LA TABLA (Se mantiene la vista bonita) ---
    @admin.display(description='Médico Profesional')
    def medico_info(self, obj):
        return format_html(
            "<b>Dr/a. {}</b><br><span style='color:gray;'>{}</span>", 
            obj.user.last_name, 
            obj.especialidad
        )

    @admin.display(description='Días y Horas de Trabajo')
    def horario_semanal(self, obj):
        horarios = obj.horarios.all().order_by('dia_semana')
        if not horarios:
            return mark_safe('<span style="color: #e74c3c; font-weight: bold; padding: 5px; background: #fadbd8; border-radius: 5px;">Sin horario asignado</span>')
        
        html = '<ul style="margin: 0; padding-left: 20px; color: #2c3e50;">'
        for h in horarios:
            inicio = h.hora_inicio.strftime('%H:%M')
            fin = h.hora_fin.strftime('%H:%M')
            html += f'<li><b>{h.get_dia_semana_display()}:</b> {inicio} - {fin}</li>'
        html += '</ul>'
        
        return mark_safe(html)
# ================================================================
# 3. CONFIGURACIÓN DE CITAS Y PROPUESTAS
# ================================================================

class CitaAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'medico', 'fecha', 'hora_inicio', 'urgencia', 'estado')
    list_filter = ('estado', 'fecha', 'medico')
    
    # FORZAR ORDEN LÓGICO DEL FORMULARIO
    fields = ('paciente', 'especialidad', 'centro', 'medico', 'fecha', 'hora_inicio', 'urgencia', 'estado')
    
    formfield_overrides = {
        models.TimeField: {'widget': forms.TimeInput(format='%H:%M', attrs={'type': 'time', 'step': '1800'})},
    }

    change_form_template = 'admin/gestion_citas/cita/change_form.html'
    
    # La lógica ahora vive inline en el template change_form.html
    # class Media:
    #     js = ('admin/js/citas_admin_v4.js',)
    
    def get_horarios_json(self):
        medicos = Medico.objects.all()
        return {m.id: list(m.horarios.values_list('dia_semana', flat=True)) for m in medicos}

    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['horarios_json'] = self.get_horarios_json()
        return super().add_view(request, form_url, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['horarios_json'] = self.get_horarios_json()
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

class PropuestaAdmin(admin.ModelAdmin):
    list_display = ('cita_original', 'get_fecha', 'get_hora', 'estado')
    list_filter = ('estado', 'hueco__fecha')

    @admin.display(description='Fecha Oferta')
    def get_fecha(self, obj):
        return obj.hueco.fecha if obj.hueco else '-'

    @admin.display(description='Hora Oferta')
    def get_hora(self, obj):
        return obj.hueco.hora_inicio if obj.hueco else '-'

# ================================================================
# 4. REGISTRO DE MODELOS
# ================================================================

admin.site.register(Medico, MedicoAdmin) 
admin.site.register(Paciente, PacienteAdmin)
admin.site.register(Administrativo, AdministrativoAdmin) 

admin.site.register(Centro)
admin.site.register(Especialidad)
admin.site.register(Cita, CitaAdmin)
admin.site.register(PropuestaReasignacion, PropuestaAdmin) 
admin.site.register(Notificacion)
admin.site.register(ConfiguracionReasignacion)

# ¡AQUÍ REGISTRAMOS TU NUEVO MENÚ VISUAL DE HORARIOS!
admin.site.register(GestionHorario, GestionHorarioAdmin)

admin.site.site_header = "Administración de Gestión de Citas Médicas"
admin.site.site_title = "Portal de Citas"
admin.site.index_title = "Panel de Control del Hospital"