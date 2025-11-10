import sqlite3

# === (ADDED) ส่วนสำหรับจัดการฐานข้อมูล ===
DB_NAME = "src/database/thisshop.db"

def initialize_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    feedback_text TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    conn.commit()
    conn.close()
    print(f"Database '{DB_NAME}' initialized successfully.")
    
initialize_database() 

#IF NOT EXISTS: ป้องกัน error ถ้ารันซ้ำ (มันจะไม่สร้างทับของเดิมถ้ามีอยู่แล้ว)
#ON DELETE CASCADE: (ใส่เพิ่มให้ในบางจุด) เช่น ถ้าลบ user ทิ้ง ข้อมูลในตะกร้าของ user นั้นจะหายไปด้วยอัตโนมัติ เพื่อไม่ให้มีข้อมูลขยะตกค้างครับ
#REAL: ใช้เก็บตัวเลขที่มีทศนิยม (เหมาะกับราคาและ VAT)