from django.core.management.base import BaseCommand
from django.utils import timezone
from gestion_citas.models import PropuestaReasignacion, EstadoPropuesta, Notificacion
from gestion_citas.algoritmo_reasignacion import iniciar_reasignacion

class Command(BaseCommand):
    help = 'Revisa las propuestas de reasignación con TTL superado y dispara la cascada para el siguiente paciente.'

    def handle(self, *args, **kwargs):
        ahora = timezone.now()
        
        # 1. Buscar propuestas pendientes que ya hayan superado el TTL límite
        propuestas_expiradas = PropuestaReasignacion.objects.filter(
            estado=EstadoPropuesta.PENDIENTE,
            fecha_limite__lt=ahora
        )

        cantidad = propuestas_expiradas.count()
        if cantidad == 0:
            self.stdout.write(self.style.SUCCESS(f"[{ahora.strftime('%Y-%m-%d %H:%M:%S')}] TTL OK: No hay propuestas caducadas."))
            return

        self.stdout.write(self.style.WARNING(f"\n[{ahora.strftime('%Y-%m-%d %H:%M:%S')}] ⚠️ TTL ACTIVADO: Se han detectado {cantidad} propuesta(s) expirada(s)."))

        # 2. Procesar cada propuesta activando la Cascada
        for propuesta in propuestas_expiradas:
            paciente = propuesta.paciente
            hueco = propuesta.hueco

            # Cambiar estado a EXPIRADA para que la Regla E.1 lo bloquee inteligentemente en el siguiente intento
            propuesta.estado = EstadoPropuesta.EXPIRADA
            propuesta.save()

            # Notificar al paciente impuntual que perdió el turno
            Notificacion.objects.create(
                paciente=paciente,
                propuesta=propuesta,
                mensaje=f"⏳ Tu propuesta de adelanto para el día {hueco.fecha.strftime('%d/%m/%Y')} ha expirado (han pasado más de 24h) y ha sido cedida de forma automática al siguiente paciente en la lista."
            )

            self.stdout.write(self.style.ERROR(f"   => ❌ Propuesta de {paciente} bloqueada permanentemente por caducidad."))

            # EL NÚCLEO ARQUITECTÓNICO: Relanzar el Motor (Reevaluación en Cascada)
            self.stdout.write(self.style.NOTICE(f"   => 🔄 Relanzando motor de reasignación para el hueco de las {hueco.hora_inicio.strftime('%H:%M')}..."))
            
            # Ejecutamos el algoritmo original con el mismo hueco.
            # Como la propuesta actual está en estado EXPIRADA, la Regla E.1 ignora a este paciente y avanza al siguiente.
            iniciar_reasignacion(hueco)

        self.stdout.write(self.style.SUCCESS(f"✅ CICLO DE EXPIRACIÓN FINALIZADO CON ÉXITO.\n"))
