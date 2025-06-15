#!/usr/bin/env python3
"""
Test script to simulate printer output in console
This script fetches order data from the database and shows how the bills would look when printed
"""

import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prince.settings')  # Replace 'your_project' with your actual project name
django.setup()

# Import models after Django setup
from orders.models import Order, OrderItem


class MockPrinter:
    """Mock printer class that outputs to console instead of actual printer"""
    
    def __init__(self, printer_ip=None):
        self.printer_ip = printer_ip
        self.align = 'left'
        self.bold = False
        self.width = 1
        self.height = 1
        self.output = []
        
    def set(self, align='left', bold=False, width=1, height=1):
        self.align = align
        self.bold = bold
        self.width = width
        self.height = height
        
    def text(self, text):
        # Apply formatting
        formatted_text = text
        
        # Apply bold
        if self.bold:
            formatted_text = f"**{formatted_text.strip()}**" if formatted_text.strip() else formatted_text
            
        # Apply width/height scaling (simulate larger text)
        if self.width > 1 or self.height > 1:
            if formatted_text.strip():
                scale_indicator = f"[{self.width}x{self.height}] "
                formatted_text = scale_indicator + formatted_text
                
        # Apply alignment
        if self.align == 'center' and formatted_text.strip():
            formatted_text = formatted_text.center(40)
        elif self.align == 'right' and formatted_text.strip():
            formatted_text = formatted_text.rjust(40)
            
        self.output.append(formatted_text)
        
    def cut(self):
        self.output.append("\n" + "="*50 + " CUT HERE " + "="*50 + "\n")
        
    def close(self):
        pass
        
    def print_output(self):
        print("\n".join(self.output))


def get_order_data_from_db(token_number):
    """Fetch order data from database using token number (order ID)"""
    try:
        order = Order.objects.get(id=token_number)
        order_items = OrderItem.objects.filter(order=order)
        
        # Convert to the format expected by the printer functions
        order_data = {
            'id': order.id,
            'order_type': order.order_type,
            'table_number': order.table_number,
            'ordered_at': order.ordered_at.isoformat(),
            'total_amount': str(order.total_amount),
            'item': []
        }
        
        for order_item in order_items:
            item_data = {
                'quantity': order_item.quantity,
                'note': order_item.note,
                'total_amount': str(order_item.total_amount),
                'item': {
                    'name': order_item.item.name,
                    'price': str(order_item.item.price)
                }
            }
            order_data['item'].append(item_data)
            
        return order_data
        
    except Order.DoesNotExist:
        print(f"Order with token number {token_number} not found!")
        return None
    except Exception as e:
        print(f"Error fetching order data: {e}")
        return None


def print_kitchen_bill_mock(order_data, printer_ip=None):
    """Mock version of print_kitchen_bill that outputs to console"""
    printer = MockPrinter(printer_ip)
    
    # ========== Top Branding ==========
    printer.set(align='center', bold=True, width=2, height=2)
    printer.text("PRINCE BAKERY\n")
    printer.text("KITCHEN COPY\n\n")

    # ========== Order Type (First Letter with Large Font) ==========
    order_type = order_data.get('order_type', 'delivery').upper()
    first_letter = order_type[0]  # Get first letter (D, P, T)
    
    # Make the first letter bigger in font size
    printer.set(align='center', bold=True, width=6, height=6)
    printer.text(f"{first_letter}\n")
    
    printer.set(align='center', bold=True, width=2, height=2)
    printer.text(f"{order_type}\n")
    
    # Add table number if it's a table order
    if order_type == 'TABLE' and order_data.get('table_number'):
        printer.text(f"TABLE: {order_data['table_number']}\n")
    
    printer.text("\n")

    # ========== Divider ==========
    printer.set(align='center', bold=False, width=1, height=1)
    printer.text("=" * 32 + "\n")

    # ========== Order Details ==========
    printer.set(align='left', bold=True, width=1, height=1)
    printer.text(f"TOKEN: {order_data.get('id', 'N/A')}\n")
    
    ordered_at = order_data.get('ordered_at', '')
    if ordered_at:
        time_part = ordered_at[11:16] if len(ordered_at) > 16 else ordered_at
        printer.text(f"TIME: {time_part}\n")
    
    printer.text("=" * 32 + "\n")

    # ========== Items Section ==========
    printer.set(align='left', bold=True, width=2, height=2)
    printer.text("ITEMS:\n")
    
    printer.set(align='left', bold=False, width=1, height=1)
    for item in order_data.get("item", []):
        qty = item.get("quantity", 1)
        
        # Fixed item name access
        name = item.get("item", {}).get("name", "Unknown Item")
        if not name or name == "Unknown Item":
            # Try alternative access patterns
            if hasattr(item.get("item"), 'name'):
                name = item["item"].name
            elif isinstance(item.get("item"), dict) and "name" in item["item"]:
                name = item["item"]["name"]
            else:
                name = "Unknown Item"
        
        printer.set(align='left', bold=True, width=2, height=2)
        printer.text(f"{qty} x {name.upper()}\n")
        
        # Add note if present
        if item.get('note'):
            printer.set(align='left', bold=False, width=1, height=1)
            printer.text(f"   Note: {item['note']}\n")
        
        printer.set(align='left', bold=False, width=1, height=1)
        printer.text("\n")

    # ========== Bottom ==========
    printer.set(align='center', bold=False, width=1, height=1)
    printer.text("=" * 32 + "\n")
    printer.text("\n\n\n")

    printer.cut()
    return printer


