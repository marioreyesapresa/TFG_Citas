from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime
import uuid
from datetime import timedelta

DURACION_CITA = 30

# ==========================================
# 1. ENUMERACIONES 
# ==========================================
class RolUsuario(models.TextChoices):
    PACIENTE = 'PACIENTE', 'Paciente'
    MEDICO = 'MEDICO', 'Médico'
    ADMINISTRATIVO = 'ADMINISTRATIVO', 'Administrativo'

class Turno(models.TextChoices):
    MANANA = 'M', 'Mañana'
    TARDE = 'T', 'Tarde'

class NivelUrgencia(models.IntegerChoices):
    ALTA = 3, 'Alta'
    MEDIA = 2, 'Media'
    BAJA = 1, 'Baja'

# ==========================================
# 2. ENTIDADES PRINCIPALES
# ==========================================
class Centro(models.Model):
    nombre = models.CharField(max_length=100)
    
    def __str__(self):
        return self.nombre
    
class Especialidad(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name_plural = "Especialidades"

# ==========================================
# 3. PERFILES DE USUARIO 
# ==========================================
class Paciente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='paciente')
    dni = models.CharField(max_length=9, unique=True, null=True, blank=True)
    telefono = models.CharField(max_length=15)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    preferencia_turno = models.CharField(
        max_length=1, 
        choices=Turno.choices, 
        default=Turno.MANANA
    )

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"


