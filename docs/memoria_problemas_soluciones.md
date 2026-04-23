# Desafíos Técnicos y Resolución de Problemas en el Desarrollo

El desarrollo de un Motor de Reasignación inteligente, asíncrono y con capacidades de comunicación en tiempo real conlleva retos arquitectónicos significativos. Esta sección documenta los principales problemas descubiertos durante el ciclo de desarrollo y las soluciones lógicas implementadas para asegurar un entorno de producción robusto, escalable y seguro.

---

## 1. El Bucle Infinito y la Saturación del Servidor (Cascada Incontrolada)

**Contexto del Problema:**
El corazón del sistema es el "Efecto Cascada", mediante el cual la reasignación de una cita libera otro hueco, desencadenando una nueva búsqueda de candidatos. Sin embargo, durante las pruebas de estrés con agendas densamente fragmentadas, se detectó que el algoritmo podía calcular combinaciones de forma casi interminable. Esto provocaba que el hilo principal del servidor se bloqueara, la CPU alcanzara el 100% de uso y la base de datos quedara inaccesible para otros procesos del centro clínico.

**Solución Implementada:**
Se integró un patrón de diseño tipo *Circuit Breaker* (Cortocircuito) basado en profundidad de recursividad. 
Se introdujo una variable de control estricta: un **límite máximo de 5 iteraciones (saltos)** por cada evento desencadenante original. Al alcanzar este número, la función de cascada retorna una señal de parada controlada. Esto establece un límite superior en la complejidad algorítmica ($O(1)$ en términos prácticos, ya que el crecimiento está acotado), asegurando que ninguna cancelación, por muy compleja que sea la agenda, pueda comprometer la estabilidad y el rendimiento general de la plataforma.

## 2. Acoso Digital y la Fatiga de Notificaciones (El Filtro Anti-Spam)

**Contexto del Problema:**
La arquitectura asíncrona depende del correo electrónico para proponer las citas. En las primeras iteraciones del desarrollo, si el Motor ofrecía un hueco a un paciente y este pulsaba "Rechazar" (porque no le convenía la hora), el hueco volvía a quedar libre. Segundos después, si otro paciente cancelaba en una fecha cercana, el Motor volvía a evaluarlo todo. Al ser el primer paciente el que ostentaba la mayor puntuación de Urgencia, el sistema le **volvía a enviar exactamente la misma propuesta** que acababa de rechazar.

**Solución Implementada:**
Para proteger la Experiencia de Usuario (UX) y evitar que los proveedores de correo clasificaran el sistema como remitente de *spam*, se desarrolló un mecanismo de **Memoria de Estados y Exclusiones**. 
Ahora, cuando un paciente rechaza una propuesta (o expira el tiempo límite), esa relación `[ID_Paciente] - [ID_Hueco]` queda registrada en la base de datos con un estado de exclusión. La solución es inyectar una regla preventiva en la consulta SQL principal: la primera fase del algoritmo es filtrar y descartar de la lista de candidatos a todos los pacientes que cuenten con una marca de rechazo para el bloque horario específico que se está evaluando.

## 3. Fragilidad del Sistema por Dependencias de Terceros (Fallo de SMTP)

**Contexto del Problema:**
El Motor no opera de manera aislada; depende de servicios externos (como el servidor SMTP de Gmail) para completar su flujo de trabajo. Originalmente, el código operaba de forma síncrona: *Calcula candidato -> Asigna en Base de Datos -> Envía Email*. 
Si la API de correo tardaba mucho en responder (latencia) bloqueaba toda la operación clínica. Peor aún, si el servicio de correo fallaba por un problema global de red, el sistema entero arrojaba una excepción, ejecutando un *rollback* que deshacía la reasignación médica simplemente porque un email no había podido salir.

**Solución Implementada:**
Se adoptó un modelo de **Desacoplamiento y Resiliencia mediante Manejo de Excepciones**.
La lógica médica transaccional (la toma de la decisión y la reserva en base de datos) se aisló del componente de comunicaciones. Se implementó un bloque `try-catch` silencioso para el envío del correo. Si el proveedor de email externo se cae, el sistema captura la excepción, registra el incidente en un archivo log interno (para conocimiento del administrador), pero **valida la transacción médica**. Esto garantiza que los fallos temporales de red no paralicen la gestión interna de citas del centro de salud.

## 4. El Riesgo de Fraude en la Digitalización de Documentos Médicos

**Contexto del Problema:**
Uno de los pilares del proyecto era eliminar el papel enviando las recetas clínicas directamente al correo electrónico del paciente en formato PDF. El problema lógico es evidente: un archivo PDF es editable. Un paciente podría, de forma ilícita, alterar las fechas, las dosis o los nombres de los medicamentos antes de imprimir la receta para presentarla en una farmacia, incurriendo en un grave riesgo para la salud pública y legal.

**Solución Implementada:**
Se aplicó un cambio de paradigma arquitectónico conocido como **Validación Externa Unívoca (El "Modo Dios")**. 
El archivo PDF en sí mismo deja de ser considerado "el documento de valor oficial". Su única función pasa a ser el transporte de un **Código QR dinámico**. Este QR no contiene el texto de la receta, sino una URL criptográfica que apunta directamente a un portal alojado en el servidor de la clínica. De este modo, la fuente de verdad no es lo que está impreso en el papel, sino lo que la base de datos dicta en tiempo real cuando el profesional de la farmacia escanea el código, eliminando cualquier posibilidad técnica de manipulación documental por parte del usuario final.

## 5. Condiciones de Carrera y Concurrencia de Usuarios

**Contexto del Problema:**
En un entorno multi-usuario, especialmente con notificaciones "push", existía la posibilidad de que se produjeran *Race Conditions* (Condiciones de Carrera). Por ejemplo: el Motor le propone un hueco al Paciente A. Al mismo tiempo, el Administrativo intenta asignar manualmente ese mismo hueco libre a otro paciente que acaba de entrar por la puerta de la clínica. Sin mecanismos de control, ambos sistemas (el automatizado y el manual) colisionarían.

**Solución Implementada:**
Implementación de **Bloqueos Lógicos Temporales (Estados Transitorios)**.
Cuando el Motor selecciona un hueco y lanza una propuesta, ese hueco no figura como "Libre", sino que cambia su estado a "Bloqueado Temporalmente (Pendiente de Aceptación)". Este bloqueo impide que el administrativo (o cualquier otra instancia del motor) pueda ver o disponer de dicho horario. El bloqueo incluye un *Time-To-Live* (Tiempo de Expiración); si el Paciente A no responde en un plazo determinado, el bloqueo se destruye automáticamente y el hueco vuelve a ser un activo negociable en la siguiente iteración del sistema.
