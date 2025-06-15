from django.urls import path
from .views import *

urlpatterns = [
    path('Categories/create/', CategoriesCreateView.as_view(), name='Categories-create'),
    path('Categories/', CategoriesListView.as_view(), name='Categories-list'),
    path('Productss/', ProductsListView.as_view(), name='Products-list'),
    path('Productss/<int:pk>/', ProductsDetailView.as_view(), name='Products-detail'),
]