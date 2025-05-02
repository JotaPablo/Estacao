from django.urls import path
from .views import DirecaoVentoListView, DirecaoVentoDetailView

urlpatterns = [
    path('direcao_vento/', DirecaoVentoListView.as_view()),
    path('direcao_vento/<int:id>/', DirecaoVentoDetailView.as_view()),
]