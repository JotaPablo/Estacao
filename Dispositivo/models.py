import uuid
from django.db import models
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point



class Dispositivo(models.Model):
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    descricao = models.TextField(blank=True, null=True)
    localizacao = models.PointField(geography=True, null=True, default=Point(0.0, 0.0))

    def __str__(self):
        return f"{self.descricao} ({self.token})"