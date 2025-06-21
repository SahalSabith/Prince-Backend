from django.urls import path
from .views import *

urlpatterns = [
    # Cart management
    path('cart/', CartDetailView.as_view(), name='cart-detail'),
    path('cart/add/', AddToCartView.as_view(), name='add-to-cart'),
    
    # Cart item management
    path('cart/item/<int:item_id>/update/', CartItemUpdateView.as_view(), name='update-cart-item'),
    path('cart/item/<int:item_id>/delete/', CartItemDeleteView.as_view(), name='delete-cart-item'),
    
    # Orders
    path('order/', PlaceOrderView.as_view(), name='place-order'),
    path('orders/', OrderListView.as_view(), name='order-list'),
]