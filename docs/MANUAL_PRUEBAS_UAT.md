# 🎓 MANUAL DE VALIDACIÓN DEL TFG (PARA TUTORES Y TRIBUNAL)

**Plataforma de pruebas en vivo:** `https://tfgmarreyapr.pythonanywhere.com`
**Público Objetivo:** Tutor del TFG y Tribunal Evaluador.
**Objetivo:** Servir de guía paso a paso para la comprobación total de los requisitos funcionales del proyecto (Documentados en el Acta de Constitución como R1 al R16).

---

## 🔑 Credenciales Generales de Prueba
Todos los usuarios generados en el sistema de pruebas comparten la misma contraseña para facilitar la evaluación:
*   **Contraseña Universal:** `password123`
*   **Contraseña Admin:** `admin`

*(Nota: En algunas pruebas usaremos un usuario concreto, especificado en cada paso).*

---

## FASE 1: PERFILES, AGENDAS Y CONFIGURACIÓN

Esta fase comprueba que los distintos roles (Administrativo, Médico y Paciente) pueden acceder y realizar sus funciones básicas **(Requisitos R1, R6, R9, R10, R11)**.

### Prueba 1.1: Acceso del Administrativo y Panel de Control
1.  **Acción:** Ve a `https://tfgmarreyapr.pythonanywhere.com/admin/` e inicia sesión con el usuario `admin`.
2.  **Verificación:** Comprueba que puedes ver un panel completo con apartados como "Usuarios", "Citas", "Médicos" y "Centros". 
3.  **Gestión de Citas (R11):** Entra en "Citas", selecciona cualquiera y cambia su estado de "Confirmada" a "Pendiente", y luego otra vez a "Confirmada". Guarda los cambios. *Resultado: El sistema te confirma la modificación mediante un aviso claro en la parte superior.*

### Prueba 1.2: Configuración del Motor Algorítmico (R6)
1.  **Acción:** Dentro del panel Administrativo, haz clic en **ConfiguracionReasignacion**.
2.  **Verificación:** Entra en el registro existente. Comprueba que el sistema permite al administrador decidir qué peso numérico darle a la "**Urgencia**" del paciente, al "**Turno preferido**" y a la "**Antigüedad en lista**". Esto demuestra que el algoritmo no es estático, sino gobernable por el hospital.

### Prueba 1.3: Acceso del Médico y Visión de Agenda (R9)
1.  **Acción:** Cierra sesión en el Administrador y entra en la web principal (`https://tfgmarreyapr.pythonanywhere.com/`). Pulsa en "Acceder" e inicia sesión como un médico (ej. usuario: `medico_pablo`).
2.  **Verificación:** El sistema te redirige a un Panel de Médico. Puedes ver tu agenda de citas confirmadas para los próximos días, diferenciadas del resto de la plataforma. **Cierra sesión al terminar.**

---

## FASE 2: EXPERIENCIA DEL PACIENTE Y RESERVAS

Esta fase valida que el paciente puede operar autónomamente y que el sistema evita errores humanos **(Requisitos R2, R12, R13, R14)**.

### Prueba 2.1: Búsqueda y Filtros Clínicos (R12, R13)
1.  **Acción:** En la web principal, inicia sesión como paciente (ej. usuario: `paciente_mario`).
2.  **Verificación:** En el menú, ve a "Solicitar Cita". Comprueba que puedes usar los desplegables dinámicos: primero eliges Especialidad, luego Centro, Médico, y finalmente un calendario interactivo que te muestra solo las horas disponibles.

### Prueba 2.2: Prevención de Solapamientos Multicita (R14)
1.  **Acción:** En tu menú de `paciente_mario`, fíjate en la fecha y hora de la cita que ya tienes asignada.
2.  **Intento de Error:** Ve a "Solicitar Cita", elige el mismo médico e intenta reservar *exactamente a la misma hora* que la cita que ya tienes.
3.  **Verificación:** Al intentar guardar, el sistema arroja un mensaje de error claro (R16) indicando que "Ya tienes una cita programada a esa hora" o que el hueco ha sido ocupado, bloqueando la reserva solapada. **Cierra sesión al terminar.**

---

## FASE 3: EL MOTOR DE REASIGNACIÓN EN ACCIÓN (EL NÚCLEO DEL TFG)

Aquí probaremos la "Inteligencia" del sistema: cómo reacciona ante un hueco libre de forma automática **(Requisitos R3, R4, R5, R7, R8, R15, R16)**.

