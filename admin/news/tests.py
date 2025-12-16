from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from .models import News, Category, NewsCategory


class CategoryModelTest(TestCase):
    """Tests para el modelo Category"""
    
    def setUp(self):
        self.category = Category.objects.create(
            name='Salud',
            description='Noticias de salud'
        )
    
    def test_category_creation(self):
        """Test creación de categoría"""
        self.assertEqual(self.category.name, 'Salud')
        self.assertEqual(self.category.slug, 'salud')
        self.assertTrue(self.category.is_active)
    
    def test_category_str(self):
        """Test string representation"""
        self.assertEqual(str(self.category), 'Salud')


class NewsModelTest(TestCase):
    """Tests para el modelo News"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='General')
        self.news = News.objects.create(
            title='Test News',
            content='Test content',
            status='draft',
            created_by=self.user
        )
    
    def test_news_creation(self):
        """Test creación de novedad"""
        self.assertEqual(self.news.title, 'Test News')
        self.assertEqual(self.news.slug, 'test-news')
        self.assertEqual(self.news.status, 'draft')
        self.assertEqual(self.news.created_by, self.user)
        self.assertIsNone(self.news.deleted_at)
    
    def test_soft_delete(self):
        """Test soft delete"""
        self.news.soft_delete(user=self.user)
        self.assertIsNotNone(self.news.deleted_at)
        
        # Verificar que no aparece en el queryset por defecto
        self.assertEqual(News.objects.count(), 0)
        self.assertEqual(News.all_objects.count(), 1)
    
    def test_restore(self):
        """Test restaurar novedad"""
        self.news.soft_delete()
        self.news.restore()
        self.assertIsNone(self.news.deleted_at)
        self.assertEqual(News.objects.count(), 1)
    
    def test_is_published(self):
        """Test propiedad is_published"""
        self.assertFalse(self.news.is_published)
        
        self.news.status = 'published'
        self.news.published_at = timezone.now()
        self.news.save()
        
        self.assertTrue(self.news.is_published)
    
    def test_increment_views(self):
        """Test incrementar visualizaciones"""
        initial_count = self.news.view_count
        self.news.increment_views()
        self.assertEqual(self.news.view_count, initial_count + 1)


class NewsAPITest(APITestCase):
    """Tests para la API de News"""
    
    def setUp(self):
        # Crear usuarios
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        self.normal_user = User.objects.create_user(
            username='user',
            email='user@test.com',
            password='user123'
        )
        
        # Crear categorías
        self.category = Category.objects.create(name='General')
        
        # Crear novedades
        self.news = News.objects.create(
            title='Test News',
            content='Test content',
            status='published',
            published_at=timezone.now(),
            created_by=self.admin_user
        )
        self.news.categories.add(self.category)
        
        # Cliente API
        self.client = APIClient()
    
    def test_list_news_as_admin(self):
        """Test listar novedades como admin"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/news/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_create_news_as_admin(self):
        """Test crear novedad como admin"""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'title': 'New News',
            'content': 'New content',
            'status': 'draft',
            'category_ids': [self.category.id]
        }
        response = self.client.post('/api/news/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(News.objects.count(), 2)
    
    def test_create_news_as_normal_user(self):
        """Test que usuario normal no puede crear"""
        self.client.force_authenticate(user=self.normal_user)
        data = {
            'title': 'New News',
            'content': 'New content',
            'status': 'draft'
        }
        response = self.client.post('/api/news/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_soft_delete_news(self):
        """Test soft delete de novedad"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(f'/api/news/{self.news.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verificar que está marcada como eliminada
        self.news.refresh_from_db()
        self.assertIsNotNone(self.news.deleted_at)
    
    def test_restore_news(self):
        """Test restaurar novedad"""
        self.news.soft_delete()
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/news/{self.news.id}/restore/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.news.refresh_from_db()
        self.assertIsNone(self.news.deleted_at)
    
    def test_publish_news(self):
        """Test publicar novedad"""
        draft_news = News.objects.create(
            title='Draft News',
            content='Draft content',
            status='draft',
            created_by=self.admin_user
        )
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/news/{draft_news.id}/publish/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        draft_news.refresh_from_db()
        self.assertEqual(draft_news.status, 'published')
        self.assertIsNotNone(draft_news.published_at)
    
    def test_public_news_endpoint(self):
        """Test endpoint público de novedades"""
        response = self.client.get('/api/public/news/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_increment_views_public(self):
        """Test incrementar vistas desde endpoint público"""
        response = self.client.post(f'/api/public/news/{self.news.id}/view/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.news.refresh_from_db()
        self.assertEqual(self.news.view_count, 1)
