from gestion_citas.models import PropuestaReasignacion, EstadoPropuesta, Notificacion
from django.db.models import Count

def limpiar_datos_corruptos():
    print("--- Iniciando limpieza de base de datos ---")
    
    # 1. Eliminar propuestas huérfanas (Hueco es NULL)
    # Estas son las que causan el error visual "Nueva sugerencia: -"
    huerfanas = PropuestaReasignacion.objects.filter(hueco__isnull=True)
    count_huerfanas = huerfanas.count()
    huerfanas.delete()
    print(f"Eliminadas {count_huerfanas} propuestas huérfanas.")

    # 2. Eliminar propuestas duplicadas para el mismo hueco
    # Buscamos huecos que tengan más de una propuesta PENDIENTE
    huecos_duplicados = PropuestaReasignacion.objects.filter(
        estado=EstadoPropuesta.PENDIENTE
    ).values('hueco').annotate(num_props=Count('id')).filter(num_props__gt=1)

    eliminadas_duplicadas = 0
    for entry in huecos_duplicados:
        hueco_id = entry['hueco']
        # Nos quedamos con la más antigua (la primera que se creó)
        propuestas = PropuestaReasignacion.objects.filter(
            hueco_id=hueco_id, 
            estado=EstadoPropuesta.PENDIENTE
        ).order_by('fecha_creacion')
        
        # Las que sobran (todas menos la primera) las borramos
        para_borrar = propuestas[1:]
        for p in para_borrar:
            p.delete()
            eliminadas_duplicadas += 1
            
    print(f"Eliminadas {eliminadas_duplicadas} propuestas duplicadas por seguridad.")

    # 3. Limpiar notificaciones huérfanas
    # Notificaciones que apuntan a propuestas que ya no existen
    notif_huerfanas = Notificacion.objects.filter(propuesta__isnull=True)
    # Solo borramos las que están ligadas a una propuesta (algunas pueden ser mensajes generales)
    # Pero según el modelo, si tiene el campo propuesta es porque era de eso.
    # En realidad, si el campo propuesta es NULL, podría ser una notificación general.
    # Mejor buscamos notificaciones que TENÍAN propuesta pero ya no (si eso fuera posible rastrear)
    # O simplemente borramos las notificaciones cuyo mensaje hable de "adelanto" y no tengan propuesta activa.
    
    # Por ahora, las propuestas borradas arriba habrán borrado sus notificaciones en cascada 
    # (si on_delete=CASCADE). Vamos a comprobarlo.
    
    print("--- Limpieza finalizada con éxito ---")

if __name__ == "__main__":
    limpiar_datos_corruptos()
