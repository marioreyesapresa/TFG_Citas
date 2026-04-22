#!/bin/bash

# Script de automatización de Testing y Cobertura (TFG)

echo "🚀 Iniciando suite de pruebas blindada..."

# 1. Limpiar reportes anteriores
rm -rf htmlcov
rm -f .coverage

# 2. Ejecutar tests con cobertura
# Usamos el archivo .coveragerc configurado
./env/bin/python3 -m coverage run manage.py test gestion_citas.tests

# 3. Generar reporte consola
echo -e "\n📊 Resumen de Cobertura de Negocio:"
./env/bin/python3 -m coverage report

# 4. Generar reporte HTML
echo -e "\n✨ Generando reporte HTML en carpeta 'htmlcov'..."
./env/bin/python3 -m coverage html

echo "✅ Proceso finalizado."
echo "👉 Abre 'htmlcov/index.html' en tu navegador para ver el detalle y tomar capturas."
