# models.py
from django.db import models
from django.contrib.auth.models import User
from products.models import Product
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
    table_number = models.CharField(max_length=10, blank=True, null=True)  # Changed to CharField for flexibility

    def __str__(self):
        return f"{self.user.username}'s Cart"

    def save(self, *args, **kwargs):
        # Clear table_number if order_type is not 'table'
        if self.order_type != 'table':
            self.table_number = None
        super().save(*args, **kwargs)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    quantity = models.PositiveIntegerField()
    note = models.TextField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    item = models.ForeignKey('products.Product',on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        self.total_amount = self.item.price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item.name} x {self.quantity} in {self.cart.user.username}'s cart"


class Order(models.Model):
    ORDER_TYPE_CHOICES = (
        ('delivery', 'Delivery'),
        ('parcel', 'Parcel'),
        ('table', 'Table'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    table_number = models.CharField(max_length=10, blank=True, null=True)  # Add table_number to Order model too
    ordered_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey('products.Product',on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    note = models.TextField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.item.name} x {self.quantity}"