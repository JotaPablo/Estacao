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

class DadoClimaticoListView(APIView):

    def get(self, request):
        dados = DadoClimatico.objects.all()
        serializer = DadoClimaticoSerializer(dados, many=True)
        return Response({
            'status': 200,
            'msg': 'Lista de dados climáticos.',
            'dados_climaticos': serializer.data
        }, status=200)

    def post(self, request):
        token = request.data.get('token')
        dados_input = request.data.get('dado')

        # Validação de campos obrigatórios
        if not token or not dados_input:
            return Response({
                'status': 400,
                'msg': 'Token do dispositivo e dados climáticos são obrigatórios.'
            }, status=400)

        if not is_valid_uuid(token):
            return Response({'status': 400, 'msg': 'UUID inválido'}, status=400)

        try:
            dispositivo = Dispositivo.objects.get(token=token)
        except Dispositivo.DoesNotExist:
            return Response({
                'status': 404,
                'msg': 'Dispositivo com esse token não encontrado.'
            }, status=404)

        # Garante que estamos lidando com uma lista
        dados = dados_input if isinstance(dados_input, list) else [dados_input]

        criados = []
        erros = []

        for idx, dado in enumerate(dados):
            try:
                data = dado.get('data')
                temperatura = dado.get('temperatura')
                umidade = dado.get('umidade')
                precipitacao = dado.get('precipitacao')
                velocidade_vento = dado.get('velocidade_vento')
                direcao_nome = dado.get('direcao_vento')

                direcao = None
                if direcao_nome:
                    direcao_nome = direcao_nome.upper()
                    try:
                        direcao = DirecaoVento.objects.get(nome__iexact=direcao_nome)
                    except DirecaoVento.DoesNotExist:
                        erros.append({
                            'index': idx,
                            'msg': f'Direção do vento "{direcao_nome}" não encontrada.'
                        })
                        continue

                novo_dado = DadoClimatico.objects.create(
                    dispositivo=dispositivo,
                    time=data,
                    temperatura=float(temperatura) if temperatura else None,
                    umidade=float(umidade) if umidade else None,
                    precipitacao=float(precipitacao) if precipitacao else None,
                    velocidade_vento=float(velocidade_vento) if velocidade_vento else None,
                    direcao_vento_id=direcao
                )

                criados.append(DadoClimaticoSerializer(novo_dado).data)

            except (ValueError, TypeError):
                erros.append({
                    'index': idx,
                    'msg': 'Erro ao converter campos numéricos.'
                })

        return Response({
            'status': 207 if erros else 201,
            'msg': 'Alguns dados não foram criados.' if erros else 'Todos os dados foram criados com sucesso.',
            'dados_criados': criados,
            'erros': erros
        }, status=207 if erros else 201)
            
class DadoClimaticoDetailView(APIView):
    def get_object(self, id):
        try:
            return DadoClimatico.objects.get(id=id)
        except DadoClimatico.DoesNotExist:
            return None

    def get(self, request, id):
        dado = self.get_object(id)
        if not dado:
            return Response({
                'status': 404,
                'msg': 'Dado climático não encontrado.'
            }, status=404)

        serializer = DadoClimaticoSerializer(dado)
        return Response({
            'status': 200,
            'msg': 'Dado climático encontrado.',
            'dado_climatico': serializer.data
        }, status=200)

    def put(self, request, id):
        dado = self.get_object(id)
        if not dado:
            return Response({
                'status': 404,
                'msg': 'Dado climático não encontrado.'
            }, status=404)

        data = request.data.get('data')
        temperatura = request.data.get('temperatura')
        umidade = request.data.get('umidade')
        precipitacao = request.data.get('precipitacao')
        velocidade_vento = request.data.get('velocidade_vento')
        direcao_vento_nome = request.data.get('direcao_vento')

        if data is not None:
            dado.time = data
        if temperatura is not None:
            try:
                dado.temperatura = float(temperatura)
            except ValueError:
                return Response({'status': 400, 'msg': 'Temperatura inválida.'}, status=400)
        if umidade is not None:
            try:
                dado.umidade = float(umidade)
            except ValueError:
                return Response({'status': 400, 'msg': 'Umidade inválida.'}, status=400)
        if precipitacao is not None:
            try:
                dado.precipitacao = float(precipitacao)
            except ValueError:
                return Response({'status': 400, 'msg': 'Precipitação inválida.'}, status=400)
        if velocidade_vento is not None:
            try:
                dado.velocidade_vento = float(velocidade_vento)
            except ValueError:
                return Response({'status': 400, 'msg': 'Velocidade do vento inválida.'}, status=400)

        # Atualizar direção do vento se fornecida
        if direcao_vento_nome:
            try:
                direcao = DirecaoVento.objects.get(nome__iexact=direcao_vento_nome.upper())
                dado.direcao_vento_id = direcao
            except DirecaoVento.DoesNotExist:
                return Response({
                    'status': 404,
                    'msg': f'Direção do vento "{direcao_vento_nome}" não encontrada.'
                }, status=404)

        dado.save()
        return Response({
            'status': 200,
            'msg': 'Dado climático atualizado com sucesso.',
            'dado_climatico': DadoClimaticoSerializer(dado).data
        }, status=200)

    def delete(self, request, id):
        dado = self.get_object(id)
        if not dado:
            return Response({
                'status': 404,
                'msg': 'Dado climático não encontrado.'
            }, status=404)

        dado.delete()
        return Response({
            'status': 204,
            'msg': 'Dado climático deletado com sucesso.'
        }, status=204)

class DadoClimaticoDispositivoView(APIView):
    
      def get(self, request, identificador):
        dispositivo = get_dispositivo(identificador)
        if not dispositivo:
            return Response({
                'status': 404,
                'msg': 'Dispositivo não encontrado.'
            }, status=404)

        dados = DadoClimatico.objects.filter(dispositivo_id=dispositivo.id)
        serializer = DadoClimaticoSerializer(dados, many=True)
        return Response({
            'status': 200,
            'msg': f'Dados climáticos do dispositivo {identificador}.',
            'dados_climaticos': serializer.data
        }, status=200)

        
