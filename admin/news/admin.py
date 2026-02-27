# news/admin.py

import os
import uuid

from django.conf import settings
from django.contrib import admin
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.urls import path
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .forms import NewsAdminForm
from .models import Category, News, NewsCategory


# @admin.register(Category)
# class CategoryAdmin(admin.ModelAdmin):
#     list_display = ['name', 'slug', 'display_order', 'is_active']
#     list_filter = ['is_active', 'created_at']
#     search_fields = ['name', 'slug']
#     ordering = ['display_order', 'name']


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    form = NewsAdminForm

    list_display = [
        'title',
        'status_badge',
        'view_count',
        'published_at',
        'created_at',
        'is_deleted'
    ]

    list_filter = ['status', 'created_at', 'published_at']
    search_fields = ['title', 'excerpt', 'content', 'slug']

    readonly_fields = ['slug', 'view_count', 'created_by', 'updated_by', 'published_by', 'created_at', 'updated_at', 'deleted_at']

    # ── Upload endpoint ───────────────────────────────────────────────────────
    def get_urls(self):
        """Registra el endpoint de upload de imágenes bajo la URL del admin."""
        custom_urls = [
            path(
                "upload-image/",
                self.admin_site.admin_view(self.upload_image_view),
                name="news_news_upload_image",
            ),
        ]
        return custom_urls + super().get_urls()

    def upload_image_view(self, request):
        """
        POST /admin/news/news/upload-image/
        Recibe un archivo de imagen, lo guarda en MEDIA_ROOT/news/images/
        y devuelve JSON con la URL absoluta.
        """
        if request.method != "POST":
            return JsonResponse({"error": "Método no permitido."}, status=405)

        if "image" not in request.FILES:
            return JsonResponse({"error": "No se recibió ninguna imagen."}, status=400)

        file = request.FILES["image"]

        if file.content_type not in ALLOWED_IMAGE_TYPES:
            return JsonResponse(
                {"error": "Tipo no permitido. Usá JPG, PNG, GIF o WebP."},
                status=400,
            )

        if file.size > MAX_UPLOAD_SIZE:
            return JsonResponse(
                {"error": "La imagen supera el límite de 5MB."},
                status=400,
            )

        ext = os.path.splitext(file.name)[1].lower() or ".jpg"
        filename = f"news/images/{uuid.uuid4().hex}{ext}"
        saved_path = default_storage.save(filename, ContentFile(file.read()))
        url = f"/{settings.MEDIA_URL}{saved_path}"

        return JsonResponse({"url": url})

    def get_fieldsets(self, request, obj=None):
        """Ocultar published_at al crear, mostrarlo al editar"""

        # Al CREAR - sin published_at, slug se genera automáticamente
        if obj is None:
            return (
                ('Información Principal', {
                    'fields': ('title', 'excerpt', 'content')
                }),
                ('Multimedia y Enlaces', {
                    'fields': ('image_url', 'external_link'),
                }),
                ('Estado', {
                    'fields': ('status',)
                }),
            )

        # Al EDITAR - con published_at
        return (
            ('Información Principal', {
                'fields': ('title', 'slug', 'excerpt', 'content')
            }),
            ('Multimedia y Enlaces', {
                'fields': ('image_url', 'external_link'),
            }),
            ('Estado y Publicación', {
                'fields': ('status', )
            }),
            ('Métricas', {
                'fields': ('view_count',),
                'classes': ('collapse',)
            }),
            ('Auditoría', {
                'fields': (
                    'created_by',
                    'updated_by',
                    'published_by',
                    'created_at',
                    'updated_at',
                    'deleted_at'
                ),
                'classes': ('collapse',)
            }),
        )

    def get_queryset(self, request):
        """Mostrar todos los registros (incluidos eliminados)"""
        return News.all_objects.all()

    def save_model(self, request, obj, form, change):
        """Guardar con auditoría"""
        if not change:  # Si es nuevo
            obj.created_by = request.user.id
        else:  # Si es actualización
            obj.updated_by = request.user.id
        
        # Si se está publicando por primera vez
        if obj.status == 'published' and not obj.published_by:
            obj.published_by = request.user.id
            if not obj.published_at:
                obj.published_at = timezone.now()
        
        super().save_model(request, obj, form, change)

    def status_badge(self, obj):
        """Badge de color según el estado"""
        colors = {
            'draft': '#999',
            'scheduled': '#f39c12',
            'published': '#27ae60',
            'archived': '#7f8c8d',
        }
        labels = {
            'draft': 'Borrador',
            #'scheduled': 'Programada',
            'published': 'Publicada',
            'archived': 'Archivada',
        }
        color = colors.get(obj.status, '#999')
        label = labels.get(obj.status, obj.status or 'Sin estado')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color, label
        )
    status_badge.short_description = 'Estado'

    def is_deleted(self, obj):
        """Indicador de eliminado"""
        if obj.deleted_at:
            return mark_safe(
                '<span style="color: #e74c3c; font-weight: bold;">✗ Eliminado</span>'
            )
        return mark_safe(
            '<span style="color: #27ae60;">✓ Activo</span>'
        )
    is_deleted.short_description = 'Estado de Registro'

    actions = ['archive_news', 'soft_delete_news', 'restore_news'] ##'publish_news',

    def publish_news(self, request, queryset):
        """Publicar novedades seleccionadas"""
        updated = 0
        for news in queryset:
            if news.deleted_at is None:
                news.status = 'published'
                if not news.published_at:
                    news.published_at = timezone.now()
                if not news.published_by:
                    news.published_by = request.user.id
                news.save()
                updated += 1
        
        self.message_user(request, f'{updated} novedad(es) publicada(s).')
    publish_news.short_description = '✓ Publicar novedades'

    def archive_news(self, request, queryset):
        """Archivar novedades"""
        updated = 0
        for news in queryset.filter(deleted_at__isnull=True):
            news.status = 'archived'
            news.updated_by = request.user.id
            news.save()
            updated += 1
        
        self.message_user(request, f'{updated} novedad(es) archivada(s).')
    archive_news.short_description = '📦 Archivar novedades'

    def soft_delete_news(self, request, queryset):
        """Soft delete de novedades"""
        deleted = 0
        for news in queryset:
            if news.deleted_at is None:
                news.soft_delete(user_id=request.user.id)
                deleted += 1
        
        self.message_user(request, f'{deleted} novedad(es) eliminada(s).')
    soft_delete_news.short_description = '🗑️ Eliminar novedades'

    def restore_news(self, request, queryset):
        """Restaurar novedades eliminadas"""
        restored = 0
        for news in queryset:
            if news.deleted_at is not None:
                news.restore()
                restored += 1
        
        self.message_user(request, f'{restored} novedad(es) restaurada(s).')
    restore_news.short_description = '♻️ Restaurar novedades'

# @admin.register(NewsCategory)
# class NewsCategoryAdmin(admin.ModelAdmin):
#     list_display = ['id', 'news_id', 'category_id', 'created_at']
#     list_filter = ['created_at']