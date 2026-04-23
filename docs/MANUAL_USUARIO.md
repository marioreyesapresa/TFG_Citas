# 🏥 MANUAL DE USUARIO - PREMIUM v2.1 (TFG)

**Acceso a la plataforma en vivo:** `https://tfgmarreyapr.pythonanywhere.com`

Bienvenido al Manual de Usuario de la **versión Premium v2.1**. Este sistema ha sido diseñado no solo para ser funcional mediante su **Motor de Reasignación en Cascada**, sino para ofrecer una experiencia de usuario moderna, intuitiva y plenamente adaptada a dispositivos móviles.

---

## 🔐 1. CREDENCIALES DE ACCESO Y POLÍTICA DE REGISTRO

Por motivos de seguridad y cumplimiento normativo (simulando un entorno clínico real), **la plataforma no permite el registro libre de usuarios**. Las cuentas son creadas exclusivamente por el personal de admisión del hospital tras verificar la identidad física del paciente.

Para evaluar este prototipo, se ha precargado una base de datos con usuarios de prueba. Utilice las siguientes credenciales para navegar por los diferentes roles:

| Perfil | Nombre de Usuario (Login) | Contraseña | Notas |
| :--- | :--- | :--- | :--- |
| **Administrador** | `admin` | `admin` | Acceso total al panel de control (`/admin`). |
| **Paciente 1** | `paciente_manuel` | `password123` | Ideal para probar la recepción de correos. |
| **Paciente 2** | `paciente_mario` | `password123` | Ideal para probar cruces de citas. |
| **Paciente 3** | `paciente_clara` | `password123` | Cuenta de pruebas adicional. |
| **Médico 1** | `medico_pablo` | `password123` | Vista de agenda de consultas. |

*(Nota: Existen decenas de pacientes y médicos precargados, todos utilizan la contraseña universal `password123` salvo el administrador `admin`, puediendo ver todos los usuarios en el panel de control `/admin`)*.

---

## 📱 2. INTERFAZ Y ACCESIBILIDAD (DISEÑO PREMIUM)

La plataforma utiliza el sistema de diseño **Premium v2.1**, enfocado en la claridad visual y la facilidad de uso.

*   **Diseño Adaptativo (Mobile First):** Puede acceder a la plataforma desde su smartphone o tablet. La interfaz se ajustará automáticamente, convirtiendo las tarjetas de citas y los menús en elementos fáciles de pulsar con el dedo.
*   **Dashboards Inteligentes:** Cada perfil (Paciente, Médico, Administrativo) tiene su propio panel de control con la información crítica resaltada mediante tarjetas visuales (*Cards*) y etiquetas de colores (*Badges*).
*   **Navegación Intuitiva:** El sistema utiliza la tipografía *Outfit* y una paleta de colores suaves para reducir la fatiga visual durante el uso prolongado.

---

## 👤 2. GUÍA DEL PACIENTE

Esta sección explica cómo los pacientes gestionan sus citas y cómo interactúan con el sistema de reasignación automática.

### 2.1. Iniciar Sesión y Panel Principal (Dashboard)
1. Acceda a la página web y haga clic en **Acceder**.
2. Introduzca sus credenciales (ej. `paciente_mario` / `password123`).
3. En su **Panel Personal**, podrá visualizar un listado claro de sus próximas citas confirmadas, mostrando fecha, hora, especialista y centro médico.

### 2.2. Solicitar una Nueva Cita
El sistema guía al paciente para evitar errores en la reserva.
1. Haga clic en la sección **"Solicitar Cita"**.
2. Rellene los filtros en orden: seleccione la **Especialidad**, luego el **Centro Médico** y, finalmente, el **Médico**.
3. El sistema cargará los huecos reales disponibles. Elija el que mejor le convenga y confirme.
4. **Sistema Anti-Solapamientos:** Por su seguridad, el sistema le impedirá reservar una cita si usted ya tiene otra cita médica programada exactamente para el mismo día (Regla de Inmutabilidad). En ese caso, la pantalla mostrará un aviso bloqueando la operación.

### 2.3. El Motor Inteligente: Recibir una Propuesta de Adelanto
Si usted tiene una cita lejana, pero otro paciente cancela la suya para mañana, el **Motor del Hospital** podría elegirle a usted para heredar ese hueco (basándose en su urgencia y tiempo de espera). 
Si es seleccionado, el sistema le notificará por dos vías simultáneas:

* **Vía Correo Electrónico:** Recibirá un email detallado en su teléfono móvil con los datos de la nueva cita propuesta. Este correo contiene botones seguros para que pueda contestar directamente sin necesidad de entrar a la web.
* **Vía Intranet (Web):** Si entra a su Panel Personal, verá una **Alerta Visual Verde** (Panel de Notificaciones) destacada en la parte superior, informándole de la disponibilidad del hueco.

