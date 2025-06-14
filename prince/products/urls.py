from django.urls import path
from .views import *

urlpatterns = [
    path('category/create/', CategoryCreateView.as_view(), name='category-create'),
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
]