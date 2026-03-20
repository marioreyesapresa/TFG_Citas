from datetime import datetime, timedelta
from typing import List, Dict, Any, Union
from .models import Medico, Especialidad, Cita, HorarioMedico, EstadoCita, DURACION_CITA


def buscar_huecos_disponibles(
    especialidad: Union[int, str, Especialidad], 
    fecha_inicio, 
    fecha_fin
) -> List[Dict[str, Any]]:
    """
    Cruza los días laborables de los médicos con esa especialidad, 
    restando las citas que ya tienen asignadas, para devolver una lista de huecos libres.
    """
    
    # 1. Validaciones iniciales
    if fecha_inicio > fecha_fin:
        return []

    # 2. Determinar la especialidad
    if isinstance(especialidad, int):
        q_especialidad = Especialidad.objects.filter(id=especialidad).first()
    elif isinstance(especialidad, str):
        q_especialidad = Especialidad.objects.filter(nombre__iexact=especialidad).first()
    else:
        q_especialidad = especialidad
        
    if not q_especialidad:
        return []

    # 3. Obtener médicos de esa especialidad
    medicos = list(Medico.objects.filter(especialidad=q_especialidad).select_related('user'))
    if not medicos:
        return []
        
    medicos_ids = [m.id for m in medicos]

    # 4. Pre-cargar los HorarioMedico para O(1)
    # Clave: (medico_id, dia_semana) -> HorarioMedico
    horarios_qs = HorarioMedico.objects.filter(medico_id__in=medicos_ids)
    horarios_dict = {(h.medico_id, h.dia_semana): h for h in horarios_qs}

    # 5. Agrupar las citas ocupadas de los médicos en ese rango de fechas
    # (Se excluyen las canceladas, porque equivalen a huecos libres)
    citas_qs = Cita.objects.filter(
        medico_id__in=medicos_ids,
        fecha__range=[fecha_inicio, fecha_fin]
    ).exclude(estado=EstadoCita.CANCELADA)
    
    # Set de tuplas para búsqueda en O(1)
    citas_ocupadas = {(c.medico_id, c.fecha, c.hora_inicio) for c in citas_qs}

    # 6. Iterar y generar huecos libres
    huecos_libres = []
    fecha_actual = fecha_inicio
    
    while fecha_actual <= fecha_fin:
        dia_semana_actual = fecha_actual.weekday() # 0=Lunes, 6=Domingo
        
        for medico in medicos:
            horario = horarios_dict.get((medico.id, dia_semana_actual))
            if horario:
                # Calculamos slots de tiempo desde inicio hasta fin según DURACION_CITA
                dt_dummy = datetime.combine(fecha_actual, horario.hora_inicio)
                dt_fin = datetime.combine(fecha_actual, horario.hora_fin)
                
                while dt_dummy < dt_fin:
                    slot_hora = dt_dummy.time()
                    
                    # Verificamos si este slot está en el Set de citas ocupadas
                    if (medico.id, fecha_actual, slot_hora) not in citas_ocupadas:
                        huecos_libres.append({
                            "fecha": fecha_actual,
                            "hora_inicio": slot_hora,
                            "medico": medico
                        })
                    
                    dt_dummy += timedelta(minutes=DURACION_CITA)
                    
        fecha_actual += timedelta(days=1)
        
    # Ordenar por fecha y luego hora de inicio
    huecos_libres.sort(key=lambda x: (x['fecha'], x['hora_inicio']))
    
    return huecos_libres
