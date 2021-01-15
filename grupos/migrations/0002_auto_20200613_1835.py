# Generated by Django 2.2.13 on 2020-06-13 18:35

from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('grupos', '0001_initial'),
        ('miembros', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='predica',
            name='miembro',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='miembros.Miembro'),
        ),
        migrations.AddField(
            model_name='historialestado',
            name='grupo',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='historiales', to='grupos.Grupo', verbose_name='grupo'),
        ),
        migrations.AddField(
            model_name='grupo',
            name='barrio',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='miembros.Barrio', verbose_name='barrio'),
        ),
        migrations.AddField(
            model_name='grupo',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='children_set', to='grupos.Grupo', verbose_name='grupo origen'),
        ),
        migrations.AddField(
            model_name='grupo',
            name='red',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='grupos.Red', verbose_name='red'),
        ),
        migrations.AddField(
            model_name='enseñanza',
            name='creado_por',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enseñanzas_creadas', to='miembros.Miembro'),
        ),
        migrations.AddField(
            model_name='asistenciadiscipulado',
            name='miembro',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='discipulados', to='miembros.Miembro'),
        ),
        migrations.AddField(
            model_name='asistenciadiscipulado',
            name='reunion',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='asistencia', to='grupos.ReunionDiscipulado'),
        ),
        migrations.CreateModel(
            name='GrupoTree',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('grupos.grupo',),
            managers=[
                ('_objects', django.db.models.manager.Manager()),
            ],
        ),
    ]
