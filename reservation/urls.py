from django.urls import path
from reservation.apps import ReservationConfig
from reservation.views import home

app_name = ReservationConfig.name

urlpatterns = [
    path('', home, name='home')
]
