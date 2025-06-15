# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from escpos.printer import Network
import logging

logger = logging.getLogger(__name__)


def print_kitchen_bill(order_data, printer_ip):
    """Clear and readable kitchen print with bakery name, icon, and items"""
    try:
        printer = Network(printer_ip)

        # ========== Top Branding ==========
        printer.set(align='center', bold=True, width=2, height=2)
        printer.text("PRINCE BAKERY\n\n")

        # ========== Order Type (Table or Delivery with icon) ==========
        order_type = order_data.get('order_type', '').upper()
        is_table = order_type.startswith('T')
        icon = '🅣' if is_table else '🅓'
        type_label = 'TABLE' if is_table else 'DELIVERY'

        printer.set(align='center', bold=True, width=3, height=3)
        printer.text(f"{icon}\n")
        printer.set(align='center', bold=True, width=2, height=2)
        printer.text(f"{type_label}\n\n")

        # ========== Divider ==========
        printer.set(align='center', bold=False, width=1, height=1)
        printer.text("=" * 32 + "\n\n")

        # ========== Order Section ==========
        printer.set(align='center', bold=True, width=2, height=2)
        printer.text("ORDER\n\n")

        for item in order_data.get("items", []):
            qty = item["quantity"]
            name = item["Products"].upper()

            printer.set(align='center', bold=True, width=3, height=3)
            printer.text(f"{qty} x {name}\n\n")

        # ========== Bottom Divider ==========
        printer.set(align='center', bold=False, width=1, height=1)
        printer.text("=" * 32 + "\n\n")

        # ========== Time and Date ==========
        ordered_at = order_data.get('ordered_at', '')
        date_part = ordered_at[:10]
        time_part = ordered_at[11:16]

        printer.set(align='center', bold=True, width=2, height=2)
        printer.text(f"DATE: {date_part}\n")
        printer.text(f"TIME: {time_part}\n\n\n")

        printer.cut()
        printer.close()
        return True

    except Exception as e:
        logger.error(f"Kitchen printer failed: {e}")
        print(f"Kitchen print failed: {e}")
        return False


def print_counter_bill(order_data, printer_ip):
    """Print counter copy with full details including prices"""
    try:
        printer = Network(printer_ip)
        
        # Header
        printer.set(align='center', bold=True, width=2, height=2)
        printer.text("Prince Bakery\n")
        printer.set(bold=False, width=1, height=1)
        printer.text("Customer Copy\n")
        printer.text("-" * 32 + "\n")
        
        # Order details
        printer.set(align='left')
        printer.text(f"Order #: {order_data['id']}\n")
        printer.text(f"Type: {order_data['order_type'].upper()}\n")
        printer.text(f"Date: {order_data['ordered_at'][:19]}\n")
        printer.text(f"Customer: {order_data['user']['username']}\n")
        printer.text("-" * 32 + "\n")
        
        # Items with prices
        printer.set(bold=True)
        printer.text("ITEMS:\n")
        printer.set(bold=False)
        
        for item in order_data.get('items', []):
            name = item['Products']['name']
            qty = item['quantity']
            price = float(item['total_amount'])
            
            # Format item line
            item_line = f"{qty}x {name}"
            price_str = f"₹{price:.2f}"
            
            # Print item and price on same line
            spaces_needed = 32 - len(item_line) - len(price_str)
            printer.text(f"{item_line}{' ' * max(1, spaces_needed)}{price_str}\n")
            
            if item.get('note'):
                printer.text(f"   Note: {item['note']}\n")
        
        printer.text("-" * 32 + "\n")
        
        # Total
        printer.set(bold=True)
        total_line = f"TOTAL: ₹{float(order_data['total_amount']):.2f}"
        printer.text(total_line + "\n")
        printer.set(bold=False)
        
        printer.text("-" * 32 + "\n")
        printer.text("Thank you for your order!\n")
        printer.text("\n\n")
        
        printer.cut()
        printer.close()
        return True
        
    except Exception as e:
        logger.error(f"Counter printer failed: {e}")
        print(f"Counter print failed: {e}")
        return False


# Alternative: Single print function with different formats
def print_bill(order_data, printer_ip, print_type="counter"):
    """
    Single function to handle both kitchen and counter printing
    print_type: 'kitchen' or 'counter'
    """
    try:
        printer = Network(printer_ip)
        
        if print_type == "kitchen":
            # Kitchen format - simpler, no prices
            printer.set(align='center', bold=True, width=2, height=2)
            printer.text("KITCHEN COPY\n")
            printer.text("Prince Bakery\n")
            printer.set(bold=False, width=1, height=1)
            printer.text("-" * 32 + "\n")
            
            printer.set(align='left')
            printer.text(f"Order #: {order_data['id']}\n")
            printer.text(f"Type: {order_data['order_type'].upper()}\n")
            printer.text(f"Time: {order_data['ordered_at'][:19]}\n")
            printer.text("-" * 32 + "\n")
            
            printer.set(bold=True)
            printer.text("ITEMS:\n")
            printer.set(bold=False)
            
            for item in order_data.get('items', []):
                printer.text(f"{item['quantity']}x {item['Products']['name']}\n")
                if item.get('note'):
                    printer.text(f"   Note: {item['note']}\n")
                    
        else:  # counter format
            # Counter format - full receipt with prices
            printer.set(align='center', bold=True, width=2, height=2)
            printer.text("Prince Bakery\n")
            printer.set(bold=False, width=1, height=1)
            printer.text("Customer Copy\n")
            printer.text("-" * 32 + "\n")
            
            printer.set(align='left')
            printer.text(f"Order #: {order_data['id']}\n")
            printer.text(f"Type: {order_data['order_type'].upper()}\n")
            printer.text(f"Date: {order_data['ordered_at'][:19]}\n")
            printer.text(f"Customer: {order_data['user']['username']}\n")
            printer.text("-" * 32 + "\n")
            
            printer.set(bold=True)
            printer.text("ITEMS:\n")
            printer.set(bold=False)
            
            for item in order_data.get('items', []):
                name = item['Products']['name']
                qty = item['quantity']
                price = float(item['total_amount'])
                
                item_line = f"{qty}x {name}"
                price_str = f"₹{price:.2f}"
                spaces_needed = 32 - len(item_line) - len(price_str)
                printer.text(f"{item_line}{' ' * max(1, spaces_needed)}{price_str}\n")
                
                if item.get('note'):
                    printer.text(f"   Note: {item['note']}\n")
            
            printer.text("-" * 32 + "\n")
            printer.set(bold=True)
            printer.text(f"TOTAL: ₹{float(order_data['total_amount']):.2f}\n")
            printer.set(bold=False)
            printer.text("-" * 32 + "\n")
            printer.text("Thank you for your order!\n")
        
        printer.text("\n\n")
        printer.cut()
        printer.close()
        return True
        
    except Exception as e:
        logger.error(f"{print_type.capitalize()} printer failed: {e}")
        print(f"{print_type.capitalize()} print failed: {e}")
        return False