from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import DadoClimatico
from .serializer import DadoClimaticoSerializer
from django.db.models import Count, Avg
from Dispositivo.models import Dispositivo
from Direcao_Vento.models import DirecaoVento
from django.utils import timezone
from datetime import datetime
from utils import is_valid_uuid, get_dispositivo
import numpy as np
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiExample

#Ultimo dado enviado por um dispositivo
class UltimoDadoView(APIView):
    def get(self, request, identificador):
        dado = DadoClimatico.objects.filter(dispositivo_id=identificador).order_by('-time').first()
        if not dado:
            return Response({'msg': 'Nenhum dado encontrado.'}, status=404)
        
        serializer = DadoClimaticoSerializer(dado)
        return Response(serializer.data)
    
    
class QueryMediaUnicaView(APIView):
    def get(self, request, identificador):
        dispositivo = get_dispositivo(identificador)
        if not dispositivo:
            return Response({
                'status': 404,
                'msg': 'Dispositivo não encontrado.'
            }, status=404)

        inicio_str = request.GET.get('inicio')
        fim_str = request.GET.get('fim')
        tipo = request.GET.get('tipo', 'temperatura')

        if not inicio_str or not fim_str:
            return Response({
                'status': 400,
                'msg': 'Parâmetros "inicio" e "fim" são obrigatórios.'
            }, status=400)

        if tipo not in ['temperatura', 'umidade', 'precipitacao', 'velocidade_vento']:
            return Response({
                'status': 400,
                'msg': 'Parâmetro "tipo" inválido.'
            }, status=400)

        periodo = request.GET.get('periodo', 'semana')  # dia, semana, mes
        quantidade = int(request.GET.get('quantidade', 1))

        mapa_periodo = {
            'dia': 'day',
            'semana': 'week',
            'mes': 'month'
        }

        if periodo not in mapa_periodo:
            return Response({
                'status': 400,
                'msg': 'Parâmetro "periodo" inválido. Use "dia", "semana" ou "mes".'
            }, status=400)

        if quantidade < 1 or quantidade > 31:
            return Response({
                'status': 400,
                'msg': 'Parâmetro "quantidade" deve ser entre 1 e 31.'
            }, status=400)

        # Intervalo formatado: '2 weeks', '1 day', etc.
        intervalo = f"{quantidade} {mapa_periodo[periodo]}"

        try:
            inicio = timezone.make_aware(datetime.fromisoformat(inicio_str))
            fim = timezone.make_aware(datetime.fromisoformat(fim_str))
        except ValueError:
            return Response({
                'status': 400,
                'msg': 'Data "inicio" ou "fim" inválida'
            }, status=400)

        
        campo_avg = f'{tipo}_avg'
        

        query = (
            DadoClimatico.timescale
            .filter(dispositivo=dispositivo, time__range=(inicio, fim))
            .time_bucket_gapfill('time', intervalo, inicio, fim)
            .annotate(**{campo_avg: Avg(tipo)})
            .order_by('bucket')
        )

        return Response({
            'status': 200,
            'tipo': tipo,
            'intervalo': intervalo,
            'dados': list(query)
        })
    
