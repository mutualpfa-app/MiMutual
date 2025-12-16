from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NewsViewSet,
    CategoryViewSet,
    PublicNewsViewSet,
    PublicCategoryViewSet
)

# Router para endpoints autenticados (admin)
router = DefaultRouter()
router.register(r'news', NewsViewSet, basename='news')
router.register(r'categories', CategoryViewSet, basename='category')

# Router para endpoints públicos (sin auth)
public_router = DefaultRouter()
public_router.register(r'news', PublicNewsViewSet, basename='public-news')
public_router.register(r'categories', PublicCategoryViewSet, basename='public-category')

app_name = 'news'

urlpatterns = [
    # Endpoints autenticados (para admins)
    path('', include(router.urls)),

    # Endpoints públicos (para la app mobile)
    path('public/', include(public_router.urls)),
]
