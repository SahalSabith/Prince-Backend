from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from login.views import *
from products.views import *

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
]