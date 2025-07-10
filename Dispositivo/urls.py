from django.urls import path
from .views import DispositivoListView, DispositivoDetailView
from .queryviews import DispositivoMaisProximoView,DispositivosProximosRaioView

urlpatterns = [
  path('dispositivo/', DispositivoListView.as_view()),
  path('dispositivo/<str:identificador>/', DispositivoDetailView.as_view()),
  path('dispositivos/proximo/', DispositivoMaisProximoView.as_view()),
  path('dispositivos/raio/', DispositivosProximosRaioView.as_view()),
]