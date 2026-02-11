from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import datetime
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

# ==========================================
# 2. ENTIDADES INDEPENDIENTES
# ==========================================
class Centro(models.Model):
    nombre = models.CharField(max_length=100)
    
    def __str__(self):
        return self.nombre
    
class Especialidad(models.Model):
    #Datos que tendra la clase
    nombre = models.CharField(max_length=100)

    # Esto es una función especial de Python para que, 
    # al ver el objeto, nos diga su nombre real(string) y no un código raro(object 1)
    def __str__(self):
        return self.nombre
    
    #Para indicar como se escribe el plural, por defecto (si no ponemos esta funcion) añade solo una s
    class Meta:
        verbose_name_plural = "Especialidades"

# ==========================================
# 3. PERFILES DE USUARIO 
# ==========================================

class Paciente(models.Model):
    # Relación 1 a 1 con el usuario de Django (Login)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='paciente')
    
    # Datos específicos del Paciente 
    telefono = models.CharField(max_length=15)
    preferencia_turno = models.CharField(
        max_length=1, 
        choices=Turno.choices, 
        default=Turno.MANANA
    )

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"


class Medico(models.Model):
    # Relación 1 a 1 con el usuario de Django
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='medico')
    
    # Datos específicos del Médico (UML)
    numero_colegiado = models.CharField(max_length=20)
     #con foreignkey hacemos q ese campo sea una elección de la lista de Especialidades que ya exist
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
        # Evita duplicados: Un médico no puede tener dos horarios el mismo día
        unique_together = ('medico', 'dia_semana', 'hora_inicio') 

    def clean(self):
        # 1. PROTECCIÓN (NUEVO): Si los campos están vacíos, salimos de la función.
        # Esto evita el error "NoneType has no attribute minute" en el Admin.
        if not self.hora_inicio or not self.hora_fin:
            return

        # 2. VALIDACIÓN DE MINUTOS (Solo si las horas existen)
        if self.hora_inicio.minute not in [0, 30]:
            raise ValidationError({'hora_inicio': "La hora de inicio debe ser exacta (ej: 09:00 o 09:30)."})
        if self.hora_fin.minute not in [0, 30]:
            raise ValidationError({'hora_fin': "La hora de fin debe ser exacta (ej: 14:00 o 14:30)."})
        
        # 3. VALIDACIÓN DE COHERENCIA
        if self.hora_inicio >= self.hora_fin:
            raise ValidationError("La hora de inicio debe ser anterior a la de fin.")

    def __str__(self):
        # También protegemos el string por si acaso se llama sin hora
        inicio = self.hora_inicio.strftime('%H:%M') if self.hora_inicio else "??"
        fin = self.hora_fin.strftime('%H:%M') if self.hora_fin else "??"
        return f"{self.medico} - {self.get_dia_semana_display()} ({inicio}-{fin})"
    
# ==========================================
# 5. CITA 
# ==========================================
class EstadoCita(models.TextChoices):
    PENDIENTE = 'P', 'Pendiente'
    CONFIRMADA = 'C', 'Confirmada'
    CANCELADA = 'X', 'Cancelada'
    EN_ESPERA = 'R', 'En espera de reasignación'

class Cita(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='citas')
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name='citas')
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    urgencia = models.IntegerField(default=1) # 1: Baja, 2: Media, 3: Alta
    
    estado = models.CharField(
        max_length=1, 
        choices=EstadoCita.choices, 
        default=EstadoCita.PENDIENTE
    )

    class Meta:
        ordering = ['fecha', 'hora_inicio']

    def __str__(self):
        return f"Cita: {self.paciente} con {self.medico} el {self.fecha}"
    
    def clean(self):
        # 1. Validar que la cita no sea en el pasado 
        if self.fecha < datetime.date.today() and self.estado != EstadoCita.CANCELADA:
            raise ValidationError("No se pueden crear citas en el pasado.")
      
        # 2. Validar Disponibilidad del Médico y TURNOS (Mejora Tutor)
        dia_semana_cita = self.fecha.weekday() 
        
        # Recuperamos el horario concreto para saber a qué hora empieza a trabajar
        horario = HorarioMedico.objects.filter(
            medico=self.medico,              
            dia_semana=dia_semana_cita,      
        ).first()

        # Validación A: ¿Trabaja ese día?
        if not horario:
            raise ValidationError(f"El Dr/a. {self.medico.user.last_name} no trabaja los {self.fecha.strftime('%A')}.")
        
        # Validación B: ¿La hora está dentro del rango?
        # Nota: Ajustamos para que la hora de la cita sea estrictamente menor a la hora de fin
        if not (horario.hora_inicio <= self.hora_inicio < horario.hora_fin):
             raise ValidationError(f"La hora debe estar entre {horario.hora_inicio.strftime('%H:%M')} y {horario.hora_fin.strftime('%H:%M')}.")

        # Validación C: ¿Encaja en los slots de 30 min? (Lógica Matemática)
        minutos_inicio_medico = horario.hora_inicio.hour * 60 + horario.hora_inicio.minute
        minutos_cita = self.hora_inicio.hour * 60 + self.hora_inicio.minute
        
        diferencia = minutos_cita - minutos_inicio_medico
        
        if diferencia % DURACION_CITA != 0:
            raise ValidationError(f"Las citas deben ser cada {DURACION_CITA} minutos exactos (ej: {horario.hora_inicio.strftime('%H:%M')}, "
                                  f"{(datetime.datetime.combine(datetime.date.today(), horario.hora_inicio) + timedelta(minutes=DURACION_CITA)).strftime('%H:%M')}...).")

        # 3. Validar Solapamientos (R14)
        cita_medico_ocupada = Cita.objects.filter(
            medico=self.medico,
            fecha=self.fecha,
            hora_inicio=self.hora_inicio
        ).exclude(id=self.id).exists()

        if cita_medico_ocupada:
            raise ValidationError("El médico ya tiene una cita asignada a esa hora.")

        cita_paciente_ocupada = Cita.objects.filter(
            paciente=self.paciente,
            fecha=self.fecha,
            hora_inicio=self.hora_inicio
        ).exclude(id=self.id).exists()

        if cita_paciente_ocupada:
            raise ValidationError("El paciente ya tiene una cita a esa hora.")

    def save(self, *args, **kwargs):
            # 1. Ejecutar validaciones 
            self.full_clean()

            # 2. Detectar si es una cancelación
            activar_motor = False
            
            if self.pk: 
                cita_anterior = Cita.objects.get(pk=self.pk)
                # Si NO estaba cancelada Y AHORA SÍ lo está...
                if cita_anterior.estado != EstadoCita.CANCELADA and self.estado == EstadoCita.CANCELADA:
                    activar_motor = True

            # 3. Guardar el cambio en la base de datos
            super().save(*args, **kwargs)

            # 4. Si hay que activar el motor, lo hacemos DESPUÉS de guardar
            if activar_motor:
                from .algoritmo_reasignacion import iniciar_reasignacion 
                iniciar_reasignacion(self)