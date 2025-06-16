# products/models.py
from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Fixed: Changed from IntegerField to DecimalField
    image = models.ImageField(upload_to='uploads/images/', null=True, blank=True)

    def __str__(self):
        return self.name