# news/models.py

from django.db import models
from django.utils.text import slugify
from django.utils import timezone


class SoftDeleteManager(models.Manager):
    """Manager que excluye registros eliminados por defecto"""
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class Category(models.Model):
    """Categorías para clasificar las novedades"""
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'categories'
        managed = False  # No gestionar con Django
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class News(models.Model):
    """Modelo de Novedades/Noticias - Usando tabla existente"""
    
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        #('scheduled', 'Programada'),
        ('published', 'Publicada'),
        ('archived', 'Archivada'),
    ]

    # Campos que coinciden EXACTAMENTE con tu DB
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255, verbose_name = 'Título')
    slug = models.CharField(max_length=255, unique=True, verbose_name = 'Identificador')
    excerpt = models.TextField(blank=True, null=True, verbose_name = 'Resumen')
    content = models.TextField(blank=True, null=True, verbose_name = 'Contenido')
    image_url = models.TextField(blank=True, null=True, verbose_name = 'URL Imagen')
    external_link = models.CharField(max_length=500, blank=True, null=True, verbose_name = 'Link externo')
    
    # Status es un ENUM en PostgreSQL, Django lo maneja como CharField
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        default='draft',
        blank=True,
        null=True,
        verbose_name = 'Estado'
    )
    
    view_count = models.IntegerField(default=0, blank=True, null=True, verbose_name = 'Contador de visitas')
    published_at = models.DateTimeField(blank=True, null=True, verbose_name = 'Fecha de publicación')
    
    # Campos de auditoría (INTEGER, no ForeignKey)
    created_by = models.IntegerField(blank=True, null=True, verbose_name = 'Creado por')
    updated_by = models.IntegerField(blank=True, null=True, verbose_name = 'Actualizado por')
    published_by = models.IntegerField(blank=True, null=True, verbose_name = 'Publicado por')
    
    # Timestamps (sin auto_now para no sobreescribir defaults de DB)
    created_at = models.DateTimeField(blank=True, null=True, verbose_name = 'Fecha de creación')
    updated_at = models.DateTimeField(blank=True, null=True, verbose_name = 'Fecha de actualización')
    deleted_at = models.DateTimeField(blank=True, null=True, verbose_name = 'Fecha de eliminación')

    # Relación ManyToMany con categorías a través de la tabla intermedia
    categories = models.ManyToManyField(
        Category,
        through='NewsCategory',
        through_fields=('news', 'category'),
        related_name='news_items',
        blank=True
    )

    # Managers
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'news'
        managed = False  # IMPORTANTE: Django no gestiona esta tabla
        verbose_name = 'Novedad'
        verbose_name_plural = 'Novedades'

    def save(self, *args, **kwargs):
        """Override save para manejar campos automáticos"""
        # Auto-generar slug si no existe
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while News.all_objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Establecer timestamps si son None
        now = timezone.now()
        if self.created_at is None:
            self.created_at = now
        self.updated_at = now
        
        super().save(*args, **kwargs)

    def soft_delete(self, user_id=None):
        """Soft delete: marca como eliminado"""
        self.deleted_at = timezone.now()
        if user_id:
            self.updated_by = user_id
        self.save()

    def restore(self):
        """Restaurar un registro eliminado"""
        self.deleted_at = None
        self.save()

    def increment_views(self):
        """Incrementar contador de visualizaciones"""
        self.view_count = (self.view_count or 0) + 1
        self.save(update_fields=['view_count'])

    @property
    def is_published(self):
        """Verifica si la novedad está publicada"""
        if self.status != 'published' or self.published_at is None:
            return False

        # Manejar tanto datetimes naive como aware
        now = timezone.now()
        published_at = self.published_at

        # Si published_at es naive, hacerlo aware
        if timezone.is_naive(published_at):
            published_at = timezone.make_aware(published_at)

        return published_at <= now

    def __str__(self):
        return self.title


class NewsCategory(models.Model):
    """Tabla intermedia para la relación News-Category"""
    id = models.AutoField(primary_key=True)
    news = models.ForeignKey('News', on_delete=models.CASCADE, db_column='news_id')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, db_column='category_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'news_categories'
        managed = False
        unique_together = ['news', 'category']

    def __str__(self):
        return f"News {self.news_id} - Category {self.category_id}"