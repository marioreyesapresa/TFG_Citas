# Informe de Estado Global (Status Report) - Plataforma de Gestión de Citas Médicas

**Fecha:** 18 de Marzo de 2026
**Elaborado por:** Dirección Técnica (Mario Reyes / CTO)
**Para:** Consultoría Externa / Auditoría TFG

---

## 1. Arquitectura de Sistemas y Base de Datos

El sistema está construido sobre el framework **Django (Python)**, apoyándose en su ORM nativo y empleando *SQLite* como motor de persistencia transaccional (ideal para el contexto del prototipo del TFG). 

El modelado de datos (`models.py`) está altamente normalizado y define una estructura relacional robusta que soporta toda la lógica de negocio:
*   **Entidades Core:** `Centro`, `Especialidad`.
*   **Gestión de Identidad (RBAC):** Extensión del modelo `auth.User` mediante relaciones `OneToOne` para consolidar tres perfiles o roles distintos: `Paciente` (con preferencias horarias), `Medico` (con números de colegiado, adscrito a centros y especialidades) y `Administrativo`.
*   **Inventario Térmico (Disponibilidad):** La entidad `HorarioMedico` define las franjas operativas semanales protegidas por restricciones `unique_together` e inflexiones a nivel de validación (`clean()`) para garantizar congruencia en bloques de 30 minutos.
*   **Entidades Transaccionales:** La `Cita` como unidad de negocio primaria. La `PropuestaReasignacion`, que modela el estado temporal de una propuesta de adelanto de cita (TTL constraints) y `Notificacion`, para el sistema de alertas.

Además, el entorno cuenta con la herramienta de *seeding* o *mocking* custom (`poblar_bd.py`) en formato de *Management Command* de Django, permitiendo levantar entornos pre-poblados para testing en segundos.

## 2. Modularidad y Patrones de Diseño

El ecosistema hace uso intensivo del patrón arquitectónico **MVT (Model-View-Template)** dictado por Django. Todo el paradigma está pivotando a una arquitectura basada en **Roles y Privilegios**, factor esencial en el sector de saludo (Healthcare Tech).

Recientemente, el código base ha sido sometido a un *Refactoring* estructural separando responsabilidades:
*   **Desacoplamiento Front/Back:** Segregación de lógicas para Pacientes, Médicos y Administradores en diferentes módulos de vistas (`views/paciente.py`, `views/medico.py`, etc.) y formularios (`forms/paciente.py`).
*   **Inyección de Ajax:** Uso de asincronía (JS Fetch/AJAX) para dependencias en cascada en los formularios front-end (Carga de Centros -> Especialidad -> Médicos -> Horas libres de `HorarioMedico`).

## 3. Lógica Core: Motor Algorítmico en Cascada

El cerebro y valor diferencial de la plataforma recae en el `Motor de Reasignación en Cascada` (`algoritmo_reasignacion.py`). Es un sistema determinista disparado mediante *Event-Driven Architecture* (sobre el método `save()` al detectar una cancelación).

El algoritmo implementa un sistema de validación restrictivo (Hard Constraints) para colisiones (Inmutabilidad Diaria - Regla D) y prevención de Infinite Loops por rechazos pasados (Regla E.1 y E.2). Simultáneamente, categoriza a los pacientes futuros aptos según un `Scoring` paramétrico inyectable desde base de datos (`ConfiguracionReasignacion`), sumando pesos por Urgencia, Coincidencia de Turnos y Días en Espera. Si un paciente rechaza un adelanto de forma explícita, el Motor implementa recursividad (Cascada), auto-evaluando en background y asignando iterativamente al siguiente nodo de la lista.

## 4. Interfaz y Experiencia de Usuario (UI / UX)

El *Front-end* está operativo y distingue funcionalmente a los consumidores de la plataforma:
*   **Dashboards Contextuales:** Redirecciones directas post-login dependiendo del rol autenticado.
*   **Panel Paciente:** Visualización del historial clínico (Citas pasadas y futuras). Interfaz de preferencias de usuario donde el paciente configura su preferencia horaria global (Turno M/T) inyectable para el algoritmo.
*   **Alertas Interactivas (Sistema de Notificaciones):** Interfaz para la gestión de notificaciones web (persistencia de lectura) y un flujo UX intuitivo compuesto por botones interactivos asíncronos para **Aceptar** o **Rechazar** propuestas de reasignación generadas por el Motor.
*   **Gestión Administrativa:** Apoyo en plantillas adaptadas como "Jazzmin" para el panel de administración core y selectores estáticos condicionados (JS nativo) para blindar la entrada de datos erróneos de administrativos y médicos.

## 5. Próximos Pasos (Next Sprint Roadmap)

De acuerdo al análisis de las ramas y estado del código `HEAD` actual, el sistema es altamente funcional y estable, pero adolece de la finalización de los siguientes *Epics* preventivos para considerarse un producto 100% finalizado (Ready for QA):

1.  **Expiración Automática de Propuestas (Cron Jobs / TTL):**
    *   *Bloqueante:* Hemos construido el esquema y el parámetro `fecha_limite` (24 horas) para que el paciente acepte el correo. Sin embargo, nos falta el *worker* en segundo plano o *Cron Job* que revise qué propuestas no han sido respondidas en el plazo de vida, las marque en estado *EXPIRADA* (TTL alcanzado) y active obligatoriamente el descenso de la cascada para no perder el hueco liberado.
2.  **Integración Continua de Ramas (Merge de Refactor):** 
    *   *Operativo:* Sincronizar y hacer *Merge* oficial de la rama de refactorización visual (directorios y plantillas) con la rama actual que contiene la lógica en cascada del algoritmo (*feature/reasignacion-cascada*), resolviendo posibles conflictos de estructura de directorios (`views.py` vs *folder* `views/`).
3.  **Configuración de Producción:**
    *   *Técnico:* Configurar el verdadero credencialismo de SMTP en `core/settings.py` para levantar un servidor de envíos real (sustituyendo el de consola) de cara a la defensa final o demostración del prototipo.
