# utils.py

from escpos.printer import Network
import logging
import qrcode
from io import BytesIO

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


def generate_upi_qr_for_printer(upi_id, name, amount, note):
    """Generate UPI QR code and return as bytes for printer"""
    try:
        upi_url = f"upi://pay?pa={upi_id}&pn={name}&am={amount}&cu=INR&tn={note}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=4,
            border=2,
        )
        qr.add_data(upi_url)
        qr.make(fit=True)
        
        # Create QR code image
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        img_buffer = BytesIO()
        qr_img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        return img_buffer.getvalue()
    except Exception as e:
        logger.error(f"Error generating UPI QR code: {e}")
        return None


def print_kitchen_bill(order_data, printer_ip):
    """Print kitchen bill with improved error handling"""
    try:
        printer = Network(printer_ip)

        # Header
        printer.set(align='center', bold=True, width=2, height=2)
        printer.text("PRINCE BAKERY\n")
        printer.text("KITCHEN COPY\n\n")

        # Order type
        order_type = order_data.get('order_type', 'delivery').upper()
        printer.set(align='center', bold=True, width=6, height=6)
        printer.text(f"{order_type[0]}\n")

        printer.set(align='center', bold=True, width=2, height=2)
        printer.text(f"{order_type}\n")

        if order_type == 'TABLE' and order_data.get('table_number'):
            printer.text(f"TABLE: {order_data['table_number']}\n")

        printer.text("\n")

        # Token & Time
        printer.set(align='left', bold=True, width=1, height=1)
        printer.text("=" * 32 + "\n")
        printer.text(f"TOKEN: {order_data.get('id', 'N/A')}\n")

        # Fixed: Handle both 'ordered_at' and 'created_at'
        ordered_at = order_data.get('ordered_at') or order_data.get('created_at', '')
        if ordered_at:
            if len(ordered_at) > 16:
                time_part = ordered_at[11:16]
            else:
                time_part = ordered_at
            printer.text(f"TIME: {time_part}\n")
        printer.text("=" * 32 + "\n")

        # Items
        printer.set(align='left', bold=True, width=2, height=2)
        printer.text("ITEMS:\n\n")

        printer.set(align='left', bold=False, width=1, height=1)
        for item in order_data.get("items", []):
            qty = item.get("quantity", 1)
            name = get_item_name(item)

            printer.set(align='left', bold=True, width=2, height=2)
            printer.text(f"{qty} x {name.upper()}\n")

            note = item.get('note', '') or item.get('notes', '')
            if note:
                printer.set(align='left', bold=False, width=1, height=1)
                printer.text(f"   Note: {note}\n")

            printer.text("\n")

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
    """Print counter bill with improved error handling and UPI QR code"""
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

        # Fixed: Handle both 'ordered_at' and 'created_at'
        ordered_at = order_data.get('ordered_at') or order_data.get('created_at', '')
        if len(ordered_at) >= 19:
            printer.text(f"DATE: {ordered_at[:10]}\n")
            printer.text(f"TIME: {ordered_at[11:19]}\n")
        elif ordered_at:
            printer.text(f"ORDERED: {ordered_at}\n")

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

        # Generate and print UPI QR code
        try:
            token_id = order_data.get('id', 'N/A')
            table_info = f", Table {order_data['table_number']}" if order_data.get('table_number') else ""
            qr_note = f"Bill #{token_id}{table_info}"
            
            qr_data = generate_upi_qr_for_printer(
                upi_id="sahalsabith111-1@okicici",
                name="Prince Restaurant",
                amount=f"{float(total_amount):.2f}",
                note=qr_note
            )
            
            if qr_data:
                printer.set(align='center')
                printer.text("SCAN TO PAY:\n")
                printer.image(qr_data)
                printer.text("\n")
        except Exception as e:
            logger.error(f"Failed to print QR code: {e}")
            # Continue without QR code if it fails

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