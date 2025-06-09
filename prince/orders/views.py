from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Cart, CartItem, Order, OrderItem
from products.models import Dish
from .serializers import CartSerializer, CartItemSerializer, OrderSerializer
from rest_framework.permissions import IsAuthenticated


class CartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_or_create_cart(self, user):
        cart = Cart.objects.filter(user=user, is_active=True).first()
        if not cart:
            cart = Cart.objects.create(user=user)
        return cart

    def get(self, request):
        cart = self.get_or_create_cart(request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    def patch(self, request):
        cart = self.get_or_create_cart(request.user)
        serializer = CartSerializer(cart, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        cart = self.get_or_create_cart(request.user)
        cart.items.all().delete()
        cart.calculate_total()
        return Response({'message': 'Cart cleared successfully'}, status=status.HTTP_200_OK)

class CartItemAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_or_create_cart(self, user):
        cart = Cart.objects.filter(user=user, is_active=True).first()
        if not cart:
            cart = Cart.objects.create(user=user)
        return cart

    def get(self, request):
        cart = self.get_or_create_cart(request.user)
        items = cart.items.all()
        serializer = CartItemSerializer(items, many=True)
        return Response(serializer.data)

    def post(self, request):
        cart = self.get_or_create_cart(request.user)
        
        try:
            dish_id = request.data.get('dish')
            quantity = int(request.data.get('quantity', 1))
            
            if quantity <= 0:
                return Response({'error': 'Quantity must be greater than 0'}, status=status.HTTP_400_BAD_REQUEST)
            
            dish = get_object_or_404(Dish, id=dish_id)
            
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                dish=dish,
                defaults={'quantity': quantity}
            )
            
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
                message = 'Item quantity updated in cart'
            else:
                message = 'Item added to cart'
            
            serializer = CartItemSerializer(cart_item)
            return Response({
                'message': message,
                'item': serializer.data
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
            
        except (ValueError, TypeError):
            return Response({'error': 'Invalid quantity'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CartItemDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        return get_object_or_404(CartItem, pk=pk, cart__user=user, cart__is_active=True)

    def get(self, request, pk):
        item = self.get_object(pk, request.user)
        serializer = CartItemSerializer(item)
        return Response(serializer.data)

    def patch(self, request, pk):
        item = self.get_object(pk, request.user)
        
        try:
            quantity = int(request.data.get('quantity', item.quantity))
            
            if quantity <= 0:
                return Response({'error': 'Quantity must be greater than 0'}, status=status.HTTP_400_BAD_REQUEST)
            
            item.quantity = quantity
            item.save()
            
            serializer = CartItemSerializer(item)
            return Response(serializer.data)
            
        except (ValueError, TypeError):
            return Response({'error': 'Invalid quantity'}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        item = self.get_object(pk, request.user)
        cart = item.cart
        item.delete()
        cart.calculate_total()
        return Response({'message': 'Item removed from cart'}, status=status.HTTP_204_NO_CONTENT)

class PlaceOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        try:
            cart = Cart.objects.filter(user=request.user, is_active=True).first()
            
            if not cart or not cart.items.exists():
                return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
            
            order = Order.objects.create(
                user=cart.user,
                table_number=cart.table_number or "Not specified",
                order_type=cart.order_type,
                total_amount=cart.total_amount
            )
            
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    dish=cart_item.dish,
                    dish_name=cart_item.dish.name,
                    dish_price=cart_item.dish.price,
                    quantity=cart_item.quantity,
                    amount=cart_item.amount
                )
            
            cart.is_active = False
            cart.save()
            
            serializer = OrderSerializer(order)
            return Response({
                'message': 'Order placed successfully',
                'order': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class OrderListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

class OrderDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk, user=request.user)
        serializer = OrderSerializer(order)
        return Response(serializer.data)