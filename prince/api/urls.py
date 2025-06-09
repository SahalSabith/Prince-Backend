from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from login.views import *
from products.views import *
from orders.views import *

urlpatterns = [
    # USER SIDE AUTHENTICATIONS
    path('signup/', RegisterUserAPIView.as_view(), name='signup'),
    path('login/', LoginUserAPIView.as_view(), name='login'),
    path('logout/', LogoutUserAPIView.as_view(), name='logout'),
    path('profile/', UserProfileAPIView.as_view(), name='profile'),
    path('change-password/', ChangePasswordAPIView.as_view(), name='change_password'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('health/', HealthCheckAPIView.as_view(), name='health_check'),


    # USER PRODUCTS AND CATEGORY
    path('categories/', CategoryListAPI.as_view(), name='category-list'),
    path('create-category/', CategoryCreateAPI.as_view(), name='create-category'),
    path('dishes/', DishListAPI.as_view(), name='dish-list'),
    path('create-dish/', DishCreateAPI.as_view(), name='create-dish'),

    # USER CART
    path('cart/', CartAPIView.as_view(), name='cart-detail'),
    path('cart/items/', CartItemAPIView.as_view(), name='cart-items'),
    path('cart/items/<int:pk>/',CartItemDetailAPIView.as_view(), name='cart-item-detail'),
    path('cart/clear/',CartAPIView.as_view(), name='cart-clear'),
    
    # USER ORDER
    path('orders/place/',PlaceOrderAPIView.as_view(), name='place-order'),
    path('orders/',OrderListAPIView.as_view(), name='order-list'),
    path('orders/<int:pk>/',OrderDetailAPIView.as_view(), name='order-detail'),
]