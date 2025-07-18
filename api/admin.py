from django.contrib import admin
from .models import UserProfile, Product, Cart, CartItem, Order, OrderItem, SocialMedia

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'address', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone']
    list_filter = ['created_at']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'stock', 'active', 'created_at']
    search_fields = ['name', 'description']
    list_filter = ['active', 'created_at']
    list_editable = ['price', 'stock', 'active']

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at']
    search_fields = ['user__username']
    list_filter = ['created_at']

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'quantity']
    search_fields = ['cart__user__username', 'product__name']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'status', 'total', 'created_at']
    search_fields = ['order_number', 'user__username', 'user__email']
    list_filter = ['status', 'created_at']
    list_editable = ['status']
    inlines = [OrderItemInline]

@admin.register(SocialMedia)
class SocialMediaAdmin(admin.ModelAdmin):
    list_display = ['name', 'url', 'active']
    list_editable = ['active']