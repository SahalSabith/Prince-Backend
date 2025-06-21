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
    path('orders/<int:order_id>/', OrderDetailView.as_view(), name='order-detail'),
    path('cart/items/<int:item_id>/extras/', CartItemExtraView.as_view(), name='cart-item-extra'),
    path('cart/items/<int:item_id>/extras/<int:extra_id>/', CartItemExtraView.as_view(), name='cart-item-extra-delete'),
    path('orders/<int:order_id>/repeat/', RepeatOrderView.as_view(), name='repeat-order'),

]