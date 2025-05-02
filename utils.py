import uuid
from Dispositivo.models import Dispositivo
from rest_framework.response import Response


def is_valid_uuid(value):
    try:
        uuid.UUID(str(value))
        return True
    except ValueError:
        return False
    
def get_dispositivo(identificador):
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