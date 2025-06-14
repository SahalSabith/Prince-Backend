from rest_framework import serializers
from .models import Cart, CartItem, Product
from products.serializers import ProductSerializer
from rest_framework import serializers
from .models import Order, OrderItem, Product


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'note', 'total_amount']
        read_only_fields = fields 

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'order_type', 'total_amount', 'items']
        read_only_fields = fields


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.StringRelatedField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'note', 'total_amount']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'order_type', 'total_amount', 'ordered_at', 'items']
