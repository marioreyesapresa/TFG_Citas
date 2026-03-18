# TFG: Diseño y Funcionamiento del Algoritmo de Reasignación en Cascada

Este documento describe en profundidad el mecanismo inteligente de reasignación automática de citas (Motor de Reasignación), el cual es la piedra angular del Trabajo de Fin de Grado. Su objetivo es optimizar los recursos médicos al reasignar automáticamente los huecos liberados por cancelaciones a los pacientes idóneos según reglas clínicas y operativas.

## 1. Disparador del Algoritmo (Event-Driven)

El motor nunca se ejecuta de forma arbitraria; es un sistema reactivo. Su ejecución comienza exactamente en el momento en el que una cita que estaba en estado `CONFIRMADA` o `PENDIENTE` pasa a estado `CANCELADA`.
Esto se detecta a través del método sobreescrito `save()` en el modelo `Cita`. Si hay un cambio de estado hacia cancelación, se invoca a la función principal `iniciar_reasignacion(cita_cancelada)`.

## 2. Parámetros Globales (Configuración Dinámica)

Antes de buscar candidatos, el algoritmo carga la entidad `ConfiguracionReasignacion`, la cual contiene tres pesos modificables por el Administrador o Clínico:
*   **Peso Urgencia (`peso_urgencia`)**: Multiplicador para la gravedad clínica del candidato.
*   **Peso Turno (`prioridad_turno`)**: Puntuación que se otorga cuando las preferencias horarias del paciente coinciden con el hueco liberado (ej. prefiere mañanas y el hueco es a las 11:30).
*   **Peso Antigüedad (`peso_antiguedad`)**: Valor para beneficiar a los pacientes que tienen una cita programada más lejos en el tiempo (y que, por tanto, llevan más tiempo esperando o tienen "más ganas" de adelantarla).

En caso de que no haya configuración en base de datos, el sistema implementa unos valores por defecto (fallback) asumiendo que la *Urgencia Clínica* es el pilar de mayor peso numérico.

## 3. Búsqueda y Evaluación Continua (Reglas A-C)

El núcleo algorítmico selecciona a todos los pacientes del mismo médico que tengan citas programadas en fechas posteriores al hueco liberado y los evalúa matemáticamente en base a un sistema de puntuación acumulativo (`Score`). 

### Regla A: Preferencia de Turno (Operativa)
El sistema deduce si el hueco librado es de "Mañana" (<15:00) o de "Tarde" (>=15:00). Posteriormente, analiza las preferencias configuradas en el perfil de cada candidato:
*   Si **coincide**: Suma `+peso_turno`.
*   Si **no coincide**: Aplica una penalización proporcional restando `peso_turno / 2`.

### Regla B: Urgencia y Triaje Clínico
Esta es la regla más crítica. El algoritmo procesa el nivel de urgencia asignado a la cita futura del candidato (BAJA=1, MEDIA=2, ALTA=3), y lo multiplica por el `peso_urgencia` global. Esto garantiza que un paciente grave escale rápidamente al top de la lista de ranking, priorizando el estado de salud.

### Regla C: Antigüedad de Espera
Busca ser justo con aquellos pacientes que llevan más tiempo esperando su consulta. El algoritmo calcula los días de diferencia entre la cita liberada y la cita futura original del paciente, y lo multiplica por el `peso_antiguedad`. 

## 4. Restricciones Duras (Reglas Anti-Colisión y Lógica de Cascada)

Una alta puntuación matemática no garantiza la asignación. El Motor introduce reglas "estrictas booleanas" que actúan como cortafuegos (filtros) para asegurar la viabilidad de la propuesta y no vulnerar la experiencia de usuario. Son las Reglas D y E.

### Regla D: Inmutabilidad Diaria (Anti-Solapamiento)
Consultando el historial del paciente, si el sistema detecta que el paciente **ya tiene otra cita médica** confirmada ese mismo día natural, el individuo **es descartado instantáneamente**. Esto evita hacer ir repetidamente al centro al paciente o colisionar tratamientos.

### Regla E: Control de Ofertas e Inferencia de Cascada (Anti-Spam)
Para permitir una verdadera reevaluación en cascada, esta regla se subdivide en dos bloqueos:

1.  **Regla E.1 (Lista negra de Hueco):** Si la persona ya ha rechazado este hueco específico anteriormente (o se le expiró la propuesta en el pasado), **es ignorado sistemáticamente**. Esto previene el clásico problema de *bucle algorítmico infinito*: El motor le ofrece a Pepe el hueco de las 9:00 -> Pepe lo rechaza en la web -> pero Pepe sigue siendo el #1 en puntuación -> el motor vuelve a generar otro código para Pepe a las 9:00 -> Pepe repite el rechazo... 
2.  **Regla E.2 (Saturación de Banda):** Si el paciente ganador tiene **ya una propuesta de cualquier otro hueco en estado PENDIENTE**, es bloqueado. Un paciente no puede recibir otra oferta hasta responder a la anterior; esto permite que el sistema gire hacia otros candidatos.

## 5. Salida del Motor (Propuesta y Notificación)

Cuando el bucle acaba, la cita que posea mayor `Score` gana. A diferencia de un sistema de fuerza bruta, el algoritmo no "roba" el hueco automáticamente.
Crea un registro intermedio en base de datos llamado **`PropuestaReasignacion`**, con una validación temporal `fecha_limite` (TTL de 24h). 

A su vez, dispara el subsistema de notificaciones:
1.  **Notificación Web (Intranet):** Genera alerta persistente en el *Dashboard*.
2.  **Email Broadcast (Extranet):** Llama a la API de Django `send_mail` para mandar el aviso externo mediante un origen SMTP en la bandeja del paciente.

## 6. La Reevaluación en Cascada (Resiliencia)

La grandeza del mecanismo reside en lo reactivo que es ante la negativa de un usuario.
Si el paciente ganador entra en su Panel Web y clica explícitamente en el botón de rechazo asíncrono, la función `rechazar_propuesta()` emite una alerta, cambia el estado de su entrada a *RECHAZADA* y consecuentemente **relanza de forma autónoma (recursiva) todo el motor algorítmico**. 
En esa iteración nueva, el algoritmo "choca" limpiamente con la **Regla E.1** y descarta a este primer paciente, permitiendo que la oferta "descienda en cascada" hasta llegar al segundo paciente mejor clasificado, remitiéndole automáticamente su propia propuesta y correo.
