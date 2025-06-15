from django.db import models

class Categories(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Products(models.Model):
    Categories = models.ForeignKey(Categories, on_delete=models.CASCADE, related_name='Productss')
    name = models.CharField(max_length=200)
    price = models.IntegerField()
    image = models.ImageField(upload_to='uploads/images/')

    def __str__(self):
        return self.name