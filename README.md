# Sistema Inteligente de Reasignación de Citas Médicas 

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.1-green.svg)](https://www.djangoproject.com/)
[![Coverage](https://img.shields.io/badge/Coverage-91.79%25-brightgreen.svg)](#)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](#)

Este proyecto es un **Trabajo Fin de Grado (TFG)** desarrollado para optimizar la gestión de agendas médicas mediante un sistema automatizado de reasignación en tiempo real. El núcleo del sistema es el **Motor MRI (Medical Reassignment Intelligence)**, diseñado para eliminar los "huecos fantasma" producidos por cancelaciones de última hora.

## 🚀 Características Principales

- **Motor de Reasignación en Cascada (MRI):** Algoritmo determinista que evalúa candidatos basándose en urgencia médica, antigüedad de la cita y preferencias horarias.
- **Flujo One-Click:** Confirmación de adelanto de cita directamente desde el correo electrónico del paciente.
- **Circuit Breaker:** Protección contra bucles de reasignación infinitos mediante control de profundidad de cascada.
- **Integridad Documental:** Generación de justificantes médicos en PDF con validación de integridad mediante códigos QR y UUIDs.
- **Panel Administrativo Premium:** Interfaz de gestión para personal clínico y administrativo con visualización de métricas de ocupación.

## 🛠️ Stack Tecnológico

- **Backend:** Python 3.12 + Django 5.1
- **Base de Datos:** SQLite (Portabilidad total)
- **Frontend:** Vanilla CSS (Diseño Premium responsivo)
- **Generación PDF:** xhtml2pdf
- **Testing:** Suite de pruebas con cobertura >91%

## 📂 Estructura del Proyecto

```text
├── core/               # Configuración global del proyecto Django
├── gestion_citas/      # Aplicación principal de lógica de negocio
│   ├── algoritmo_reasignacion.py  # Núcleo del Motor MRI
│   ├── models.py       # Modelo de datos y señales (Triggers)
│   ├── views/          # Controladores (Paciente, Médico, Administrativo)
│   └── tests/          # Suite completa de pruebas unitarias e integración
├── templates/          # Interfaz de usuario y plantillas de correo
└── static/             # Recursos estáticos (CSS, JS, Imágenes)
```

## ⚙️ Instalación y Configuración

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/tu-usuario/TFG_Citas.git
   cd TFG_Citas
   ```

2. **Crear entorno virtual e instalar dependencias:**
   ```bash
   python3 -m venv env
   source env/bin/activate  # En Windows: env\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Ejecutar migraciones y servidor:**
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

## 🧪 Testing y Calidad

Para ejecutar la suite de pruebas y generar el informe de cobertura:

```bash
bash run_tests.sh
```

El proyecto mantiene una cobertura del **91.79%**, asegurando la estabilidad de los flujos críticos de reasignación.

---
**Autor:** Mario Reyes Apresa  
**TFG:** Grado en Ingeniería Informática - Ingeniería del Software (Sevilla, 2026)
