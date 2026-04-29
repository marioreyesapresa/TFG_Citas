from datetime import datetime, timedelta
from typing import List, Dict, Any, Union
from .models import Medico, Especialidad, Cita, HorarioMedico, EstadoCita, DURACION_CITA

def buscar_huecos_disponibles(
    especialidad: Union[int, str, Especialidad], 
    fecha_inicio, 
    fecha_fin
) -> List[Dict[str, Any]]:
    """
    Calcula los huecos libres disponibles cruzando los horarios laborales de los médicos
    con las citas ya programadas en el rango de fechas proporcionado.
    """
    
    if fecha_inicio > fecha_fin:
        return []

    # Determinación de la especialidad
    if isinstance(especialidad, int):
        q_especialidad = Especialidad.objects.filter(id=especialidad).first()
    elif isinstance(especialidad, str):
        q_especialidad = Especialidad.objects.filter(nombre__iexact=especialidad).first()
    else:
        q_especialidad = especialidad
        
    if not q_especialidad:
        return []

    # Obtener médicos de la especialidad seleccionada
    medicos = list(Medico.objects.filter(especialidad=q_especialidad).select_related('user'))
    if not medicos:
        return []
        
    medicos_ids = [m.id for m in medicos]

    # Carga de horarios laborales
    horarios_qs = HorarioMedico.objects.filter(medico_id__in=medicos_ids)
    horarios_dict = {(h.medico_id, h.dia_semana): h for h in horarios_qs}

    # Búsqueda de citas ya ocupadas en el rango solicitado (excluyendo cancelaciones)
    citas_qs = Cita.objects.filter(
        medico_id__in=medicos_ids,
        fecha__range=[fecha_inicio, fecha_fin]
    ).exclude(estado=EstadoCita.CANCELADA)
    
    citas_ocupadas = {(c.medico_id, c.fecha, c.hora_inicio) for c in citas_qs}

    # Generación de la lista de huecos disponibles
    huecos_libres = []
    fecha_actual = fecha_inicio
    
    while fecha_actual <= fecha_fin:
        dia_semana_actual = fecha_actual.weekday()
        
        for medico in medicos:
            horario = horarios_dict.get((medico.id, dia_semana_actual))
            if horario:
                # Iterar por cada intervalo de tiempo dentro de la jornada laboral
                current_dt = datetime.combine(fecha_actual, horario.hora_inicio)
                dt_fin = datetime.combine(fecha_actual, horario.hora_fin)
                
                while current_dt < dt_fin:
                    slot_hora = current_dt.time()
                    
                    if (medico.id, fecha_actual, slot_hora) not in citas_ocupadas:
                        huecos_libres.append({
                            "fecha": fecha_actual,
                            "hora_inicio": slot_hora,
                            "medico": medico
                        })
                    
                    current_dt += timedelta(minutes=DURACION_CITA)
                    
        fecha_actual += timedelta(days=1)
        
    # Devolver resultados ordenados cronológicamente
    huecos_libres.sort(key=lambda x: (x['fecha'], x['hora_inicio']))
    
    return huecos_libres
