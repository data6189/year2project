import sqlite3

DB_NAME = "src/database/thisshop.db"

# ข้อมูลที่จะเพิ่ม
new_product = (
    'A Thing Called Truth',
    r'src\img\cover\AThingCalledTruth_01_Page_01.jpg',
    'IMAGE'  # ใช้ r'' (raw string) สำหรับ path
)

# คำสั่ง SQL ที่ใช้ placeholders
sql_command = """
INSERT INTO product (
    name, cover_img, category
) 
VALUES (?, ?, ?);
"""

try:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # รันคำสั่งโดยส่งข้อมูล (new_product) เป็น argument ที่สอง
    cursor.execute(sql_command, new_product)
    
    # ยืนยันการเปลี่ยนแปลง
    conn.commit()
    
    print(f"เพิ่มข้อมูล '{new_product[1]}' (ID: {new_product[0]}) สำเร็จ!")

except sqlite3.IntegrityError:
    # กรณีนี้มักเกิดเมื่อ ID (Primary Key) ซ้ำ
    print(f"ข้อผิดพลาด: ID '{new_product[0]}' มีอยู่แล้วในฐานข้อมูล")
    conn.rollback() # ย้อนกลับ
    
except sqlite3.Error as e:
    print(f"เกิดข้อผิดพลาด SQLite: {e}")
    conn.rollback() # ย้อนกลับ

finally:
    if conn:
        conn.close()