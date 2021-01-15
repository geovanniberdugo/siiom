# Generated by Django 2.2.13 on 2020-06-13 18:35

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Encontrista',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('primer_nombre', models.CharField(max_length=60, verbose_name='Primer Nombre')),
                ('segundo_nombre', models.CharField(blank=True, max_length=60, verbose_name='Segundo Nombre')),
                ('primer_apellido', models.CharField(max_length=60, verbose_name='Primer Apellido')),
                ('segundo_apellido', models.CharField(blank=True, max_length=60, verbose_name='Segundo Apellido')),
                ('talla', models.CharField(blank=True, max_length=3, verbose_name='Talla')),
                ('genero', models.CharField(choices=[('M', 'MASCULINO'), ('F', 'FEMENINO')], max_length=1, verbose_name='Género')),
                ('identificacion', models.BigIntegerField(verbose_name='Identificación')),
                ('email', models.EmailField(max_length=254, verbose_name='Email')),
                ('asistio', models.BooleanField(default=False, verbose_name='Asistio')),
            ],
        ),
        migrations.CreateModel(
            name='Encuentro',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_inicial', models.DateTimeField(verbose_name='Fecha Inicial')),
                ('fecha_final', models.DateField(verbose_name='Fecha Final')),
                ('hotel', models.CharField(max_length=100, verbose_name='Hotel')),
                ('direccion', models.CharField(blank=True, max_length=100, verbose_name='Direccion')),
                ('observaciones', models.TextField(blank=True, verbose_name='Observaciones')),
                ('dificultades', models.TextField(blank=True, verbose_name='Dificultades')),
                ('estado', models.CharField(choices=[('A', 'ACTIVO'), ('I', 'INACTIVO')], default='A', max_length=1, verbose_name='Estado')),
            ],
        ),
    ]