

| NOMBRE DEL PROYECTO: | Actualización de citas médicas |
| :---- | :---- |
| **PROPIETARIO DEL PROYECTO:** | Mario Reyes Apresa |
| **DIRECTOR DEL PROYECTO:** | Antonio Jesús Cañete Martín |
| **FECHA DE CREACIÓN:** | 10/11/2025 |
| **ELABORADO POR:** | Mario Reyes Apresa |
| **VERSIÓN DEL DOCUMENTO:** | v1.0 |

**HISTÓRICO DE MODIFICACIONES DEL DOCUMENTO**

| Fecha | Realizada por | Breve descripción de los cambios |
| :---- | :---- | :---- |
| 10/11/2025 | Mario Reyes Apresa | Creada primera versión |

**PROPÓSITO DEL PROYECTO**

| El propósito de este Trabajo Fin de Grado es desarrollar una aplicación web para la gestión de citas médicas en un centro sanitario, incorporando un mecanismo inteligente de reasignación automática que optimice la ocupación de citas ante cancelaciones.El sistema prioriza criterios como el nivel de urgencia, preferencias horarias (mañana/tarde) y la inmutabilidad de citas el mismo día, garantizando una reprogramación eficiente. |
| :---- |

**DESCRIPCIÓN DE ALTO NIVEL DEL PROYECTO, RESULTADO(S)/PRODUCTO(S)**

| Este proyecto consiste en el diseño, desarrollo e implementación de una aplicación web para la gestión y actualización automática de citas médicas en un centro sanitario.El sistema permitirá administrar citas por parte del personal médico y administrativo, y ofrecer a los pacientes una plataforma sencilla para gestionar sus reservas y preferencias horarias. La característica principal del proyecto es el mecanismo de reasignación automática de citas cuando se produce una cancelación. Este motor evaluará diferentes condiciones predefinidas —como el nivel de urgencia del paciente, la preferencia de turno (mañana o tarde) y la no modificación de citas en el mismo día— con el objetivo de optimizar el aprovechamiento de los huecos disponibles y reducir los tiempos de espera. El proyecto se desarrollará siguiendo una metodología de ingeniería del software basada en iteraciones o sprints, aplicando buenas prácticas de análisis de requisitos, diseño, pruebas y documentación técnica. Los principales resultados esperados son: Un sistema web funcional que gestione citas médicas con distintos roles (paciente, médico, administrador). Un módulo de reasignación automática que se activa tras una cancelación y realiza pruebas en varios escenarios simulados. La memoria del Trabajo Fin de Grado, incluyendo la justificación metodológica, el análisis de requisitos, diseño, pruebas y conclusiones. El producto final será una aplicación web plenamente funcional, documentada y trazable, que sirva como demostración de un sistema automatizado de gestión de citas médicas eficiente y equitativo, y como base para futuras mejoras o integraciones en entornos sanitarios reales. |
| :---- |

**EXCLUIDO DEL PROYECTO**

| Quedan fuera del alcance de este proyecto: La integración con sistemas sanitarios reales (bases de datos de pacientes, historiales clínicos o plataformas del Servicio Andaluz de Salud). El uso de datos personales reales; se trabajará con datos simulados o anonimizados para pruebas. El mantenimiento del sistema una vez finalizado el TFG. La implementación de funcionalidades avanzadas de inteligencia artificial o predicción médica (por ejemplo, priorización automática basada en aprendizaje automático). La comunicación telefónica o integración con servicios externos de mensajería más allá del correo electrónico o SMS básico. |
| :---- |

**ENTREGABLES DEL PROYECTO**

| Id | Nombre | Descripción |
| :---- | :---- | :---- |
| E1 | Producto | Sistema web funcional con distintos roles que permite la gestión y reasignación automática de citas médicas.  |
| E2 | Memoria |  Documento final del Trabajo de Fin de Grado que incluye la contextualización del proyecto, planificación, análisis de requisitos, resultados y conclusiones.   |
| E3 | Presentación | Exposición oral apoyada en una presentación visual, donde se resumen los aspectos más relevantes del proyecto y se defienden los resultados ante el tribunal.  |

**OBJETIVOS DEL PROYECTO**

| Id | Objetivo |
| :---- | :---- |
| O1 | Desarrollo de la plataforma web indicada anteriormente. |
| O2 | Diseñar e implementar un algoritmo de reasignación automática que optimice los huecos producidos por cancelaciones. |
| O3 | Mejorar la eficiencia del proceso de atención médica reduciendo tiempos de espera y huecos libres. |
| O4 | Aplicar metodologías de ingeniería del software para el análisis, diseño y desarrollo del sistema. |

**REQUISITOS DE ALTO NIVEL**