def print_counter_bill_mock(order_data, printer_ip=None):
    """Mock version of print_counter_bill that outputs to console"""
    printer = MockPrinter(printer_ip)
    
    # ========== Header ==========
    printer.set(align='center', bold=True, width=2, height=2)
    printer.text("PRINCE BAKERY\n")
    
    printer.set(align='center', bold=False, width=1, height=1)
    printer.text("CUSTOMER COPY\n")
    printer.text("-" * 32 + "\n")
    
    # ========== Token Number (Large) - Only Once ==========
    printer.set(align='center', bold=True, width=3, height=3)
    printer.text(f"TOKEN: {order_data.get('id', 'N/A')}\n\n")
    
    # ========== Order Details ==========
    printer.set(align='left', bold=True, width=1, height=1)
    
    order_type = order_data.get('order_type', 'delivery').upper()
    printer.text(f"TYPE: {order_type}\n")
    
    # Add table number if it's a table order
    if order_type == 'TABLE' and order_data.get('table_number'):
        printer.text(f"TABLE: {order_data['table_number']}\n")
    
    # Date and time
    ordered_at = order_data.get('ordered_at', '')
    if ordered_at:
        if len(ordered_at) >= 19:
            date_part = ordered_at[:10]
            time_part = ordered_at[11:19]
            printer.text(f"DATE: {date_part}\n")
            printer.text(f"TIME: {time_part}\n")
        else:
            printer.text(f"ORDERED: {ordered_at}\n")
    
    printer.text("-" * 32 + "\n")
    
    # ========== Items with Prices ==========
    printer.set(bold=True)
    printer.text("ITEMS:\n")
    printer.set(bold=False)
    
    total_calculated = 0
    
    for item in order_data.get('item', []):
        # Fixed item name access
        name = item.get("item", {}).get("name", "Unknown Item")
        if not name or name == "Unknown Item":
            # Try alternative access patterns
            if hasattr(item.get("item"), 'name'):
                name = item["item"].name
            elif isinstance(item.get("item"), dict) and "name" in item["item"]:
                name = item["item"]["name"]
            else:
                name = "Unknown Item"
        
        qty = item.get('quantity', 1)
        
        # Handle price calculation
        if 'total_amount' in item:
            price = float(item['total_amount'])
        else:
            # Fallback to calculating from product price
            unit_price = float(item.get("item", {}).get("price", 0))
            if unit_price == 0 and hasattr(item.get("item"), 'price'):
                unit_price = float(item["item"].price)
            price = unit_price * qty
        
        total_calculated += price
        
        # Format item line with proper spacing
        item_line = f"{qty}x {name}"
        price_str = f"Rs{price:.2f}"  # Changed from ₹ to Rs to avoid ? mark
        
        # Calculate spaces needed for alignment
        line_length = len(item_line) + len(price_str)
        if line_length < 32:
            spaces_needed = 32 - line_length
            printer.text(f"{item_line}{' ' * spaces_needed}{price_str}\n")
        else:
            # If line is too long, print on separate lines
            printer.text(f"{item_line}\n")
            printer.text(f"{' ' * (32 - len(price_str))}{price_str}\n")
        
        # Add note if present
        if item.get('note'):
            printer.text(f"   Note: {item['note']}\n")
    
    printer.text("-" * 32 + "\n")
    
    # ========== Total ==========
    printer.set(bold=True)
    total_amount = order_data.get('total_amount', total_calculated)
    total_line = f"TOTAL: Rs{float(total_amount):.2f}"  # Changed from ₹ to Rs to avoid ? mark
    printer.text(f"{total_line}\n")
    printer.set(bold=False)
    
    printer.text("-" * 32 + "\n")
    
    # ========== Footer ==========
    printer.set(align='center')
    printer.text("Thank you for your order!\n")
    printer.text("\n\n\n")
    
    printer.cut()
    return printer


def test_printer_output():
    """Main test function"""
    print("=" * 60)
    print("PRINCE BAKERY - PRINTER OUTPUT SIMULATOR")
    print("=" * 60)
    
    # Get token number from user
    while True:
        try:
            token_number = input("\nEnter token number (Order ID) to test: ").strip()
            if not token_number:
                print("Please enter a valid token number.")
                continue
            token_number = int(token_number)
            break
        except ValueError:
            print("Please enter a valid number.")
    
    # Fetch order data
    print(f"\nFetching order data for token: {token_number}")
    order_data = get_order_data_from_db(token_number)
    
    if not order_data:
        return
    
    print(f"Order found! Type: {order_data['order_type']}, Items: {len(order_data['item'])}")
    
    # Test both bill types
    print("\n" + "="*60)
    print("KITCHEN BILL OUTPUT:")
    print("="*60)
    
    kitchen_printer = print_kitchen_bill_mock(order_data)
    kitchen_printer.print_output()
    
    print("\n" + "="*60)
    print("COUNTER BILL OUTPUT:")
    print("="*60)
    
    counter_printer = print_counter_bill_mock(order_data)
    counter_printer.print_output()
    
    # Show raw order data for debugging
    print("\n" + "="*60)
    print("RAW ORDER DATA (for debugging):")
    print("="*60)
    import json
    print(json.dumps(order_data, indent=2, default=str))


if __name__ == "__main__":
    test_printer_output()