class Medico(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='medico')
    numero_colegiado = models.CharField(max_length=20)
    especialidad = models.ForeignKey(Especialidad, on_delete=models.CASCADE)
    centro = models.ForeignKey(Centro, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Dr/a. {self.user.last_name} ({self.especialidad})"

class Administrativo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='administrativo')
    centro = models.ForeignKey(Centro, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Admin: {self.user.first_name} {self.user.last_name} ({self.centro})"

# ==========================================
# 4. DISPONIBILIDAD 
# ==========================================
class HorarioMedico(models.Model):
    DIAS_SEMANA = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name='horarios')
    dia_semana = models.IntegerField(choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    class Meta:
        unique_together = ('medico', 'dia_semana', 'hora_inicio') 

    def clean(self):
        if not self.hora_inicio or not self.hora_fin:
            return

        if self.hora_inicio.minute not in [0, 30]:
            raise ValidationError({'hora_inicio': "La hora de inicio debe ser exacta (ej: 09:00 o 09:30)."})
        if self.hora_fin.minute not in [0, 30]:
            raise ValidationError({'hora_fin': "La hora de fin debe ser exacta (ej: 14:00 o 14:30)."})
        
        if self.hora_inicio >= self.hora_fin:
            raise ValidationError("La hora de inicio debe ser anterior a la de fin.")

    def __str__(self):
        inicio = self.hora_inicio.strftime('%H:%M') if self.hora_inicio else "??"
        fin = self.hora_fin.strftime('%H:%M') if self.hora_fin else "??"
        return f"{self.medico} - {self.get_dia_semana_display()} ({inicio}-{fin})"

# ==========================================
# 5. GESTIÓN DE CITAS 
# ==========================================
class EstadoCita(models.TextChoices):
    PENDIENTE = 'P', 'Pendiente'
    CONFIRMADA = 'C', 'Confirmada'
    CANCELADA = 'X', 'Cancelada'
    EN_ESPERA = 'R', 'En espera de reasignación'
    ATENDIDA = 'A', 'Atendida'

class Cita(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='citas', null=True, blank=True)
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name='citas')
    especialidad = models.ForeignKey(Especialidad, on_delete=models.CASCADE, null=True, blank=True)
    centro = models.ForeignKey(Centro, on_delete=models.CASCADE, null=True, blank=True)
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    urgencia = models.IntegerField(
        choices=NivelUrgencia.choices, 
        default=NivelUrgencia.BAJA
    )
    estado = models.CharField(
        max_length=1, 
        choices=EstadoCita.choices, 
        default=EstadoCita.CONFIRMADA
    )
    nivel_cascada = models.IntegerField(
        default=0,
        help_text="Control de profundidad de la reasignación automática."
    )

    class Meta:
        ordering = ['fecha', 'hora_inicio']

    def __str__(self):
        return f"Cita: {self.paciente} con {self.medico} el {self.fecha}"
    
    def clean(self):
        # Validación de futuro: Solo se pueden solicitar citas a partir de mañana (R26)
        # Usamos localdate() para que coincida con la fecha actual en España
        hoy = timezone.localdate()
        if not self.id and self.estado != EstadoCita.CANCELADA: 
            if self.fecha <= hoy:
                raise ValidationError("Para una mejor gestión, las nuevas citas deben solicitarse al menos con un día de antelación. Los huecos de hoy están reservados para reasignaciones urgentes.")

        if self.medico and self.especialidad:
            if self.medico.especialidad != self.especialidad:
                raise ValidationError({
                    'medico': f"Error de coherencia: El médico seleccionado no pertenece a la especialidad {self.especialidad}."
                })
        
        if self.medico and self.centro:
            if self.medico.centro != self.centro:
                raise ValidationError({
                    'medico': f"Error de ubicación: El médico seleccionado no trabaja en el centro {self.centro}."
                })
      
        if not self.fecha or not self.hora_inicio or not self.medico:
            return

        dia_semana_cita = self.fecha.weekday() 
        horario = HorarioMedico.objects.filter(
            medico=self.medico,              
            dia_semana=dia_semana_cita,      
        ).first()

        if not horario:
            raise ValidationError(f"El médico seleccionado no trabaja el día {self.fecha.strftime('%d/%m/%Y')}.")
        
        if not (horario.hora_inicio <= self.hora_inicio < horario.hora_fin):
             raise ValidationError(f"La hora debe estar dentro de la jornada laboral ({horario.hora_inicio.strftime('%H:%M')} - {horario.hora_fin.strftime('%H:%M')}).")

        minutos_inicio_medico = horario.hora_inicio.hour * 60 + horario.hora_inicio.minute
        minutos_cita = self.hora_inicio.hour * 60 + self.hora_inicio.minute
        diferencia = minutos_cita - minutos_inicio_medico
        
        if diferencia % DURACION_CITA != 0:
            raise ValidationError(f"Las citas deben respetar los intervalos de {DURACION_CITA} minutos.")

        # Validación de solapamientos (Ignoramos canceladas y en espera de reasignación)
        cita_medico_ocupada = Cita.objects.filter(
            medico=self.medico,
            fecha=self.fecha,
            hora_inicio=self.hora_inicio
        ).exclude(id=self.id).exclude(estado__in=[EstadoCita.CANCELADA, EstadoCita.EN_ESPERA]).exists()

        if cita_medico_ocupada:
            raise ValidationError("El médico ya tiene una cita asignada en este horario.")

        cita_paciente_ocupada = Cita.objects.filter(
            paciente=self.paciente,
            fecha=self.fecha,
            hora_inicio=self.hora_inicio
        ).exclude(id=self.id).exclude(estado__in=[EstadoCita.CANCELADA, EstadoCita.EN_ESPERA]).exists()

        if cita_paciente_ocupada:
            raise ValidationError("El paciente ya tiene una cita programada en este horario.")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        activar_motor = False
        
        if not self.pk and self.estado == EstadoCita.CANCELADA:
            activar_motor = True
        elif self.pk: 
            cita_anterior = Cita.objects.get(pk=self.pk)
            if cita_anterior.estado != EstadoCita.CANCELADA and self.estado == EstadoCita.CANCELADA:
                activar_motor = True

        super().save(*args, **kwargs)

        if activar_motor:
            from .algoritmo_reasignacion import iniciar_reasignacion 
            iniciar_reasignacion(self)

# ==========================================
# 6. GESTIÓN ADMINISTRATIVA
# ==========================================
class GestionHorario(Medico):
    class Meta:
        proxy = True
        verbose_name = "Gestión de Horario"
        verbose_name_plural = "Gestión de Horarios"

# ==========================================
# 7. MOTOR DE REASIGNACIÓN
# ==========================================
class EstadoPropuesta(models.TextChoices):
    PENDIENTE = 'PENDIENTE', 'Pendiente de respuesta'
    ACEPTADA = 'ACEPTADA', 'Aceptada por el paciente'
    RECHAZADA = 'RECHAZADA', 'Rechazada por el paciente'
    EXPIRADA = 'EXPIRADA', 'Tiempo límite agotado'

