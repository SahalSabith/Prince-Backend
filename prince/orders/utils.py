# utils.py
from django.utils.timezone import localtime
from escpos.printer import Network
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def get_item_name(item):
    """Extract item name from various data structures"""
    # For direct item name
    if 'item_name' in item:
        return item['item_name']
    
    # For nested item object
    item_data = item.get("item") or item.get("product")
    if isinstance(item_data, dict):
        return item_data.get("name", "Unknown Item")
    elif hasattr(item_data, "name"):
        return item_data.name
    
    # Fallback to direct name field
    return item.get("name", "Unknown Item")


def get_item_price(item_data, qty=1):
    """Extract item price and calculate total - Fixed version"""
    try:
        price = 0
        
        # Check for direct price field first
        if isinstance(item_data, dict) and "price" in item_data:
            price = float(item_data["price"])
        elif hasattr(item_data, "price"):
            price = float(item_data.price)
        else:
            # If item_data is nested, extract it
            nested_item = item_data.get("item") or item_data.get("product")
            if isinstance(nested_item, dict) and "price" in nested_item:
                price = float(nested_item["price"])
            elif hasattr(nested_item, "price"):
                price = float(nested_item.price)
        
        return price * qty
            
    except (ValueError, TypeError, AttributeError) as e:
        logger.error(f"Error calculating price for item: {item_data}, Error: {e}")
        return 0.0


def get_base_item_price(item):
    """Get base item price without extras"""
    try:
        qty = item.get("quantity", 1)
        
        # Try to get price from nested item/product object
        item_data = item.get("item") or item.get("product")
        if isinstance(item_data, dict):
            price = float(item_data.get("price", 0))
        elif hasattr(item_data, "price"):
            price = float(item_data.price)
        else:
            # Fallback to direct price field
            price = float(item.get("price", 0))
        
        return price * qty
        
    except (ValueError, TypeError, AttributeError) as e:
        logger.error(f"Error getting base price for item: {item}, Error: {e}")
        return 0.0


def get_extras_total(item):
    """Calculate total price of all extras for an item"""
    try:
        extras_total = 0
        extras = item.get('extras', [])
        
        if not extras:
            return 0.0
            
        for extra in extras:
            # Try different ways to get extra price
            if 'total_amount' in extra:
                extras_total += float(extra['total_amount'])
            elif 'price' in extra:
                extra_qty = extra.get('quantity', 1)
                extras_total += float(extra['price']) * extra_qty
            else:
                # Try nested extra object
                extra_data = extra.get('extra')
                if isinstance(extra_data, dict) and 'price' in extra_data:
                    extra_qty = extra.get('quantity', 1)
                    extras_total += float(extra_data['price']) * extra_qty
                elif hasattr(extra_data, 'price'):
                    extra_qty = extra.get('quantity', 1)
                    extras_total += float(extra_data.price) * extra_qty
        
        return extras_total
        
    except (ValueError, TypeError, AttributeError) as e:
        logger.error(f"Error calculating extras total: {e}")
        return 0.0


def get_item_total(item):
    """Get total price for an item including base price and extras"""
    base_price = get_base_item_price(item)
    extras_total = get_extras_total(item)
    return base_price + extras_total


def format_datetime(datetime_obj):
    """Format timezone-aware datetime to local format"""
    try:
        if isinstance(datetime_obj, str):
            # Convert string to datetime
            datetime_obj = datetime.fromisoformat(datetime_obj.replace('Z', '+00:00'))

        # Localize datetime
        dt_local = localtime(datetime_obj)
        date_str = dt_local.strftime("%d-%m-%Y")
        time_str = dt_local.strftime("%H:%M")
        return date_str, time_str

    except Exception as e:
        logger.error(f"Error formatting datetime: {e}")
        return "N/A", "N/A"


