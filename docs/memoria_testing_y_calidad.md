# Aseguramiento de la Calidad (QA) y Estrategia de Testing

En el desarrollo de un software sanitario que gestiona agendas médicas y procesa datos clínicos, la tolerancia a fallos debe ser mínima. Un error en la asignación podría resultar en la pérdida de una cita médica crítica. Por ello, el proyecto se ha construido sobre una sólida arquitectura de pruebas automatizadas (*Testing*), alcanzando una cobertura de código sobresaliente (superior al 90%).

Este documento detalla la estrategia de validación, la taxonomía de las pruebas diseñadas y las metodologías empleadas para garantizar la máxima fiabilidad del sistema.

---

## 1. La Estrategia Global de Testing

La meta no era simplemente alcanzar un porcentaje alto de cobertura (*Coverage*) por cumplir un requisito académico, sino establecer una malla de seguridad que permitiera evolucionar el código (añadir nuevas funcionalidades o refactorizar) sin miedo a introducir "regresiones" (romper algo que ya funcionaba).

Para lograrlo, la suite de pruebas se diseñó cubriendo todo el espectro de la aplicación, desde la validación del dato más básico en la base de datos, hasta la simulación del comportamiento de un usuario navegando por la web.

## 2. Arquitectura de las Pruebas (Taxonomía)

El sistema de pruebas se dividió estratégicamente en módulos independientes para facilitar la trazabilidad de los errores:

### 2.1. Pruebas de Lógica de Negocio y Algoritmia (Domain Logic)
Este es el núcleo duro del sistema y donde se concentra el mayor esfuerzo de testing. Las pruebas de lógica (`test_logic.py`, `test_logic_domain.py`) no prueban botones ni colores, prueban matemáticas y toma de decisiones.
*   **Pruebas del Motor de Reasignación:** Se crearon decenas de escenarios simulados (Mocks). Por ejemplo, se inyectan virtualmente 10 pacientes en la lista de espera con diferentes combinaciones de Urgencia, Antigüedad y Turno. La prueba ejecuta el algoritmo y afirma (*assert*) que el paciente seleccionado por el Motor coincide exactamente con el que la ética médica y matemática dictan que debe ser elegido.
*   **Pruebas de Estrés y Límites:** Se validó el comportamiento del "Efecto Cascada" y se comprobó explícitamente que el *Circuit Breaker* detiene el bucle al alcanzar el límite máximo de saltos, asegurando la estabilidad del servidor.

### 2.2. Pruebas de Modelos e Integridad de Datos (Data Layer)
Antes de procesar nada, la base de datos debe ser robusta. Las pruebas de modelos (`test_models.py`) aseguran:
*   Que los campos requeridos no aceptan valores nulos.
*   Que los estados de las citas ("Pendiente", "Aceptada", "Expirada") transicionan de manera coherente según la máquina de estados definida.
*   Que los valores por defecto (como el nivel de cascada inicial a 0) se aplican correctamente al crear un registro nuevo.

### 2.3. Pruebas de Formularios y Validación de Entrada
Nunca se debe confiar en los datos introducidos por el usuario. Las pruebas de formularios (`test_forms.py`) comprueban el muro de contención de la aplicación:
*   Se inyectan intencionadamente datos incorrectos: fechas en el pasado, formatos de correo inválidos, o intentos de solicitar citas para especialidades inexistentes.
*   La prueba se considera "exitosa" solo si el sistema detecta el fraude, bloquea la acción y devuelve el mensaje de error adecuado al usuario.

### 2.4. Pruebas de Vistas, Integración y Seguridad (End-to-End)
Estas pruebas (`test_views_paciente.py`, `test_views_clinico.py`) simulan el ciclo de vida completo emulando peticiones HTTP (GET, POST):
*   **Simulación de Flujos:** Verifican que si un paciente envía una petición POST para cancelar su cita, el sistema no solo actualiza la base de datos, sino que redirige correctamente a la pantalla de éxito.
*   **Control de Acceso (RBAC - Role-Based Access Control):** Pruebas críticas de seguridad. Se emula el inicio de sesión de un Paciente y se intenta acceder por la fuerza a las URL del panel del Médico o del Administrativo. La prueba verifica que el servidor rechaza la conexión de inmediato (Acceso Denegado / Redirect), demostrando que la partición de roles es impenetrable.

---

## 3. ¿Cómo se alcanzó la alta Cobertura (Coverage)?

Lograr más de un 90% de código testeado requirió disciplina metodológica y el uso de técnicas avanzadas de ingeniería de software:

1.  **Simulación de Servicios Externos (Mocking):**
    El Motor de Reasignación envía correos a través de Gmail. Si las pruebas enviaran correos reales, el test tardaría minutos en ejecutarse y colapsaría la bandeja de entrada. Para solucionarlo, se utilizó la técnica de *Mocking* (Simulación). El sistema de testing "engaña" al código, reemplazando la función real de envío de correo por una versión "simulada" en memoria. Esto permite probar el flujo completo en milisegundos y afirmar internamente: *"Sí, el sistema ordenó enviar un correo con estos datos"*, sin llegar a conectarse a la red.

2.  **Cobertura de Casos Límite (Edge Cases):**
    Un error común es probar solo el "Camino Feliz" (cuando todo sale bien). La alta cobertura se consiguió programando pruebas específicas para cuando las cosas salen mal:
    *   ¿Qué pasa si el Motor intenta buscar candidatos, pero la lista de espera está vacía?
    *   ¿Qué pasa si hay un empate perfecto a puntos entre dos pacientes?
    *   ¿Qué pasa si el código QR escaneado es falso o ha caducado?
    Al escribir código de prueba para todos los caminos alternativos y excepciones, el índice de cobertura se eleva cubriendo las "zonas oscuras" del software.

3.  **Auditoría de Cobertura Continua:**
    Se implementaron herramientas de reporte automático (Coverage HTML Reports). Tras cada sesión de programación, la herramienta escaneaba el código y generaba un mapa visual (en verde el código testeado, en rojo el código sin probar). Esto permitió una aproximación quirúrgica, identificando exactamente qué ramas condicionales (`if/else`) habían quedado huérfanas de testing para escribir pruebas dirigidas a ellas.

## Conclusión

El esfuerzo invertido en la creación de esta suite de pruebas garantiza que el Motor de Reasignación es un producto de software de grado profesional. Demuestra que no solo se ha escrito código que "funciona" en condiciones ideales, sino que se ha validado rigurosamente su comportamiento ante anomalías, ataques y estrés, asegurando su viabilidad real para ser desplegado en un entorno sanitario en producción.