### 2.4. Responder a la Propuesta (Aceptar o Rechazar)
Cuando reciba una propuesta, tendrá 3 opciones:
1. **Aceptar Adelanto:** Al hacer clic en este botón (en el correo o en la web), su cita original se actualizará automáticamente a la nueva fecha más cercana. La alerta desaparecerá.
2. **Rechazar:** Si el nuevo horario no le viene bien, al pulsar "Rechazar", usted conservará su cita original intacta. El sistema pasará al siguiente paciente de la lista de espera (Efecto Cascada).
3. **Ignorar (Expiración):** Las propuestas tienen un tiempo de validez (ej. 24 horas). Si usted no responde en ese plazo, la propuesta caducará para no bloquear el hueco del hospital, y el sistema buscará a otro paciente automáticamente.

---

## 💼 3. GUÍA DEL PERSONAL ADMINISTRATIVO

El personal administrativo gestiona la configuración del motor y el estado de las agendas médicas desde el panel de control.

### 3.1. Acceso al Panel de Control
1. Diríjase a la ruta de administración: `https://tfgmarreyapr.pythonanywhere.com/admin/`
2. Inicie sesión con su usuario Administrador.

### 3.2. Gestión de Agendas y Disparo del Algoritmo
El algoritmo es completamente invisible y autónomo. El personal administrativo solo tiene que hacer su trabajo habitual:
1. En el menú, diríjase a la tabla de **Citas**.
2. Si un paciente llama para avisar de que no puede asistir, busque su cita.
3. Cambie el campo **Estado** de *Confirmada* a **Cancelada**.
4. Haga clic en **Guardar**.
5. **Resultado:** En el instante en el que usted guarda, el sistema detecta la cancelación, evalúa a todos los pacientes futuros de ese mismo médico, elige al más idóneo y le envía el correo de adelanto automáticamente.

### 3.3. Configuración de los Pesos del Algoritmo
La gerencia del hospital tiene el control total sobre "quién gana" los huecos libres.
1. Diríjase a la sección **Configuración Reasignación**.
2. Aquí podrá ajustar matemáticamente las prioridades del hospital modificando tres valores:
   * **Peso Urgencia:** Puntos otorgados a pacientes con cuadros clínicos más graves.
   * **Peso Turno:** Puntos otorgados si el paciente prefiere acudir en el mismo turno (mañana/tarde) en el que se ha liberado el hueco.
   * **Peso Antigüedad:** Recompensa a los pacientes que llevan más días en la lista de espera.
3. Guarde los cambios. El algoritmo usará estas nuevas reglas en la siguiente cancelación.

### 3.4. Auditoría de Propuestas (El Historial)
En la sección **Propuestas Reasignación**, el administrativo puede ver un registro histórico de todas las ofertas que ha hecho el motor, sabiendo en todo momento qué pacientes han aceptado, cuáles han rechazado y a qué hora caducan las ofertas pendientes.

---

## 🩺 4. GUÍA DEL MÉDICO

Los médicos disponen de una interfaz libre de distracciones, enfocada únicamente en su labor asistencial.

### 4.1. Visualización de la Agenda Diaria
1. Acceda a la plataforma e inicie sesión con una cuenta de médico (ej. `medico_pablo`).
2. El sistema lo enrutará automáticamente a su **Dashboard Clínico**.
3. Desde aquí, el médico puede visualizar su agenda de pacientes programados para los próximos días, reflejando siempre el estado real después de las reasignaciones automáticas que haya hecho el sistema.

---

## 🩺 5. INFORME CLÍNICO Y VALIDACIÓN POR QR

Para garantizar la seguridad de sus datos y evitar el fraude en recetas, el sistema utiliza tecnología de sellado digital.

### 5.1. Descarga de su Receta/Informe
Tras su consulta, usted puede descargar su informe médico en formato PDF desde su Panel Personal. Este documento incluye el diagnóstico, el plan de tratamiento y la medicación prescrita.

### 5.2. ¿Cómo funciona el Código QR?
En la parte inferior de cada receta encontrará un **Código QR**. Este código permite a cualquier farmacia o centro sanitario verificar que el documento es auténtico.
1. No es necesario que el farmacéutico tenga acceso a su cuenta.
2. Al escanear el código, se abrirá una ventana de validación en el servidor oficial del hospital confirmando los datos de la receta.
3. Esto protege su salud asegurando que solo se le suministre la medicación exacta prescrita por su médico.

---
*Manual Actualizado para la Defensa Final (Abril 2026).*