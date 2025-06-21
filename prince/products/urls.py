from django.urls import path
from .views import *

urlpatterns = [
    # Category URLs
    path('categories/create/', CategoriesCreateView.as_view(), name='categories-create'),
    path('categories/', CategoriesListView.as_view(), name='categories-list'),
    path('categories/<int:pk>/', CategoriesDetailView.as_view(), name='categories-detail'),
    
    # Product URLs
    path('products/create/', ProductsCreateView.as_view(), name='products-create'),
    path('products/', ProductsListView.as_view(), name='products-list'),
    path('products/<int:pk>/', ProductsDetailView.as_view(), name='products-detail'),
    path('categories/<int:category_id>/products/', ProductsByCategoryView.as_view(), name='products-by-category'),
    
    # Extra URLs
    path('extras/create/', ExtrasCreateView.as_view(), name='extras-create'),
    path('extras/', ExtrasListView.as_view(), name='extras-list'),
    path('extras/<int:pk>/', ExtrasDetailView.as_view(), name='extras-detail'),
    path('products/<int:product_id>/extras/', ProductExtrasView.as_view(), name='product-extras'),
]