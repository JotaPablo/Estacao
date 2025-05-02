from django.db import models
from Dispositivo.models import Dispositivo
from Direcao_Vento.models import DirecaoVento

class DadoClimatico(models.Model):
    dispositivo = models.ForeignKey(Dispositivo, on_delete=models.CASCADE)
    data = models.DateTimeField()
    temperatura = models.FloatField(null=True, blank=True)
    umidade = models.FloatField(null=True, blank=True)
    precipitacao = models.FloatField(null=True, blank=True)
    velocidade_vento = models.FloatField(null=True, blank=True)
    direcao_vento_id = models.ForeignKey(DirecaoVento, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.dispositivo} - {self.data}"