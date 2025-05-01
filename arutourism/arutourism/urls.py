from django.contrib import admin
from django.urls import path, include
from accounts import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('home/', views.home, name='home'),  # Página inicial
    path('', views.home, name='home_redirect'),  # Redireciona para 'home' ao acessar a raiz
    path('accounts/', include('accounts.urls')),  # URLs do app 'accounts'
]
