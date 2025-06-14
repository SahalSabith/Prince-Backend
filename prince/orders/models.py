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
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.user.username}'s Cart"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    note = models.TextField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total_amount = self.product.price * self.quantity
        super().save(*args, **kwargs)


class Order(models.Model):
    ORDER_TYPE_CHOICES = (
        ('delivery', 'Delivery'),
        ('parcel', 'Parcel'),
        ('table', 'Table'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    ordered_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    note = models.TextField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
