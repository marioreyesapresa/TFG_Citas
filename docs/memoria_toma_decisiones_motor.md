# Lógica de Toma de Decisiones del Motor: Scoring y Exclusiones

Este documento detalla conceptual y funcionalmente cómo el Motor de Reasignación selecciona al paciente idóneo para un hueco liberado. El proceso garantiza un equilibrio perfecto entre la ética médica, la eficiencia operativa y una experiencia de usuario sin fricciones.

---

## 1. El Sistema de Puntuación (Scoring): Los 3 Pilares

Para decidir quién es el "mejor candidato" de entre toda la lista de espera, el Motor no opera de manera secuencial simple (FIFO - First In, First Out), sino que utiliza un sistema de **Scoring ponderado**. A cada paciente elegible se le asigna una puntuación calculada a partir de tres pilares fundamentales:

### A. Urgencia Clínica (El Factor Dominante)
Es el criterio con el peso más alto en la fórmula de decisión. Clasifica la necesidad de la cita desde revisiones rutinarias hasta atenciones prioritarias.
*   **¿Por qué es el factor más pesado?** Al priorizar la Urgencia Clínica por encima de cualquier otro dato, el Motor garantiza que su comportamiento esté regido por la **ética médica**. En sanidad, el tiempo de espera no siempre define la necesidad. Un paciente con una dolencia aguda o riesgo médico siempre será priorizado para ocupar un hueco libre frente a un paciente que requiere un chequeo anual, sin importar si este último lleva más meses en lista de espera.

### B. Continuidad de Turno (Preferencia de Horario)
El sistema analiza si el hueco que se ha quedado libre (por ejemplo, a las 10:00 AM) coincide con el turno preferido por el paciente (mañana o tarde) según su histórico o solicitud inicial.
*   **El valor de negocio:** Este pilar es clave para la eficiencia operativa. Al ofrecer citas que encajan con las preferencias del paciente, se dispara exponencialmente la **tasa de aceptación** de la propuesta, cerrando el ciclo rápidamente y evitando iteraciones innecesarias del motor.

### C. Antigüedad (Tiempo en Espera)
Representa la cantidad de días que la petición del paciente lleva activa en el sistema.
*   **El valor de negocio:** Actúa como el elemento de **justicia social y equidad**. Cuando dos pacientes tienen exactamente el mismo nivel de urgencia clínica, el Motor desempata otorgando la máxima prioridad a la persona que lleva más tiempo esperando, evitando así el estancamiento crónico de solicitudes antiguas.

---

## 2. Reglas de Exclusión: Limpiando el Ruido

Antes de que el motor empiece a calcular puntuaciones, ejecuta una fase de **Cribado Previo**. Su objetivo es descartar de forma temprana a aquellos pacientes para los que la asignación del hueco no es viable ni lógica, ahorrando recursos computacionales y protegiendo al usuario.

Las reglas de exclusión más importantes son:

1.  **Exclusión por Solapamiento (Ya tienen cita ese día):**
    El Motor descarta automáticamente a cualquier paciente que ya tenga una cita confirmada para la misma fecha del hueco liberado. Esto evita duplicidades absurdas en la agenda del paciente y del centro, previniendo que un paciente sea citado dos veces el mismo día para la misma especialidad.

2.  **Exclusión por Incoherencia Temporal (Citas en el pasado):**
    Si el paciente original solicitaba una cita para un rango de fechas que ya ha vencido (el paciente ya fue atendido por otras vías o la necesidad caducó), el motor lo ignora. El sistema siempre proyecta sus soluciones hacia adelante, manteniendo la integridad temporal de la agenda.

3.  **Prevención de Spam (Filtro Anti-Rechazo):**
    Esta es una de las reglas más vitales para la Experiencia de Usuario (UX). Si el Motor propone un hueco a un paciente y este lo rechaza (o deja que el tiempo de la propuesta expire), el sistema memoriza esta decisión. En las siguientes iteraciones para cubrir ese *mismo hueco*, el paciente será excluido.
    *   **¿Por qué es crucial?** Evita el acoso digital. Sin esta regla, el paciente podría recibir múltiples correos electrónicos ofreciéndole exactamente el mismo horario que ya indicó que no le viene bien, lo que degradaría la imagen del servicio y generaría fatiga en el usuario.
