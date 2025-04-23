from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.home_view, name='home-url'),
    path('register/', views.register_view, name='register-url'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login-url'),
    path('logout/', LogoutView.as_view(next_page='login-url'), name='logout-url'),
]