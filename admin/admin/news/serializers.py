from rest_framework import serializers
from django.utils import timezone
from .models import News, Category, NewsCategory


class CategorySerializer(serializers.ModelSerializer):
    """Serializer para categorías"""
    
    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'display_order',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']


class CategorySimpleSerializer(serializers.ModelSerializer):
    """Serializer simplificado para categorías (para usar en News)"""
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


class NewsListSerializer(serializers.ModelSerializer):
    """Serializer para listado de novedades (vista simplificada)"""
    
    categories = CategorySimpleSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )
    is_published = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = News
        fields = [
            'id',
            'title',
            'slug',
            'excerpt',
            'image_url',
            'status',
            'view_count',
            'published_at',
            'created_at',
            'categories',
            'created_by_name',
            'is_published'
        ]


class NewsDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalle de novedades (vista completa)"""
    
    categories = CategorySimpleSerializer(many=True, read_only=True)
    category_ids = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        many=True,
        write_only=True,
        source='categories'
    )
    
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )
    updated_by_name = serializers.CharField(
        source='updated_by.get_full_name',
        read_only=True,
        allow_null=True
    )
    published_by_name = serializers.CharField(
        source='published_by.get_full_name',
        read_only=True,
        allow_null=True
    )
    is_published = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = News
        fields = [
            'id',
            'title',
            'slug',
            'excerpt',
            'content',
            'image_url',
            'external_link',
            'status',
            'view_count',
            'published_at',
            'created_at',
            'updated_at',
            'deleted_at',
            'categories',
            'category_ids',
            'created_by_name',
            'updated_by_name',
            'published_by_name',
            'is_published'
        ]
        read_only_fields = [
            'slug',
            'view_count',
            'created_at',
            'updated_at',
            'deleted_at'
        ]

    def create(self, validated_data):
        """Crear nueva novedad con auditoría"""
        categories = validated_data.pop('categories', [])
        request = self.context.get('request')
        
        # Asignar usuario creador
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        
        news = News.objects.create(**validated_data)
        
        # Asignar categorías
        if categories:
            news.categories.set(categories)
        
        return news

    def update(self, instance, validated_data):
        """Actualizar novedad con auditoría"""
        categories = validated_data.pop('categories', None)
        request = self.context.get('request')
        
        # Asignar usuario que actualiza
        if request and hasattr(request, 'user'):
            validated_data['updated_by'] = request.user
        
        # Si se está publicando por primera vez
        if (validated_data.get('status') == 'published' and 
            instance.status != 'published' and 
            request and hasattr(request, 'user')):
            validated_data['published_by'] = request.user
            if not instance.published_at:
                validated_data['published_at'] = timezone.now()
        
        # Actualizar campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Actualizar categorías si se proporcionaron
        if categories is not None:
            instance.categories.set(categories)
        
        return instance


class NewsCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear novedades (sin campos de solo lectura)"""
    
    category_ids = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True),
        many=True,
        required=False,
        write_only=True
    )
    
    class Meta:
        model = News
        fields = [
            'title',
            'excerpt',
            'content',
            'image_url',
            'external_link',
            'status',
            'published_at',
            'category_ids'
        ]

    def create(self, validated_data):
        """Crear nueva novedad"""
        category_ids = validated_data.pop('category_ids', [])
        request = self.context.get('request')
        
        # Asignar usuario creador
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        
        # Si se publica directamente
        if (validated_data.get('status') == 'published' and 
            not validated_data.get('published_at')):
            validated_data['published_at'] = timezone.now()
            if request and hasattr(request, 'user'):
                validated_data['published_by'] = request.user
        
        news = News.objects.create(**validated_data)
        
        # Asignar categorías
        if category_ids:
            news.categories.set(category_ids)
        
        return news


class NewsUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar novedades"""
    
    category_ids = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True),
        many=True,
        required=False,
        write_only=True
    )
    
    class Meta:
        model = News
        fields = [
            'title',
            'excerpt',
            'content',
            'image_url',
            'external_link',
            'status',
            'published_at',
            'category_ids'
        ]

    def update(self, instance, validated_data):
        """Actualizar novedad"""
        category_ids = validated_data.pop('category_ids', None)
        request = self.context.get('request')
        
        # Asignar usuario que actualiza
        if request and hasattr(request, 'user'):
            instance.updated_by = request.user
        
        # Si se está publicando por primera vez
        if (validated_data.get('status') == 'published' and 
            instance.status != 'published'):
            if not instance.published_at:
                instance.published_at = timezone.now()
            if request and hasattr(request, 'user'):
                instance.published_by = request.user
        
        # Actualizar campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Actualizar categorías si se proporcionaron
        if category_ids is not None:
            instance.categories.set(category_ids)
        
        return instance


class NewsPublicSerializer(serializers.ModelSerializer):
    """Serializer para novedades públicas (para la app mobile)"""
    
    categories = CategorySimpleSerializer(many=True, read_only=True)
    
    class Meta:
        model = News
        fields = [
            'id',
            'title',
            'slug',
            'excerpt',
            'content',
            'image_url',
            'external_link',
            'view_count',
            'published_at',
            'categories'
        ]
