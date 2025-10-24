from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Autenticação
    path('login/', auth_views.LoginView.as_view(template_name='travels/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),

    # Home
    path('', views.home, name='home'),

    # Solicitante
    path('minhas-solicitacoes/', views.my_requests, name='my_requests'),
    path('nova-solicitacao/', views.create_request, name='create_request'),
    path('conta-bancaria/', views.bank_account, name='bank_account'),

    # Visualização de solicitação
    path('solicitacao/<int:pk>/', views.request_detail, name='request_detail'),

    # Aprovador
    path('dashboard/', views.dashboard, name='dashboard'),
    path('todas-solicitacoes/', views.all_requests, name='all_requests'),
    path('aprovar/<int:pk>/', views.approve_request, name='approve_request'),
    path('rejeitar/<int:pk>/', views.reject_request, name='reject_request'),
]
