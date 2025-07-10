from datetime import datetime
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.exceptions import PermissionDenied
from .models import DadoClimatico
from .serializer import DadoClimaticoSerializer
from Dispositivo.models import Dispositivo
from Direcao_Vento.models import DirecaoVento
from utils import is_valid_uuid, get_dispositivo
from drf_spectacular.utils import (
    extend_schema, 
    OpenApiParameter, 
    OpenApiExample,
    OpenApiResponse
)


class DadoClimaticoListView(APIView):
    @extend_schema(
        description="Lista todos os dados climáticos cadastrados",
        responses={status.HTTP_200_OK: DadoClimaticoSerializer(many=True)},
        examples=[
            OpenApiExample(
                "Exemplo de resposta",
                value=[
                    {
                        "id": 1,
                        "dispositivo": 1,
                        "dispositivo_uuid": "550e8400-e29b-41d4-a716-446655440000",
                        "data": "2023-10-15T14:30:00Z",
                        "temperatura": 25.5,
                        "umidade": 65.0,
                        "precipitacao": 0.0,
                        "velocidade_vento": 10.2,
                        "direcao_vento": "NORTE"
                    }
                ],
                response_only=True
            )
        ]
    )
    
    # GET: Lista todos os dados climáticos cadastrados
    def get(self, request):
        """Recupera todos os dados climáticos do banco de dados"""
        dados = DadoClimatico.objects.all()
        serializer = DadoClimaticoSerializer(dados, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        description=(
            "Cria um ou mais dados climáticos.\n\n"
            "**Campos obrigatórios**:\n"
            "- `token`: UUID do dispositivo\n"
            "- `dados`: Lista de objetos contendo:\n"
            "  - `data`: Data/hora da medição\n"
            "  - Pelo menos um dos campos: `temperatura`, `umidade`, "
            "`precipitacao`, `velocidade_vento` ou `direcao_vento`"
        ),
        request=serializers.DictField,
        responses={
            status.HTTP_201_CREATED: DadoClimaticoSerializer(many=True),
            status.HTTP_207_MULTI_STATUS: serializers.DictField,
            status.HTTP_400_BAD_REQUEST: serializers.DictField,
            status.HTTP_404_NOT_FOUND: serializers.DictField,
        },
        examples=[
            OpenApiExample(
                "Requisição válida",
                value={
                    "token": "550e8400-e29b-41d4-a716-446655440000",
                    "dados": [
                        {
                            "data": "2023-10-15T14:30:00Z",
                            "temperatura": 25.5,
                            "umidade": 65.0,
                            "precipitacao": 0.0,
                            "velocidade_vento": 10.2,
                            "direcao_vento": "NORTE"
                        },
                        {
                            "data": "2023-10-15T14:30:00Z",
                            "umidade": 65.0
                        }
                    ]
                },
                request_only=True
            ),
            OpenApiExample(
                "Resposta 201: todos os dados criados com sucesso",
                value=[
                    {
                        "id": 1,
                        "dispositivo": 1,
                        "data": "2023-10-15T14:30:00Z",
                        "temperatura": 25.5,
                        "umidade": 65.0
                    }
                ],
                response_only=True,
                status_codes=["201"]
            ),
            OpenApiExample(
                "Resposta 207: alguns dados com erro",
                value={
                    "dados_criados": [
                        {
                            "id": 1,
                            "dispositivo": 1,
                            "data": "2023-10-15T14:30:00Z",
                            "temperatura": 25.5
                        }
                    ],
                    "erros": [
                        {
                            "index": 1,
                            "msg": "Direção do vento inválida: SULESTE"
                        },
                        {
                            "index": 2,
                            "msg": "Campo data obrigatório"
                        },
                        {
                            "index": 3,
                            "msg": "Pelo menos uma medição é obrigatória"
                        }
                    ]
                },
                response_only=True,
                status_codes=["207"]
            ),
            OpenApiExample(
                "Resposta 400: token inválido",
                value={"token": ["UUID inválido"]},
                response_only=True,
                status_codes=["400"]
            ),
            OpenApiExample(
                "Resposta 400: campo obrigatório",
                value={"dados": ["Campo obrigatório"]},
                response_only=True,
                status_codes=["400"]
            ),
            OpenApiExample(
                "Resposta 400: lista de erros por índice",
                value=[
                    {"index": 0, "msg": "Campo data obrigatório"},
                    {"index": 1, "msg": "Pelo menos uma medição é obrigatória"}
                ],
                response_only=True,
                status_codes=["400"]
            ),
            OpenApiExample(
                "Resposta 404: dispositivo não encontrado",
                value={"erro": "Dispositivo não encontrado"},
                response_only=True,
                status_codes=["404"]
            )
        ]
    )
    
    # POST: Cria um ou mais dados climáticos
    def post(self, request):
        """
        Cria novos dados climáticos com validações:
        1. Valida token e presença de dados
        2. Verifica existência do dispositivo
        3. Valida cada item da lista de dados:
           - Campo data obrigatório
           - Pelo menos uma medição presente
           - Formato de data válido
           - Direção do vento existente
        4. Retorna respostas multi-status quando aplicável
        """
        token = request.data.get('token')
        dados_input = request.data.get('dados')  

        # Validações básicas de campos obrigatórios
        if not token:
            return Response({"token": ["Campo obrigatório"]}, status=400)
        if not dados_input:
            return Response({"dados": ["Campo obrigatório"]}, status=400)
        if not is_valid_uuid(token):
            return Response({"token": ["UUID inválido"]}, status=400)

        try:
            # Busca dispositivo pelo token
            dispositivo = Dispositivo.objects.get(token=token)
        except Dispositivo.DoesNotExist:
            return Response({"erro": "Dispositivo não encontrado"}, status=404)

        # Normaliza entrada para lista
        dados = dados_input if isinstance(dados_input, list) else [dados_input]
        criados = []
        erros = []

        # Processa cada item de dados individualmente
        for idx, dado in enumerate(dados):
            # Validação de campos obrigatórios
            if not dado.get('data'):
                erros.append({'index': idx, 'msg': 'Campo data obrigatório'})
                continue
            
            campos_medicao = ['temperatura', 'umidade', 'precipitacao', 'velocidade_vento', 'direcao_vento']
            if not any(dado.get(campo) is not None for campo in campos_medicao):
                erros.append({'index': idx, 'msg': 'Pelo menos uma medição é obrigatória'})
                continue

            try:
                # Valida formato ISO da data
                datetime.fromisoformat(dado['data'])
                
                # Busca direção do vento se existir
                direcao = None
                if direcao_nome := dado.get('direcao_vento'):
                    direcao = DirecaoVento.objects.get(nome__iexact=direcao_nome.upper())
                
                # Cria novo registro no banco
                novo_dado = DadoClimatico.objects.create(
                    dispositivo=dispositivo,
                    time=dado['data'],
                    temperatura=dado.get('temperatura'),
                    umidade=dado.get('umidade'),
                    precipitacao=dado.get('precipitacao'),
                    velocidade_vento=dado.get('velocidade_vento'),
                    direcao_vento_id=direcao
                )
                criados.append(DadoClimaticoSerializer(novo_dado).data)
                
            except ValueError as e:
                erros.append({'index': idx, 'msg': f'Formato inválido: {str(e)}'})
            except DirecaoVento.DoesNotExist:
                erros.append({'index': idx, 'msg': f'Direção do vento inválida: {direcao_nome}'})
            except Exception as e:
                erros.append({'index': idx, 'msg': f'Erro interno: {str(e)}'})

        # Define resposta apropriada baseada nos resultados
        if erros and not criados:
            return Response(erros, status=status.HTTP_400_BAD_REQUEST)
        elif erros:
            return Response({
                "dados_criados": criados,
                "erros": erros
            }, status=status.HTTP_207_MULTI_STATUS)
        else:
            return Response(criados, status=status.HTTP_201_CREATED)


