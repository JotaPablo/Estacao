from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Dispositivo
from .serializer import DispositivoSerializer
from utils import is_valid_uuid
from django.contrib.gis.geos import Point


class DispositivoListView(APIView):

    def get(self, request):
        dispositivos = Dispositivo.objects.all()
        serializer = DispositivoSerializer(dispositivos, many=True)
        return Response({
            'status': 200,
            'msg': 'Lista de dispositivos.',
            'dispositivos': serializer.data
        }, status=200)

    def post(self, request):
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        descricao = request.data.get('descricao')

        if not latitude or not longitude:
            return Response({
                'status': 400,
                'msg': 'Latitude e longitude são obrigatórias.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            
            #Cria o ponto geográfico usando latitude e longitude
            ponto_geografico = Point(float(longitude), float(latitude))
            
            dispositivo = Dispositivo.objects.create(
                descricao=descricao,
                localizacao = ponto_geografico
            )

            return Response({
                'status': 201,
                'msg': 'Dispositivo criado com sucesso.',
                'dispositivo': DispositivoSerializer(dispositivo).data
            }, status=status.HTTP_201_CREATED)

        except (ValueError, TypeError):
            return Response({
                'status': 400,
                'msg': 'Latitude e longitude devem ser números válidos.'
            }, status=status.HTTP_400_BAD_REQUEST)


class DispositivoDetailView(APIView):
    def get_dispositivo(self, identificador):
        try:
            if identificador.isdigit():
                return Dispositivo.objects.get(id=int(identificador))
            else:
                if not is_valid_uuid(identificador):
                    return Response({'status': 404,
                                     'msg': 'UUID inválido'
                                     }, status=400)
                return Dispositivo.objects.get(token=identificador)
        except Dispositivo.DoesNotExist:
            return None

    def get(self, request, identificador):
        dispositivo = self.get_dispositivo(identificador)
        if not dispositivo:
            return Response({
                'status': 404,
                'msg': 'Dispositivo não encontrado.'
            }, status=404)

        serializer = DispositivoSerializer(dispositivo)
        return Response({
            'status': 200,
            'msg': 'Dispositivo encontrado.',
            'dispositivo': serializer.data
        }, status=200)

    def put(self, request, identificador):
        dispositivo = self.get_dispositivo(identificador)
        if not dispositivo:
            return Response({
                'status': 404,
                'msg': 'Dispositivo não encontrado.'
            }, status=404)

        descricao = request.data.get('descricao')
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')

        try:
            if latitude is not None and longitude is not None:
                ponto_geografico = Point(float(longitude), float(latitude))
                dispositivo.localizacao = ponto_geografico
                
            if descricao is not None:
                dispositivo.descricao = descricao

            dispositivo.save()

            return Response({
                'status': 200,
                'msg': 'Dispositivo atualizado com sucesso.',
                'dispositivo': DispositivoSerializer(dispositivo).data
            }, status=200)

        except (ValueError, TypeError):
            return Response({
                'status': 400,
                'msg': 'Latitude e longitude devem ser números válidos.'
            }, status=400)

    def delete(self, request, identificador):
        dispositivo = self.get_dispositivo(identificador)
        if not dispositivo:
            return Response({
                'status': 404,
                'msg': 'Dispositivo não encontrado.'
            }, status=404)

        dispositivo.delete()
        return Response({
            'status': 204,
            'msg': 'Dispositivo deletado com sucesso.'
        }, status=204)
