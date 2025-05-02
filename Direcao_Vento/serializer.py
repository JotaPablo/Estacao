from rest_framework import serializers
from .models import DirecaoVento

class DirecaoVentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DirecaoVento
        fields = ['id', 'nome']