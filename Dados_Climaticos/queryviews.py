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
    
class DadoClimaticoPorPeriodoView(APIView):

    def get(self, request):
        dispositivos_ids = request.query_params.getlist('dispositivos')
        inicio_str = request.query_params.get('inicio')
        fim_str = request.query_params.get('fim')

        if not dispositivos_ids or not inicio_str or not fim_str:
            return Response({
                'status': 400,
                'msg': 'Parâmetros "dispositivos", "inicio" e "fim" são obrigatórios.'
            }, status=400)

        try:
            dispositivos_ids = [int(i) for i in dispositivos_ids]
        except ValueError:
            return Response({
                'status': 400,
                'msg': 'IDs inválidos em "dispositivos".'
            }, status=400)

        try:
            inicio = timezone.make_aware(datetime.fromisoformat(inicio_str))
            fim = timezone.make_aware(datetime.fromisoformat(fim_str))
        except ValueError:
            return Response({
                'status': 400,
                'msg': 'Datas "inicio" e "fim" devem estar no formato ISO 8601.'
            }, status=400)

        dados = DadoClimatico.objects.filter(
            dispositivo_id__in=dispositivos_ids,
            time__range=(inicio, fim)
        )

        serializer = DadoClimaticoSerializer(dados, many=True)

        return Response({
            'status': 200,
            'msg': f'Dados climáticos dos dispositivos no período {inicio_str} a {fim_str}.',
            'dados_climaticos': serializer.data
        })

    

class HistogramaPorDispositivosView(APIView):
    def get(self, request):
        dispositivos_ids = request.query_params.getlist('dispositivos')
        campo = request.query_params.get('campo')
        inicio_str = request.query_params.get('inicio')
        fim_str = request.query_params.get('fim')
        bins = request.query_params.get('bins', 10)

        if not dispositivos_ids:
            return Response({'status': 400, 'msg': '"dispositivos" deve ser uma lista de IDs.'}, status=400)

        if campo not in ['temperatura', 'umidade']:
            return Response({'status': 400, 'msg': 'Campo deve ser "temperatura" ou "umidade".'}, status=400)

        if not inicio_str or not fim_str:
            return Response({'status': 400, 'msg': 'Parâmetros "inicio" e "fim" são obrigatórios.'}, status=400)

        try:
            dispositivos_ids = [int(i) for i in dispositivos_ids]
            inicio = timezone.make_aware(datetime.fromisoformat(inicio_str))
            fim = timezone.make_aware(datetime.fromisoformat(fim_str))
            bins = int(bins)
        except Exception:
            return Response({'status': 400, 'msg': 'Parâmetros inválidos.'}, status=400)

        valores_qs = DadoClimatico.objects.filter(
            dispositivo_id__in=dispositivos_ids,
            time__range=(inicio, fim),
        ).values_list(campo, flat=True).exclude(**{f'{campo}__isnull': True})

        valores = list(valores_qs)

        if not valores:
            return Response({'status': 200, 'msg': 'Nenhum dado encontrado no período para os dispositivos.', 'histograma': []})

        counts, bin_edges = np.histogram(valores, bins=bins)

        histograma = []
        for i in range(len(counts)):
            histograma.append({
                'bin_inicio': float(bin_edges[i]),
                'bin_fim': float(bin_edges[i+1]),
                'quantidade': int(counts[i])
            })

        return Response({
            'status': 200,
            'msg': f'Histograma de {campo} para dispositivos {dispositivos_ids} entre {inicio_str} e {fim_str}.',
            'histograma': histograma
        })