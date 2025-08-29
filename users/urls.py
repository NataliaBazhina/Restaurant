from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from users.apps import UsersConfig
from users.views import UserCreateView, email_verification, change_password, UserUpdateView, UserDeleteView, \
    UserListView, UserDetailView

app_name = UsersConfig.name

urlpatterns = [
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', UserCreateView.as_view(), name='register'),
    path('email-confirm/<str:token>/', email_verification, name='email-confirm'),
    path('change_password/', change_password, name="change_password"),
    path('users/list/', UserListView.as_view(),name='users_list'),
    path('user/detail/<int:pk>/', UserDetailView.as_view(), name='user_detail'),
    path('user/update/<int:pk>/', UserUpdateView.as_view(), name='user_update'),
    path('users/delete/<int:pk>/', UserDeleteView.as_view(), name='user_delete'),
]
