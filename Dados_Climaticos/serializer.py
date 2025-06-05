from rest_framework import serializers
from .models import DadoClimatico
        
class DadoClimaticoSerializer(serializers.ModelSerializer):
    direcao_vento = serializers.CharField(source='direcao_vento_id.nome', read_only=True)
    data = serializers.DateTimeField(source='time', read_only=True)

    class Meta:
        model = DadoClimatico
        fields = [
            "id",
            "dispositivo",
            "data",  # Agora JSON terá "data", mas internamente usa "time"
            "temperatura",
            "umidade",
            "precipitacao",
            "velocidade_vento",
            "direcao_vento",
        ]