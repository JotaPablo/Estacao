from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from Dispositivo.models import Dispositivo
from Dispositivo.serializer import DispositivoSerializer, DispositivoSimplesSerializer
from django.contrib.gis.measure import Distance as D

class DispositivosProximosRaioView(APIView):
    def get(self, request):
        try:
            lat = float(request.GET.get('lat'))
            lon = float(request.GET.get('lon'))
            raio_km = float(request.GET.get('raio'))
        except (TypeError, ValueError):
            return Response({
                'status': 400,
                'msg': 'Parâmetros "lat", "lon" e "raio" são obrigatórios e devem ser válidos.'
            }, status=400)

        ponto_referencia = Point(lon, lat, srid=4326)

        dispositivos = Dispositivo.objects.annotate(
            distancia=Distance('localizacao', ponto_referencia)
        ).filter(
            localizacao__distance_lte=(ponto_referencia, raio_km * 1000)  # metros
        ).order_by('distancia')

        # Monta resposta com distância incluída
        dispositivos_data = []
        for dispositivo in dispositivos:
            dispositivo_serializado = DispositivoSerializer(dispositivo).data
            dispositivo_serializado['distancia_km'] = round(dispositivo.distancia.km, 3)
            dispositivos_data.append(dispositivo_serializado)

        return Response({
            'status': 200,
            'msg': f'Dispositivos encontrados num raio de {raio_km} km.',
            'dispositivos': dispositivos_data
        })
    
class DispositivoMaisProximoView(APIView):
    def get(self, request):
        try:
            lat = float(request.GET.get('lat'))
            lon = float(request.GET.get('lon'))
        except (TypeError, ValueError):
            return Response({
                'status': 400,
                'msg': 'Parâmetros "lat" e "lon" são obrigatórios e devem ser válidos.'
            }, status=400)

        ponto_referencia = Point(lon, lat, srid=4326)

        estacao = Dispositivo.objects.annotate(
            distancia=Distance('localizacao', ponto_referencia)
        ).order_by('distancia').first()

        if estacao:
            serializer = DispositivoSimplesSerializer(instance=estacao)
            distancia_km = estacao.distancia.km
            return Response({
                'status': 200,
                'msg': 'Estação mais próxima encontrada.',
                'estacao': serializer.data,
                'distancia_km': round(distancia_km, 3)  # arredonda para 3 casas decimais
            })
        else:
            return Response({
                'status': 404,
                'msg': 'Nenhuma estação encontrada.'
            }, status=404)