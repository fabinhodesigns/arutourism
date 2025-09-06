
from django.conf import settings
from django.conf.urls.static import static

# from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.urls import path, include, reverse_lazy
from core.views import senha_redefinida_redirect

urlpatterns = [
    path('', include('core.urls')),
    # path('admin/', admin.site.urls),

    path(
        "senha/redefinir/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="core/password_reset_confirm.html",
            success_url=reverse_lazy("password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    # ✅ após redefinir: só redireciona pro login
    path(
        'senha/redefinida/',
        senha_redefinida_redirect,
        name='password_reset_complete',
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    
handler404 = "core.views.page_not_found"
handler500 = "core.views.server_error"