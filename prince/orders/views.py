from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Cart
from .serializers import OrderSerializer
from .models import Order, OrderItem, Cart, CartItem
from products.models import Product
from .serializers import CartSerializer
from .utils import print_bill,print_kitchen_bill,print_counter_bill
import logging

logger = logging.getLogger(__name__)

class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        note = request.data.get('note', '')

        if not product_id:
            return Response({'error': 'Product ID is required'}, status=400)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=404)

        # 1. Get or create the cart
        cart, created = Cart.objects.get_or_create(
            user=user,
            defaults={'order_type': 'table', 'total_amount': 0}
        )

        # 2. Check if item already exists in cart
        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity, 'note': note}
        )

        if not item_created:
            # Update quantity and note
            cart_item.quantity += quantity
            cart_item.note = note or cart_item.note
            cart_item.save()

        # 3. Recalculate cart total
        total = 0
        for item in cart.items.all():
            total += item.total_amount
        cart.total_amount = total
        cart.save()

        return Response({'detail': 'Product added to cart successfully.'}, status=200)


class PlaceOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            cart = request.user.cart
        except Cart.DoesNotExist:
            return Response({'detail': 'No cart found'}, status=404)

        if not cart.items.exists():
            return Response({'detail': 'Cart is empty'}, status=400)

        order = Order.objects.create(
            user=request.user,
            order_type=cart.order_type,
            total_amount=cart.total_amount
        )

        order_items = []
        for item in cart.items.all():
            order_item = OrderItem.objects.create(
                order=order,
                product=item.product,
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
        kitchen_ip = '192.168.1.103'  # Kitchen printer IP
        counter_ip = '192.168.1.103'  # Counter printer IP (change this)

        print_kitchen = print_kitchen_bill(order_data, kitchen_ip)
        print_counter = print_counter_bill(order_data, counter_ip)
        
        # Log printing results
        logger.info(f"Order {order.id} - Kitchen print: {'Success' if print_kitchen else 'Failed'}")
        logger.info(f"Order {order.id} - Counter print: {'Success' if print_counter else 'Failed'}")
        
        if not print_kitchen and not print_counter:
            return Response({
                "message": "Order saved but both printers failed",
                "order_id": order.id
            }, status=status.HTTP_206_PARTIAL_CONTENT)
        elif not (print_kitchen and print_counter):
            failed_printer = "kitchen" if not print_kitchen else "counter"
            return Response({
                "message": f"Order saved but {failed_printer} printer failed",
                "order_id": order.id
            }, status=status.HTTP_206_PARTIAL_CONTENT)

        return Response({
            'detail': 'Order placed successfully!', 
            'order_id': order.id,
            'printing_status': 'Both printers successful'
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
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)