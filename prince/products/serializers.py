from rest_framework import serializers
from .models import Categories, Products

class CategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = ['id', 'name']

class ProductsSerializer(serializers.ModelSerializer):
    Categories = CategoriesSerializer(read_only=True)

    class Meta:
        model = Products
        fields = ['id', 'Categories', 'name', 'price', 'image']
