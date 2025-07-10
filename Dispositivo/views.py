from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from .models import Dispositivo
from .serializer import DispositivoSerializer
from utils import is_valid_uuid
from django.contrib.gis.geos import Point
from drf_spectacular.utils import (
    extend_schema, 
    OpenApiParameter, 
    OpenApiExample
)


class DispositivoListView(APIView):

    @extend_schema(
        description="Lista todos os dispositivos cadastrados",
        responses={status.HTTP_200_OK: DispositivoSerializer(many=True)},
        examples=[
            OpenApiExample(
                "Exemplo de resposta",
                value=[
                    {
                        "id": 1,
                        "token": "550e8400-e29b-41d4-a716-446655440000",
                        "descricao": "Sensor Central",
                        "latitude": -23.550520,
                        "longitude": -46.633308
                    }
                ],
                response_only=True
            )
        ]
    )
    
    # GET: Lista todos os dispositivos cadastrados
    def get(self, request):
        """Recupera todos os dispositivos do banco de dados"""
        dispositivos = Dispositivo.objects.all()
        serializer = DispositivoSerializer(dispositivos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    @extend_schema(
        description=(
            "Cria um novo dispositivo.\n\n"
            "**Latitude**:\n"
                "- Campo obrigatório\n"
                "- Deve estar entre -90 e 90 graus\n\n"
            "**Longitude**:\n"
                "- Campo obrigatório\n"
                "- Deve estar entre -180 e 180 graus"
        ),
        request=DispositivoSerializer,
        responses={
            status.HTTP_201_CREATED: DispositivoSerializer,
            status.HTTP_400_BAD_REQUEST: serializers.DictField
        },
        examples=[
            OpenApiExample(
                "Requisição válida",
                value={
                    "descricao": "Novo Sensor",
                    "latitude": -23.550520,
                    "longitude": -46.633308
                },
                request_only=True
            ),
            OpenApiExample(
                "Erro: campos obrigatórios",
                value={
                    "latitude": ["Este campo é obrigatório."],
                    "longitude": ["Este campo é obrigatório."]
                },
                response_only=True,
                status_codes=['400']
            ),
            OpenApiExample(
                "Erro: latitude inválida",
                value={
                    "latitude": ["A latitude deve estar entre -90 e 90 graus."]
                },
                response_only=True,
                status_codes=['400']
            ),
            OpenApiExample(
                "Erro: longitude inválida",
                value={
                    "longitude": ["A longitude deve estar entre -180 e 180 graus."]
                },
                response_only=True,
                status_codes=['400']
            ),
            OpenApiExample(
                "Erro: formato numérico inválido",
                value={
                    "latitude": ["Um número válido é necessário."],
                    "longitude": ["Um número válido é necessário."]
                },
                response_only=True,
                status_codes=['400']
            )
        ]
    )

    # POST: Cria um novo dispositivo
    def post(self, request):
        """
        Cria novo dispositivo com validações:
        1. Valida os dados usando o serializer
        2. Verifica obrigatoriedade de latitude e longitude
        3. Valida limites geográficos das coordenadas
        """
        serializer = DispositivoSerializer(data=request.data)
        if serializer.is_valid():
            dispositivo = serializer.save()
            return Response(
                DispositivoSerializer(dispositivo).data, 
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DispositivoDetailView(APIView):

    # Função auxiliar: Busca dispositivo por ID ou token
    def get_dispositivo(self, id):
        """Busca dispositivo por ID ou token com tratamento de erros"""
        try:
            if is_valid_uuid(id):
                return Dispositivo.objects.get(token=id)
            elif id.isdigit():
                return Dispositivo.objects.get(id=int(id))
            return None
        except (Dispositivo.DoesNotExist, ValueError):
            return None


    @extend_schema(
        description="Obtém detalhes de um dispositivo pelo ID ou token",
        parameters=[
            OpenApiParameter(
                name='id',
                type=str,
                location=OpenApiParameter.PATH,
                description="ID numérico ou token UUID do dispositivo"
            )
        ],
        responses={
            status.HTTP_200_OK: DispositivoSerializer,
            status.HTTP_404_NOT_FOUND: serializers.DictField
        },
        examples=[
            OpenApiExample(
                "Não encontrado",
                value={"erro": "Dispositivo não encontrado"},  
                response_only=True,
                status_codes=['404']
            )
        ]
    )
    
    # GET: Recupera um dispositivo específico por ID ou token
    def get(self, request, id):
        """Busca dispositivo pelo ID/token, retorna 404 se não encontrado"""
        dispositivo = self.get_dispositivo(id)
        if not dispositivo:
            return Response(
                {"erro": "Dispositivo não encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = DispositivoSerializer(dispositivo)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        description=(
            "Atualiza um dispositivo existente pelo ID ou token.\n\n"
            "**Latitude**:\n"
                "- Deve estar entre -90 e 90 graus\n\n"
            "**Longitude**:\n"
                "- Deve estar entre -180 e 180 graus"
        ),
        request=DispositivoSerializer,
        parameters=[
            OpenApiParameter(
                name='id',
                type=str,
                location=OpenApiParameter.PATH,
                description="ID numérico ou token UUID do dispositivo"
            )
        ],
        responses={
            status.HTTP_200_OK: DispositivoSerializer,
            status.HTTP_400_BAD_REQUEST: serializers.DictField,
            status.HTTP_404_NOT_FOUND: serializers.DictField
        },
        examples=[
            OpenApiExample(
                "Atualização bem-sucedida",
                value={
                    "id": 1,
                    "token": "550e8400-e29b-41d4-a716-446655440000",
                    "descricao": "Sensor Atualizado",
                    "latitude": -23.551000,
                    "longitude": -46.634000
                },
                response_only=True,
                status_codes=['200']
            ),
            OpenApiExample(
                "Não encontrado",
                value={"erro": "Dispositivo não encontrado"},
                response_only=True,
                status_codes=['404']
            ),
            OpenApiExample(
                "Erro: latitude inválida",
                value={
                    "latitude": ["A latitude deve estar entre -90 e 90 graus."]
                },
                response_only=True,
                status_codes=['400']
            ),
            OpenApiExample(
                "Erro: longitude inválida",
                value={
                    "longitude": ["A longitude deve estar entre -180 e 180 graus."]
                },
                response_only=True,
                status_codes=['400']
            ),
            OpenApiExample(
                "Erro: formato numérico inválido",
                value={
                    "latitude": ["Um número válido é necessário."]
                },
                response_only=True,
                status_codes=['400']
            ),
             OpenApiExample(
                "Erro: campos obrigatórios",
                value={
                    "latitude": ["Este campo é obrigatório."],
                    "longitude": ["Este campo é obrigatório."]
                },
                response_only=True,
                status_codes=['400']
            )
        ]
    )
   
    # PUT: Atualiza dispositivo existente
    def put(self, request, id):
        """
        Atualiza dispositivo existente com validações:
        1. Verifica existência do dispositivo
        2. Valida dados usando serializer
        3. Atualiza campos permitidos (partial=True)
        """
        dispositivo = self.get_dispositivo(id)
        if not dispositivo:
            return Response(
                {"erro": "Dispositivo não encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = DispositivoSerializer(dispositivo, data=request.data, partial=True)
        if serializer.is_valid():
            dispositivo = serializer.save()
            return Response(
                DispositivoSerializer(dispositivo).data, 
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        description="Exclui um dispositivo pelo seu ID ou Token",
        parameters=[ 
            OpenApiParameter(
                name='id',
                type=str,
                location=OpenApiParameter.PATH,
                description="ID numérico ou token UUID do dispositivo"
            )
        ],
        responses={
            status.HTTP_204_NO_CONTENT: None,
            status.HTTP_404_NOT_FOUND: serializers.DictField
        },
        examples=[
            OpenApiExample(
                "Não encontrado",
                value={"erro": "Dispositivo não encontrado"},  # Corrigido
                response_only=True,
                status_codes=['404']
            )
        ]
    )
    
    # DELETE: Remove dispositivo existente
    def delete(self, request, id):
        """Exclui dispositivo se existir, retorna 404 se não encontrado"""
        dispositivo = self.get_dispositivo(id)
        if not dispositivo:
            return Response(
                {"erro": "Dispositivo não encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        dispositivo.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)