from django.urls import path
from .views import *

urlpatterns = [
    path('Category/create/', CategoryCreateView.as_view(), name='Category-create'),
    path('Category/', CategoryListView.as_view(), name='Category-list'),
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
]