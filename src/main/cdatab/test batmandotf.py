import sqlite3

DB_NAME = "src/database/thisshop.db"

# ข้อมูลที่จะเพิ่ม
new_product = (
    '9781401246020',
    'BATMAN : DEATH OF THE FAMILY ',
    'VOL.3',
    'James T Tynion IV, Scott Snyder',
    'Teen',
    "After having his face sliced off, The Joker makes his horrifying return to Gotham City in this epic from issues #13-17 that shook Batman to his core! But even for a man who's committed a lifetime of murder, he's more dangerous than ever before. How can Batman protect his city and those he's closest to?",
    613.00,
    10,
    r'src\img\cover\batdotf.png',
    'DC'  # ใช้ r'' (raw string) สำหรับ path
)

# คำสั่ง SQL ที่ใช้ placeholders
sql_command = """
INSERT INTO product (
    id, name, volume_issue, writer, rated, 
    description, price, stock, cover_img, category
) 
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
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