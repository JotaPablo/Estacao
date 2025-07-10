from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import DirecaoVento
from .serializer import DirecaoVentoSerializer
from drf_spectacular.utils import (
    extend_schema, 
    OpenApiParameter, 
    OpenApiExample
)
from rest_framework import serializers

class DirecaoVentoListView(APIView):

    @extend_schema(
        description="Lista todas as direções do vento cadastradas",
        responses={status.HTTP_200_OK: DirecaoVentoSerializer(many=True)},
        examples=[
            OpenApiExample(
                "Exemplo de resposta",
                value=[
                    {"id": 1, "nome": "NORTE"},
                    {"id": 2, "nome": "SUL"}
                ],
                response_only=True
            )
        ]
    )
    
    # GET: Lista todas as direções de vento
    def get(self, request):
        """Recupera todas as direções de vento do banco de dados"""
        direcoes = DirecaoVento.objects.all()
        serializer = DirecaoVentoSerializer(direcoes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    @extend_schema(
        description="Cria uma nova direção do vento",
        request=DirecaoVentoSerializer,
        responses={
            status.HTTP_201_CREATED: DirecaoVentoSerializer,
            status.HTTP_400_BAD_REQUEST: serializers.DictField
        },
        examples=[
            OpenApiExample(
                "Requisição válida",
                value={"nome": "Leste"},
                request_only=True
            ),
            OpenApiExample(
                "Resposta de sucesso",
                value={"id": 3, "nome": "LESTE"},
                response_only=True
            ),
            OpenApiExample(
                "Campo obrigatório",
                value={"error": "O campo 'nome' é obrigatório"},
                response_only=True,
                status_codes=['400']
            ),
            OpenApiExample(
                "Nome duplicado",
                value={"error": "Já existe uma direção do vento com esse nome"},
                response_only=True,
                status_codes=['400']
            )
        ]
    )
    
    # POST: Cria nova direção de vento
    def post(self, request):
        """
        Cria nova direção de vento com validações:
        1. Verifica se nome foi fornecido
        2. Converte nome para maiúsculas
        3. Verifica se nome já existe
        """
        nome = request.data.get('nome')
        if not nome:  # Validação de campo obrigatório
            return Response({"error": "O campo 'nome' é obrigatório"}, status=400)
        
        nome_upper = nome.upper()  # Padronização para maiúsculas
        
        # Verifica duplicatas
        if DirecaoVento.objects.filter(nome=nome_upper).exists():
            return Response({"error": "Nome já existe"}, status=400)

        # Cria e retorna o novo objeto
        direcao = DirecaoVento.objects.create(nome=nome_upper)
        serializer = DirecaoVentoSerializer(direcao)
        return Response(serializer.data, status=201)


class DirecaoVentoDetailView(APIView):

    @extend_schema(
        description="Obtém detalhes de uma direção do vento pelo ID",
        parameters=[
            OpenApiParameter(
                name='id',
                type=int,
                location=OpenApiParameter.PATH,
                description="ID da direção do vento"
            )
        ],
        responses={
            status.HTTP_200_OK: DirecaoVentoSerializer,
            status.HTTP_404_NOT_FOUND: serializers.DictField
        },
        examples=[
            OpenApiExample(
                "Exemplo de resposta",
                value={"id": 1, "nome": "NORTE"},
                response_only=True
            ),
            OpenApiExample(
                "Não encontrado",
                value={"error": "Direção do vento não encontrada"},
                response_only=True,
                status_codes=['404']
            )
        ]
    )
    
    # GET: Recupera uma direção específica por ID
    def get(self, request, id):
        """Busca direção pelo ID, retorna 404 se não encontrada"""
        try:
            direcao = DirecaoVento.objects.get(id=id)
            serializer = DirecaoVentoSerializer(direcao)
            return Response(serializer.data)
        except DirecaoVento.DoesNotExist:
            return Response({"error": "Não encontrada"}, status=404)

    @extend_schema(
        description="Atualiza uma direção do vento existente",
        request=DirecaoVentoSerializer,
        responses={
            status.HTTP_200_OK: DirecaoVentoSerializer,
            status.HTTP_400_BAD_REQUEST: serializers.DictField,
            status.HTTP_404_NOT_FOUND: serializers.DictField
        },
        examples=[
            OpenApiExample(
                "Requisição válida",
                value={"nome": "Nordeste"},
                request_only=True
            ),
            OpenApiExample(
                "Resposta de sucesso",
                value={"id": 1, "nome": "NORDESTE"},
                response_only=True
            ),
            OpenApiExample(
                "Campo obrigatório",
                value={"error": "O campo 'nome' é obrigatório para atualização"},
                response_only=True,
                status_codes=['400']
            ),
            OpenApiExample(
                "Nome duplicado",
                value={"error": "Já existe uma direção do vento com esse nome"},
                response_only=True,
                status_codes=['400']
            ),
            OpenApiExample(
                "Não encontrado",
                value={"error": "Direção do vento não encontrada"},
                response_only=True,
                status_codes=['404']
            )
        ]
    )
    
    # PUT: Atualiza direção existente
    def put(self, request, id):
        """
        Atualiza direção existente com validações:
        1. Verifica existência do recurso
        2. Valida campo obrigatório
        3. Verifica duplicatas (excluindo o próprio objeto)
        """
        try:
            direcao = DirecaoVento.objects.get(id=id)
            nome = request.data.get('nome')
            
            if not nome:  # Validação de campo obrigatório
                return Response({"error": "Nome obrigatório"}, status=400)
            
            nome_upper = nome.upper()
            
            # Verifica duplicatas excluindo o próprio registro
            if DirecaoVento.objects.filter(nome=nome_upper).exclude(id=id).exists():
                return Response({"error": "Nome já existe"}, status=400)

            # Atualiza e salva
            direcao.nome = nome_upper
            direcao.save()
            serializer = DirecaoVentoSerializer(direcao)
            return Response(serializer.data)
        except DirecaoVento.DoesNotExist:
            return Response({"error": "Não encontrada"}, status=404)

    @extend_schema(
        description="Exclui uma direção do vento",
        responses={
            status.HTTP_204_NO_CONTENT: None,
            status.HTTP_404_NOT_FOUND: serializers.DictField
        },
        examples=[
            OpenApiExample(
                "Não encontrado",
                value={"error": "Direção do vento não encontrada"},
                response_only=True,
                status_codes=['404']
            )
        ]
    )
    
    # DELETE: Remove direção existente
    def delete(self, request, id):
        """Exclui direção se existir, retorna 404 se não encontrada"""
        try:
            direcao = DirecaoVento.objects.get(id=id)
            direcao.delete()
            return Response(status=204)  # Resposta vazia para sucesso
        except DirecaoVento.DoesNotExist:
            return Response({"error": "Não encontrada"}, status=404)