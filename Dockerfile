# 1. Usar una base de Python ligera (Según doc AURA [cite: 223])
FROM python:3.12-slim

# 2. Evitar que Python genere archivos .pyc y permitir logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Crear directorio de trabajo
WORKDIR /app

# 4. Instalar dependencias del sistema necesarias para compilar cosas
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. Copiar dependencias e instalarlas [cite: 225]
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copiar el resto del código [cite: 224]
COPY . /app/

# 7. Recopilar archivos estáticos (para Whitenoise)
RUN python manage.py collectstatic --noinput

# 8. Comando de arranque usando Gunicorn [cite: 226]
# NOTA: Cambia 'gestion_citas_medicas' por el nombre real de tu carpeta de settings
# Según tus archivos parece ser 'gestion_citas' o el nombre de la carpeta principal.
# Si tu wsgi.py está en la carpeta 'gestion_citas', pon: gestion_citas.wsgi:application
# ... (todo lo anterior igual) ...

# 8. Comando de arranque: PRIMERO migra la base de datos, LUEGO arranca Gunicorn
CMD sh -c "python manage.py migrate && gunicorn --bind 0.0.0.0:8080 gestion_citas.wsgi:application"