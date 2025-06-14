from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey('products.Category', on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    price = models.IntegerField()
    image = models.ImageField(upload_to='uploads/images/',null=True, blank=True)

    def __str__(self):
        return self.name