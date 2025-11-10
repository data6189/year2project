from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
import os

# --- ใส่ Path ที่ถูกต้องตรงนี้ ---
IMAGE_PATH = "src/img/icon/logo.png"  # <-- แก้ตรงนี้ให้ถูก

c = canvas.Canvas("debug_single_image.pdf", pagesize=A4)
w, h = A4

if os.path.exists(IMAGE_PATH):
    print(f"Found image at: {os.path.abspath(IMAGE_PATH)}")
    try:
        # วาดสี่เหลี่ยมสีแดงไว้ก่อน เพื่อดูตำแหน่ง
        c.setStrokeColorRGB(1, 0, 0)
        c.rect(50*mm, h - 100*mm, 50*mm, 50*mm, stroke=1, fill=0)
        
        # วาดรูปทับลงไปในกรอบ
        # สังเกตตำแหน่ง y: h - 100*mm คือวัดจากด้านล่างขึ้นมา
        c.drawImage(IMAGE_PATH, 50*mm, h - 100*mm, width=50*mm, height=50*mm, mask='auto')
        print("Draw command executed.")
    except Exception as e:
        print(f"Error drawing image: {e}")
else:
    print("Error: Image path not found!")

c.save()
print("PDF saved.")