@extend_schema(
    description="Retorna os dados climáticos dos dispositivos no período especificado.",
    parameters=[
        OpenApiParameter(
            name='dispositivos',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Lista de IDs dos dispositivos (ex: dispositivos=1&dispositivos=2)'
        ),
        OpenApiParameter(
            name='inicio',
            type=OpenApiTypes.DATETIME,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Data/hora de início no formato ISO 8601 (ex: 2025-03-31T07:54:57)'
        ),
        OpenApiParameter(
            name='fim',
            type=OpenApiTypes.DATETIME,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Data/hora de fim no formato ISO 8601 (ex: 2025-04-01T07:54:57)'
        ),
    ],
    responses={
        200: OpenApiTypes.OBJECT,
        400: OpenApiTypes.OBJECT,
    },
    examples=[
        OpenApiExample(
            'Parâmetros obrigatórios ausentes',
            value={
                "status": 400,
                "msg": 'Parâmetros "dispositivos", "inicio" e "fim" são obrigatórios.'
            },
            response_only=True,
            status_codes=['400']
        ),
        OpenApiExample(
            'IDs inválidos em dispositivos',
            value={
                "status": 400,
                "msg": 'IDs inválidos em "dispositivos".'
            },
            response_only=True,
            status_codes=['400']
        ),
        OpenApiExample(
            'Formato inválido de datas',
            value={
                "status": 400,
                "msg": 'Datas "inicio" e "fim" devem estar no formato ISO 8601.'
            },
            response_only=True,
            status_codes=['400']
        ),
        OpenApiExample(
            'Sucesso com dados climáticos',
            value={
                "status": 200,
                "msg": "Dados climáticos dos dispositivos no período 2025-03-31T07:00:00 a 2025-03-31T09:00:00.",
                "dados_climaticos": [
                    {
                        "id": 1,
                        "dispositivo": 1,
                        "data": "2025-03-31T07:54:57-03:00",
                        "temperatura": 30.2,
                        "umidade": 0.8,
                        "precipitacao": 0.2,
                        "velocidade_vento": 10.5
                    },
                    {
                        "id": 2,
                        "dispositivo": 1,
                        "data": "2025-03-31T08:54:57-03:00",
                        "temperatura": 20.2,
                        "umidade": 0.8,
                        "precipitacao": 0.2,
                        "velocidade_vento": 5.5
                    }
                ]
            },
            response_only=True,
            status_codes=['200']
        ),
        OpenApiExample(
            'Nenhum dado encontrado',
            value={
                "status": 200,
                "msg": "Nenhum dado climático encontrado para os dispositivos no período 2025-03-31T07:00:00 a 2025-03-31T09:00:00.",
                "dados_climaticos": []
            },
            response_only=True,
            status_codes=["200"]
        )
    ]
)

class DadoClimaticoPorPeriodoView(APIView):
    def get(self, request):
        # Captura os parâmetros da URL: lista de dispositivos, data de início e data de fim
        dispositivos_ids = request.query_params.getlist('dispositivos')
        inicio_str = request.query_params.get('inicio')
        fim_str = request.query_params.get('fim')

        # Valida se todos os parâmetros foram fornecidos
        if not dispositivos_ids or not inicio_str or not fim_str:
            return Response({
                'status': 400,
                'msg': 'Parâmetros "dispositivos", "inicio" e "fim" são obrigatórios.'
            }, status=400)

        # Tenta converter os IDs dos dispositivos para inteiros
        try:
            dispositivos_ids = [int(i) for i in dispositivos_ids]
        except ValueError:
            return Response({
                'status': 400,
                'msg': 'IDs inválidos em "dispositivos".'
            }, status=400)

        # Tenta converter as strings de data para objetos datetime conscientes de fuso horário
        try:
            inicio = timezone.make_aware(datetime.fromisoformat(inicio_str))
            fim = timezone.make_aware(datetime.fromisoformat(fim_str))
        except ValueError:
            return Response({
                'status': 400,
                'msg': 'Datas "inicio" e "fim" devem estar no formato ISO 8601.'
            }, status=400)

        # Filtra os dados climáticos no intervalo de tempo e pelos dispositivos
        dados = DadoClimatico.objects.filter(
            dispositivo_id__in=dispositivos_ids,
            time__range=(inicio, fim)
        )

         # Retorno específico se não houver dados encontrados
        if not dados.exists():
            return Response({
                'status': 200,
                'msg': f'Nenhum dado climático encontrado para os dispositivos no período {inicio_str} a {fim_str}.',
                'dados_climaticos': []
            })
        
        # Serializa os dados para retorno em JSON
        serializer = DadoClimaticoSerializer(dados, many=True)

        # Retorna a resposta com status e dados encontrados
        return Response({
            'status': 200,
            'msg': f'Dados climáticos dos dispositivos no período {inicio_str} a {fim_str}.',
            'dados_climaticos': serializer.data
        })

  
