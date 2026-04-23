# Efecto Cascada y Mecanismos de Seguridad del Motor

Este documento detalla el comportamiento más avanzado del Motor de Reasignación: la capacidad de encadenar reasignaciones para maximizar el impacto, junto con las salvaguardas técnicas implementadas para garantizar la estabilidad del sistema y proteger la experiencia de usuario. Este punto es clave para demostrar el control sobre los riesgos de la automatización en un entorno de producción.

---

## 1. El Efecto Dominó (Cascada): Comprimiendo la Lista de Espera

El verdadero poder y la mayor innovación del Motor de Reasignación reside en su capacidad de generar un **"Efecto Dominó" o Reacción en Cadena**. El sistema no se conforma con rellenar un solo hueco puntual; su diseño arquitectónico busca una optimización global de la agenda.

### Ejemplo Práctico
Para entender el impacto de este efecto, imaginemos el siguiente escenario:
1.  El **Paciente A** cancela repentinamente su cita prevista para el **Lunes**. Se genera un "hueco perdido".
2.  El Motor actúa de inmediato y selecciona al **Paciente B**, quien actualmente tiene una cita programada para el **Miércoles**.
3.  El Paciente B acepta la propuesta y su cita se adelanta al Lunes. 
4.  En el mismo momento en que el Paciente B acepta, **su hueco del Miércoles queda automáticamente libre**.
5.  Lejos de detenerse, el Motor entra en "Modo Cascada". Vuelve a evaluar la lista de espera con el nuevo hueco del Miércoles y encuentra al **Paciente C** (cuya cita estaba agendada para el **Viernes**), y le lanza una nueva propuesta.

### El Valor de Negocio
Este proceso logra lo que humanamente es casi imposible: **"comprimir" activamente la lista de espera hacia el presente**. Una única cancelación desencadena una onda expansiva de optimización que puede adelantar las citas de múltiples pacientes. El resultado es un aprovechamiento superlativo del tiempo médico y una reducción drástica de los tiempos medios de espera para el conjunto de los pacientes.

---

## 2. El "Seguro de Vida" (Circuit Breaker): Límite de Saltos

A pesar de que la Cascada es la funcionalidad más potente del sistema, la ingeniería de software profesional requiere prever escenarios de riesgo. Un sistema autónomo y recursivo sin restricciones podría descontrolarse y provocar un fallo catastrófico en un entorno real. Por ello, el Motor incluye un mecanismo de seguridad crítico denominado *Circuit Breaker* (Cortocircuito), que establece un **límite estricto de 5 saltos consecutivos**.

### ¿Por qué es funcionalmente imprescindible este límite?
1.  **Prevención de Saturación (Rendimiento del Servidor):** En una clínica grande con agendas muy fragmentadas, la búsqueda recursiva podría entrar en bucles de evaluación extremadamente largos. El límite de 5 saltos actúa como un cortafuegos para evitar picos de consumo de CPU y Memoria, garantizando que el servidor principal nunca colapse.
2.  **Prevención de Spam y "Bombardeo" de Correos:** En cada salto de la cascada se envía un email al candidato propuesto. Si el sistema realizara 50 saltos en un minuto, desencadenaría una avalancha masiva de notificaciones, lo que podría ser clasificado como SPAM por los proveedores de correo electrónico e incomodar a decenas de pacientes simultáneamente.
3.  **Estabilidad Predecible:** Limitar la recursividad asegura que cada intervención del algoritmo tenga un tiempo de ejecución y un impacto acotados, manteniendo el comportamiento del sistema controlable y auditable.

---

## 3. Fiabilidad Técnica y Resiliencia en las Comunicaciones

Además del control de la cascada, el sistema incorpora resiliencia frente a dependencias externas. El envío de las propuestas por correo electrónico no es una tarea bloqueante ("cuello de botella") para el flujo central. 

Si el servidor de envío de correos (ej. el servicio de SMTP o un proveedor de terceros) sufre una caída, latencia alta o problemas de red temporal, **el Motor de Reasignación no se detiene ni se corrompe**. El sistema está diseñado para capturar la excepción silenciosamente, registrar internamente que ha habido un problema de comunicación, y continuar asegurando la integridad de los datos en la base de datos. Esto garantiza que una caída técnica del proveedor de email no paralice la operativa clínica de la aplicación ni "congele" el sistema de reasignaciones.
