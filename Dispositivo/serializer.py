from rest_framework import serializers
from .models import Dispositivo
from django.contrib.gis.geos import Point
from rest_framework_gis.serializers import GeoFeatureModelSerializer


class DispositivoSerializer(serializers.ModelSerializer):
    # Validação geográfica da latitude e longitude
    latitude = serializers.FloatField(
        write_only=True,
        min_value=-90,
        max_value=90,
        error_messages={
            'min_value': 'A latitude deve estar entre -90 e 90 graus.',
            'max_value': 'A latitude deve estar entre -90 e 90 graus.'
        }
    )
    longitude = serializers.FloatField(
        write_only=True,
        min_value=-180,
        max_value=180,
        error_messages={
            'min_value': 'A longitude deve estar entre -180 e 180 graus.',
            'max_value': 'A longitude deve estar entre -180 e 180 graus.'
        }
    )
    
    class Meta:
        model = Dispositivo
        fields = ['id', 'token', 'descricao', 'latitude', 'longitude']
        read_only_fields = ['id', 'token']
        
    def create(self, validated_data):
        # Extrai e remove campos de coordenadas
        latitude = validated_data.pop('latitude')
        longitude = validated_data.pop('longitude')
        
        # Cria ponto geográfico (valores já validados)
        validated_data['localizacao'] = Point(longitude, latitude)
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Atualiza localização se coordenadas forem fornecidas
        if 'latitude' in validated_data or 'longitude' in validated_data:
            latitude = validated_data.pop('latitude', instance.localizacao.y)
            longitude = validated_data.pop('longitude', instance.localizacao.x)
            # Cria o novo ponto (validação já ocorreu se estiverem em validated_data)
            instance.localizacao = Point(longitude, latitude)
            
        return super().update(instance, validated_data)
    
    def to_representation(self, instance):
        # Customiza representação para incluir coordenadas
        rep = super().to_representation(instance)
        rep['latitude'] = instance.localizacao.y if instance.localizacao else None
        rep['longitude'] = instance.localizacao.x if instance.localizacao else None
        return rep
    
class DispositivoSimplesSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Dispositivo
        fields = ['id', 'descricao', 'localizacao']  
        geo_field = 'localizacao'  # Especifica o campo geográfico