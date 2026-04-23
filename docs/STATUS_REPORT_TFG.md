# Informe de Estado Global (Status Report) - Plataforma de Gestión de Citas Médicas

**Fecha:** 22 de Abril de 2026
**Elaborado por:** Dirección Técnica (Mario Reyes / CTO)
**Para:** Consultoría Externa / Auditoría TFG

---

## 1. Arquitectura de Sistemas y Base de Datos

El sistema está construido sobre el framework **Django (Python)**, apoyándose en su ORM nativo y empleando *SQLite* como motor de persistencia transaccional. El modelado de datos ha evolucionado para incluir campos de control de flujo como `nivel_cascada` y sistemas de verificación de integridad documental.

## 2. Modularidad y Patrones de Diseño

El ecosistema hace uso intensivo del patrón **MVT (Model-View-Template)**. Se ha consolidado una arquitectura basada en **Roles y Privilegios** (RBAC) robusta.
*   **Desacoplamiento Front/Back:** Segregación total de lógicas en la carpeta `views/` y `forms/`.
*   **Resiliencia en Comunicaciones:** El envío de correos vía SMTP (Gmail) está desacoplado del flujo principal para evitar fallos por latencia de red.

## 3. Hitos Clave Conseguidos (Abril 2026)

### 3.1. Motor de Reasignación Inteligente con Circuit Breaker
El algoritmo de reasignación en cascada es ahora 100% estable. Se ha implementado un mecanismo de **Circuit Breaker** que limita las reacciones en cadena a un máximo de 5 niveles, protegiendo el rendimiento del servidor y evitando bucles infinitos.

### 3.2. Validación Documental mediante Código QR ("Modo Dios")
Se ha profesionalizado el módulo clínico con la generación de recetas en PDF que incluyen un **Código QR de validación pública**. Este sistema permite a terceros (farmacias) verificar la autenticidad del documento directamente contra el servidor, eliminando el riesgo de fraude.

### 3.3. Aseguramiento de la Calidad (Testing > 90%)
Se ha alcanzado una **cobertura de código superior al 90%** mediante una suite de pruebas exhaustiva que incluye:
*   Pruebas unitarias de lógica algorítmica.
*   Pruebas de integración de vistas y control de acceso (RBAC).
*   Pruebas de validación de formularios y estados de base de datos.

## 4. Interfaz y Experiencia de Usuario (UI / UX)

*   **Responsive Design:** La plataforma es plenamente funcional en dispositivos móviles.
*   **Aceptación "One-Click":** El flujo de reasignación permite al paciente aceptar propuestas de adelanto directamente desde su correo electrónico sin fricciones.

## 5. Próximos Pasos (Defensa Final)

1.  **Ensayo de Defensa:** Preparación de la demo en vivo utilizando el script de poblado de base de datos para mostrar el efecto cascada en directo.
2.  **Cierre de Documentación:** Consolidación de la memoria final integrando los nuevos capítulos de Testing, Seguridad y Problemas/Soluciones.
3.  **Despliegue Final:** Verificación de las variables de entorno en el servidor de producción (PythonAnywhere).
sola) de cara a la defensa final o demostración del prototipo.