class PropuestaReasignacion(models.Model):
    cita_original = models.ForeignKey(Cita, on_delete=models.CASCADE, related_name='propuestas')
    hueco = models.ForeignKey(Cita, on_delete=models.SET_NULL, related_name='es_propuesta_de', null=True, blank=True)
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='propuestas_recibidas', null=True, blank=True)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_limite = models.DateTimeField(help_text="Fecha límite para la validez de la oferta.")
    
    estado = models.CharField(
        max_length=20, 
        choices=EstadoPropuesta.choices, 
        default=EstadoPropuesta.PENDIENTE
    )
    
    token_respuesta = models.UUIDField(
        default=uuid.uuid4, 
        editable=False, 
        unique=True,
        help_text="Token único para la validación de la arquitectura One-Click."
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['hueco'],
                condition=Q(estado='PENDIENTE'),
                name='unique_pending_propuesta_per_hueco',
            ),
        ]

    def __str__(self):
        fecha = self.hueco.fecha if self.hueco else '??'
        hora = self.hueco.hora_inicio if self.hueco else '??'
        return f"Propuesta para {self.paciente}: {fecha} a las {hora}"

class Notificacion(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='notificaciones')
    propuesta = models.ForeignKey(PropuestaReasignacion, on_delete=models.CASCADE, null=True, blank=True)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notificación para {self.paciente}: {'Leída' if self.leida else 'No leída'}"

class ConfiguracionReasignacion(models.Model):
    peso_urgencia = models.FloatField(default=15.0)
    peso_antiguedad = models.FloatField(default=0.1)
    prioridad_turno = models.FloatField(default=10.0)

    class Meta:
        verbose_name = "Configuración de Reasignación"
        verbose_name_plural = "Configuraciones de Reasignación"

    def clean(self):
        if not self.pk and ConfiguracionReasignacion.objects.exists():
            raise ValidationError("Solo puede existir una configuración activa.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return "Configuración Global del Motor"

# ==========================================
# 8. MÓDULO CLÍNICO
# ==========================================
class ConsultaMedica(models.Model):
    cita = models.OneToOneField(Cita, on_delete=models.CASCADE, related_name='consulta_medica')
    motivo_consulta = models.CharField(max_length=255)
    
    antecedentes_alergias = models.TextField(blank=True, null=True)
    descripcion_problema = models.TextField(blank=True, null=True)
    exploracion_medica = models.TextField(blank=True, null=True)
    pruebas_solicitadas = models.TextField(blank=True, null=True)
    
    diagnostico_principal = models.TextField(blank=True, null=True)
    tratamiento_pautas = models.TextField(blank=True, null=True)
    
    token_verificacion = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    observaciones = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Consulta: {self.motivo_consulta} ({self.cita.paciente})"

    def save(self, *args, **kwargs):
        if not self.token_verificacion:
            self.token_verificacion = uuid.uuid4()
        super().save(*args, **kwargs)

class Receta(models.Model):
    consulta = models.ForeignKey(ConsultaMedica, on_delete=models.CASCADE, related_name='recetas')
    medicamento = models.CharField(max_length=255)
    posologia = models.CharField(max_length=255)
    duracion = models.CharField(max_length=255)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.medicamento} - {self.posologia}"

# ==========================================
# 9. GESTIÓN AUTOMATIZADA
# ==========================================
from django.db.models.signals import post_delete
from django.dispatch import receiver

@receiver(post_delete, sender=Cita)
def procesar_borrado_cita(sender, instance, **kwargs):
    """
    Gestiona la liberación de huecos tras un borrado físico en el sistema.
    """
    if instance.fecha >= datetime.date.today() and instance.estado not in [EstadoCita.CANCELADA, EstadoCita.ATENDIDA]:
        try:
            Cita.objects.create(
                paciente=None, # El hueco queda libre sin dueño
                medico=instance.medico,
                especialidad=instance.especialidad,
                centro=instance.centro,
                fecha=instance.fecha,
                hora_inicio=instance.hora_inicio,
                estado=EstadoCita.CANCELADA
            )
        except Exception:
            pass