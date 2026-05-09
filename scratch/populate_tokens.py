import os
import sys
import django
import uuid

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from gestion_citas.models import PropuestaReasignacion

for p in PropuestaReasignacion.objects.filter(token_respuesta__isnull=True):
    p.token_respuesta = uuid.uuid4()
    p.save()
    print(f"Propuesta {p.id} actualizada con token.")

# Also update existing ones that might have shared the same default (if any)
all_tokens = set()
for p in PropuestaReasignacion.objects.all():
    if p.token_respuesta in all_tokens:
        p.token_respuesta = uuid.uuid4()
        p.save()
        print(f"Propuesta {p.id} (duplicada) actualizada con nuevo token.")
    all_tokens.add(p.token_respuesta)

print("Actualización de tokens finalizada.")
