from django.urls import path
from .views import DadoClimaticoListView, DadoClimaticoDetailView, DadoClimaticoDispositivoView
from .queryviews import UltimoDadoView, QueryMediaUnicaView, DadoClimaticoPorPeriodoView, HistogramaPorDispositivosView

urlpatterns = [
    path('dados_climaticos/', DadoClimaticoListView.as_view()),
    path('dados_climaticos/<int:id>/', DadoClimaticoDetailView.as_view()),
    path('dados_climaticos/dispositivo/<str:identificador>/', DadoClimaticoDispositivoView.as_view()),
    path('dados_climaticos/dispositivo/<str:identificador>/media/', QueryMediaUnicaView.as_view()),
    path('dados_climaticos/dispositivos/<str:identificador>/ultimo-dado/', UltimoDadoView.as_view()), 
    path('dados_climaticos/dispositivos/por_periodo/', DadoClimaticoPorPeriodoView.as_view()),
    path('dados_climaticos/dispositivos/histograma/', HistogramaPorDispositivosView.as_view()),
]