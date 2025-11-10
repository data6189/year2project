import sqlite3
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- ตั้งค่าพื้นฐาน ---
# (สมมติว่าไฟล์ DB, Font, Logo อยู่ในตำแหน่งที่ถูกต้อง)
DB_PATH = "src/database/thisshop.db"
FONT_PATH = "src/font/THSarabunNew.ttf"
LOGO_PATH = "src/img/icon/logo.png"
PDF_OUTPUT_DIR = "receipts"

# ลงทะเบียนฟอนต์ภาษาไทย
try:
    pdfmetrics.registerFont(TTFont('ThaiFont', FONT_PATH))
    MAIN_FONT = 'ThaiFont'
except Exception as e:
    print(f"คำเตือน: ไม่พบฟอนต์ {FONT_PATH} กำลังใช้ฟอนต์มาตรฐาน")
    MAIN_FONT = 'Helvetica'

if not os.path.exists(PDF_OUTPUT_DIR):
    os.makedirs(PDF_OUTPUT_DIR)

def get_order_data(order_id_param):
    """ดึงข้อมูลออเดอร์จากฐานข้อมูล"""
    if not os.path.exists(DB_PATH):
        print(f"ข้อผิดพลาด: ไม่พบไฟล์ฐานข้อมูลที่ {DB_PATH}")
        # สร้างข้อมูลจำลองเพื่อการทดสอบ
        print("กำลังใช้ข้อมูลจำลอง...")
        return {
            "info": {
                'order_id': order_id_param, 'user_id': 'TestUser001', 
                'order_date': '2025-11-10', 'subtotal': 1500.00, 
                'vat': 105.00, 'shipping_fee': 50.00, 'total': 1655.00
            },
            "items": [
                {'product_id': 'P001', 'name': 'สินค้า A (ชื่อยาวๆ เพื่อทดสอบการตัดคำ)', 'unit_price': 500.00, 'quantity': 2},
                {'product_id': 'P002', 'name': 'สินค้า B', 'unit_price': 250.00, 'quantity': 2}
            ]
        }
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # 1. ดึงข้อมูลส่วนหัวและยอดเงิน
        cursor.execute("""
            SELECT order_id, user_id, order_date, subtotal, vat, shipping_fee, total 
            FROM orders 
            WHERE order_id = ?
        """, (order_id_param,))
        order_info = cursor.fetchone()

        if not order_info:
            print(f"ไม่พบข้อมูลออเดอร์ ID: {order_id_param}")
            conn.close()
            return None

        # 2. ดึงรายการสินค้า
        cursor.execute("""
            SELECT oi.product_id, p.name, oi.unit_price, oi.quantity
            FROM order_items oi
            LEFT JOIN product p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        """, (order_id_param,))
        items = cursor.fetchall()

    except sqlite3.Error as e:
        print(f"Database Error: {e}")
        conn.close()
        return None

    conn.close()

    return {
        "info": dict(order_info),
        "items": [dict(item) for item in items]
    }

