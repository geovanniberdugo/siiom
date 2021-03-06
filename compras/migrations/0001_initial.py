# Generated by Django 2.2.13 on 2020-06-13 18:35

import compras.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('organizacional', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Parametros',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dias_habiles', models.PositiveSmallIntegerField(verbose_name='dias hábiles')),
                ('tope_monto', models.PositiveIntegerField(verbose_name='monto tope para presidencia')),
            ],
            options={
                'verbose_name': 'parametro',
                'verbose_name_plural': 'parametros',
            },
        ),
        migrations.CreateModel(
            name='Proveedor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255, verbose_name='nombre')),
                ('identificacion', models.BigIntegerField(verbose_name='identificación')),
                ('codigo', models.CharField(blank=True, max_length=200, verbose_name='código')),
                ('correo', models.EmailField(max_length=254, verbose_name='email')),
                ('telefono', models.IntegerField(blank=True, null=True, verbose_name='teléfono')),
                ('celular', models.IntegerField(blank=True, null=True, verbose_name='celular')),
                ('contacto', models.CharField(blank=True, max_length=255, verbose_name='contacto')),
            ],
            options={
                'verbose_name': 'proveedor',
                'verbose_name_plural': 'proveedores',
            },
        ),
        migrations.CreateModel(
            name='Requisicion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_ingreso', models.DateTimeField(auto_now_add=True, verbose_name='fecha de ingreso')),
                ('observaciones', models.TextField(verbose_name='observaciones')),
                ('asunto', models.CharField(max_length=255, verbose_name='asunto')),
                ('prioridad', models.CharField(choices=[('A', 'ALTA'), ('B', 'MEDIA'), ('C', 'BAJA')], max_length=1, verbose_name='prioridad')),
                ('estado', models.CharField(choices=[('PE', 'PENDIENTE'), ('PR', 'PROCESO'), ('TE', 'TERMINADA'), ('AN', 'RECHAZADA')], default='PE', max_length=2, verbose_name='estado')),
                ('fecha_pago', models.DateField(blank=True, null=True, verbose_name='fecha de pago')),
                ('fecha_termina', models.DateField(blank=True, null=True, verbose_name='fecha terminada')),
                ('form_pago', models.CharField(blank=True, choices=[('E', 'EFECTIVO'), ('C', 'CRÉDITO')], max_length=1, verbose_name='forma de pago')),
                ('estado_pago', models.CharField(blank=True, choices=[('PP', 'PAGO AL PROVEEDOR'), ('AP', 'ANTICIPO AL PROVEEDOR'), ('EP', 'EFECTIVO AL PROVEEDOR')], max_length=2, verbose_name='estado de pago')),
                ('presupuesto_aprobado', models.CharField(blank=True, choices=[('SI', 'SI'), ('ES', 'EN ESPERA')], max_length=2, verbose_name='presupuesto aprobado')),
                ('fecha_solicitud', models.DateField(blank=True, null=True, verbose_name='fecha solicitud recurso')),
                ('fecha_proyeccion', models.DateField(blank=True, null=True, verbose_name='fecha proyección pago')),
                ('empleado', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='organizacional.Empleado', verbose_name='empleado')),
            ],
            options={
                'verbose_name': 'requisición',
                'verbose_name_plural': 'requisiciones',
            },
        ),
        migrations.CreateModel(
            name='Historial',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateTimeField(auto_now_add=True, verbose_name='fecha')),
                ('observacion', models.TextField(blank=True, verbose_name='observación')),
                ('estado', models.CharField(choices=[('A', 'Aprobada'), ('R', 'Rechazada')], max_length=1, verbose_name='estado')),
                ('empleado', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='organizacional.Empleado', verbose_name='empleado')),
                ('requisicion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='compras.Requisicion', verbose_name='requisición')),
            ],
            options={
                'verbose_name': 'historial',
                'verbose_name_plural': 'historial',
            },
        ),
        migrations.CreateModel(
            name='DetalleRequisicion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad', models.PositiveIntegerField(blank=True, null=True, verbose_name='cantidad')),
                ('descripcion', models.TextField(verbose_name='descripción')),
                ('referencia', models.CharField(blank=True, max_length=50, verbose_name='referencia')),
                ('marca', models.CharField(blank=True, max_length=100, verbose_name='marca')),
                ('valor_aprobado', models.PositiveIntegerField(blank=True, null=True, verbose_name='valor unitario')),
                ('total_aprobado', models.PositiveIntegerField(blank=True, null=True, verbose_name='valor total')),
                ('forma_pago', models.CharField(blank=True, choices=[('E', 'EFECTIVO'), ('D', 'CHEQUE'), ('C', 'CRÉDITO')], max_length=1, verbose_name='forma de pago')),
                ('cumplida', models.BooleanField(default=False, verbose_name='cumplida')),
                ('proveedor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='compras.Proveedor', verbose_name='proveedor')),
                ('requisicion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='compras.Requisicion', verbose_name='requisición')),
            ],
            options={
                'verbose_name': 'detalle de la requisición',
                'verbose_name_plural': 'detalles de la requisición',
            },
        ),
        migrations.CreateModel(
            name='Adjunto',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('archivo', models.FileField(upload_to=compras.models.Adjunto.ruta_adjuntos, verbose_name='archivo')),
                ('requisicion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='compras.Requisicion', verbose_name='requisición')),
            ],
            options={
                'verbose_name': 'adjunto',
                'verbose_name_plural': 'adjuntos',
            },
        ),
    ]
