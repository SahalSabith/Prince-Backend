# utils.py
from escpos.printer import Network
import logging

logger = logging.getLogger(__name__)


def print_kitchen_bill(order_data, printer_ip):
    """Clear and readable kitchen print with bakery name and order type letter"""
    try:
        printer = Network(printer_ip)

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
        
        # Debug: Print raw item data structure
        print(f"DEBUG - order_data keys: {order_data.keys()}")
        print(f"DEBUG - items data: {order_data.get('item', [])}")
        
        printer.set(align='left', bold=False, width=1, height=1)
        for item in order_data.get("item", []):
            print(f"DEBUG - Processing item: {item}")
            
            qty = item.get("quantity", 1)
            
            # Multiple ways to get item name - try all possible patterns
            name = "Unknown Item"
            
            # Method 1: Direct access from nested dict
            if isinstance(item.get("item"), dict) and "name" in item["item"]:
                name = item["item"]["name"]
            # Method 2: If item is a Django model instance
            elif hasattr(item.get("item"), 'name'):
                name = item["item"].name
            # Method 3: Direct name field in item
            elif "name" in item:
                name = item["name"]
            # Method 4: If the structure is different
            elif "product" in item:
                if isinstance(item["product"], dict) and "name" in item["product"]:
                    name = item["product"]["name"]
                elif hasattr(item["product"], 'name'):
                    name = item["product"].name
            
            print(f"DEBUG - Item name resolved to: {name}")
            
            printer.set(align='left', bold=True, width=2, height=2)
            printer.text(f"{qty} x {name.upper()}\n")
            
            # Add note if present
            note = item.get('note', '') or item.get('notes', '')
            if note:
                printer.set(align='left', bold=False, width=1, height=1)
                printer.text(f"   Note: {note}\n")
            
            printer.set(align='left', bold=False, width=1, height=1)
            printer.text("\n")

        # ========== Bottom ==========
        printer.set(align='center', bold=False, width=1, height=1)
        printer.text("=" * 32 + "\n")
        printer.text("\n\n\n")

        printer.cut()
        printer.close()
        return True

    except Exception as e:
        logger.error(f"Kitchen printer failed: {e}")
        print(f"Kitchen print failed: {e}")
        return False


def print_counter_bill(order_data, printer_ip):
    """Print customer copy with full details including prices"""
    try:
        printer = Network(printer_ip)
        
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
        
        # Debug: Print raw item data structure
        print(f"DEBUG - order_data keys: {order_data.keys()}")
        print(f"DEBUG - items data: {order_data.get('item', [])}")
        
        total_calculated = 0
        
        for item in order_data.get('item', []):
            print(f"DEBUG - Processing item: {item}")
            
            # Multiple ways to get item name - try all possible patterns
            name = "Unknown Item"
            
            # Method 1: Direct access from nested dict
            if isinstance(item.get("item"), dict) and "name" in item["item"]:
                name = item["item"]["name"]
            # Method 2: If item is a Django model instance
            elif hasattr(item.get("item"), 'name'):
                name = item["item"].name
            # Method 3: Direct name field in item
            elif "name" in item:
                name = item["name"]
            # Method 4: If the structure is different
            elif "product" in item:
                if isinstance(item["product"], dict) and "name" in item["product"]:
                    name = item["product"]["name"]
                elif hasattr(item["product"], 'name'):
                    name = item["product"].name
            
            qty = item.get('quantity', 1)
            
            # Handle price calculation - try multiple patterns
            price = 0
            
            # Method 1: Use total_amount from item
            if 'total_amount' in item and item['total_amount']:
                price = float(item['total_amount'])
            # Method 2: Calculate from nested item price
            elif isinstance(item.get("item"), dict) and "price" in item["item"]:
                unit_price = float(item["item"]["price"])
                price = unit_price * qty
            # Method 3: If item is Django model instance
            elif hasattr(item.get("item"), 'price'):
                unit_price = float(item["item"].price)
                price = unit_price * qty
            # Method 4: Direct price field
            elif "price" in item:
                unit_price = float(item["price"])
                price = unit_price * qty
            # Method 5: Product field
            elif "product" in item:
                if isinstance(item["product"], dict) and "price" in item["product"]:
                    unit_price = float(item["product"]["price"])
                    price = unit_price * qty
                elif hasattr(item["product"], 'price'):
                    unit_price = float(item["product"].price)
                    price = unit_price * qty
            
            print(f"DEBUG - Item name: {name}, Qty: {qty}, Price: {price}")
            
            total_calculated += price
            
            # Format item line with proper spacing
            item_line = f"{qty}x {name}"
            price_str = f"Rs{price:.2f}"
            
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
            note = item.get('note', '') or item.get('notes', '')
            if note:
                printer.text(f"   Note: {note}\n")
        
        printer.text("-" * 32 + "\n")
        
        # ========== Total ==========
        printer.set(bold=True)
        total_amount = order_data.get('total_amount', total_calculated)
        total_line = f"TOTAL: Rs{float(total_amount):.2f}"
        printer.text(f"{total_line}\n")
        printer.set(bold=False)
        
        printer.text("-" * 32 + "\n")
        
        # ========== Footer ==========
        printer.set(align='center')
        printer.text("Thank you for your order!\n")
        printer.text("\n\n\n")
        
        printer.cut()
        printer.close()
        return True
        
    except Exception as e:
        logger.error(f"Counter printer failed: {e}")
        print(f"Counter print failed: {e}")
        return False


def print_bill(order_data, printer_ip, print_type="counter"):
    """
    Single function to handle both kitchen and counter printing
    print_type: 'kitchen' or 'counter'
    """
    if print_type == "kitchen":
        return print_kitchen_bill(order_data, printer_ip)
    else:
        return print_counter_bill(order_data, printer_ip)