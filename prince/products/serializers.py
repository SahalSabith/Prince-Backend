from rest_framework import serializers
from .models import Categories, Product

class CategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = ['id', 'name']

class ProductSerializer(serializers.ModelSerializer):
    Categories = CategoriesSerializer(read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'Categories', 'name', 'price', 'image']
