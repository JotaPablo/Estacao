from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import Dispositivo


class DispositivoSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Dispositivo
        fields = ['id', 'token', 'descricao', 'localizacao']  
        geo_field = 'localizacao'  # Especifica o campo geográfico
        
class DispositivoSimplesSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Dispositivo
        fields = ['id', 'descricao', 'localizacao']  
        geo_field = 'localizacao'  # Especifica o campo geográfico