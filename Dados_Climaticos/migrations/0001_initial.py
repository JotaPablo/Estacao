# Generated by Django 4.2.20 on 2025-05-29 00:00

from django.db import migrations, models
import django.db.models.deletion
import timescale.db.models.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('Dispositivo', '0003_remove_dispositivo_latitude_and_more'),
        ('Direcao_Vento', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DadoClimatico',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', timescale.db.models.fields.TimescaleDateTimeField(interval='1 day')),
                ('temperatura', models.FloatField(blank=True, null=True)),
                ('umidade', models.FloatField(blank=True, null=True)),
                ('precipitacao', models.FloatField(blank=True, null=True)),
                ('velocidade_vento', models.FloatField(blank=True, null=True)),
                ('direcao_vento_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Direcao_Vento.direcaovento')),
                ('dispositivo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Dispositivo.dispositivo')),
            ],
            options={
                'db_table': 'dados_climaticos',
            },
        ),
    ]
