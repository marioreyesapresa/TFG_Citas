import os
import sys
import django
from datetime import time, timedelta, datetime

# Configurar el entorno de Django dinámicamente
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TFG_Citas.settings')
django.setup()

from gestion_citas.models import Medico, HorarioMedico, Cita, EstadoCita

def automatizar_horarios_tarde():
    print("=== INICIANDO CONVERSIÓN AUTOMÁTICA A HORARIOS DE TARDE ===")
    
    # Seleccionamos 5 médicos de la base de datos para pasarlos al turno de tarde
    medicos_tarde = Medico.objects.all()[:5]
    
    if not medicos_tarde.exists():
        print("No se encontraron médicos en la base de datos.")
        return
        
    for medico in medicos_tarde:
        print(f"\nProcesando al {medico}...")
        
        # 1. Modificar su Horario de Trabajo a la tarde (15:00 - 21:00)
        # Borramos sus horarios antiguos
        HorarioMedico.objects.filter(medico=medico).delete()
        
        # Creamos los nuevos horarios de Lunes a Viernes
        for dia in range(5):
            HorarioMedico.objects.create(
                medico=medico,
                dia_semana=dia,
                hora_inicio=time(15, 0),
                hora_fin=time(21, 0)
            )
        print(f"-> Horario laboral asignado: Lunes a Viernes de 15:00 a 21:00.")
        
        # 2. Corregir y desplazar sus citas existentes para que coincidan con el nuevo turno
        # Cualquier cita de mañana (de 8:00 a 14:00) la desplazamos sumándole 7 horas (ej: 08:00 -> 15:00)
        citas = Cita.objects.filter(medico=medico)
        citas_desplazadas = 0
        
        for cita in citas:
            hora_original = cita.hora_inicio
            if hora_original.hour < 15: # Es una cita de mañana
                # Convertimos a datetime para operar fácilmente con horas
                dt_original = datetime.combine(cita.fecha, hora_original)
                dt_nueva = dt_original + timedelta(hours=7)
                
                # Actualizamos directamente en la base de datos con .update() para evitar disparar 
                # validaciones intermedias hasta que estén guardadas las nuevas horas.
                Cita.objects.filter(id=cita.id).update(hora_inicio=dt_nueva.time())
                citas_desplazadas += 1
                
        print(f"-> Desplazadas {citas_desplazadas} citas de mañana al turno de tarde (+7 horas).")

    print("\n=== CONVERSIÓN FINALIZADA CON ÉXITO ===")

if __name__ == "__main__":
    automatizar_horarios_tarde()
