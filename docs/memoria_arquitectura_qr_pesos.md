# Arquitectura de Integraciones y Lógica Matemática del Motor

Este documento explora en profundidad las decisiones de arquitectura relacionadas con la integración de herramientas externas y desarrolla una valoración exhaustiva sobre la lógica de negocio que rige el sistema de puntuación (Scoring) del Motor de Reasignación.

---

## 1. El Ecosistema de Verificación Externa (Integración QR y "Modo Dios")

La transformación digital en el ámbito sanitario exige que el paso del papel al medio digital no comprometa la seguridad. La emisión de Recetas Clínicas o justificantes de asistencia debía ser inmediata y asíncrona, pero 100% auditable.

### La Lógica de la Doble Vía
Se ha diseñado una arquitectura basada en el principio de la "Doble Vía de Información":
*   **Vía del Paciente (El Soporte Físico/Digital):** El paciente recibe un archivo PDF en su correo electrónico. Este archivo funciona visualmente como una receta tradicional (con el membrete de la clínica, los datos del médico y el diagnóstico). Sin embargo, el sistema asume, por diseño, que este documento es *desconfiable*, puesto que reside en el dispositivo del usuario y es susceptible de manipulación (edición digital del texto).
*   **Vía de Auditoría (La Criptografía y el QR):** El verdadero "documento legal" no es el PDF, sino un registro inmutable alojado en la base de datos del servidor. Para vincular el papel físico con el registro seguro del servidor, el sistema estampa dinámicamente un Código QR en cada PDF.

### El Token Inmutable y el Portal Público
El Código QR generado no contiene texto plano legible (no dice "Paracetamol 500mg"). Contiene una URL parametrizada con un identificador único universal (UUID) o un hash criptográfico.
*   **Valoración Lógica (El "Modo Dios"):** Cuando un actor externo (por ejemplo, el boticario en una farmacia) necesita validar la receta, no necesita instalar ningún software. Simplemente utiliza la cámara de cualquier teléfono móvil estándar para escanear el QR.
*   El escaneo abre un navegador web y accede a un "Portal de Validación Pública" de la clínica. Este portal actúa en "Modo Dios": no requiere inicio de sesión, pero tiene permisos de solo-lectura sobre la tabla de recetas válidas. Muestra en pantalla un "Sello Verde" confirmando la autenticidad del documento y exponiendo los datos médicos reales extraídos directamente del servidor.
*   **Conclusión:** Esta integración traslada la carga de la confianza desde el documento físico hacia la infraestructura del servidor, erradicando cualquier vector de ataque por falsificación y dotando a la clínica de una capa de protección legal absoluta.

---

## 2. El Motor de Comunicaciones Asíncronas (Integración Gmail/SMTP)

Para que el Motor de Reasignación sea verdaderamente proactivo, necesita la capacidad de alcanzar al paciente fuera del ecosistema del portal médico. De nada sirve un algoritmo brillante si el paciente tiene que hacer *login* cada hora para ver si tiene propuestas.

### El Correo como Interfaz de Usuario ("Call to Action")
La integración con el servidor SMTP (utilizando infraestructuras estables como Gmail para el entorno de desarrollo) no se utiliza como un mero tablón de anuncios informativo ("Le informamos que..."). Se ha diseñado para convertir el propio correo electrónico en una extensión de la interfaz de la aplicación.
*   **La Aceptación "One-Click":** Los correos electrónicos enviados contienen enlaces de acción con *tokens* de seguridad de un solo uso incrustados en la URL. 
*   **Valoración Lógica:** Cuando el paciente lee "Tenemos un hueco libre para mañana, pulse aquí para aceptarlo", el clic en el botón envía el *token* de vuelta al servidor. El servidor verifica el *token*, identifica inequívocamente de qué paciente y de qué hueco se trata, y procesa la transacción en la base de datos de manera automática. El usuario nunca tuvo que recordar su contraseña, iniciar sesión, ni navegar por engorrosos menús móviles. La fricción operativa se reduce a prácticamente cero.

---

## 3. Valoración de la Lógica Matemática: El Sistema de Pesos

El cerebro central del sistema huye de arquitecturas de colas tradicionales como FIFO (*First In, First Out*). Utilizar FIFO en medicina es negligente, ya que asume que el orden de llegada es equivalente al nivel de necesidad médica. Por ello, se diseñó una **Cola de Prioridad Ponderada**.

El reto principal fue asignar los pesos porcentuales a cada pilar para asegurar que el sistema tomara decisiones éticas pero también operativamente eficientes.

### 3.1. El Dominio Absoluto: La Urgencia Clínica (Aprox. 60-70% del peso total)
Desde el punto de vista puramente lógico, la Urgencia Clínica debía ser parametrizada no solo como el factor de mayor puntuación, sino con una **distancia matemática insalvable**.
*   **Valoración:** Si la Urgencia Alta suma 1000 puntos y la Urgencia Baja suma 10 puntos, el algoritmo garantiza que un paciente grave **jamás** será desplazado por uno leve. Incluso si el paciente leve lograra la puntuación máxima en los criterios secundarios (Antigüedad y Turno), la suma de esos secundarios nunca alcanzará la diferencia matemática impuesta por la Urgencia. Esto sella el comportamiento ético del motor a nivel de código.

### 3.2. El Desempate Social: Antigüedad en Espera (Aprox. 20-30% del peso total)
Sabiendo que la Urgencia domina el algoritmo, ¿qué ocurre cuando el sistema se enfrenta a decenas de pacientes con exactamente el **mismo nivel** de gravedad clínica?
*   **Valoración:** Aquí es donde interviene la lógica de la "justicia social". La antigüedad funciona como un medidor de fricción acumulada. Entre dos perfiles médicamente idénticos, la lógica matemática inclina la balanza hacia la persona que lleva más tiempo en lista de espera, penalizando el retraso e impidiendo que una solicitud antigua quede crónicamente estancada por la entrada continua de nuevos pacientes.

### 3.3. El Acelerador Operativo: Continuidad de Turno (Aprox. 10% del peso total)
Este es el componente más estratégico desde el punto de vista del negocio. 
*   **Valoración:** Supongamos un empate clínico y una antigüedad muy similar. El algoritmo de desempate busca ahora la eficiencia pura. Si el hueco liberado es un martes por la mañana a las 10:00 AM, el sistema otorgará este "bonus" de puntuación al paciente que en su histórico demuestra preferencia por los turnos de mañana. 
*   **El impacto:** Al ofrecerle un hueco que se adapta a su rutina de vida, la probabilidad estadística de que el paciente pulse el botón de "Aceptar" en el correo electrónico se dispara. Esto reduce drásticamente los rechazos y minimiza el tiempo de procesamiento, convirtiendo un simple filtro de horario en el principal engrasador del ciclo "One-Click".
