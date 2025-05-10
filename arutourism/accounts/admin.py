from django.contrib import admin
from django.contrib.admin import AdminSite
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin 

class CustomAdminSite(AdminSite):
    site_header = "Administração do AruTourism"
    site_title = "AruTourism Admin"
    index_title = "Bem-vindo ao painel administrativo"

    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }

admin_site = CustomAdminSite(name='custom_admin')

admin_site.register(User, UserAdmin)