from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
import io
import csv
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from app.database import get_db

router = APIRouter(prefix="/api/exports", tags=["Reports & Data Exports"])

@router.get("/orders/excel")
def export_orders_excel():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT o.order_number, o.order_date, o.customer_name, o.customer_phone,
               o.shipping_locality, o.shipping_pincode, o.subtotal, o.discount,
               o.gst, o.delivery_fee, o.total_amount, o.payment_method,
               o.payment_status, o.order_status, d.name as driver_name
        FROM orders o
        LEFT JOIN delivery_personnel d ON o.assigned_delivery_person_id = d.id
        ORDER BY o.id DESC
        """)
        orders = cursor.fetchall()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Orders Summary"

    # Brand Title
    ws.merge_cells("A1:O1")
    title_cell = ws["A1"]
    title_cell.value = "DJ MICROGREENS CHENNAI - OFFICIAL ORDERS EXPORT"
    title_cell.font = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
    title_cell.fill = PatternFill(start_color="166534", end_color="166534", fill_type="solid")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 32

    # Headers
    headers = [
        "Order ID", "Order Date", "Customer Name", "Phone",
        "Locality", "Pincode", "Subtotal (₹)", "Discount (₹)",
        "GST 5% (₹)", "Delivery (₹)", "Total (₹)", "Payment Mode",
        "Payment Status", "Order Status", "Delivery Partner"
    ]
    ws.append(headers)
    ws.row_dimensions[2].height = 24

    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="15803D", end_color="15803D", fill_type="solid")
    thin_border = Border(
        left=Side(style='thin', color='E5E7EB'),
        right=Side(style='thin', color='E5E7EB'),
        top=Side(style='thin', color='E5E7EB'),
        bottom=Side(style='thin', color='E5E7EB')
    )

    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=2, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # Rows
    for row_idx, o in enumerate(orders, start=3):
        row_vals = [
            o["order_number"], o["order_date"], o["customer_name"], o["customer_phone"],
            o["shipping_locality"] or "Chennai", o["shipping_pincode"],
            round(o["subtotal"], 2), round(o["discount"], 2), round(o["gst"], 2),
            round(o["delivery_fee"], 2), round(o["total_amount"], 2),
            o["payment_method"], o["payment_status"], o["order_status"],
            o["driver_name"] or "Assigned"
        ]
        ws.append(row_vals)
        for col_idx in range(1, len(row_vals) + 1):
            c = ws.cell(row=row_idx, column=col_idx)
            c.border = thin_border
            if col_idx in [7, 8, 9, 10, 11]:
                c.number_format = '₹#,##0.00'
                c.alignment = Alignment(horizontal="right")

    # Auto-fit column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"DJ_Microgreens_Orders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/orders/csv")
def export_orders_csv():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT o.order_number, o.order_date, o.customer_name, o.customer_phone,
               o.shipping_address, o.shipping_pincode, o.total_amount,
               o.payment_method, o.payment_status, o.order_status
        FROM orders o
        ORDER BY o.id DESC
        """)
        orders = cursor.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Order ID", "Date", "Customer Name", "Phone",
        "Delivery Address", "Pincode", "Total Amount (INR)",
        "Payment Method", "Payment Status", "Order Status"
    ])
    for o in orders:
        writer.writerow([
            o["order_number"], o["order_date"], o["customer_name"], o["customer_phone"],
            o["shipping_address"], o["shipping_pincode"], o["total_amount"],
            o["payment_method"], o["payment_status"], o["order_status"]
        ])

    output.seek(0)
    filename = f"DJ_Microgreens_Orders_{datetime.now().strftime('%Y%m%d')}.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
