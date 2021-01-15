# Generated by Django 2.2.13 on 2020-06-13 18:35

from django.db import migrations, models
import django.db.models.deletion
import pqr.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('organizacional', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Caso',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_acontecimiento', models.DateField(blank=True, null=True, verbose_name='fecha acontecimiento')),
                ('nombre', models.CharField(max_length=255, verbose_name='nombre')),
                ('identificacion', models.BigIntegerField(verbose_name='identificación')),
                ('direccion', models.CharField(blank=True, max_length=255, verbose_name='dirección')),
                ('telefono', models.BigIntegerField(verbose_name='teléfono')),
                ('email', models.EmailField(max_length=254, verbose_name='email')),
                ('descripcion', models.TextField(verbose_name='descripción')),
                ('asunto', models.CharField(max_length=255, verbose_name='asunto')),
                ('fecha_registro', models.DateTimeField(auto_now_add=True, verbose_name='fecha registro')),
                ('cerrado', models.BooleanField(default=False, verbose_name='cerrado')),
                ('llave', models.SlugField(verbose_name='llave')),
                ('valido', models.BooleanField(default=False, verbose_name='valido')),
                ('fecha_ingreso_habil', models.DateField(blank=True, null=True, verbose_name='fecha ingreso hábil')),
                ('empleado_cargo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='casos_cargo', to='organizacional.Empleado', verbose_name='empleado a cargo')),
                ('integrantes', models.ManyToManyField(blank=True, related_name='casos_implicado', to='organizacional.Empleado', verbose_name='integrantes')),
            ],
            options={
                'verbose_name': 'Caso PQR',
                'verbose_name_plural': 'Casos PQR',
            },
        ),
        migrations.CreateModel(
            name='Invitacion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mensaje', models.TextField(verbose_name='mensaje')),
                ('fecha', models.DateTimeField(auto_now_add=True, verbose_name='fecha')),
                ('caso', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pqr.Caso', verbose_name='caso')),
                ('emisor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invitaciones_realizadas', to='organizacional.Empleado', verbose_name='emisor')),
                ('receptor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invitaciones_recibidas', to='organizacional.Empleado', verbose_name='receptor')),
            ],
            options={
                'verbose_name': 'Invitación',
                'verbose_name_plural': 'Invitaciones',
            },
        ),
        migrations.CreateModel(
            name='Documento',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('archivo', models.FileField(upload_to=pqr.models.Documento.ruta_archivo, verbose_name='Archivo')),
                ('caso', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documentos', to='pqr.Caso', verbose_name='Caso')),
            ],
        ),
        migrations.CreateModel(
            name='Comentario',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mensaje', models.TextField(verbose_name='mensaje')),
                ('fecha', models.DateTimeField(auto_now_add=True, verbose_name='fecha')),
                ('importante', models.BooleanField(default=False, verbose_name='importante')),
                ('documento', models.BooleanField(default=False, verbose_name='documento')),
                ('caso', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pqr.Caso', verbose_name='caso')),
                ('empleado', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='organizacional.Empleado', verbose_name='empleado')),
            ],
        ),
    ]
