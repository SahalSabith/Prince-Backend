# utils.py

from escpos.printer import Network
import logging

logger = logging.getLogger(__name__)


def get_item_name(item):
    item_data = item.get("item") or item.get("product")
    if isinstance(item_data, dict):
        return item_data.get("name", "Unknown Item")
    elif hasattr(item_data, "name"):
        return item_data.name
    return item.get("name", "Unknown Item")


def get_item_price(item, qty=1):
    item_data = item.get("item") or item.get("product")
    try:
        if 'total_amount' in item:
            return float(item['total_amount'])
        elif isinstance(item_data, dict) and "price" in item_data:
            return float(item_data["price"]) * qty
        elif hasattr(item_data, "price"):
            return float(item_data.price) * qty
        elif "price" in item:
            return float(item["price"]) * qty
    except Exception:
        return 0.0
    return 0.0


def print_kitchen_bill(order_data, printer_ip):
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

        ordered_at = order_data.get('ordered_at', '')
        if ordered_at:
            time_part = ordered_at[11:16] if len(ordered_at) > 16 else ordered_at
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

        ordered_at = order_data.get('ordered_at', '')
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
    if print_type == "kitchen":
        return print_kitchen_bill(order_data, printer_ip)
    return print_counter_bill(order_data, printer_ip)
