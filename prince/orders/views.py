# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Cart, CartItem
from .serializers import OrderSerializer
from .models import Order, OrderItem, Cart, CartItem
from products.models import Product
from .serializers import CartSerializer, CartItemSerializer
from .utils import print_bill, print_kitchen_bill, print_counter_bill
import logging

logger = logging.getLogger(__name__)


class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        Products_id = request.data.get('item')
        quantity = int(request.data.get('quantity', 1))
        note = request.data.get('note', '')

        if not Products_id:
            return Response({'error': 'Products ID is required'}, status=400)

        try:
            Products = Product.objects.get(id=Products_id)
        except Products.DoesNotExist:
            return Response({'error': 'Products not found'}, status=404)

        # 1. Get or create the cart
        cart, created = Cart.objects.get_or_create(
            user=user,
            defaults={'order_type': 'table', 'total_amount': 0}
        )

        # 2. Check if item already exists in cart
        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart,
            item=Products,
            defaults={'quantity': quantity, 'note': note}
        )

        if not item_created:
            # Update quantity and note
            cart_item.quantity += quantity
            cart_item.note = note or cart_item.note
            cart_item.save()

        # 3. Recalculate cart total
        total = sum(item.total_amount for item in cart.items.all())
        cart.total_amount = total
        cart.save()

        # Return updated cart data
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=200)


class CartItemUpdateView(APIView):
    """Update individual cart item quantity and note"""
    permission_classes = [IsAuthenticated]

    def patch(self, request, item_id):
        try:
            # Get the cart item and ensure it belongs to the user
            cart_item = CartItem.objects.select_related('cart', 'item').get(
                id=item_id,
                cart__user=request.user
            )
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found'}, status=404)

        # Get the data from request
        quantity = request.data.get('quantity')
        note = request.data.get('note', cart_item.note)

        # Validate quantity
        if quantity is not None:
            try:
                quantity = int(quantity)
                if quantity <= 0:
                    return Response({'error': 'Quantity must be greater than 0'}, status=400)
            except (ValueError, TypeError):
                return Response({'error': 'Invalid quantity'}, status=400)

            cart_item.quantity = quantity

        # Update note if provided
        if note is not None:
            cart_item.note = note

        cart_item.save()

        # Recalculate cart total
        cart = cart_item.cart
        total = sum(item.total_amount for item in cart.items.all())
        cart.total_amount = total
        cart.save()

        # Return updated cart
        cart_serializer = CartSerializer(cart)
        return Response({
            'message': 'Cart item updated successfully',
            'cart': cart_serializer.data,
            'item': CartItemSerializer(cart_item).data
        }, status=200)


class CartItemDeleteView(APIView):
    """Remove individual cart item"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        try:
            # Get the cart item and ensure it belongs to the user
            cart_item = CartItem.objects.select_related('cart').get(
                id=item_id,
                cart__user=request.user
            )
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found'}, status=404)

        cart = cart_item.cart
        cart_item.delete()

        # Recalculate cart total
        total = sum(item.total_amount for item in cart.items.all())
        cart.total_amount = total
        cart.save()

        # Return updated cart
        cart_serializer = CartSerializer(cart)
        return Response({
            'message': 'Cart item removed successfully',
            'cart': cart_serializer.data
        }, status=200)


class PlaceOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            cart = request.user.cart
        except Cart.DoesNotExist:
            return Response({'detail': 'No cart found'}, status=404)

        if not cart.items.exists():
            return Response({'detail': 'Cart is empty'}, status=400)

        # Get order data from request or use cart data
        order_type = request.data.get('order_type', cart.order_type)
        table_number = request.data.get('table_number', cart.table_number)

        order = Order.objects.create(
            user=request.user,
            order_type=order_type,
            total_amount=cart.total_amount
        )

        order_items = []
        for item in cart.items.all():
            order_item = OrderItem.objects.create(
                order=order,
                item=item.item,
                quantity=item.quantity,
                note=item.note,
                total_amount=item.total_amount
            )
            order_items.append(order_item)

        # Clear Cart
        cart.items.all().delete()
        cart.total_amount = 0
        cart.save()

        serializer = OrderSerializer(order)
        order_data = serializer.data

        # Different IPs for different printers
        kitchen_ip = '192.168.0.106'  # Kitchen printer IP
        counter_ip = '192.168.0.103'  # Counter printer IP (change this)

        print_kitchen = print_kitchen_bill(order_data, kitchen_ip)
        print_counter = print_counter_bill(order_data, counter_ip)
        
        # Log printing results
        logger.info(f"Order {order.id} - Kitchen print: {'Success' if print_kitchen else 'Failed'}")
        logger.info(f"Order {order.id} - Counter print: {'Success' if print_counter else 'Failed'}")
        
        if not print_kitchen and not print_counter:
            return Response({
                "detail": "Order saved but kitchen printer failed",
                "order_id": order.id
            }, status=status.HTTP_206_PARTIAL_CONTENT)

        return Response({
            'detail': 'Order placed successfully!', 
            'order_id': order.id,
            'printing_status': 'Kitchen printer successful'
        })


class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by('-ordered_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
    

class CartDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user's cart"""
        try:
            cart, created = Cart.objects.get_or_create(
                user=request.user,
                defaults={
                    'order_type': 'delivery',
                    'total_amount': 0
                }
            )
            serializer = CartSerializer(cart)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': 'Failed to fetch cart', 'detail': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def patch(self, request):
        """Update user's cart"""
        try:
            cart, created = Cart.objects.get_or_create(
                user=request.user,
                defaults={
                    'order_type': 'delivery',
                    'total_amount': 0
                }
            )
            
            # Log the incoming data for debugging
            logger.info(f"Cart update request data: {request.data}")
            
            # Use partial=True to allow partial updates
            serializer = CartSerializer(cart, data=request.data, partial=True)
            
            if serializer.is_valid():
                updated_cart = serializer.save()
                logger.info(f"Cart updated successfully: {updated_cart.order_type}, {updated_cart.table_number}")
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                logger.error(f"Cart update validation errors: {serializer.errors}")
                return Response(
                    {'error': 'Invalid data', 'details': serializer.errors}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Cart update exception: {str(e)}")
            return Response(
                {'error': 'Failed to update cart', 'detail': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request):
        """Clear user's cart"""
        try:
            cart = Cart.objects.filter(user=request.user).first()
            if cart:
                cart.delete()
                return Response(
                    {'message': 'Cart cleared successfully'}, 
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'message': 'Cart not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            return Response(
                {'error': 'Failed to clear cart', 'detail': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )