from django.urls import path
from .views import *

urlpatterns = [
    path('cart/', CartDetailView.as_view(), name='cart-detail'),
    path('cart/add/', AddToCartView.as_view(), name='add-to-cart'),
    path('order/', PlaceOrderView.as_view(), name='place-order'),
    path('orders/', OrderListView.as_view(), name='order-list'),

]