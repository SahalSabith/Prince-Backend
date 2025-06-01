from django.db import models

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=10)

    def __str__(self):
        return f"Category {self.name} id {self.id}"
    
class Dish(models.Model):
    dish_name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    category = models.ForeignKey(Category,on_delete=models.CASCADE,related_name="dishes")
    dish_image = models.ImageField(upload_to='dish_images/')
    description = models.TextField()

    def __str__(self):
        return f"Dish {self.dish_name} id {self.id}"