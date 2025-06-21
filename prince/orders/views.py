# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem, CartItemExtra, Order, OrderItem, OrderItemExtra
from .serializers import OrderSerializer, CartSerializer, CartItemSerializer
from products.models import Product, Extra
from .utils import print_bill, print_kitchen_bill, print_counter_bill
import logging

logger = logging.getLogger(__name__)


class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        product_id = request.data.get('item')
        quantity = int(request.data.get('quantity', 1))
        note = request.data.get('note', '')
        extras = request.data.get('extras', [])  # List of {extra_id, quantity}

        if not product_id:
            return Response({'error': 'Product ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        if quantity <= 0:
            return Response({'error': 'Quantity must be greater than 0'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            # Get or create the cart
            cart, created = Cart.objects.get_or_create(
                user=user,
                defaults={'order_type': 'delivery', 'total_amount': 0}
            )

            # Check if item already exists in cart
            cart_item, item_created = CartItem.objects.get_or_create(
                cart=cart,
                item=product,
                defaults={'quantity': quantity, 'note': note}
            )

            if not item_created:
                # Update existing item
                cart_item.quantity += quantity
                cart_item.note = note or cart_item.note
                cart_item.save()
                # Clear existing extras to add new ones
                cart_item.extras.all().delete()

            # Add extras to cart item
            if extras:
                for extra_data in extras:
                    extra_id = extra_data.get('extra_id')
                    extra_quantity = extra_data.get('quantity', 1)
                    
                    if extra_id and extra_quantity > 0:
                        try:
                            extra = Extra.objects.get(id=extra_id)
                            CartItemExtra.objects.create(
                                cart_item=cart_item,
                                extra=extra,
                                quantity=extra_quantity
                            )
                        except Extra.DoesNotExist:
                            continue

            # Recalculate cart total
            self._recalculate_cart_total(cart)

        # Return updated cart data
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _recalculate_cart_total(self, cart):
        """Helper method to recalculate cart total"""
        total = 0
        for item in cart.items.all():
            base_total = item.item.price * item.quantity
            extras_total = sum(extra.total_amount for extra in item.extras.all())
            total += base_total + extras_total
        cart.total_amount = total
        cart.save()


class CartItemUpdateView(APIView):
    """Update individual cart item quantity and note"""
    permission_classes = [IsAuthenticated]

    def patch(self, request, item_id):
        try:
            cart_item = CartItem.objects.select_related('cart', 'item').get(
                id=item_id,
                cart__user=request.user
            )
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)

        quantity = request.data.get('quantity')
        note = request.data.get('note')
        extras = request.data.get('extras', [])

        with transaction.atomic():
            # Update quantity
            if quantity is not None:
                try:
                    quantity = int(quantity)
                    if quantity <= 0:
                        return Response({'error': 'Quantity must be greater than 0'}, status=status.HTTP_400_BAD_REQUEST)
                    cart_item.quantity = quantity
                except (ValueError, TypeError):
                    return Response({'error': 'Invalid quantity'}, status=status.HTTP_400_BAD_REQUEST)

            # Update note
            if note is not None:
                cart_item.note = note

            cart_item.save()

            # Update extras if provided
            if extras:
                cart_item.extras.all().delete()
                for extra_data in extras:
                    extra_id = extra_data.get('extra_id')
                    extra_quantity = extra_data.get('quantity', 1)
                    
                    if extra_id and extra_quantity > 0:
                        try:
                            extra = Extra.objects.get(id=extra_id)
                            CartItemExtra.objects.create(
                                cart_item=cart_item,
                                extra=extra,
                                quantity=extra_quantity
                            )
                        except Extra.DoesNotExist:
                            continue

            # Recalculate cart total
            cart = cart_item.cart
            self._recalculate_cart_total(cart)

        # Return updated cart
        cart_serializer = CartSerializer(cart)
        return Response({
            'message': 'Cart item updated successfully',
            'cart': cart_serializer.data,
            'item': CartItemSerializer(cart_item).data
        }, status=status.HTTP_200_OK)

    def _recalculate_cart_total(self, cart):
        """Helper method to recalculate cart total"""
        total = 0
        for item in cart.items.all():
            base_total = item.item.price * item.quantity
            extras_total = sum(extra.total_amount for extra in item.extras.all())
            total += base_total + extras_total
        cart.total_amount = total
        cart.save()


class CartItemDeleteView(APIView):
    """Remove individual cart item"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        try:
            cart_item = CartItem.objects.select_related('cart').get(
                id=item_id,
                cart__user=request.user
            )
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            cart = cart_item.cart
            cart_item.delete()

            # Recalculate cart total
            total = 0
            for item in cart.items.all():
                base_total = item.item.price * item.quantity
                extras_total = sum(extra.total_amount for extra in item.extras.all())
                total += base_total + extras_total
            cart.total_amount = total
            cart.save()

        # Return updated cart
        cart_serializer = CartSerializer(cart)
        return Response({
            'message': 'Cart item removed successfully',
            'cart': cart_serializer.data
        }, status=status.HTTP_200_OK)


class PlaceOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            cart = request.user.cart
        except Cart.DoesNotExist:
            return Response({'error': 'No cart found'}, status=status.HTTP_404_NOT_FOUND)

        if not cart.items.exists():
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

        # Get order data from request or use cart data
        order_type = request.data.get('order_type', cart.order_type)
        table_number = request.data.get('table_number', cart.table_number)

        # Validate order type
        if order_type not in ['delivery', 'parcel', 'table']:
            return Response({'error': 'Invalid order type'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate table number for table orders
        if order_type == 'table' and not table_number:
            return Response({'error': 'Table number is required for table orders'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Create Order instance
            order = Order.objects.create(
                user=request.user,
                order_type=order_type,
                table_number=table_number if order_type == 'table' else None,
                total_amount=cart.total_amount
            )

            # Create OrderItems and OrderItemExtras
            order_items = []
            for cart_item in cart.items.all():
                # Calculate base total for order item
                base_total = cart_item.item.price * cart_item.quantity
                extras_total = sum(extra.total_amount for extra in cart_item.extras.all())
                
                order_item = OrderItem.objects.create(
                    order=order,
                    item=cart_item.item,
                    quantity=cart_item.quantity,
                    note=cart_item.note,
                    total_amount=base_total + extras_total
                )
                
                # Create OrderItemExtras
                for cart_extra in cart_item.extras.all():
                    OrderItemExtra.objects.create(
                        order_item=order_item,
                        extra=cart_extra.extra,
                        quantity=cart_extra.quantity,
                        total_amount=cart_extra.total_amount
                    )
                
                order_items.append(order_item)

            # Clear cart
            cart.items.all().delete()
            cart.total_amount = 0
            cart.save()

        # Prepare order data for printing
        order_data = {
            "id": order.id,
            "user": order.user.username,
            "order_type": order.order_type,
            "table_number": order.table_number,
            "total_amount": float(order.total_amount),
            "ordered_at": order.ordered_at.strftime("%Y-%m-%d %H:%M:%S"),
            "items": []
        }

        for order_item in order_items:
            item_data = {
                "item_id": order_item.item.id,
                "item_name": order_item.item.name,
                "quantity": order_item.quantity,
                "note": order_item.note,
                "total_amount": float(order_item.total_amount),
                "extras": []
            }
            
            for extra in order_item.extras.all():
                item_data["extras"].append({
                    "name": extra.extra.name,
                    "quantity": extra.quantity,
                    "total_amount": float(extra.total_amount)
                })
            
            order_data["items"].append(item_data)

        # Print to Kitchen and Counter
        kitchen_ip = '192.168.0.101'
        counter_ip = '192.168.0.100'

        try:
            print_kitchen = print_kitchen_bill(order_data, kitchen_ip)
            print_counter = print_counter_bill(order_data, counter_ip)
        except Exception as e:
            logger.error(f"Printing error for order {order.id}: {str(e)}")
            print_kitchen = False
            print_counter = False

        logger.info(f"Order {order.id} - Kitchen print: {'Success' if print_kitchen else 'Failed'}")
        logger.info(f"Order {order.id} - Counter print: {'Success' if print_counter else 'Failed'}")

        if not print_kitchen and not print_counter:
            return Response({
                "message": "Order placed but printing failed",
                "order_id": order.id,
                "printing_status": {
                    "kitchen": "Failed",
                    "counter": "Failed"
                }
            }, status=status.HTTP_206_PARTIAL_CONTENT)

        return Response({
            "message": "Order placed successfully!",
            "order_id": order.id,
            "printing_status": {
                "kitchen": "Success" if print_kitchen else "Failed",
                "counter": "Success" if print_counter else "Failed"
            }
        }, status=status.HTTP_201_CREATED)


class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get query parameters for filtering
        order_type = request.query_params.get('order_type')
        limit = request.query_params.get('limit')
        
        orders = Order.objects.filter(user=request.user).order_by('-ordered_at')
        
        # Apply filters
        if order_type:
            orders = orders.filter(order_type=order_type)
        
        if limit:
            try:
                limit = int(limit)
                orders = orders[:limit]
            except ValueError:
                pass
        
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)
            serializer = OrderSerializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)


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
            logger.error(f"Error fetching cart: {str(e)}")
            return Response(
                {'error': 'Failed to fetch cart', 'detail': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def patch(self, request):
        """Update user's cart (order_type, table_number)"""
        try:
            cart, created = Cart.objects.get_or_create(
                user=request.user,
                defaults={
                    'order_type': 'delivery',
                    'total_amount': 0
                }
            )
            
            logger.info(f"Cart update request data: {request.data}")
            
            # Validate order_type if provided
            order_type = request.data.get('order_type')
            if order_type and order_type not in ['delivery', 'parcel', 'table']:
                return Response(
                    {'error': 'Invalid order type. Must be delivery, parcel, or table'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
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
                with transaction.atomic():
                    cart.items.all().delete()
                    cart.total_amount = 0
                    cart.save()
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
            logger.error(f"Error clearing cart: {str(e)}")
            return Response(
                {'error': 'Failed to clear cart', 'detail': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CartItemExtraView(APIView):
    """Manage extras for cart items"""
    permission_classes = [IsAuthenticated]

    def post(self, request, item_id):
        """Add extra to cart item"""
        try:
            cart_item = CartItem.objects.get(
                id=item_id,
                cart__user=request.user
            )
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)

        extra_id = request.data.get('extra_id')
        quantity = request.data.get('quantity', 1)

        if not extra_id:
            return Response({'error': 'Extra ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            quantity = int(quantity)
            if quantity <= 0:
                return Response({'error': 'Quantity must be greater than 0'}, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid quantity'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            extra = Extra.objects.get(id=extra_id)
        except Extra.DoesNotExist:
            return Response({'error': 'Extra not found'}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            # Check if extra already exists for this cart item
            cart_item_extra, created = CartItemExtra.objects.get_or_create(
                cart_item=cart_item,
                extra=extra,
                defaults={'quantity': quantity}
            )

            if not created:
                cart_item_extra.quantity += quantity
                cart_item_extra.save()

            # Recalculate cart total
            cart = cart_item.cart
            total = 0
            for item in cart.items.all():
                base_total = item.item.price * item.quantity
                extras_total = sum(e.total_amount for e in item.extras.all())
                total += base_total + extras_total
            cart.total_amount = total
            cart.save()

        # Return updated cart
        cart_serializer = CartSerializer(cart)
        return Response({
            'message': 'Extra added successfully',
            'cart': cart_serializer.data
        }, status=status.HTTP_200_OK)

    def delete(self, request, item_id, extra_id):
        """Remove extra from cart item"""
        try:
            cart_item_extra = CartItemExtra.objects.get(
                cart_item_id=item_id,
                extra_id=extra_id,
                cart_item__cart__user=request.user
            )
        except CartItemExtra.DoesNotExist:
            return Response({'error': 'Cart item extra not found'}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            cart = cart_item_extra.cart_item.cart
            cart_item_extra.delete()

            # Recalculate cart total
            total = 0
            for item in cart.items.all():
                base_total = item.item.price * item.quantity
                extras_total = sum(e.total_amount for e in item.extras.all())
                total += base_total + extras_total
            cart.total_amount = total
            cart.save()

        # Return updated cart
        cart_serializer = CartSerializer(cart)
        return Response({
            'message': 'Extra removed successfully',
            'cart': cart_serializer.data
        }, status=status.HTTP_200_OK)


class RepeatOrderView(APIView):
    """Add items from a previous order to cart"""
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            # Get or create cart
            cart, created = Cart.objects.get_or_create(
                user=request.user,
                defaults={'order_type': 'delivery', 'total_amount': 0}
            )

            # Add order items to cart
            for order_item in order.items.all():
                cart_item, item_created = CartItem.objects.get_or_create(
                    cart=cart,
                    item=order_item.item,
                    defaults={
                        'quantity': order_item.quantity,
                        'note': order_item.note
                    }
                )

                if not item_created:
                    cart_item.quantity += order_item.quantity
                    cart_item.save()
                    # Clear existing extras
                    cart_item.extras.all().delete()

                # Add extras
                for order_extra in order_item.extras.all():
                    CartItemExtra.objects.create(
                        cart_item=cart_item,
                        extra=order_extra.extra,
                        quantity=order_extra.quantity
                    )

            # Recalculate cart total
            total = 0
            for item in cart.items.all():
                base_total = item.item.price * item.quantity
                extras_total = sum(e.total_amount for e in item.extras.all())
                total += base_total + extras_total
            cart.total_amount = total
            cart.save()

        # Return updated cart
        cart_serializer = CartSerializer(cart)
        return Response({
            'message': 'Order items added to cart successfully',
            'cart': cart_serializer.data
        }, status=status.HTTP_200_OK)