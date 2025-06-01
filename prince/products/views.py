from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Category, Dish
from .serializers import CategorySerializer, DishSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny

class CategoryListAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)
    
class CategoryCreateAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DishListAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        dishes = Dish.objects.select_related('category').all()
        serializer = DishSerializer(dishes, many=True)
        return Response(serializer.data)

class DishCreateAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DishSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            print(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)