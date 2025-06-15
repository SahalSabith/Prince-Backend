# serializers.py
from rest_framework import serializers
from .models import Cart, CartItem, Product, Order, OrderItem
from products.serializers import productserializer


class CartItemSerializer(serializers.ModelSerializer):
    item = productserializer(read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'item', 'quantity', 'note', 'total_amount']
        read_only_fields = ['id', 'item', 'total_amount']

    def get_total_amount(self, obj):
        """Calculate total amount for the cart item"""
        return obj.item.price * obj.quantity

    def update(self, instance, validated_data):
        """Custom update method for cart items"""
        instance.quantity = validated_data.get('quantity', instance.quantity)
        instance.note = validated_data.get('note', instance.note)
        instance.save()
        return instance


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'order_type', 'total_amount', 'table_number', 'items']
        read_only_fields = ['id', 'total_amount', 'items']

    def get_total_amount(self, obj):
        """Calculate total amount for the cart"""
        return sum(item.item.price * item.quantity for item in obj.items.all())

    def update(self, instance, validated_data):
        """Custom update method to handle cart updates"""
        instance.order_type = validated_data.get('order_type', instance.order_type)
        instance.table_number = validated_data.get('table_number', instance.table_number)
        
        # Recalculate and save total amount
        total = sum(item.item.price * item.quantity for item in instance.items.all())
        instance.total_amount = total
        
        instance.save()
        return instance


class OrderItemSerializer(serializers.ModelSerializer):
    Products = serializers.StringRelatedField()

    class Meta:
        model = OrderItem
        fields = ['id', 'item', 'quantity', 'note', 'total_amount']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'order_type', 'total_amount', 'ordered_at', 'items']