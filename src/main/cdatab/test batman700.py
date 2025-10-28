import sqlite3

DB_NAME = "src/database/thisshop.db"

# ข้อมูลที่จะเพิ่ม
new_product = (
    'B003PMU5K0',
    'Batman Vol.1',
    '#700',
    'Grant Morrison',
    'Default',
    "Grant Morrison returns to BATMAN with this oversized special! And he's brought an all-star roster of artists along with him including Andy Kubert, Tony Daniel and Frank Quitely to celebrate this milestone 700th issue featuring stories spotlighting each of the Batmen from different eras – Bruce Wayne, Dick Grayson and Damian Wayne. You won't want to miss this blockbuster story that paves the way for the return of Bruce Wayne and sports mind-boggling covers by superstars David Finch (BRIGHTEST DAY) and Mike Mignola (BATMAN: GOTHAM BY GASLIGHT, Hellboy)!",
    587.73,
    1,
    r'src\img\cover\batman700.png' # ใช้ r'' (raw string) สำหรับ path
)

# คำสั่ง SQL ที่ใช้ placeholders
sql_command = """
INSERT INTO product (
    id, name, volume_issue, writer, rated, 
    description, price, stock, cover_img
) 
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
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