from rest_framework import serializers
from .models import Category, Product

class CategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class productserializer(serializers.ModelSerializer):
    Categories = CategoriesSerializer(read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'Categories', 'name', 'price', 'image']
