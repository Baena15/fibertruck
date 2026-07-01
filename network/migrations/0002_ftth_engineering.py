# Generated manually for FiberTruck v2 - FTTH Engineering Models

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('network', '0001_initial'),
    ]

    operations = [
        # ============================================================
        # NUEVO: FiberCable - Cable de fibra optica
        # ============================================================
        migrations.CreateModel(
            name='FiberCable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(help_text='Ej: CBL-FDR-01, CBL-DST-ERA-01', max_length=20, unique=True, verbose_name='Codigo')),
                ('name', models.CharField(max_length=100, verbose_name='Nombre')),
                ('cable_type', models.CharField(choices=[('feeder', 'Feeder (Central -> Zona)'), ('distribution', 'Distribution (Splitter -> Caja)'), ('drop', 'Drop (Caja -> Cliente)')], max_length=20, verbose_name='Tipo de cable')),
                ('fiber_count', models.PositiveIntegerField(help_text='12, 72, 144, etc.', verbose_name='Numero de fibras')),
                ('length_m', models.FloatField(help_text='Longitud del cable en metros', verbose_name='Longitud (m)')),
                ('description', models.TextField(blank=True, verbose_name='Descripcion')),
                ('is_active', models.BooleanField(default=True, verbose_name='Activo')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Cable de Fibra',
                'verbose_name_plural': 'Cables de Fibra',
                'ordering': ['code'],
            },
        ),

        # ============================================================
        # NUEVO: SpliceClosure - Caja de empalme
        # ============================================================
        migrations.CreateModel(
            name='SpliceClosure',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(help_text='Ej: SPC-ERA-01', max_length=20, unique=True, verbose_name='Codigo')),
                ('name', models.CharField(max_length=100, verbose_name='Nombre')),
                ('closure_type', models.CharField(choices=[('inline', 'Inline'), ('dome', 'Dome / Encapsulado'), ('rack', 'Rack')], max_length=20, verbose_name='Tipo de cierre')),
                ('latitude', models.FloatField(verbose_name='Latitud')),
                ('longitude', models.FloatField(verbose_name='Longitud')),
                ('address', models.CharField(max_length=200, verbose_name='Direccion')),
                ('fiber_capacity', models.PositiveIntegerField(default=144, verbose_name='Capacidad de fibras')),
                ('fiber_count_used', models.PositiveIntegerField(default=0, verbose_name='Fibras usadas')),
                ('notes', models.TextField(blank=True, verbose_name='Notas')),
                ('is_active', models.BooleanField(default=True, verbose_name='Activo')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('input_cable', models.ForeignKey(blank=True, help_text='Cable que entra al empalme', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='input_splices', to='network.fibercable', verbose_name='Cable de entrada')),
                ('output_cable', models.ForeignKey(blank=True, help_text='Cable que sale del empalme', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='output_splices', to='network.fibercable', verbose_name='Cable de salida')),
                ('zone', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='splices', to='network.zone', verbose_name='Zona')),
            ],
            options={
                'verbose_name': 'Caja de Empalme',
                'verbose_name_plural': 'Cajas de Empalme',
                'ordering': ['code'],
            },
        ),

        # ============================================================
        # ACTUALIZAR: OLT - anadir campos de potencia
        # ============================================================
        migrations.AddField(
            model_name='olt',
            name='output_power_dbm',
            field=models.FloatField(default=3.0, help_text='Potencia de salida del OLT en dBm (tipico: +3 dBm)', verbose_name='Potencia de salida (dBm)'),
        ),
        migrations.AddField(
            model_name='olt',
            name='splitter_ratio',
            field=models.CharField(choices=[('1x32', '1x32'), ('1x64', '1x64')], default='1x32', help_text='Ratio de splitter que soporta el OLT', max_length=10, verbose_name='Ratio splitter'),
        ),

        # ============================================================
        # ACTUALIZAR: Splitter - anadir campos de ingenieria
        # ============================================================
        migrations.AddField(
            model_name='splitter',
            name='input_fiber_number',
            field=models.PositiveIntegerField(blank=True, help_text='Numero de fibra del cable feeder que entra al splitter', null=True, verbose_name='Fibra de entrada'),
        ),
        migrations.AddField(
            model_name='splitter',
            name='input_cable',
            field=models.ForeignKey(blank=True, help_text='Cable feeder que alimenta este splitter', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='splitter_inputs', to='network.fibercable', verbose_name='Cable feeder de entrada'),
        ),
        migrations.AddField(
            model_name='splitter',
            name='output_power_dbm',
            field=models.FloatField(blank=True, help_text='Potencia de salida por puerto en dBm', null=True, verbose_name='Potencia de salida (dBm)'),
        ),
        migrations.AddField(
            model_name='splitter',
            name='splice_in',
            field=models.ForeignKey(blank=True, help_text='Empalme donde se conecta el splitter', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='splitters', to='network.spliceclosure', verbose_name='Empalme de entrada'),
        ),

        # ============================================================
        # ACTUALIZAR: FiberBox - anadir campos de ingenieria
        # ============================================================
        migrations.AddField(
            model_name='fiberbox',
            name='input_cable',
            field=models.ForeignKey(blank=True, help_text='Cable distribution que alimenta esta caja', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='box_inputs', to='network.fibercable', verbose_name='Cable de entrada'),
        ),
        migrations.AddField(
            model_name='fiberbox',
            name='input_fiber_number',
            field=models.PositiveIntegerField(blank=True, help_text='Numero de fibra del cable que alimenta esta caja', null=True, verbose_name='Fibra de entrada'),
        ),
        migrations.AddField(
            model_name='fiberbox',
            name='measured_power_dbm',
            field=models.FloatField(blank=True, help_text='Potencia optica medida en la caja en dBm', null=True, verbose_name='Potencia medida (dBm)'),
        ),
        migrations.AddField(
            model_name='fiberbox',
            name='expected_power_dbm',
            field=models.FloatField(blank=True, help_text='Potencia esperada calculada en la caja en dBm', null=True, verbose_name='Potencia esperada (dBm)'),
        ),
        migrations.AddField(
            model_name='fiberbox',
            name='splice_in',
            field=models.ForeignKey(blank=True, help_text='Empalme por el que llega el cable a esta caja', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='boxes', to='network.spliceclosure', verbose_name='Empalme de entrada'),
        ),

        # ============================================================
        # ACTUALIZAR: Client - anadir campos de ingenieria
        # ============================================================
        migrations.AddField(
            model_name='client',
            name='drop_fiber_number',
            field=models.PositiveIntegerField(blank=True, help_text='Numero de fibra drop asignada al cliente', null=True, verbose_name='Fibra drop'),
        ),
        migrations.AddField(
            model_name='client',
            name='expected_power_dbm',
            field=models.FloatField(blank=True, help_text='Potencia optica esperada calculada en la ONT del cliente', null=True, verbose_name='Potencia esperada (dBm)'),
        ),

        # ============================================================
        # ACTUALIZAR: FiberIncident - anadir campos de diagnostico avanzado
        # ============================================================
        migrations.AddField(
            model_name='fiberincident',
            name='affected_fibers',
            field=models.CharField(blank=True, help_text='Fibras afectadas del cable, separadas por coma', max_length=100, verbose_name='Fibras afectadas'),
        ),
        migrations.AddField(
            model_name='fiberincident',
            name='affected_route',
            field=models.TextField(blank=True, help_text='JSON con coordenadas del tramo afectado para pintar en mapa', verbose_name='Ruta afectada'),
        ),
        migrations.AddField(
            model_name='fiberincident',
            name='recommended_action',
            field=models.TextField(blank=True, help_text='Accion recomendada con detalle para el tecnico', verbose_name='Accion recomendada'),
        ),

        # ============================================================
        # NUEVO: FiberAssignment - Asignacion de fibra a elemento
        # ============================================================
        migrations.CreateModel(
            name='FiberAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fiber_number', models.PositiveIntegerField(help_text='Numero de fibra en el cable (1-N)', verbose_name='Numero de fibra')),
                ('from_splitter_port', models.PositiveIntegerField(blank=True, null=True, verbose_name='Puerto splitter origen')),
                ('status', models.CharField(choices=[('active', 'Activa'), ('fault', 'Con fallo'), ('reserved', 'Reservada')], default='active', max_length=20, verbose_name='Estado')),
                ('notes', models.CharField(blank=True, max_length=200, verbose_name='Notas')),
                ('box', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='fiber_assignments', to='network.fiberbox', verbose_name='Caja alimentada')),
                ('cable', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fiber_assignments', to='network.fibercable', verbose_name='Cable')),
                ('client', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='fiber_assignments', to='network.client', verbose_name='Cliente alimentado')),
                ('from_splice', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='output_fibers', to='network.spliceclosure', verbose_name='Empalme de origen')),
                ('splitter', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='fiber_assignments', to='network.splitter', verbose_name='Splitter alimentado')),
            ],
            options={
                'verbose_name': 'Asignacion de Fibra',
                'verbose_name_plural': 'Asignaciones de Fibra',
                'ordering': ['cable', 'fiber_number'],
                'unique_together': {('cable', 'fiber_number')},
            },
        ),

        # ============================================================
        # NUEVO: CableSegment - Tramo de cable entre dos elementos
        # ============================================================
        migrations.CreateModel(
            name='CableSegment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('segment_type', models.CharField(choices=[('olt_to_splice', 'OLT -> Empalme'), ('splice_to_splitter', 'Empalme -> Splitter'), ('splitter_to_box', 'Splitter -> Caja'), ('splice_to_box', 'Empalme -> Caja'), ('box_to_client', 'Caja -> Cliente')], max_length=30, verbose_name='Tipo de tramo')),
                ('fiber_numbers', models.CharField(blank=True, help_text='Numeros de fibra separados por coma. Ej: 1,2,3', max_length=100, verbose_name='Fibras utilizadas')),
                ('length_m', models.FloatField(help_text='Longitud real de este tramo en metros', verbose_name='Longitud real (m)')),
                ('route_coordinates', models.TextField(blank=True, help_text='JSON array de [lat,lng] con la trayectoria por calles', verbose_name='Coordenadas de ruta')),
                ('attenuation_db', models.FloatField(default=0.0, help_text='Perdida de este tramo en dB', verbose_name='Atenuacion (dB)')),
                ('is_active', models.BooleanField(default=True, verbose_name='Activo')),
                ('notes', models.TextField(blank=True, verbose_name='Notas')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('cable', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='segments', to='network.fibercable', verbose_name='Cable')),
                ('from_box', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='outgoing_segments', to='network.fiberbox', verbose_name='Desde Caja')),
                ('from_olt', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='outgoing_segments', to='network.olt', verbose_name='Desde OLT')),
                ('from_splice', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='outgoing_segments', to='network.spliceclosure', verbose_name='Desde Empalme')),
                ('from_splitter', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='outgoing_segments', to='network.splitter', verbose_name='Desde Splitter')),
                ('to_box', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='incoming_segments', to='network.fiberbox', verbose_name='Hacia Caja')),
                ('to_client', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='incoming_segments', to='network.client', verbose_name='Hacia Cliente')),
                ('to_splice', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='incoming_segments', to='network.spliceclosure', verbose_name='Hacia Empalme')),
                ('to_splitter', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='incoming_segments', to='network.splitter', verbose_name='Hacia Splitter')),
            ],
            options={
                'verbose_name': 'Tramo de Cable',
                'verbose_name_plural': 'Tramos de Cable',
                'ordering': ['cable', 'segment_type'],
            },
        ),

        # ============================================================
        # ACTUALIZAR: FiberIncident - anadir ForeignKeys a nuevos modelos
        # ============================================================
        migrations.AddField(
            model_name='fiberincident',
            name='affected_segment',
            field=models.ForeignKey(blank=True, help_text='Tramo de cable afectado por la incidencia', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='incidents', to='network.cablesegment', verbose_name='Tramo afectado'),
        ),
        migrations.AddField(
            model_name='fiberincident',
            name='splice_fault',
            field=models.ForeignKey(blank=True, help_text='Empalme donde se detecto el fallo', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='incidents', to='network.spliceclosure', verbose_name='Empalme fallido'),
        ),
    ]
