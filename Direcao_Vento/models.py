from django.db import models

class DirecaoVento(models.Model):
    
    class Meta:
        db_table = "direcao_vento"
    
    nome = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nome