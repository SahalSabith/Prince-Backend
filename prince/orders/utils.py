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
    """Get base item price without extras - Fixed for all data structures"""
    try:
        qty = item.get("quantity", 1)
        price = 0
        
        logger.info(f"Processing item for price: {item}")
        
        # Method 1: Try serialized structure (from API)
        # Structure: { "item": { "price": "10.00", "name": "Product Name" } }
        if "item" in item and isinstance(item["item"], dict):
            item_data = item["item"]
            price_value = item_data.get("price")
            if price_value is not None:
                price = float(str(price_value))
                logger.info(f"Got price from serialized item: {price}")
        
        # Method 2: Try direct structure (from PlaceOrderView)
        # Structure: { "item_name": "Product Name", "price": 10.00 }
        elif "price" in item:
            price_value = item.get("price")
            if price_value is not None:
                price = float(str(price_value))
                logger.info(f"Got price from direct field: {price}")
        
        # Method 3: Try total_amount field (fallback)
        elif "total_amount" in item:
            total_amount = float(item["total_amount"])
            # If there are extras, subtract them to get base price
            extras_total = get_extras_total(item)
            price = (total_amount - extras_total) / qty if qty > 0 else 0
            logger.info(f"Calculated price from total_amount: {price}")
        
        if price == 0:
            logger.warning(f"Price still 0. Item structure: {list(item.keys())}")
            if "item" in item:
                logger.warning(f"Nested item structure: {list(item['item'].keys()) if isinstance(item['item'], dict) else type(item['item'])}")
        
        total_price = price * qty
        logger.info(f"Final calculation: {price} * {qty} = {total_price}")
        
        return total_price
        
    except (ValueError, TypeError, AttributeError) as e:
        logger.error(f"Error getting base price for item: {item}, Error: {e}")
        return 0.0


def get_extras_total(item):
    """Calculate total price of all extras for an item - Fixed for all structures"""
    try:
        extras_total = 0
        extras = item.get('extras', [])
        
        if not extras:
            return 0.0
        
        for extra in extras:
            # Method 1: Check for total_amount (from serializer)
            if 'total_amount' in extra and extra['total_amount'] is not None:
                extras_total += float(extra['total_amount'])
                logger.info(f"Added extra total_amount: {extra['total_amount']}")
            # Method 2: Check for direct price and quantity
            elif 'price' in extra:
                extra_price = float(str(extra.get('price', 0)))
                extra_qty = extra.get('quantity', 1)
                extra_total = extra_price * extra_qty
                extras_total += extra_total
                logger.info(f"Calculated extra total: {extra_price} * {extra_qty} = {extra_total}")
            # Method 3: Check for nested extra object
            else:
                extra_data = extra.get('extra')
                if extra_data and isinstance(extra_data, dict):
                    extra_price = float(str(extra_data.get('price', 0)))
                    extra_qty = extra.get('quantity', 1)
                    extra_total = extra_price * extra_qty
                    extras_total += extra_total
                    logger.info(f"Calculated nested extra total: {extra_price} * {extra_qty} = {extra_total}")
        
        logger.info(f"Total extras amount: {extras_total}")
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
    """Print kitchen bill with single line format and fixed pricing"""
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

        # Items - Single line format
        printer.set(align='center', bold=True, width=2, height=2)
        printer.text("ITEMS:\n\n")

        total_calculated = 0
        
        for item in order_data.get("items", []):
            qty = item.get("quantity", 1)
            name = get_item_name(item)
            
            # Calculate item total (base + extras)
            item_total = get_item_total(item)
            total_calculated += item_total

            # Single line format: "2 x CHICKEN FRIED RICE Rs 150.00"
            printer.set(align='center', bold=True, width=2, height=2)
            printer.text(f"{qty} x {name.upper()} Rs {item_total:.2f}\n")

            # Show extras details in smaller font
            extras = item.get('extras', [])
            if extras:
                printer.set(align='center', bold=False, width=1, height=1)
                for extra in extras:
                    extra_name = extra.get('extra_name') or extra.get('name', 'Extra')
                    if 'extra' in extra and isinstance(extra['extra'], dict):
                        extra_name = extra['extra'].get('name', extra_name)
                    
                    extra_qty = extra.get('quantity', 1)
                    printer.text(f"  + {extra_qty}x {extra_name}\n")

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
    """Print counter bill with single line format and fixed pricing"""
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

        # Items - Single line format
        printer.set(bold=True)
        printer.text("ITEMS:\n")
        printer.set(bold=False)

        total_calculated = 0

        for item in order_data.get("items", []):
            qty = item.get('quantity', 1)
            name = get_item_name(item)

            # Calculate item total (base + extras)
            item_total = get_item_total(item)
            total_calculated += item_total

            # Single line format with proper alignment
            item_line = f"{qty}x {name}"
            price_str = f"Rs{item_total:.2f}"
            
            if len(item_line + price_str) <= 32:
                spaces = 32 - len(item_line + price_str)
                printer.text(f"{item_line}{' ' * spaces}{price_str}\n")
            else:
                printer.text(f"{item_line}\n")
                printer.text(f"{' ' * (32 - len(price_str))}{price_str}\n")

            # Show extras details
            extras = item.get('extras', [])
            if extras:
                for extra in extras:
                    extra_name = extra.get('extra_name') or extra.get('name', 'Extra')
                    if 'extra' in extra and isinstance(extra['extra'], dict):
                        extra_name = extra['extra'].get('name', extra_name)
                    
                    extra_qty = extra.get('quantity', 1)
                    printer.text(f"  + {extra_qty}x {extra_name}\n")

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