# Memoria de Funcionalidad: Expiración Automática de Propuestas (TTL)

## 1. Funcionalidad Completada
Se ha implementado el **Epic 1: Expiración Automática (TTL)** del algoritmo de reasignación. El objetivo alcanzado es dotar al sistema de resiliencia frente a pacientes que reciben un correo con una propuesta de adelanto de cita pero nunca llegan a responder (ni "Aceptar" ni "Rechazar"), bloqueando el hueco libre para otros pacientes de forma indefinida.

## 2. Cómo se ha implementado
En lugar de depender de sistemas complejos de colas en segundo plano como *Celery* o *Redis* (que añadirían una carga infraestructural innecesaria e inestable para el prototipo de un TFG), la solución arquitectónica se ha diseñado bajo un enfoque nativo y ligero de Django: mediante un **Custom Management Command** actuando de demonio (*Cron Job*).

Se ha creado y programado el archivo de control principal: `gestion_citas/management/commands/verificar_expiraciones.py`.
Cuando este *worker* se invoca de forma programada en la consola, ejecuta fluidamente las siguientes validaciones lógicas:
1. Realiza una búsqueda (query) de todas las instancias de `PropuestaReasignacion` cuyo estado transaccional sea `PENDIENTE` y su `fecha_limite` máxima haya quedado por detrás del momento vigente (`timezone.now()`).
2. Somete estas instancias a un bucle temporal donde las "castiga" cambiando asincronamente su estado a **`EXPIRADA`**.
3. Se crea en base de datos un objeto **`Notificacion`** enfocado al UX Front-end. El mensaje le advertirá al paciente, cuando inicie sesión, de la omisión y pérdida del turno acelerado de su cita.
4. **Relanza el Motor:** Factor diferencial de esta funcionalidad. Importa la lógica recursiva subyacente de `iniciar_reasignacion(hueco)` forzando un reinicio global pasándole la Cita raíz (cancelada originalmente). El algoritmo detecta estadísticamente al paciente recién expirado, lo inserta en lista negra gracias a la validación booleana estricta (Regla E.1), puntuando a los siguientes usuarios del centro y reenviando toda la paquetería de comunicaciones en cascada.

## 3. Problemas y Obstáculos Encontrados (Bug de Escalamiento Relacional)
Durante las pruebas de simulación, la reevaluación abortaba las subrutinas SQL con un **Error de Integridad Crítico en la Base de Datos (IntegrityError: UNIQUE constraint failed)**.

**El Origen:**
El modelo relacional Django para `PropuestaReasignacion` tenía mapeado el campo atributo `hueco` de forma bidireccional fuerte: un **`OneToOneField(Cita)`**. Esto forzaba a nivel de arquitectura física que **un único hueco liberado solo pudiese estar vinculado matemáticamente a una y solo una propuesta de paciente**.
Como el CronJob obligaba por iteración al algoritmo en cascada a generar una segunda propuesta para el *siguiente paciente de la lista* (paciente B), la validación SQLite paralizaba la transacción protegiendo la regla de unicidad del paciente A previo (ahora expirado).

**La Solución:**
Una vez trazado y logueado el bug de persistencia de datos (constraints), reescribimos el modelado ORM y relajamos la cardinalidad pasando de 1:1 a un estado de herencia 1-a-N flexible con un **`ForeignKey`**. A continuación, creamos esquemas e inyectamos un nuevo *`makemigrations & migrate`* controlando un rollback de base de datos a nivel local.
El paradigma reformulado acepta conceptualmente un modelo historial completo (Log-Audit). Un hueco libre puede contar con *N* propuestas previas (Juan rechazó, María expiró, Ana aceptó ganando legalmente la reubicación de la Cita).
