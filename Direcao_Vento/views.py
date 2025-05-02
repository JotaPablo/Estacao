from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import DirecaoVento
from .serializer import DirecaoVentoSerializer

class DirecaoVentoListView(APIView):

    def get(self, request):
        direcoes = DirecaoVento.objects.all()
        serializer = DirecaoVentoSerializer(direcoes, many=True)
        return Response({
            'status': 200,
            'msg': 'Lista de direções do vento.',
            'direcoes_vento': serializer.data
        }, status=200)

    def post(self, request):
        nome = request.data.get('nome')
        
        nome_upper = nome.upper()
        

        if DirecaoVento.objects.filter(nome=nome_upper).exists():
            return Response({
                'status': 400,
                'msg': 'Já existe uma direção do vento com esse nome.'
            }, status=400)

        if not nome:
            return Response({
                'status': 400,
                'msg': 'O campo "nome" é obrigatório.'
            }, status=400)

        
        direcao = DirecaoVento.objects.create(nome=nome_upper)

        return Response({
            'status': 201,
            'msg': 'Direção do vento criada com sucesso.',
            'direcao_vento': DirecaoVentoSerializer(direcao).data
        }, status=201)


class DirecaoVentoDetailView(APIView):

    def get(self, request, id):
        try:
            direcao = DirecaoVento.objects.get(id=id)
            serializer = DirecaoVentoSerializer(direcao)
            return Response({
                'status': 200,
                'msg': 'Direção do vento encontrada.',
                'direcao_vento': serializer.data
            }, status=200)
        except DirecaoVento.DoesNotExist:
            return Response({
                'status': 404,
                'msg': 'Direção do vento não encontrada.'
            }, status=404)

    def put(self, request, id):
        try:
            direcao = DirecaoVento.objects.get(id=id)
            nome = request.data.get('nome')
            
            nome_upper = nome.upper()

            if DirecaoVento.objects.filter(nome=nome_upper).exists():
                return Response({
                    'status': 400,
                    'msg': 'Já existe uma direção do vento com esse nome.'
                }, status=400)

            if nome:
                direcao.nome = nome
                direcao.save()
                return Response({
                    'status': 200,
                    'msg': 'Direção do vento atualizada com sucesso.',
                    'direcao_vento': DirecaoVentoSerializer(direcao).data
                }, status=200)
            else:
                return Response({
                    'status': 400,
                    'msg': 'O campo "nome" é obrigatório para atualização.'
                }, status=400)

        except DirecaoVento.DoesNotExist:
            return Response({
                'status': 404,
                'msg': 'Direção do vento não encontrada.'
            }, status=404)

    def delete(self, request, id):
        try:
            direcao = DirecaoVento.objects.get(id=id)
            direcao.delete()
            return Response({
                'status': 204,
                'msg': 'Direção do vento deletada com sucesso.'
            }, status=204)
        except DirecaoVento.DoesNotExist:
            return Response({
                'status': 404,
                'msg': 'Direção do vento não encontrada.'
            }, status=404)
