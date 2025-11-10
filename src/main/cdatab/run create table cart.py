import sqlite3

# === (ADDED) ส่วนสำหรับจัดการฐานข้อมูล ===
DB_NAME = "src/database/thisshop.db"

def initialize_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # --- 3. ตาราง Cart ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cart (
        cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER DEFAULT 1 CHECK (quantity > 0),
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES product(product_id) ON DELETE CASCADE,
        UNIQUE(user_id, product_id) -- ป้องกันสินค้าซ้ำในตะกร้าของคนเดิม
    )
    """)

    # --- 4. ตาราง Orders ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        order_date TEXT DEFAULT (datetime('now', 'localtime')),
        subtotal REAL DEFAULT 0,
        vat REAL DEFAULT 0,
        shipping_fee REAL DEFAULT 80,
        total REAL DEFAULT 0,
        status TEXT DEFAULT 'waiting_payment', -- waiting_payment, verifying, paid, cancelled, shipped
        slip_image TEXT,
        payment_date TEXT,
        cancelled_date TEXT, -- เพิ่มเก็บวันที่ยกเลิก
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    """)

    # --- 5. ตาราง Order Items ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES product(product_id)
    )
    """)

    conn.commit()
    conn.close()
    print(f"Database '{DB_NAME}' initialized successfully.")
    
initialize_database() 

#IF NOT EXISTS: ป้องกัน error ถ้ารันซ้ำ (มันจะไม่สร้างทับของเดิมถ้ามีอยู่แล้ว)
#ON DELETE CASCADE: (ใส่เพิ่มให้ในบางจุด) เช่น ถ้าลบ user ทิ้ง ข้อมูลในตะกร้าของ user นั้นจะหายไปด้วยอัตโนมัติ เพื่อไม่ให้มีข้อมูลขยะตกค้างครับ
#REAL: ใช้เก็บตัวเลขที่มีทศนิยม (เหมาะกับราคาและ VAT)