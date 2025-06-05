from django.urls import path
from .views import DadoClimaticoListView, DadoClimaticoDetailView, DadoClimaticoDispositivoView, QueryTimeBucketView

urlpatterns = [
    path('dados_climaticos/', DadoClimaticoListView.as_view()),
    path('dados_climaticos/<int:id>/', DadoClimaticoDetailView.as_view()),
    path('dados_climaticos/dispositivo/<str:identificador>/', DadoClimaticoDispositivoView.as_view()),
    path('dados_climaticos/time_bucket/dispositivo/<str:identificador>/', QueryTimeBucketView.as_view())
]