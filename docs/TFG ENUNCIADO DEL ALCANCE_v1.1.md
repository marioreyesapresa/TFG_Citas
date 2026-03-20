

| PROYECTO | Actualización de citas médicas | FECHA DE ELABORACIÓN | 27/11/2025 |
| :---: | :---- | :---: | :---: |

**ENUNCIADO DEL ALCANCE DEL PROYECTO**

| Este proyecto consiste en el diseño, desarrollo e implementación de una aplicación web para la gestión de citas médicas en un centro sanitario. La característica central es un mecanismo de reasignación automática que, ante una cancelación, optimiza la ocupación de huecos libres evaluando criterios como el nivel de urgencia, preferencia horaria y la inmutabilidad de citas en el mismo día. |
| :---- |

**ENTREGABLES DEL PROYECTO**

| E1: Producto Software  Sistema web funcional con roles (paciente, médico, administrador) que permite la gestión CRUD de citas y ejecuta el algoritmo de reasignación automática. |
| :---- |
| E2: Memoria del TFG Documento académico que incluye la justificación metodológica, análisis de requisitos, diseño técnico, pruebas y conclusiones del proyecto. |
| E3: Presentación y Defensa Material de apoyo visual para la exposición oral ante el tribunal evaluador. |

**SUPUESTOS DEL PROYECTO**

| Se asume que todos los roles del sistema (paciente, médico, administrador) están definidos conceptualmente y no requieren validación externa. |
| :---- |
| Los datos utilizados para las pruebas serán simulados; no se utilizará información real de pacientes. |
| Se cuenta con acceso a las herramientas de desarrollo necesarias (Python/Django o Spring Boot, Git, etc.). |
| El tutor académico colaborará en la supervisión y validación de los entregables. |
| La lógica de "urgencia médica" se basará en parámetros predefinidos en el sistema y no en diagnósticos reales. |

**EXCLUSIONES DEL PROYECTO**

| No se incluirá el mantenimiento de la plataforma una vez defendido el TFG. |
| :---- |
| No se realizará integración con sistemas sanitarios reales. |
| No se utilizarán datos personales reales. |
| No se implementarán funcionalidades de Inteligencia Artificial avanzada para la predicción; el algoritmo se basará en reglas lógicas deterministas. |
| No se integrarán pasarelas de SMS o mensajería real (se simularán las notificaciones por correo o log de sistema). |

**RESTRICCIONES DEL PROYECTO**

| El proyecto debe completarse estrictamente dentro de los plazos académicos establecidos por la Universidad de Sevilla para la convocatoria del TFG. |
| :---- |
| El alcance está limitado a un prototipo funcional académico, no un producto comercial final. |

**CRITERIOS DE ACEPTACIÓN**

| El sistema web debe permitir la gestión completa (crear, modificar, cancelar) de citas por parte de los usuarios. |
| :---- |
| El algoritmo de reasignación debe cumplir las reglas de prioridad (urgencia) y preferencias (mañana/tarde) sin errores lógicos. |
| El sistema debe demostrar, mediante simulación, que es capaz de reasignar correctamente una cita cancelada en al menos tres escenarios de prueba distintos. |
| La memoria debe cumplir con los estándares de formato y contenido exigidos por la normativa de la Universidad de Sevilla. |

