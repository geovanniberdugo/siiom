# Generated by Django 2.2.13 on 2020-06-13 18:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('grupos', '0001_initial'),
        ('miembros', '0001_initial'),
        ('encuentros', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='encuentro',
            name='coordinador',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='encuentros_coordinador', to='miembros.Miembro', verbose_name='Coordinador'),
        ),
        migrations.AddField(
            model_name='encuentro',
            name='grupos',
            field=models.ManyToManyField(to='grupos.Grupo', verbose_name='Grupos'),
        ),
        migrations.AddField(
            model_name='encuentro',
            name='tesorero',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='encuentros_tesorero', to='miembros.Miembro', verbose_name='Tesorero'),
        ),
        migrations.AddField(
            model_name='encontrista',
            name='encuentro',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='encuentros.Encuentro', verbose_name='Encuentro'),
        ),
        migrations.AddField(
            model_name='encontrista',
            name='grupo',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='encontristas', to='grupos.Grupo', verbose_name='Grupo'),
        ),
    ]
