from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Category, Product, Extra
from .serializers import (
    CategoriesSerializer, 
    ProductSerializer, 
    ProductCreateUpdateSerializer,
    ExtraSerializer,
    ExtraCreateUpdateSerializer
)
import logging

logger = logging.getLogger(__name__)


class CategoriesCreateView(APIView):
    permission_classes = [IsAuthenticated]  # Add authentication if needed
    
    def post(self, request):
        serializer = CategoriesSerializer(data=request.data)
        if serializer.is_valid():
            category = serializer.save()
            logger.info(f"Category '{category.name}' created successfully")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoriesListView(APIView):
    def get(self, request):
        # Get query parameters
        search = request.query_params.get('search', None)
        
        categories = Category.objects.all()
        
        # Apply search filter
        if search:
            categories = categories.filter(name__icontains=search)
        
        categories = categories.order_by('name')
        serializer = CategoriesSerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CategoriesDetailView(APIView):
    def get(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        serializer = CategoriesSerializer(category)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        serializer = CategoriesSerializer(category, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        category_name = category.name
        category.delete()
        logger.info(f"Category '{category_name}' deleted successfully")
        return Response(
            {'message': f'Category "{category_name}" deleted successfully'}, 
            status=status.HTTP_200_OK
        )


class ProductsCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ProductCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.save()
            # Return full product data with relations
            response_serializer = ProductSerializer(product)
            logger.info(f"Product '{product.name}' created successfully")
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductsListView(APIView):
    def get(self, request):
        # Get query parameters
        category_id = request.query_params.get('category', None)
        search = request.query_params.get('search', None)
        min_price = request.query_params.get('min_price', None)
        max_price = request.query_params.get('max_price', None)
        limit = request.query_params.get('limit', None)
        
        products = Product.objects.select_related('category').prefetch_related('extras')
        
        # Apply filters
        if category_id:
            products = products.filter(category_id=category_id)
        
        if search:
            products = products.filter(
                Q(name__icontains=search) | 
                Q(category__name__icontains=search)
            )
        
        if min_price:
            try:
                products = products.filter(price__gte=float(min_price))
            except ValueError:
                pass
        
        if max_price:
            try:
                products = products.filter(price__lte=float(max_price))
            except ValueError:
                pass
        
        products = products.order_by('category__name', 'name')
        
        # Apply limit
        if limit:
            try:
                limit = int(limit)
                products = products[:limit]
            except ValueError:
                pass
        
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductsDetailView(APIView):
    def get(self, request, pk):
        product = get_object_or_404(
            Product.objects.select_related('category').prefetch_related('extras'), 
            pk=pk
        )
        serializer = ProductSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductCreateUpdateSerializer(product, data=request.data)
        if serializer.is_valid():
            updated_product = serializer.save()
            # Return full product data with relations
            response_serializer = ProductSerializer(updated_product)
            logger.info(f"Product '{updated_product.name}' updated successfully")
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product_name = product.name
        product.delete()
        logger.info(f"Product '{product_name}' deleted successfully")
        return Response(
            {'message': f'Product "{product_name}" deleted successfully'}, 
            status=status.HTTP_200_OK
        )


class ProductsByCategoryView(APIView):
    def get(self, request, category_id):
        category = get_object_or_404(Category, pk=category_id)
        products = Product.objects.filter(category=category).prefetch_related('extras')
        
        # Apply search if provided
        search = request.query_params.get('search', None)
        if search:
            products = products.filter(name__icontains=search)
        
        products = products.order_by('name')
        serializer = ProductSerializer(products, many=True)
        
        return Response({
            'category': CategoriesSerializer(category).data,
            'products': serializer.data
        }, status=status.HTTP_200_OK)


class ExtrasCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ExtraCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            extra = serializer.save()
            logger.info(f"Extra '{extra.name}' created for product '{extra.product.name}'")
            return Response(ExtraSerializer(extra).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExtrasListView(APIView):
    def get(self, request):
        product_id = request.query_params.get('product', None)
        
        extras = Extra.objects.select_related('product')
        
        if product_id:
            extras = extras.filter(product_id=product_id)
        
        extras = extras.order_by('product__name', 'name')
        serializer = ExtraSerializer(extras, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ExtrasDetailView(APIView):
    def get(self, request, pk):
        extra = get_object_or_404(Extra, pk=pk)
        serializer = ExtraSerializer(extra)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        extra = get_object_or_404(Extra, pk=pk)
        serializer = ExtraCreateUpdateSerializer(extra, data=request.data)
        if serializer.is_valid():
            updated_extra = serializer.save()
            logger.info(f"Extra '{updated_extra.name}' updated successfully")
            return Response(ExtraSerializer(updated_extra).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        extra = get_object_or_404(Extra, pk=pk)
        extra_name = extra.name
        product_name = extra.product.name
        extra.delete()
        logger.info(f"Extra '{extra_name}' deleted from product '{product_name}'")
        return Response(
            {'message': f'Extra "{extra_name}" deleted successfully'}, 
            status=status.HTTP_200_OK
        )


class ProductExtrasView(APIView):
    """Get all extras for a specific product"""
    def get(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        extras = Extra.objects.filter(product=product).order_by('name')
        serializer = ExtraSerializer(extras, many=True)
        
        return Response({
            'product': {
                'id': product.id,
                'name': product.name,
                'price': product.price
            },
            'extras': serializer.data
        }, status=status.HTTP_200_OK)
