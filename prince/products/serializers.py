# products/serializers.py
from rest_framework import serializers
from .models import Category, Product

class CategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class productserializer(serializers.ModelSerializer):
    category = CategoriesSerializer(read_only=True)  # Fixed: Changed field name to match model

    class Meta:
        model = Product
        fields = ['id', 'category', 'name', 'price', 'image']