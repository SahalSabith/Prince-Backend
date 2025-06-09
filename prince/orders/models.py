from django.db import models
from products.models import *
from login.models import User

# Create your models here.
class Cart(models.Model):
    ORDER_TYPES = [
        ('dine_in', 'Dine In'),
        ('takeaway', 'Takeaway'),
        ('delivery', 'Delivery'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="carts")  # This is the waiter
    table_number = models.CharField(max_length=50, blank=True, null=True)
    order_type = models.CharField(max_length=20, choices=ORDER_TYPES, default='dine_in')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def calculate_total(self):
        """Calculate and update cart total"""
        self.total_amount = sum(item.amount for item in self.items.all())
        self.save()
        return self.total_amount

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['cart', 'dish']  # Prevent duplicate items in same cart

    def save(self, *args, **kwargs):
        # Auto-calculate amount based on dish price and quantity
        self.amount = self.dish.price * self.quantity
        super().save(*args, **kwargs)
        # Update cart total after saving item
        self.cart.calculate_total()

class Order(models.Model):
    ORDER_STATUS = [
        ('pending', 'Pending'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('served', 'Served'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")  # This is the waiter
    table_number = models.CharField(max_length=50)  # Required field for table number
    order_type = models.CharField(max_length=20, choices=Cart.ORDER_TYPES)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    total_amount = models.DecimalField(max_digits=8, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    dish_name = models.CharField(max_length=200)  # Store dish name in case dish is deleted
    dish_price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    dish = models.ForeignKey(Dish, on_delete=models.SET_NULL, null=True, blank=True)