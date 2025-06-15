from django.urls import path
from .views import *

urlpatterns = [
    path('Categories/create/', CategoriesCreateView.as_view(), name='Categories-create'),
    path('categories/', CategoriesListView.as_view(), name='Categories-list'),
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
]