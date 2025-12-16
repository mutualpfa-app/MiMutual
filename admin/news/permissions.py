from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permiso personalizado para permitir:
    - Solo admins pueden crear, editar y eliminar
    - Usuarios autenticados pueden leer
    """
    
    def has_permission(self, request, view):
        # Permitir GET, HEAD, OPTIONS a usuarios autenticados
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Solo admins pueden modificar
        return request.user and request.user.is_staff

    def has_object_permission(self, request, view, obj):
        # Permitir GET, HEAD, OPTIONS a usuarios autenticados
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Solo admins pueden modificar
        return request.user and request.user.is_staff


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permiso personalizado para permitir:
    - El creador puede editar su contenido
    - Los admins pueden editar todo
    """
    
    def has_object_permission(self, request, view, obj):
        # Permitir GET, HEAD, OPTIONS a usuarios autenticados
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # El creador o admin pueden modificar
        return (
            request.user and 
            (request.user.is_staff or obj.created_by == request.user)
        )
