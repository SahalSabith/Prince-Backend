from rest_framework import serializers
from .models import Category, Dish

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'icon']

class DishSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Dish
        fields = ['id', 'dish_name', 'price', 'category', 'category_id', 'dish_image', 'description']
        extra_kwargs = {
            'description': {'required': False, 'allow_blank': True},
            'dish_image': {'required': False, 'allow_null': True},
        }

    def validate_category_id(self, value):
        try:
            Category.objects.get(id=value)
        except Category.DoesNotExist:
            raise serializers.ValidationError("Category with this ID does not exist.")
        return value