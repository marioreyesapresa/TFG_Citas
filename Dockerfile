# 1. Usar una base de Python ligera
FROM python:3.12-slim

# 2. Evitar archivos .pyc y permitir logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Directorio de trabajo
WORKDIR /app

# 4. Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. Copiar dependencias e instalarlas
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copiar el resto del código
COPY . /app/

# 7. Recopilar estáticos
RUN python manage.py collectstatic --noinput

# 8. Comando de arranque: Migrar DB y encender Gunicorn
CMD sh -c "python manage.py migrate && gunicorn --bind 0.0.0.0:8080 core.wsgi:application"