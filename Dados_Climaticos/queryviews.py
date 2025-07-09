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
