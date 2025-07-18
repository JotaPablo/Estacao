from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from Dispositivo.models import Dispositivo
from Dispositivo.serializer import DispositivoSerializer, DispositivoSimplesSerializer
from django.contrib.gis.measure import Distance as D
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiExample, inline_serializer
from rest_framework import serializers

@extend_schema(
    description=(
        "Retorna os dispositivos localizados dentro de um raio (em km) a partir de uma coordenada "
        "geográfica (latitude e longitude). Inclui a distância individual de cada dispositivo até o ponto de referência."
    ),
    parameters=[
        OpenApiParameter(
            name='latitude',
            type=OpenApiTypes.FLOAT,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Latitude do ponto de referência (ex: -15.7801)'
        ),
        OpenApiParameter(
            name='longitude',
            type=OpenApiTypes.FLOAT,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Longitude do ponto de referência (ex: -47.9292)'
        ),
        OpenApiParameter(
            name='raio',
            type=OpenApiTypes.FLOAT,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Raio de busca em quilômetros (ex: 5)'
        ),
    ],
    responses={
        200: OpenApiTypes.OBJECT,
        400: OpenApiTypes.OBJECT
    },
    examples=[
        OpenApiExample(
            'Dispositivos encontrados',
            response_only=True,
            status_codes=['200'],
            value={
                "status": 200,
                "msg": "Dispositivos encontrados num raio de 5000.0 km.",
                "dispositivos": [
                    {
                        "id": 1,
                        "type": "Feature",
                        "geometry": "SRID=4326;POINT (-45.6789 -12.34567)",
                        "properties": {
                            "token": "ad9da4ba-9f2f-4f06-83fe-485c6b24f03c",
                            "descricao": "Estação cacau"
                        },
                        "distancia_km": 451.041
                    },
                    {
                        "id": 2,
                        "type": "Feature",
                        "geometry": "SRID=4326;POINT (-8.6789 -8.303)",
                        "properties": {
                            "token": "3d48fe06-1a2a-42f3-bc9c-304ea8a2c72b",
                            "descricao": "Estação ceplac"
                        },
                        "distancia_km": 4345.968
                    }
                ]
            }
        ),
        OpenApiExample(
            'Nenhum dispositivo encontrado',
            value={
                "status": 200,
                "msg": "Nenhum dispositivo encontrado num raio de 1.0 km.",
                "dispositivos": []
            },
            response_only=True,
            status_codes=['200'],
        ),
        OpenApiExample(
            'Parâmetros inválidos',
            response_only=True,
            status_codes=['400'],
            value={
                "status": 400,
                "msg": "Parâmetros \"latitude\", \"longitude\" e \"raio\" são obrigatórios e devem ser válidos."
            }
        )
    ]
)
class DispositivosProximosRaioView(APIView):
    def get(self, request):
        # Captura e valida os parâmetros de latitude, longitude e raio
        try:
            latitude = float(request.GET.get('latitude'))
            longitude = float(request.GET.get('longitude'))
            raio_km = float(request.GET.get('raio'))
        except (TypeError, ValueError):
            return Response({
                'status': 400,
                'msg': 'Parâmetros "latitude", "longitude" e "raio" são obrigatórios e devem ser válidos.'
            }, status=400)

        # Cria o ponto de referência geográfica
        ponto_referencia = Point(longitude, latitude, srid=4326)

        # Filtra os dispositivos dentro do raio especificado e anota a distância até o ponto
        dispositivos = Dispositivo.objects.annotate(
            distancia=Distance('localizacao', ponto_referencia)
        ).filter(
            localizacao__distance_lte=(ponto_referencia, raio_km * 1000)  # raio em metros
        ).order_by('distancia')

        if not dispositivos.exists():
            return Response({
                'status': 200,
                'msg': f'Nenhum dispositivo encontrado num raio de {raio_km} km.',
                'dispositivos': []
            })

        # Serializa os dispositivos e adiciona a distância individual (em km) ao resultado
        dispositivos_data = []
        for dispositivo in dispositivos:
            dispositivo_serializado = DispositivoSerializer(dispositivo).data
            dispositivo_serializado['distancia_km'] = round(dispositivo.distancia.km, 3)
            dispositivos_data.append(dispositivo_serializado)

        # Retorna a resposta com status, mensagem e lista de dispositivos
        return Response({
            'status': 200,
            'msg': f'Dispositivos encontrados num raio de {raio_km} km.',
            'dispositivos': dispositivos_data
        })

    
@extend_schema(
    description="Retorna a estação mais próxima de uma coordenada geográfica (latitude e longitude), incluindo a distância até ela.",
    parameters=[
        OpenApiParameter(
            name='latitude',
            type=OpenApiTypes.FLOAT,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Latitude do ponto de referência (ex: -12.3456)'
        ),
        OpenApiParameter(
            name='longitude',
            type=OpenApiTypes.FLOAT,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Longitude do ponto de referência (ex: -45.6789)'
        ),
    ],
    responses={
        200: OpenApiTypes.OBJECT,
        200: OpenApiTypes.OBJECT,
        400: OpenApiTypes.OBJECT,
    },
    examples=[
        OpenApiExample(
            name='Estação encontrada',
            value={
                "status": 200,
                "msg": "Estação mais próxima encontrada.",
                "estacao": {
                    "id": 2,
                    "type": "Feature",
                    "geometry": "SRID=4326;POINT (-8.6789 -8.303)",
                    "properties": {
                        "descricao": "Estação ceplac"
                    }
                },
                "distancia_km": 253.298
            },
            response_only=True,
            status_codes=["200"]
        ),
        OpenApiExample(
            name='Parâmetros inválidos',
            value={
                "status": 400,
                "msg": 'Parâmetros "latitude" e "longitude" são obrigatórios e devem ser válidos.'
            },
            response_only=True,
            status_codes=["400"]
        ),
        OpenApiExample(
            name='Nenhuma estação encontrada',
            value={
                "status": 200,
                "msg": "Nenhuma estação encontrada.",
                "estacao": None,
                "distancia_km": None
            },
            response_only=True,
            status_codes=["200"]
        )
    ]
)
class DispositivoMaisProximoView(APIView):
    def get(self, request):
        try:
            latitude = float(request.GET.get('latitude'))
            longitude = float(request.GET.get('longitude'))
        except (TypeError, ValueError):
            return Response({
                'status': 400,
                'msg': 'Parâmetros "latitude" e "longitude" são obrigatórios e devem ser válidos.'
            }, status=400)

        ponto_referencia = Point(longitude, latitude, srid=4326)

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
                'distancia_km': round(distancia_km, 3)
            })
        else:
            return Response({
                'status': 200,
                'msg': 'Nenhuma estação encontrada.',
                'estacao': None,
                'distancia_km': None
            })