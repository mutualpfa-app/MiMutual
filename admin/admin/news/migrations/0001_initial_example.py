"""
Script para generar migraciones que usen las tablas existentes de PostgreSQL
Ejecutar: python manage.py makemigrations --empty news
Luego reemplazar con este contenido
"""

from django.db import migrations


class Migration(migrations.Migration):

    initial = True
    
    # Si ya existen las tablas en la DB, usar managed=False temporalmente
    # Luego cambiar a True en producción

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        # Esta migración está vacía porque las tablas ya existen
        # Solo registra los modelos en Django
    ]