def create_receipt_pdf(order_id):
    """สร้างไฟล์ PDF ใบเสร็จ"""
    data = get_order_data(order_id)
    if not data:
        return

    order_info = data['info']
    items = data['items']
    
    pdf_filename = os.path.join(PDF_OUTPUT_DIR, f"Receipt_{order_id}.pdf")
    c = canvas.Canvas(pdf_filename, pagesize=A4)
    width, height = A4

    # =========================================
    # 1. ส่วนหัว (Header)
    # =========================================
    LOGO_X = 15 * mm
    LOGO_Y = height - 60 * mm
    LOGO_W = 50 * mm
    LOGO_H = 40 * mm

    if os.path.exists(LOGO_PATH):
        try:
            c.drawImage(LOGO_PATH, LOGO_X, LOGO_Y, width=LOGO_W, height=LOGO_H, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"ERROR: ไม่สามารถวาดโลโก้ได้ {e}")

    c.setFont(MAIN_FONT, 14)
    text_y = height - 55 * mm
    for line in ["ที่อยู่ร้านค้า :", "หอพักนักศึกษาชายที่ 10 มหาวิทยาลัยขอนแก่น", "ตำบล ศิลา อำเภอเมืองขอนแก่น จังหวัด ขอนแก่น 40000"]:
        c.drawString(20 * mm, text_y, line)
        text_y -= 6 * mm

    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2.0, height - 20 * mm, f"ORDER ID # {order_info['order_id']}")

    c.setFont("Helvetica", 7)
    c.drawString(135 * mm, height - 55 * mm, "CUSTOMER :")
    c.drawString(135 * mm, height - 65 * mm, "ORDER DATE :")

    c.setFont(MAIN_FONT, 14)
    c.drawString(155 * mm, height - 55 * mm, str(order_info['user_id']))
    c.drawString(155 * mm, height - 65 * mm, str(order_info['order_date']))

    # =========================================
    # 2. ตารางสินค้า (แก้ไขส่วนนี้)
    # =========================================
    table_data = [['ID', 'ITEM', 'UNIT PRICE', 'QUANTITY', 'AMOUNT']]
    for idx, item in enumerate(items, 1):
        unit_price = item['unit_price'] if item['unit_price'] is not None else 0
        quantity = item['quantity'] if item['quantity'] is not None else 0
        amount = unit_price * quantity
        table_data.append([
            str(idx),
            item['name'] if item['name'] else "Unknown Item",
            f"{unit_price:,.2f} THB",
            str(quantity),
            f"{amount:,.2f} THB"
        ])

    # *** FIX 1: ปรับ colWidths ***
    # ลดคอลัมน์ ITEM จาก 80 เป็น 60 (15+60+35+25+35 = 170mm)
    # ทำให้ตารางกว้าง 170mm + ขอบซ้าย 20mm = 190mm (เหลือขอบขวา 20mm)
    table = Table(table_data, colWidths=[10*mm, 70*mm, 35*mm, 20*mm, 35*mm])
    
    table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), MAIN_FONT, 12),
        ('ALIGN', (1, 1), (-1, 0), 'LEFT'),                 # หัวตาราง: ชิดซ้าย
        ('ALIGN', (5, 1), (-1, -1), 'RIGHT'),                # เนื้อหา (คอลัมน์ 2-4): ชิดขวา
        # (คอลัมน์ 0 (ID) และ 1 (ITEM) จะชิดซ้ายตามค่าเริ่มต้น)

        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
        # *** FIX 3: เพิ่ม WORDWRAP เพื่อให้คอลัมน์ ITEM (index 1) ตัดคำ ***
        ('WORDWRAP', (1, 1), (1, -1), True),
    ]))
    
    # *** FIX 2: คำนวณความสูงและตำแหน่งตารางแบบไดนามิก ***
    
    # คำนวณความกว้างที่มีให้สำหรับตาราง (A4 width - 20mm left margin - 20mm right margin)
    available_width = width - 40 * mm
    
    # คำนวณความสูงจริงของตาราง (table_height)
    table_width, table_height = table.wrap(available_width, height) 

    # กำหนดตำแหน่ง Y ด้านบนของตาราง (ห่างจากขอบบน 80mm)
    table_top_y = height - 80 * mm
    
    # คำนวณตำแหน่ง Y (มุมล่างซ้าย) ที่จะใช้วาด
    table_y = table_top_y - table_height
    
    # วาดตารางที่ตำแหน่ง X=20mm และ Y=table_y
    table.drawOn(c, 20 * mm, table_y)

    # =========================================
    # 3. สรุปยอดเงิน (Footer) (แก้ไขส่วนนี้)
    # =========================================
    
    # *** FIX 4: อ้างอิงตำแหน่ง Footer จาก table_y ที่คำนวณใหม่ ***
    # ให้ Footer อยู่ต่ำกว่าตาราง 20mm
    y_footer = table_y - 20 * mm
    
    c.setLineWidth(0.5)
    c.line(20*mm, y_footer + 5*mm, width-20*mm, y_footer + 5*mm)
    c.line(20*mm, y_footer + 7*mm, width-20*mm, y_footer + 7*mm)

    c.setFont(MAIN_FONT, 14)
    right_x = width - 25 * mm
    
    c.drawRightString(right_x - 40*mm, y_footer - 5*mm, "Subtotal :")
    c.drawRightString(right_x, y_footer - 5*mm, f"{order_info['subtotal']:,.2f} THB")
    
    c.drawRightString(right_x - 40*mm, y_footer - 12*mm, "Shipping :")
    c.drawRightString(right_x, y_footer - 12*mm, f"{order_info['shipping_fee']:,.2f} THB")
    
    c.drawRightString(right_x - 40*mm, y_footer - 19*mm, "VAT 7% :")
    c.drawRightString(right_x, y_footer - 19*mm, f"{order_info['vat']:,.2f} THB")

    c.line(width - 80*mm, y_footer - 24*mm, width - 20*mm, y_footer - 24*mm)
    c.setFont("Helvetica", 16)
    c.drawRightString(right_x - 40*mm, y_footer - 32*mm, "Total :")
    c.drawRightString(right_x, y_footer - 32*mm, f"{order_info['total']:,.2f} THB")

    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2.0, 30 * mm, "THANKS YOU HEROES!")

    c.save()
    print(f"สร้างใบเสร็จสำเร็จ: {pdf_filename}")
    if os.name == 'nt':
        try:
            os.startfile(pdf_filename)
        except:
            pass

if __name__ == "__main__":
    # เพิ่มข้อมูลจำลองใน get_order_data หากหา DB ไม่พบ
    # เพื่อให้สามารถรันทดสอบได้เลย
    create_receipt_pdf(8)