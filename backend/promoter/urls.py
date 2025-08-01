from .views import PromoterListCreateAPIView,PromoterRetrieveUpdateDestroyAPIView
from django.urls import path

urlpatterns = [
    path('promoter/',PromoterListCreateAPIView.as_view()),
    path('promoter/<int:id>/',PromoterRetrieveUpdateDestroyAPIView.as_view())
]

