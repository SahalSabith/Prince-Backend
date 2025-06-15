from django.urls import path
from .views import *

urlpatterns = [
    path('Categories/create/', CategoriesCreateView.as_view(), name='Categories-create'),
    path('categories/', CategoriesListView.as_view(), name='Categories-list'),
    path('products/', ProductsListView.as_view(), name='Products-list'),
    path('products/<int:pk>/', ProductsDetailView.as_view(), name='Products-detail'),
]