| Id | Requisito |
| :---- | :---- |
| R1 | El sistema debe permitir la gestión de usuarios con distintos roles: paciente, médico, administrador. |
| R2 | Los pacientes deben poder crear, consultar, modificar o cancelar sus citas médicas a través de la aplicación web. |
| R3 | El sistema debe generar automáticamente un hueco libre cuando se produzca una cancelación y activar el mecanismo de reasignación. |
| R4 | El algoritmo de reasignación debe tener en cuenta el nivel de urgencia del paciente, su preferencia de turno (mañana/tarde) y la disponibilidad del médico. |
| R5 | El sistema no debe modificar citas ya confirmadas del mismo paciente en un mismo día. |
| R6 | El administrador debe poder configurar los parámetros y prioridades del motor de reasignación (por ejemplo, pesos de urgencia o antigüedad en lista). |
| R7 | Los pacientes deben recibir una notificación (correo electrónico o SMS) cuando se les proponga una cita reasignada. |
| R8 | El paciente podrá aceptar o rechazar la propuesta de reasignación dentro de un tiempo límite (TTL) definido. |
| R9 | El sistema debe permitir la visualización de agendas de citas por parte de médicos y personal administrativo. |
| R10 | El diseño de la interfaz debe ser accesible, responsivo y de uso intuitivo. |
| R11 | Los administrativos podrán crear, modificar y eliminar citas de cualquier paciente o médico dentro de su centro asignado. |
| R12 | El sistema debe ofrecer de forma visual la disponibilidad de citas por especialidad y médico. |
| R13 | Los pacientes podrán filtrar las citas disponibles según especialidad, profesional o turno (mañana/tarde). |
| R14 | El sistema deberá impedir que un paciente tenga dos citas simultáneas o solapadas en el tiempo. |
| R15 | Las notificaciones deberán contener la información esencial: fecha, hora, médico, tipo de cita y enlace para confirmar o rechazar. |
| R16 | El sistema deberá mostrar mensajes de error y confirmación claros, informativos y adaptados al tipo de usuario. |

**CRITERIOS DE ÉXITO**

| \- Producto entregado y aceptado. \- La memoria del TFG ha sido presentada en plazo y cumple con los estándares exigidos por la Universidad de Sevilla. \- El sistema web desarrollado permite la gestión de citas médicas y la reasignación automática conforme a los requisitos establecidos. \- El algoritmo de reasignación cumple las reglas definidas (prioridad por urgencia, respeto de preferencias horarias y no modificación en el mismo día). \- Se ha obtenido evidencia mediante simulaciones de que el sistema reasigna correctamente las citas en, al menos, tres  escenarios de prueba. |
| :---- |

**HITOS CLAVE**

| Hito | Fecha |
| :---- | :---- |
| Inicio del proyecto | 10/11/2025 |
| Reunión kick-off con tutor |  |
| Acta de Constitución Finalizada  |  |
| Definición del Alcance y EDT  |  |
| Planificación del proyecto  |  |
| Fin Sprint 1 |  |
| Fin Sprint 2 |  |
| Fin Sprint 3 |  |
| Entrega Documentación  |  |
| Entrega Presentación |  |

**PRESUPUESTO RESUMIDO**

|  |
| :---- |

**INTERESADOS CLAVE**

| Interesado | Rol |
| :---- | :---- |
| Mario  Reyes Apresa | Jefe de Proyecro |
| Antonio Jesús Cañete Martín | Director del Proyecto |

**SUPUESTOS/RESTRICCIONES DE ALTO NIVEL**

| Supuestos: Se contará con la colaboración del tutor académico para la supervisión del avance del proyecto y la validación de los entregables. El entorno de trabajo proporcionará acceso a las herramientas necesarias para el desarrollo y la documentación del sistema (Visual Studio Code, Python/Django o Spring Boot, GitHub, Canva, etc.). Los datos de prueba serán simulados y representarán escenarios realistas de gestión de citas médicas, sin incluir información personal auténtica. Se asume que todos los roles del sistema (paciente, médico, administrador) estarán definidos conceptualmente. Los requisitos establecidos no sufrirán modificaciones drásticas de alcance durante la duración del TFG. El estudiante dispondrá del tiempo y los recursos tecnológicos necesarios para completar las tareas de desarrollo y documentación. Restricciones: El proyecto deberá desarrollarse dentro del periodo académico del TFG y ajustarse a los plazos establecidos por la Universidad de Sevilla. Se limitará el alcance a la implementación y validación de un prototipo funcional , quedando excluido el mantenimiento o la implantación en un entorno real. El uso de datos personales reales o de sistemas médicos externos no está permitido. Las pruebas del motor de reasignación se limitarán a simulaciones controladas en un entorno local o de prueba, sin conexión con servicios externos reales. |
| :---- |

**NIVEL DE AUTORIDAD DEL DIRECTOR DEL PROYECTO**

| Los directores del proyecto (tutor académico y supervisor empresarial) tienen autoridad para: Aprobar o modificar el enfoque metodológico y los entregables del proyecto dentro del marco académico del TFG. Validar los objetivos, supervisar el progreso y proponer ajustes en caso de desviaciones relevantes respecto al alcance original. Evaluar el desempeño del alumno tanto en lo técnico como en lo profesional, y emitir recomendaciones para la mejora continua durante el desarrollo del trabajo. |
| :---- |

**APROBACIÓN**

| Cargo | Firma | Fecha |
| :---- | :---- | :---- |
| Jefe de Proyecto |  |  |
| Director del Proyecto |  |  |