class DadoClimaticoDetailView(APIView):
    # Função auxiliar: Busca dado climático por ID
    def get_object(self, id):
        """Busca dado climático por ID com tratamento de erros"""
        try:
            return DadoClimatico.objects.get(id=id)
        except DadoClimatico.DoesNotExist:
            return None


    @extend_schema(
        parameters=[OpenApiParameter(name='id', type=int, location=OpenApiParameter.PATH, description="ID numérico do dado climático")],
        responses={
            200: DadoClimaticoSerializer,
            404: OpenApiExample("Não encontrado", value={"erro": "Registro não existe"})
        },
        examples=[
            OpenApiExample(
                "Não encontrado",
                value={"erro": "Dado climático não encontrado"},  
                response_only=True,
                status_codes=['404']
            ),
        ]
    )
    
    # GET: Recupera um dado climático específico por ID
    def get(self, request, id):
        """Busca dado climático pelo ID, retorna 404 se não encontrado"""
        dado = self.get_object(id)
        if not dado:
            return Response({"erro": "Dado climático não encontrado"}, status=404)
        serializer = DadoClimaticoSerializer(dado)
        return Response(serializer.data)

    @extend_schema(
        parameters=[OpenApiParameter(name='id', type=int, location=OpenApiParameter.PATH, description="ID numérico do dado climático")],
        request=DadoClimaticoSerializer,
        responses={
            200: DadoClimaticoSerializer,
            400: OpenApiExample("Erro", value={"temperatura": ["Valor inválido"]}),
            404: OpenApiExample("Não encontrado", value={"erro": "Registro não existe"})
        },
        examples=[
            OpenApiExample(
                "Não encontrado",
                value={"erro": "Dado climático não encontrado"},  
                response_only=True,
                status_codes=['404']
            ),
            OpenApiExample(
                "Direção do vento inválida",
                value={"erro": "Direção do vento inválida"},  
                response_only=True,
                status_codes=['400']
            ),
            OpenApiExample(
                "Valor numérico inválido",
                value={"erro": "Valor numérico inválido"},
                response_only=True,
                status_codes=['400']
            ),
            OpenApiExample(
                "Pelo menos um campo deve ser fornecido",
                value={"erro": "Pelo menos um campo deve ser fornecido"},
                response_only=True,
                status_codes=['400']
            )
        ]
    )
    
    # PUT: Atualiza dado climático existente
    def put(self, request, id):
        """
        Atualiza dado climático existente com validações:
        1. Verifica existência do dado
        2. Valida presença de pelo menos um campo
        3. Atualiza campos individualmente com conversão de tipos
        4. Valida direção do vento
        """
        dado = self.get_object(id)
        if not dado:
            return Response({"erro": "Dado não encontrado"}, status=404)

        # Verifica se pelo menos um campo válido foi fornecido
        campos_validos = ['data', 'temperatura', 'umidade', 'precipitacao', 'velocidade_vento', 'direcao_vento']
        if not any(field in request.data for field in campos_validos):
            return Response({"erro": "Pelo menos um campo deve ser fornecido"}, status=400)

        # Atualiza campos fornecidos
        if 'data' in request.data:
            dado.time = request.data['data']
        
        # Atualiza campos numéricos com conversão
        for campo in ['temperatura', 'umidade', 'precipitacao', 'velocidade_vento']:
            if campo in request.data:
                try:
                    setattr(dado, campo, float(request.data[campo]))
                except (TypeError, ValueError):
                    return Response({campo: ["Valor numérico inválido"]}, status=400)
        
        # Atualiza direção do vento se fornecida
        if 'direcao_vento' in request.data:
            try:
                direcao = DirecaoVento.objects.get(nome__iexact=request.data['direcao_vento'].upper())
                dado.direcao_vento = direcao
            except DirecaoVento.DoesNotExist:
                return Response({"erro": "Direção do vento inválida"}, status=400)

        dado.save()
        return Response(DadoClimaticoSerializer(dado).data)

    @extend_schema(
        parameters=[OpenApiParameter(name='id', type=int, location=OpenApiParameter.PATH, description="ID numérico do dado climático")],
        responses={204: None, 404: None})
    
    # DELETE: Remove dado climático existente
    def delete(self, request, id):
        """Exclui dado climático se existir, retorna 404 se não encontrado"""
        dado = self.get_object(id)
        if not dado:
            return Response(status=404)
        dado.delete()
        return Response(status=204)


class DadoClimaticoDispositivoView(APIView):
    @extend_schema(
        parameters=[OpenApiParameter(name='identificador', type=str, location=OpenApiParameter.PATH, description="ID numérico ou token UUID do dispositivo")],
        responses={
            200: DadoClimaticoSerializer(many=True),
            404: OpenApiExample("Erro", value={"erro": "Dispositivo não encontrado"})
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
    
    # GET: Lista dados climáticos de um dispositivo
    def get(self, request, identificador):
        """Busca dados por dispositivo (ID ou token)"""
        dispositivo = get_dispositivo(identificador)
        if not dispositivo:
            return Response({"erro": "Dispositivo não encontrado"}, status=404)
        dados = DadoClimatico.objects.filter(dispositivo=dispositivo)
        return Response(DadoClimaticoSerializer(dados, many=True).data)