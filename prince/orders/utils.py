# utils.py

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


def get_item_price(item, qty=1):
    """Extract item price and calculate total"""
    try:
        # First check for direct total_amount
        if 'total_amount' in item:
            return float(item['total_amount'])
        
        # Then check for nested item object with price
        item_data = item.get("item") or item.get("product")
        if isinstance(item_data, dict) and "price" in item_data:
            return float(item_data["price"]) * qty
        elif hasattr(item_data, "price"):
            return float(item_data.price) * qty
        
        # Fallback to direct price field
        if "price" in item:
            return float(item["price"]) * qty
            
    except (ValueError, TypeError, AttributeError):
        logger.error(f"Error calculating price for item: {item}")
        return 0.0
    
    return 0.0


def format_datetime(datetime_str):
    """Format datetime string to readable format"""
    try:
        if isinstance(datetime_str, str):
            # Parse the datetime string
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        else:
            dt = datetime_str
        
        # Format to readable format
        date_str = dt.strftime("%d-%m-%Y")
        time_str = dt.strftime("%H:%M")
        return date_str, time_str
    except Exception as e:
        logger.error(f"Error formatting datetime: {e}")
        return "N/A", "N/A"


def print_kitchen_bill(order_data, printer_ip):
    """Print kitchen bill with improved error handling"""
    try:
        printer = Network(printer_ip)

        # Header
        printer.set(align='center', bold=True, width=2, height=2)
        printer.text("PRINCE BAKERY\n")
        printer.text("KITCHEN COPY\n\n")

        # Order type - Large single letter
        order_type = order_data.get('order_type', 'delivery').upper()
        printer.set(align='center', bold=True, width=8, height=8)  # Increased size
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
            price = get_item_price(item, qty)
            total_calculated += price

            # Item name and quantity - centered
            printer.set(align='center', bold=True, width=2, height=2)
            printer.text(f"{qty} x {name.upper()}\n")

            # Price - centered
            printer.set(align='center', bold=True, width=1, height=1)
            printer.text(f"Rs {price:.2f}\n")

            # Extras if any
            if 'extras' in item and item['extras']:
                for extra in item['extras']:
                    extra_name = extra.get('extra_name', extra.get('name', 'Extra'))
                    extra_qty = extra.get('quantity', 1)
                    extra_price = extra.get('total_amount', 0)
                    printer.set(align='center', bold=False, width=1, height=1)
                    printer.text(f"  + {extra_qty}x {extra_name} (Rs {extra_price:.2f})\n")

            # Note
            note = item.get('note', '') or item.get('notes', '')
            if note:
                printer.set(align='center', bold=False, width=1, height=1)
                printer.text(f"Note: {note}\n")

            printer.text("\n")

        # Total
        printer.set(align='center', bold=True, width=2, height=2)
        total_amount = order_data.get('total_amount') or total_calculated
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
    """Print counter bill with improved error handling (removed UPI QR)"""
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
            price = get_item_price(item, qty)
            total_calculated += price

            item_line = f"{qty}x {name}"
            price_str = f"Rs{price:.2f}"
            if len(item_line + price_str) <= 32:
                spaces = 32 - len(item_line + price_str)
                printer.text(f"{item_line}{' ' * spaces}{price_str}\n")
            else:
                printer.text(f"{item_line}\n")
                printer.text(f"{' ' * (32 - len(price_str))}{price_str}\n")

            # Extras if any
            if 'extras' in item and item['extras']:
                for extra in item['extras']:
                    extra_name = extra.get('extra_name', extra.get('name', 'Extra'))
                    extra_qty = extra.get('quantity', 1)
                    extra_price = extra.get('total_amount', 0)
                    extra_line = f"  + {extra_qty}x {extra_name}"
                    extra_price_str = f"Rs{extra_price:.2f}"
                    if len(extra_line + extra_price_str) <= 32:
                        spaces = 32 - len(extra_line + extra_price_str)
                        printer.text(f"{extra_line}{' ' * spaces}{extra_price_str}\n")
                    else:
                        printer.text(f"{extra_line}\n")
                        printer.text(f"{' ' * (32 - len(extra_price_str))}{extra_price_str}\n")

            note = item.get('note', '') or item.get('notes', '')
            if note:
                printer.text(f"   Note: {note}\n")

        printer.text("-" * 32 + "\n")

        # Total
        printer.set(bold=True)
        total_amount = order_data.get('total_amount') or total_calculated
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