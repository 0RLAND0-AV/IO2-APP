# api/management/commands/populate_data.py
# Crear la estructura de directorios: api/management/commands/

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import Product, SocialMedia, UserProfile

class Command(BaseCommand):
    help = 'Populate database with sample data'

    def handle(self, *args, **options):
        # Crear productos de ejemplo
        products = [
            {
                'name': 'Producto 1',
                'description': 'Descripción del producto 1',
                'price': 25.50,
                'stock': 100
            },
            {
                'name': 'Producto 2',
                'description': 'Descripción del producto 2',
                'price': 45.00,
                'stock': 50
            },
            {
                'name': 'Producto 3',
                'description': 'Descripción del producto 3',
                'price': 15.75,
                'stock': 200
            }
        ]
        
        for product_data in products:
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                defaults=product_data
            )
            if created:
                self.stdout.write(f'Producto creado: {product.name}')
        
        # Crear redes sociales
        social_media = [
            {
                'name': 'Facebook',
                'url': 'https://facebook.com/tu_pagina',
                'icon': 'fab fa-facebook'
            },
            {
                'name': 'Instagram',
                'url': 'https://instagram.com/tu_cuenta',
                'icon': 'fab fa-instagram'
            },
            {
                'name': 'TikTok',
                'url': 'https://tiktok.com/@tu_cuenta',
                'icon': 'fab fa-tiktok'
            }
        ]
        
        for social_data in social_media:
            social, created = SocialMedia.objects.get_or_create(
                name=social_data['name'],
                defaults=social_data
            )
            if created:
                self.stdout.write(f'Red social creada: {social.name}')
        
        # Crear usuario vendedor
        admin_user, created = User.objects.get_or_create(
            username='vendedor',
            defaults={
                'email': 'vendedor@ejemplo.com',
                'first_name': 'Vendedor',
                'last_name': 'Principal',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        if created:
            admin_user.set_password('vendedor123')
            admin_user.save()
            
            UserProfile.objects.create(
                user=admin_user,
                phone='70000000',
                address='Dirección del vendedor'
            )
            
            self.stdout.write('Usuario vendedor creado: vendedor/vendedor123')
        
        self.stdout.write(self.style.SUCCESS('Base de datos poblada exitosamente!'))