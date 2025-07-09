from django.db import models
from Dispositivo.models import Dispositivo
from Direcao_Vento.models import DirecaoVento
from timescale.db.models.fields import TimescaleDateTimeField
from timescale.db.models.managers import TimescaleManager
from timescale.db.models.fields import TimescaleDateTimeField
from timescale.db.models.managers import TimescaleManager

from timescale.db.models.models import TimescaleModel

class DadoClimatico(TimescaleModel):
    
    class Meta:
        db_table = "dado_climatico"

    dispositivo = models.ForeignKey(Dispositivo, on_delete=models.PROTECT)
    temperatura = models.FloatField(null=True, blank=True)
    umidade = models.FloatField(null=True, blank=True)
    precipitacao = models.FloatField(null=True, blank=True)
    velocidade_vento = models.FloatField(null=True, blank=True)
    direcao_vento_id = models.ForeignKey(DirecaoVento, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.dispositivo} - {self.time}"