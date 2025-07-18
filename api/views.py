from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
import requests

from .models import UserProfile, Product, Cart, CartItem, Order, OrderItem, SocialMedia
from .serializers import (
    UserSerializer, UserProfileSerializer, RegisterSerializer, 
    ProductSerializer, CartSerializer, CartItemSerializer, 
    OrderSerializer, SocialMediaSerializer, AddToCartSerializer, CheckoutSerializer
)
from django.http import JsonResponse

def api_root(request):
    return JsonResponse({
        "message": "Bienvenido a la API de EcoStylo",
        "endpoints": [
            "/api/register/",
            "/api/login/",
            "/api/products/",
            "/api/cart/",
            "/api/orders/",
            # puedes agregar más
        ]
    })

# Autenticación
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            'message': 'Usuario registrado exitosamente',
            'user_id': user.id,
            'username': user.username
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    user = authenticate(username=username, password=password)
    if user:
        profile = UserProfile.objects.get(user=user)
        return Response({
            'message': 'Login exitoso',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': profile.phone,
                'address': profile.address
            }
        })
    return Response({'error': 'Credenciales inválidas'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
    except UserProfile.DoesNotExist:
        return Response({'error': 'Perfil no encontrado'}, status=status.HTTP_404_NOT_FOUND)

# Productos
class ProductListView(generics.ListAPIView):
    queryset = Product.objects.filter(active=True)
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.filter(active=True)
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

# Carrito
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    serializer = CartSerializer(cart)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    serializer = AddToCartSerializer(data=request.data)
    if serializer.is_valid():
        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']
        
        try:
            product = Product.objects.get(id=product_id, active=True)
            cart, created = Cart.objects.get_or_create(user=request.user)
            
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': quantity}
            )
            
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            
            return Response({'message': 'Producto agregado al carrito'})
        except Product.DoesNotExist:
            return Response({'error': 'Producto no encontrado'}, status=status.HTTP_404_NOT_FOUND)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_cart_item(request, item_id):
    try:
        cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
        quantity = request.data.get('quantity', 1)
        
        if quantity <= 0:
            cart_item.delete()
            return Response({'message': 'Producto eliminado del carrito'})
        
        cart_item.quantity = quantity
        cart_item.save()
        
        return Response({'message': 'Cantidad actualizada'})
    except CartItem.DoesNotExist:
        return Response({'error': 'Item no encontrado'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_cart(request, item_id):
    try:
        cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
        cart_item.delete()
        return Response({'message': 'Producto eliminado del carrito'})
    except CartItem.DoesNotExist:
        return Response({'error': 'Item no encontrado'}, status=status.HTTP_404_NOT_FOUND)

# Checkout y Órdenes
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def checkout(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.cartitem_set.all()
        
        if not cart_items.exists():
            return Response({'error': 'El carrito está vacío'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Crear orden
        order = Order.objects.create(
            user=request.user,
            total=cart.total
        )
        
        # Crear items de la orden
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
        
        # Enviar mensaje de WhatsApp
        send_whatsapp_message(order)
        
        # Limpiar carrito
        cart_items.delete()
        
        serializer = OrderSerializer(order)
        return Response({
            'message': 'Pedido creado exitosamente',
            'order': serializer.data
        })
        
    except Cart.DoesNotExist:
        return Response({'error': 'Carrito no encontrado'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)

def send_whatsapp_message(order):
    """Envía mensaje a WhatsApp con los detalles del pedido"""
    try:
        profile = UserProfile.objects.get(user=order.user)
        
        message = f"""
🛍️ NUEVO PEDIDO #{order.order_number}

👤 Cliente: {order.user.get_full_name()}
📱 Teléfono: {profile.phone}
📧 Email: {order.user.email}
📍 Dirección: {profile.address}

🛒 PRODUCTOS:
"""
        
        for item in order.orderitem_set.all():
            message += f"• {item.product.name} x{item.quantity} - Bs. {item.subtotal}\n"
        
        message += f"\n💰 TOTAL: Bs. {order.total}"
        
        # Aquí puedes integrar con la API de WhatsApp Business
        # Por ejemplo, usando la API de WhatsApp Business Cloud
        # Esta es una implementación básica de ejemplo
        
        whatsapp_number = "59170000000"  # Número del vendedor
        
        # Ejemplo de integración con WhatsApp Business API
        # Reemplaza con tu token y configuración real
        """
        url = "https://graph.facebook.com/v17.0/YOUR_PHONE_NUMBER_ID/messages"
        headers = {
            "Authorization": "Bearer YOUR_ACCESS_TOKEN",
            "Content-Type": "application/json"
        }
        data = {
            "messaging_product": "whatsapp",
            "to": whatsapp_number,
            "type": "text",
            "text": {"body": message}
        }
        
        response = requests.post(url, headers=headers, json=data)
        """
        
        print(f"Mensaje de WhatsApp enviado para pedido {order.order_number}")
        print(message)
        
    except Exception as e:
        print(f"Error enviando mensaje de WhatsApp: {str(e)}")

# Redes Sociales
@api_view(['GET'])
@permission_classes([AllowAny])
def social_media(request):
    social_media = SocialMedia.objects.filter(active=True)
    serializer = SocialMediaSerializer(social_media, many=True)
    return Response(serializer.data)

# Reportes de Ventas
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sales_reports(request):
    # Solo permitir acceso a staff/admin
    if not request.user.is_staff:
        return Response({'error': 'No tienes permisos para acceder a los reportes'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    # Ventas del día
    daily_sales = Order.objects.filter(
        created_at__date=today,
        status__in=['confirmed', 'processing', 'shipped', 'delivered']
    ).aggregate(
        total_sales=Sum('total'),
        total_orders=Count('id')
    )
    
    # Ventas semanales
    weekly_sales = Order.objects.filter(
        created_at__date__gte=week_ago,
        status__in=['confirmed', 'processing', 'shipped', 'delivered']
    ).aggregate(
        total_sales=Sum('total'),
        total_orders=Count('id')
    )
    
    # Productos más vendidos
    top_products = OrderItem.objects.values('product__name').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('price')
    ).order_by('-total_quantity')[:10]
    
    return Response({
        'daily_sales': {
            'total_sales': daily_sales['total_sales'] or 0,
            'total_orders': daily_sales['total_orders'] or 0
        },
        'weekly_sales': {
            'total_sales': weekly_sales['total_sales'] or 0,
            'total_orders': weekly_sales['total_orders'] or 0
        },
        'top_products': list(top_products)
    })