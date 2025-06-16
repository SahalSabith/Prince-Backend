# products/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Category, Product
from .serializers import CategoriesSerializer, productserializer
from django.shortcuts import get_object_or_404


class CategoriesCreateView(APIView):
    def post(self, request):
        serializer = CategoriesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoriesListView(APIView):
    def get(self, request):
        categories = Category.objects.all()  # Fixed: Changed variable name from Categories to categories
        serializer = CategoriesSerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductsListView(APIView):
    def get(self, request):
        products = Product.objects.all()
        serializer = productserializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class ProductsDetailView(APIView):
    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)  # Fixed: Changed Products to Product
        serializer = productserializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)