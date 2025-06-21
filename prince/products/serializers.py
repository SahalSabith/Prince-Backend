from rest_framework import serializers
from .models import Category, Product, Extra

class CategoriesSerializer(serializers.ModelSerializer):
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'products_count']
    
    def get_products_count(self, obj):
        return obj.products.count()

class ExtraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Extra
        fields = ['id', 'name', 'price']

class ProductSerializer(serializers.ModelSerializer):  # Fixed: Changed from productserializer
    category = CategoriesSerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True, required=False)
    extras = ExtraSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id','is_popular','category', 'category_id', 'name', 'price', 'image', 'extras']

    def validate_category_id(self, value):
        if not Category.objects.filter(id=value).exists():
            raise serializers.ValidationError("Category does not exist.")
        return value

class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Separate serializer for creating/updating products"""
    class Meta:
        model = Product
        fields = ['id', 'category', 'name', 'price', 'image']

class ExtraCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating extras"""
    class Meta:
        model = Extra
        fields = ['id', 'product', 'name', 'price']

    def validate_product(self, value):
        if not Product.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Product does not exist.")
        return value