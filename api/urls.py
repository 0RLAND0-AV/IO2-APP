from django.urls import path
from . import views

urlpatterns = [
    path('', views.api_root, name='api-root'),

    # Autenticación
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('profile/', views.profile, name='profile'),
    
    # Productos
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    
    # Carrito
    path('cart/', views.get_cart, name='get-cart'),
    path('cart/add/', views.add_to_cart, name='add-to-cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update-cart-item'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove-from-cart'),
    
    # Órdenes
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.my_orders, name='my-orders'),
    
    # Redes Sociales
    path('social-media/', views.social_media, name='social-media'),
    
    # Reportes
    path('reports/sales/', views.sales_reports, name='sales-reports'),
]