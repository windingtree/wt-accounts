# -*- coding: utf-8 -*-

from django.urls import path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path('registration/', views.registration, name='register'),
    path('login/', views.login, name='login_form'),
    path('logout/', views.logout, name='logout'),
    path('login/sent/', TemplateView.as_view(template_name='accounts/login_sent.html'),
         name='login_sent'),
    path('login/<uidb64>/<token>/', views.login_token, name='login_token'),
    path('profile/', views.profile, name='profile'),

]
