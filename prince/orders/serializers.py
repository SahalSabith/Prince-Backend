# serializers.py
from rest_framework import serializers
from .models import Cart, CartItem, CartItemExtra, Order, OrderItem, OrderItemExtra
from products.models import Product, Extra
from products.serializers import ProductSerializer, ExtraSerializer


class CartItemExtraSerializer(serializers.ModelSerializer):
    extra = ExtraSerializer(read_only=True)
    total_amount = serializers.SerializerMethodField()
    extra_name = serializers.SerializerMethodField()

    class Meta:
        model = CartItemExtra
        fields = ['id', 'extra', 'quantity', 'total_amount','extra_name']

    def get_total_amount(self, obj):
        return obj.extra.price * obj.quantity
    
    def get_extra_name(self, obj):
        return obj.extra.name if obj.extra else None

class CartItemSerializer(serializers.ModelSerializer):
    item = ProductSerializer(read_only=True)
    extras = CartItemExtraSerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'item', 'quantity', 'note', 'extras', 'total_amount']
        read_only_fields = ['id', 'item', 'total_amount', 'extras']

    def get_total_amount(self, obj):
        base_total = obj.item.price * obj.quantity
        extras_total = sum(extra.total_amount for extra in obj.extras.all())
        return base_total + extras_total

    def update(self, instance, validated_data):
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
        total = 0
        for item in obj.items.all():
            base_total = item.item.price * item.quantity
            extras_total = sum(extra.total_amount for extra in item.extras.all())
            total += base_total + extras_total
        return total

    def update(self, instance, validated_data):
        instance.order_type = validated_data.get('order_type', instance.order_type)
        instance.table_number = validated_data.get('table_number', instance.table_number)

        # Calculate total amount based on current items and extras
        total = 0
        for item in instance.items.all():
            base_total = item.item.price * item.quantity
            extras_total = sum(extra.total_amount for extra in item.extras.all())
            total += base_total + extras_total
        instance.total_amount = total

        instance.save()
        return instance


class OrderItemExtraSerializer(serializers.ModelSerializer):
    extra = ExtraSerializer(read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = OrderItemExtra
        fields = ['id', 'extra', 'quantity', 'total_amount']

    def get_total_amount(self, obj):
        return obj.extra.price * obj.quantity if obj.extra else obj.total_amount


class OrderItemSerializer(serializers.ModelSerializer):
    item = ProductSerializer(read_only=True)
    extras = OrderItemExtraSerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'item', 'quantity', 'note', 'extras', 'total_amount']

    def get_total_amount(self, obj):
        base_total = obj.item.price * obj.quantity if obj.item else obj.total_amount
        extras_total = sum(extra.total_amount for extra in obj.extras.all())
        return base_total + extras_total


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'order_type', 'total_amount', 'ordered_at', 'table_number', 'items']