def print_kitchen_bill(order_data, printer_ip):
    """Print kitchen bill with improved error handling and fixed pricing"""
    try:
        printer = Network(printer_ip)

        # Header
        printer.set(align='center', bold=True, width=2, height=2)
        printer.text("PRINCE BAKERY\n")
        printer.text("KITCHEN COPY\n\n")

        # Order type - Large single letter
        order_type = order_data.get('order_type', 'delivery').upper()
        printer.set(align='center', bold=True, width=8, height=8)
        printer.text(f"{order_type[0]}\n")

        # Order type full name
        printer.set(align='center', bold=True, width=2, height=2)
        printer.text(f"{order_type}\n")

        if order_type == 'TABLE' and order_data.get('table_number'):
            printer.text(f"TABLE: {order_data['table_number']}\n")

        printer.text("\n")

        # Token & Time
        printer.set(align='center', bold=True, width=1, height=1)
        printer.text("=" * 32 + "\n")
        printer.text(f"TOKEN: {order_data.get('id', 'N/A')}\n")

        # Items with prices - Centered alignment
        printer.set(align='center', bold=True, width=2, height=2)
        printer.text("ITEMS:\n\n")

        total_calculated = 0
        
        for item in order_data.get("items", []):
            qty = item.get("quantity", 1)
            name = get_item_name(item)
            
            # Get base price using our fixed function
            base_price = get_base_item_price(item)
            
            # Get extras total using our fixed function
            extras_total = get_extras_total(item)
            
            # Final item total
            item_total = base_price + extras_total
            total_calculated += item_total

            # Print base item
            printer.set(align='center', bold=True, width=2, height=2)
            printer.text(f"{qty} x {name.upper()}\n")

            printer.set(align='center', bold=True, width=1, height=1)
            printer.text(f"Rs {base_price:.2f}\n")

            # Print extras if any
            if extras_total > 0:
                extras = item.get('extras', [])
                printer.set(align='center', bold=False, width=1, height=1)
                for extra in extras:
                    extra_name = extra.get('extra_name') or extra.get('name', 'Extra')
                    # Handle nested extra object
                    if not extra_name or extra_name == 'Extra':
                        extra_data = extra.get('extra')
                        if isinstance(extra_data, dict):
                            extra_name = extra_data.get('name', 'Extra')
                        elif hasattr(extra_data, 'name'):
                            extra_name = extra_data.name
                    
                    extra_qty = extra.get('quantity', 1)
                    
                    # Get extra price
                    if 'total_amount' in extra:
                        extra_price = float(extra['total_amount'])
                    elif 'price' in extra:
                        extra_price = float(extra['price']) * extra_qty
                    else:
                        extra_data = extra.get('extra')
                        if isinstance(extra_data, dict) and 'price' in extra_data:
                            extra_price = float(extra_data['price']) * extra_qty
                        elif hasattr(extra_data, 'price'):
                            extra_price = float(extra_data.price) * extra_qty
                        else:
                            extra_price = 0.0
                    
                    printer.text(f"  + {extra_qty}x {extra_name} (Rs {extra_price:.2f})\n")

            # Print item total
            printer.set(align='center', bold=True, width=1, height=1)
            printer.text(f"Item Total: Rs {item_total:.2f}\n")

            # Note
            note = item.get('note', '') or item.get('notes', '')
            if note:
                printer.set(align='center', bold=False, width=1, height=1)
                printer.text(f"Note: {note}\n")

            printer.text("\n")

        # Total
        printer.set(align='center', bold=True, width=2, height=2)
        total_amount = order_data.get('total_amount')
        if not total_amount or float(total_amount) == 0:
            total_amount = total_calculated
        printer.text(f"TOTAL: Rs {float(total_amount):.2f}\n")
        printer.set(align='center', bold=False, width=1, height=1)
        printer.text("=" * 32 + "\n")
        printer.text("\n\n\n")

        printer.cut()
        printer.close()
        return True

    except Exception as e:
        logger.error(f"Kitchen printer failed: {e}")
        return False


