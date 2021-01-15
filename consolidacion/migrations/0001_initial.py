# Generated by Django 2.2.13 on 2020-06-13 18:35

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Visita',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('primer_nombre', models.CharField(max_length=255, verbose_name='primer nombre')),
                ('segundo_nombre', models.CharField(blank=True, max_length=255, verbose_name='segundo nombre')),
                ('primer_apellido', models.CharField(max_length=255, verbose_name='primer apellido')),
                ('segundo_apellido', models.CharField(blank=True, max_length=255, verbose_name='segundo apellido')),
                ('direccion', models.CharField(blank=True, max_length=255, verbose_name='dirección')),
                ('telefono', models.BigIntegerField(verbose_name='teléfono')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email')),
                ('fecha_ingreso', models.DateField(auto_now_add=True, verbose_name='fecha ingreso')),
                ('genero', models.CharField(choices=[('M', 'MASCULINO'), ('F', 'FEMENINO')], max_length=1, verbose_name='género')),
                ('retirado', models.BooleanField(default=False, verbose_name='retirado')),
                ('edad', models.CharField(blank=True, max_length=50, verbose_name='edad')),
                ('estado_civil', models.CharField(blank=True, choices=[('V', 'Viudo'), ('C', 'Casado'), ('S', 'Soltero'), ('D', 'Divorciado')], max_length=1, verbose_name='estado civil')),
            ],
        ),
    ]