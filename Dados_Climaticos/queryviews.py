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
from django.db.models import Count, Min, Max

#Ultimo dado enviado por um dispositivo
class UltimoDadoView(APIView):
    def get(self, request, identificador):
        
        dispositivo = get_dispositivo(identificador)
        if not dispositivo:
            return Response(
                {"erro": "Dispositivo não encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        
        dado = DadoClimatico.objects.filter(dispositivo_id=identificador).order_by('-time').first()
        if not dado:
            return Response({'erro': 'Nenhum dado encontrado.'}, status=404)
        
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
        
        
class QueryHistogramView(APIView):
    def get(self, request, identificador):
        # 1) Dispositivo
        dispositivo = get_dispositivo(identificador)
        if not dispositivo:
            return Response(
                {'status': 404, 'msg': 'Dispositivo não encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # 2) Parâmetros obrigatórios
        inicio = request.GET.get('inicio')
        fim    = request.GET.get('fim')
        tipo   = request.GET.get('tipo', 'temperatura')
        if not inicio or not fim:
            return Response(
                {'status': 400, 'msg': 'Parâmetros "inicio" e "fim" são obrigatórios.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3) Valida tipo
        campos_permitidos = ['temperatura', 'umidade', 'precipitacao', 'velocidade_vento']
        if tipo not in campos_permitidos:
            return Response(
                {'status': 400, 'msg': f'Tipo inválido. Escolha entre {campos_permitidos}.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4) Parse de datas
        try:
            inicio_dt = timezone.make_aware(datetime.fromisoformat(inicio))
            fim_dt    = timezone.make_aware(datetime.fromisoformat(fim))
        except Exception:
            return Response(
                {'status': 400, 'msg': 'Formato de data inválido. Use ISO 8601 com fuso.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 5) Parâmetros de histograma
        num_buckets = int(request.GET.get('num_buckets', 10))
        min_value = request.GET.get('min_value')
        max_value = request.GET.get('max_value')

        qs = DadoClimatico.timescale.filter(
            dispositivo=dispositivo,
            time__range=(inicio_dt, fim_dt)
        )

        # Se não vier min/max, buscamos dinamicamente
        if min_value is None or max_value is None:
            agg = qs.aggregate(
                mn=Min(tipo),
                mx=Max(tipo)
            )
            min_value = agg['mn']
            max_value = agg['mx']

        # 6) Monta o histograma
        histo_qs = (
            qs
            .histogram(
                field=tipo,
                min_value=float(min_value),
                max_value=float(max_value),
                num_of_buckets=num_buckets
            )
            .annotate(device_count=Count('dispositivo'))
        )

        # 7) Formata o resultado
        # histo_qs retorna algo tipo:
        # [ {'histogram': [..], 'device_count': 123} ]
        result = list(histo_qs)

        return Response({
            'status': 200,
            'dispositivo': identificador,
            'tipo': tipo,
            'inicio': inicio,
            'fim': fim,
            'num_buckets': num_buckets,
            'min_value': min_value,
            'max_value': max_value,
            'dados': result
        }, status=status.HTTP_200_OK)