def print_counter_bill(order_data, printer_ip):
    """Print counter bill with corrected extras breakdown and fixed pricing"""
    try:
        printer = Network(printer_ip)

        # Header
        printer.set(align='center', bold=True, width=2, height=2)
        printer.text("PRINCE BAKERY\n")

        printer.set(align='center', bold=False, width=1, height=1)
        printer.text("CUSTOMER COPY\n")
        printer.text("-" * 32 + "\n")

        # Token
        printer.set(align='center', bold=True, width=3, height=3)
        printer.text(f"TOKEN: {order_data.get('id', 'N/A')}\n\n")

        # Order info
        printer.set(align='left', bold=True, width=1, height=1)
        order_type = order_data.get('order_type', 'delivery').upper()
        printer.text(f"TYPE: {order_type}\n")

        if order_type == 'TABLE' and order_data.get('table_number'):
            printer.text(f"TABLE: {order_data['table_number']}\n")

        # Fixed datetime formatting
        ordered_at = order_data.get('ordered_at') or order_data.get('created_at', '')
        if ordered_at:
            date_str, time_str = format_datetime(ordered_at)
            printer.text(f"DATE: {date_str}\n")
            printer.text(f"TIME: {time_str}\n")

        printer.text("-" * 32 + "\n")

        # Items
        printer.set(bold=True)
        printer.text("ITEMS:\n")
        printer.set(bold=False)

        total_calculated = 0

        for item in order_data.get("items", []):
            qty = item.get('quantity', 1)
            name = get_item_name(item)

            # Get base price using our fixed function
            base_price = get_base_item_price(item)
            
            # Get extras total using our fixed function
            extras_total = get_extras_total(item)
            
            item_total = base_price + extras_total
            total_calculated += item_total

            # Print base item
            item_line = f"{qty}x {name}"
            price_str = f"Rs{base_price:.2f}"
            if len(item_line + price_str) <= 32:
                spaces = 32 - len(item_line + price_str)
                printer.text(f"{item_line}{' ' * spaces}{price_str}\n")
            else:
                printer.text(f"{item_line}\n")
                printer.text(f"{' ' * (32 - len(price_str))}{price_str}\n")

            # Print extras
            if extras_total > 0:
                extras = item.get('extras', [])
                for extra in extras:
                    extra_name = extra.get('extra_name') or extra.get('name', 'Extra')
                    # Handle nested extra object
                    if not extra_name or extra_name == 'Extra':
                        extra_data = extra.get('extra')
                        if isinstance(extra_data, dict):
                            extra_name = extra_data.get('name', 'Extra')
                        elif hasattr(extra_data, 'name'):
                            extra_name = extra_data.name
                    
                    extra_qty = extra.get('quantity', 1)
                    
                    # Get extra price
                    if 'total_amount' in extra:
                        extra_price = float(extra['total_amount'])
                    elif 'price' in extra:
                        extra_price = float(extra['price']) * extra_qty
                    else:
                        extra_data = extra.get('extra')
                        if isinstance(extra_data, dict) and 'price' in extra_data:
                            extra_price = float(extra_data['price']) * extra_qty
                        elif hasattr(extra_data, 'price'):
                            extra_price = float(extra_data.price) * extra_qty
                        else:
                            extra_price = 0.0
                    
                    extra_line = f"  + {extra_qty}x {extra_name}"
                    extra_price_str = f"Rs{extra_price:.2f}"
                    if len(extra_line + extra_price_str) <= 32:
                        spaces = 32 - len(extra_line + extra_price_str)
                        printer.text(f"{extra_line}{' ' * spaces}{extra_price_str}\n")
                    else:
                        printer.text(f"{extra_line}\n")
                        printer.text(f"{' ' * (32 - len(extra_price_str))}{extra_price_str}\n")

            # Show total for this item
            item_total_str = f"Item Total: Rs{item_total:.2f}"
            printer.text(f"{item_total_str:>32}\n")

            # Notes
            note = item.get('note', '') or item.get('notes', '')
            if note:
                printer.text(f"   Note: {note}\n")

        printer.text("-" * 32 + "\n")

        # Total
        printer.set(bold=True)
        total_amount = order_data.get('total_amount')
        if not total_amount or float(total_amount) == 0:
            total_amount = total_calculated
        printer.text(f"TOTAL: Rs{float(total_amount):.2f}\n")
        printer.set(bold=False)

        printer.text("-" * 32 + "\n")

        # Waiting message
        printer.set(align='center', bold=True)
        printer.text("PLEASE WAIT 20 MINUTES\n")
        printer.text("FOR FOOD PREPARATION\n\n")
        printer.set(bold=False)

        # Footer
        printer.set(align='center')
        printer.text("Thank you for your order!\n")
        printer.text("\n\n\n")

        printer.cut()
        printer.close()
        return True

    except Exception as e:
        logger.error(f"Counter printer failed: {e}")
        return False


def print_bill(order_data, printer_ip, print_type="counter"):
    """Generic print function"""
    if print_type == "kitchen":
        return print_kitchen_bill(order_data, printer_ip)
    return print_counter_bill(order_data, printer_ip)