# Generated by Django 2.2.13 on 2020-06-13 18:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('grupos', '0001_initial'),
        ('consolidacion', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='visita',
            name='grupo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='visitas', to='grupos.Grupo', verbose_name='grupo'),
        ),
    ]