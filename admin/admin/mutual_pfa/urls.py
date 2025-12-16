"""
URL Configuration para Mutual PFA
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

from mutual_pfa import views

urlpatterns = [
    # Admin de Django - DEBE IR PRIMERO para tener prioridad
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    # API de autenticación de DRF
    path('api-auth/', include('rest_framework.urls')),

    # App de News con prefijo 'api/'
    path('api/', include('news.urls')),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Personalizar el admin
admin.site.site_header = 'Mutual PFA - Administración'
admin.site.site_title = 'Mutual PFA Admin'
admin.site.index_title = 'Panel de Administración'
