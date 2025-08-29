from django.urls import path

from reservation import views
from reservation.apps import ReservationConfig
from reservation.views import home, ReservationDeleteView, ReservationUpdateView, ReservationCreateView, \
    ReservationListView, AboutView, ContactView, reservation_welcome, ProfileView, ReservationDetailView, \
    TablesByHallView, HallListView, FeedbackView, FeedbackThanksView

app_name = ReservationConfig.name

urlpatterns = [
    path('', home, name='home'),
    path("contacts/", ContactView.as_view(), name="contact"),
    path('reservation/list/', ReservationListView.as_view(), name='reservations_list'),
    path('reservation/create/', ReservationCreateView.as_view(), name='reservations_create'),
    path('reservation/detail/<int:pk>/', ReservationDetailView.as_view(), name='reservations_detail'),
    path('reservation/update/<int:pk>/', ReservationUpdateView.as_view(), name='reservations_update'),
    path('reservation/delete/<int:pk>/', ReservationDeleteView.as_view(), name='reservations_delete'),
    path('api/tables-by-hall/<int:hall_id>/', TablesByHallView.as_view(), name='tables_by_hall'),
    path('hall/<int:hall_id>/schema/', views.hall_schema, name='hall_schema'),
    path('halls/', HallListView.as_view(), name='hall_list'),
    path('reservation_welcome/', reservation_welcome, name='reservation_welcome'),
    path("about/", AboutView.as_view(), name="about"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("feedback/", FeedbackView.as_view(), name="feedback"),
    path("feedback/thanks/", FeedbackThanksView.as_view(), name="feedback_thanks"),

]
