# serializers.py
from rest_framework import serializers
from .models import Cart, CartItem, Order, OrderItem
from products.models import Dish

class CartItemSerializer(serializers.ModelSerializer):
    dish_name = serializers.CharField(source='dish.name', read_only=True)
    dish_price = serializers.DecimalField(source='dish.price', max_digits=8, decimal_places=2, read_only=True)
    
    class Meta:
        model = CartItem
        fields = ['id', 'dish', 'dish_name', 'dish_price', 'quantity', 'amount', 'created_at']
        read_only_fields = ['amount', 'created_at']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'user', 'table_number', 'order_type', 'created_at', 'total_amount', 'items', 'items_count']
        read_only_fields = ['user', 'created_at', 'total_amount']

    def get_items_count(self, obj):
        return obj.items.count()

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'dish_name', 'dish_price', 'quantity', 'amount']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()
    waiter_name = serializers.CharField(source='user.username', read_only=True)  # Show waiter name

    class Meta:
        model = Order
        fields = ['id', 'user', 'waiter_name', 'table_number', 'order_type', 'status', 'total_amount', 'created_at', 'items', 'items_count']
        read_only_fields = ['user', 'created_at']

    def get_items_count(self, obj):
        return obj.items.count()
