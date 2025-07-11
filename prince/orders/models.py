# models.py
from django.db import models
from django.contrib.auth.models import User
from products.models import Product, Extra
from django.utils import timezone


class Cart(models.Model):
    ORDER_TYPE_CHOICES = (
        ('delivery', 'Delivery'),
        ('parcel', 'Parcel'),
        ('table', 'Table'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES, default='delivery')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    table_number = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Cart"

    def save(self, *args, **kwargs):
        # Clear table_number if order_type is not 'table'
        if self.order_type != 'table':
            self.table_number = None
        super().save(*args, **kwargs)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    note = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    @property
    def total_amount(self):
        """Calculate total amount including extras"""
        base_total = self.item.price * self.quantity
        extras_total = sum(extra.total_amount for extra in self.extras.all())
        return base_total + extras_total

    def __str__(self):
        return f"{self.item.name} x {self.quantity} in {self.cart.user.username}'s cart"


class CartItemExtra(models.Model):
    cart_item = models.ForeignKey(CartItem, on_delete=models.CASCADE, related_name='extras')
    extra = models.ForeignKey('products.Extra', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def total_amount(self):
        return self.extra.price * self.quantity

    def __str__(self):
        return f"{self.extra.name} x {self.quantity}"


class Order(models.Model):
    ORDER_TYPE_CHOICES = (
        ('delivery', 'Delivery'),
        ('parcel', 'Parcel'),
        ('table', 'Table'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    table_number = models.CharField(max_length=10, blank=True, null=True)
    ordered_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    note = models.TextField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        # Calculate total_amount before saving if not provided
        if not self.total_amount:
            self.total_amount = self.item.price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item.name} x {self.quantity}"


class OrderItemExtra(models.Model):
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='extras')
    extra = models.ForeignKey('products.Extra', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        # Calculate total_amount before saving if not provided
        if not self.total_amount:
            self.total_amount = self.extra.price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.extra.name} x {self.quantity}"