from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q

from .models import News, Category
from .serializers import (
    NewsListSerializer,
    NewsDetailSerializer,
    NewsCreateSerializer,
    NewsUpdateSerializer,
    NewsPublicSerializer,
    CategorySerializer
)


class IsAdminOrReadOnly(IsAuthenticated):
    """
    Permiso personalizado: 
    - Solo admins pueden crear/editar/eliminar
    - Usuarios autenticados pueden leer
    """
    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_staff


class NewsViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión completa de Novedades
    
    Endpoints:
    - GET /api/news/ - Listar novedades
    - GET /api/news/{id}/ - Detalle de novedad
    - POST /api/news/ - Crear novedad (solo admins)
    - PUT/PATCH /api/news/{id}/ - Actualizar novedad (solo admins)
    - DELETE /api/news/{id}/ - Soft delete de novedad (solo admins)
    - POST /api/news/{id}/restore/ - Restaurar novedad eliminada
    - POST /api/news/{id}/publish/ - Publicar novedad
    - POST /api/news/{id}/increment_views/ - Incrementar visualizaciones
    - GET /api/news/public/ - Novedades públicas (sin auth)
    """
    
    queryset = News.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'categories']
    search_fields = ['title', 'excerpt', 'content']
    ordering_fields = ['published_at', 'created_at', 'view_count']
    ordering = ['-published_at', '-created_at']

    def get_queryset(self):
        """
        Filtrar queryset según permisos:
        - Admins ven todas (incluidas eliminadas)
        - Usuarios normales solo ven activas
        """
        queryset = News.objects.all()
        
        # Si no es admin, excluir eliminadas
        if not self.request.user.is_staff:
            queryset = queryset.filter(deleted_at__isnull=True)
        
        # Filtro por estado de eliminación
        deleted = self.request.query_params.get('deleted', None)
        if deleted == 'true':
            queryset = News.all_objects.filter(deleted_at__isnull=False)
        elif deleted == 'false':
            queryset = News.all_objects.filter(deleted_at__isnull=True)
        
        return queryset

    def get_serializer_class(self):
        """Usar diferentes serializers según la acción"""
        if self.action == 'list':
            return NewsListSerializer
        elif self.action == 'create':
            return NewsCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return NewsUpdateSerializer
        elif self.action == 'public':
            return NewsPublicSerializer
        return NewsDetailSerializer

    def perform_destroy(self, instance):
        """Soft delete en lugar de eliminar físicamente"""
        instance.soft_delete(user=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def restore(self, request, pk=None):
        """Restaurar una novedad eliminada"""
        news = self.get_object()
        
        if news.deleted_at is None:
            return Response(
                {'error': 'Esta novedad no está eliminada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        news.restore()
        serializer = self.get_serializer(news)
        
        return Response({
            'message': 'Novedad restaurada exitosamente',
            'data': serializer.data
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def publish(self, request, pk=None):
        """Publicar una novedad"""
        news = self.get_object()
        
        if news.deleted_at is not None:
            return Response(
                {'error': 'No se puede publicar una novedad eliminada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if news.status == 'published':
            return Response(
                {'message': 'Esta novedad ya está publicada'},
                status=status.HTTP_200_OK
            )
        
        news.status = 'published'
        if not news.published_at:
            news.published_at = timezone.now()
        if not news.published_by:
            news.published_by = request.user
        news.save()
        
        serializer = self.get_serializer(news)
        
        return Response({
            'message': 'Novedad publicada exitosamente',
            'data': serializer.data
        })

    @action(detail=True, methods=['post'], permission_classes=[AllowAny])
    def increment_views(self, request, pk=None):
        """Incrementar contador de visualizaciones (público)"""
        news = self.get_object()
        
        if news.deleted_at is not None or not news.is_published:
            return Response(
                {'error': 'Novedad no disponible'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        news.increment_views()
        
        return Response({
            'message': 'Visualización registrada',
            'view_count': news.view_count
        })

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def public(self, request):
        """
        Endpoint público para la app mobile
        Retorna solo novedades publicadas y no eliminadas
        """
        queryset = News.objects.filter(
            status='published',
            published_at__lte=timezone.now(),
            deleted_at__isnull=True
        )
        
        # Filtros opcionales
        category_id = request.query_params.get('category', None)
        if category_id:
            queryset = queryset.filter(categories__id=category_id)
        
        # Paginación
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = NewsPublicSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = NewsPublicSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def stats(self, request):
        """Estadísticas de novedades (solo admins)"""
        total = News.all_objects.count()
        published = News.objects.filter(status='published').count()
        draft = News.objects.filter(status='draft').count()
        archived = News.objects.filter(status='archived').count()
        deleted = News.all_objects.filter(deleted_at__isnull=False).count()
        total_views = sum(News.objects.values_list('view_count', flat=True))
        
        return Response({
            'total': total,
            'published': published,
            'draft': draft,
            'archived': archived,
            'deleted': deleted,
            'total_views': total_views,
            'active': total - deleted
        })


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de Categorías
    
    Endpoints:
    - GET /api/categories/ - Listar categorías
    - GET /api/categories/{id}/ - Detalle de categoría
    - POST /api/categories/ - Crear categoría (solo admins)
    - PUT/PATCH /api/categories/{id}/ - Actualizar categoría (solo admins)
    - DELETE /api/categories/{id}/ - Eliminar categoría (solo admins)
    """
    
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['display_order', 'name']
    ordering = ['display_order', 'name']

    def get_queryset(self):
        """Filtrar por activas si no es admin"""
        queryset = Category.objects.all()
        
        # Solo usuarios no admin ven categorías activas
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        
        return queryset

    @action(detail=True, methods=['get'])
    def news(self, request, pk=None):
        """Obtener novedades de una categoría"""
        category = self.get_object()
        news = category.news.filter(
            deleted_at__isnull=True,
            status='published',
            published_at__lte=timezone.now()
        )
        
        serializer = NewsListSerializer(news, many=True)
        return Response(serializer.data)


class PublicNewsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para novedades públicas (sin autenticación)
    Ideal para consumir desde la app mobile
    
    Endpoints:
    - GET /api/public/news/ - Listar novedades publicadas
    - GET /api/public/news/{id}/ - Detalle de novedad
    - POST /api/public/news/{id}/view/ - Registrar visualización
    """
    
    serializer_class = NewsPublicSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['categories']
    search_fields = ['title', 'excerpt', 'content']
    ordering_fields = ['published_at', 'view_count']
    ordering = ['-published_at']

    def get_queryset(self):
        """Solo novedades publicadas y no eliminadas"""
        return News.objects.filter(
            status='published',
            published_at__lte=timezone.now(),
            deleted_at__isnull=True
        )

    @action(detail=True, methods=['post'])
    def view(self, request, pk=None):
        """Registrar visualización de una novedad"""
        news = self.get_object()
        news.increment_views()
        
        return Response({
            'message': 'Visualización registrada',
            'view_count': news.view_count
        })


class PublicCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para categorías públicas (sin autenticación)
    
    Endpoints:
    - GET /api/public/categories/ - Listar categorías activas
    - GET /api/public/categories/{id}/ - Detalle de categoría
    """
    
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    ordering = ['display_order', 'name']
