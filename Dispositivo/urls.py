from django.urls import path
from .views import DispositivoListView, DispositivoDetailView

urlpatterns = [
  path('dispositivo/', DispositivoListView.as_view()),
  path('dispositivo/<str:id>/', DispositivoDetailView.as_view()),
]