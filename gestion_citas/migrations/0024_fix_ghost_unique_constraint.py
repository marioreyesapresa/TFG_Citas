from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('gestion_citas', '0023_alter_propuestareasignacion_hueco'),
    ]

    operations = [
        # 1. Eliminamos la restricción UniqueConstraint que depende de 'hueco'
        migrations.RemoveConstraint(
            model_name='propuestareasignacion',
            name='unique_pending_propuesta_per_hueco',
        ),
        # 2. Eliminamos el campo para limpiar cualquier índice UNIQUE en la BD
        migrations.RemoveField(
            model_name='propuestareasignacion',
            name='hueco',
        ),
        # 3. Lo volvemos a crear como ForeignKey pura (sin unicidad)
        migrations.AddField(
            model_name='propuestareasignacion',
            name='hueco',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='es_propuesta_de', to='gestion_citas.cita'),
        ),
        # 4. Volvemos a añadir la restricción condicional (que SÍ queremos)
        migrations.AddConstraint(
            model_name='propuestareasignacion',
            constraint=models.UniqueConstraint(condition=models.Q(('estado', 'PENDIENTE')), fields=('hueco',), name='unique_pending_propuesta_per_hueco'),
        ),
    ]