### Prueba 3.1: Preparar al "Paciente Sujeto de Pruebas" (Para recibir el Email)
Dado que el sistema envía correos reales, necesitamos ponerle tu correo personal a un paciente simulado para que puedas evaluar el diseño visual de los e-mails.
1.  Entra al panel Administrativo (`/admin`) como `admin`.
2.  Ve a **Usuarios** y busca a `paciente_manuel`. Haz clic en su nombre.
3.  Desplázate hacia abajo hasta la sección "Información Personal".
4.  Rellena el campo **Dirección de correo electrónico** con tu correo real y pulsa "Guardar" al final de la página. (Mantén esta pestaña de administrador abierta).

### Prueba 3.2: Disparar el Motor mediante Cancelación (R3, R4)
Vamos a simular que el médico tiene un hueco libre repentino a corto plazo.
1.  Como administrador, entra en **Citas**.
2.  Busca una Cita confirmada para un paciente cualquiera que NO sea Manuel (por ejemplo una cita del `paciente_david` o `paciente_jorge`). *Consejo: Procura que la cita sea para mañana o pasado mañana.*
3.  **Acción:** Entra en esa cita y cambia **Estado** de "Confirmada" a **"Cancelada"**. ¡Dale a Guardar!
4.  **Magia Silenciosa:** El servidor detiene la cancelación, procesa quién es el paciente más idóneo por urgencia para heredar ese hueco, y le envía un SMS/Email. (Nota: Si quieres asegurar que se lo manda a Manuel, debes cancelar una cita del médico que tenga asignado Manuel, pero para una fecha anterior a la suya).

### Prueba 3.3: Comprobación del Email Interactivo (R7, R15)
1.  **Acción:** Abre la bandeja de entrada de tu correo personal (el que configuraste en Manuel).
2.  **Verificación:** Has recibido un email titulado "✨ Nueva Propuesta de Adelanto de Cita Disponible". 
3.  Comprueba que el diseño es Premium (HTML y CSS) y que lee correctamente los datos clínicos reales calculados: Nombre del Médico, Nueva Fecha adelantada, y límite de tiempo para contestar (TTL).
4.  El correo tiene **dos botones interactivos (Confirmar Adelanto / Rechazar)**. No hagas clic en ellos aún.

### Prueba 3.4: La Experiencia Web y Aceptación (R10)
Los pacientes mayores a veces temen clicar en enlaces de correos. Para ellos, el sistema es omnicanal.
1.  **Acción:** Ve a la web principal (fuera del administrador) e inicia sesión como `paciente_manuel`.
2.  **Verificación del Dashboard:** Verás de inmediato una alerta visual verde muy prominente en tu portada informándote de la propuesta de adelanto de cita.
3.  **Resolución (R8):** Haz clic en el botón verde de la web **"Aceptar Adelanto"**. 
4.  **Verificación Final:** La tarjeta verde desaparece. Si miras tu lista de próximas citas en la pantalla principal de Manuel, **la fecha se ha actualizado automáticamente** a la fecha que quedó libre. 

---

## FASE 4: RESILIENCIA, CASCADAS Y EXPIRACIONES

¿Qué pasa si el paciente ignora la propuesta o dice explícitamente que no? El sistema nunca duerme para no desaprovechar los huecos públicos (El Efecto Cascada).

### Prueba 4.1: El Rechazo y el Efecto Cascada a otro Paciente
1.  Repite los pasos de la Fase 3 cancelando otra cita de un médico que tenga lista de espera.
2.  Cuando el paciente inicial recibe la alerta (o el correo), pulsa en el botón rojo: **"Rechazar"**.
3.  **Verificación de Cascada:** La cita del paciente original vuelve a ser la que tenía antes, pero internamente el motor **acaba de saltar a la persona número 2 del ránking** y le acaba de notificar a él.

### Prueba 4.2: La Expiración por Tiempo (TTL - Time To Live) (R8)
Los pacientes que no leen su móvil no pueden bloquear la lista de espera hospitalaria eternamente.
1.  **Escenario Teórico:** El paciente ideal recibe el correo de la propuesta un Viernes, pero no hace absolutamente nada durante 48 horas. El motor lo detectaría la madrugada del Lunes y declararía la oferta caducada.
2.  **Demostración Práctica (Viaje en el tiempo):**
    *   Como Administrador en `/admin`, ve al apartado **"Propuestas Reasignacion"**.
    *   Si ves una propuesta en estado *"Pendiente de respuesta"*, entra en ella.
    *   Busca el campo de "Fecha Oferta" y modifícalo simulando que se envió hace una semana. Dale a Guardar.
    *   El motor barrerá esta propuesta en su próximo ciclo y pasará sola a estado **"Expirada"**, relanzando la cascada hacia el paciente número 3 de la lista. (En la defensa, se puede forzar este barrido desde la terminal de servidores).

---
*Manual Creado como Entregable E2 de Documentación (Marzo 2026).*
