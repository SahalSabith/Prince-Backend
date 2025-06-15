from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Categories, Products
from .serializers import CategoriesSerializer, ProductsSerializer
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
        Categories = Categories.objects.all()
        serializer = CategoriesSerializer(Categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductsListView(APIView):
    def get(self, request):
        Productss = Products.objects.all()
        serializer = ProductsSerializer(Productss, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class ProductsDetailView(APIView):
    def get(self, request, pk):
        Products = get_object_or_404(Products, pk=pk)
        serializer = ProductsSerializer(Products)
        return Response(serializer.data, status=status.HTTP_200_OK)
