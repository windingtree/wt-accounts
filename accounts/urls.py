# -*- coding: utf-8 -*-

from django.urls import path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path('', views.status, name='status'),
    path('registration/', views.registration, name='register'),
    path('login/', views.login, name='login_form'),
    path('logout/', views.logout, name='logout'),
    path('login/sent/', TemplateView.as_view(template_name='accounts/login_sent.html'),
         name='login_sent'),
    path('login/<uidb64>/<token>/', views.login_token, name='login_token'),
    path('login/expired/', views.login_token_expired, name='login_token_expired'),
    path('profile/', views.profile, name='profile'),
    path('eth_sums/', views.eth_sums, name='eth_sums'),
    path('3636696d3702717ee9a8ac110b73a96bc95af05a/unregistered_accounts/', views.unregistered_accounts, name='unregistered_accounts'),
    path('headers/', views.headers, name='headers'),

    path('webhook/onfido/', views.onfido_webhook, name='onfido_webhook'),

]
