def iniciar_reasignacion(cita_cancelada):
    """
    Esta función es el cerebro del TFG.
    Se activa cuando una cita se cancela.
    """
    print("==================================================")
    print(f"🚨 ALERTA: Se ha cancelado la cita {cita_cancelada.id}")
    print(f"📅 Fecha hueco: {cita_cancelada.fecha} a las {cita_cancelada.hora_inicio}")
    print(f"👨‍⚕️ Médico: {cita_cancelada.medico}")
    print("🤖 MOTOR: Iniciando búsqueda de candidatos...")
    print("==================================================")
    
    # AQUÍ PROGRAMAREMOS EL ALGORITMO MÁS ADELANTE
    # 1. Buscar pacientes interesados
    # 2. Calcular puntuaciones
    # 3. Crear propuesta