@extend_schema(
    description="Gera um histograma dos valores de temperatura ou umidade para os dispositivos informados, dentro de um intervalo de tempo.",
    parameters=[
        OpenApiParameter(
            name='dispositivos',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Lista de IDs dos dispositivos (ex: dispositivos=1&dispositivos=2)'
        ),
        OpenApiParameter(
            name='campo',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Campo a ser analisado: "temperatura" ou "umidade"'
        ),
        OpenApiParameter(
            name='inicio',
            type=OpenApiTypes.DATETIME,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Data/hora inicial (ex: 2025-03-31T07:54:57)'
        ),
        OpenApiParameter(
            name='fim',
            type=OpenApiTypes.DATETIME,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Data/hora final (ex: 2025-04-01T07:54:57)'
        ),
        OpenApiParameter(
            name='bins',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            required=False,
            description='Quantidade de divisões (bins) no histograma. Padrão: 10'
        ),
    ],
    responses={
        200: OpenApiTypes.OBJECT,
        400: OpenApiTypes.OBJECT
    },
     examples=[
        OpenApiExample(
            'Sucesso com dados',
            value={
                "status": 200,
                "msg": "Histograma de temperatura para dispositivos [1, 2] entre 2025-03-31T07:54:57 e 2025-04-01T07:54:57.",
                "histograma": [
                    {"bin_inicio": 20.0, "bin_fim": 21.0, "quantidade": 10},
                    {"bin_inicio": 21.0, "bin_fim": 22.0, "quantidade": 15},
                    {"bin_inicio": 22.0, "bin_fim": 23.0, "quantidade": 5}
                ]
            },
            response_only=True,
            status_codes=['200']
        ),
        OpenApiExample(
            'Sucesso sem dados',
            value={
                "status": 200,
                "msg": "Nenhum dado encontrado no período para os dispositivos.",
                "histograma": []
            },
            response_only=True,
            status_codes=['200']
        ),
        OpenApiExample(
            'Parâmetros inválidos',
            value={
                "status": 400,
                "msg": "Parâmetros inválidos."
            },
            response_only=True,
            status_codes=['400']
        ),
        OpenApiExample(
            'Dispositivos ausentes',
            value={
                "status": 400,
                "msg": '"dispositivos" deve ser uma lista de IDs.'
            },
            response_only=True,
            status_codes=['400']
        ),

        OpenApiExample(
            'Campo inválido',
            value={
                "status": 400,
                "msg": 'Campo deve ser "temperatura" ou "umidade".'
            },
            response_only=True,
            status_codes=['400']
        ),

        OpenApiExample(
            'Datas ausentes',
            value={
                "status": 400,
                "msg": 'Parâmetros "inicio" e "fim" são obrigatórios.'
            },
            response_only=True,
            status_codes=['400']
        )
    ]
)
class HistogramaPorDispositivosView(APIView):
    def get(self, request):
        # Captura os parâmetros da URL
        dispositivos_ids = request.query_params.getlist('dispositivos')
        campo = request.query_params.get('campo')
        inicio_str = request.query_params.get('inicio')
        fim_str = request.query_params.get('fim')
        bins = request.query_params.get('bins', 10)  # valor padrão é 10

        # Validação dos dispositivos
        if not dispositivos_ids:
            return Response({'status': 400, 'msg': '"dispositivos" deve ser uma lista de IDs.'}, status=400)

        # Validação do campo analisado
        if campo not in ['temperatura', 'umidade']:
            return Response({'status': 400, 'msg': 'Campo deve ser "temperatura" ou "umidade".'}, status=400)

        # Validação das datas
        if not inicio_str or not fim_str:
            return Response({'status': 400, 'msg': 'Parâmetros "inicio" e "fim" são obrigatórios.'}, status=400)

        # Conversão e validação dos tipos
        try:
            dispositivos_ids = [int(i) for i in dispositivos_ids]
            inicio = timezone.make_aware(datetime.fromisoformat(inicio_str))
            fim = timezone.make_aware(datetime.fromisoformat(fim_str))
            bins = int(bins)
        except Exception:
            return Response({'status': 400, 'msg': 'Parâmetros inválidos.'}, status=400)

        # Consulta dos valores do campo específico, ignorando nulos
        valores_qs = DadoClimatico.objects.filter(
            dispositivo_id__in=dispositivos_ids,
            time__range=(inicio, fim),
        ).values_list(campo, flat=True).exclude(**{f'{campo}__isnull': True})

        valores = list(valores_qs)

        # Retorno caso não haja dados
        if not valores:
            return Response({
                'status': 200,
                'msg': 'Nenhum dado encontrado no período para os dispositivos.',
                'histograma': []
            })

        # Geração do histograma com numpy
        counts, bin_edges = np.histogram(valores, bins=bins)

        # Formata os dados para o retorno
        histograma = []
        for i in range(len(counts)):
            histograma.append({
                'bin_inicio': float(bin_edges[i]),
                'bin_fim': float(bin_edges[i+1]),
                'quantidade': int(counts[i])
            })

        # Resposta final com status, mensagem e histograma
        return Response({
            'status': 200,
            'msg': f'Histograma de {campo} para dispositivos {dispositivos_ids} entre {inicio_str} e {fim_str}.',
            'histograma': histograma
        })