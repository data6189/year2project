import sqlite3

# === (ADDED) ส่วนสำหรับจัดการฐานข้อมูล ===
DB_NAME = "src/database/thisshop.db"

def initialize_database():
    """สร้างไฟล์ database และตาราง users หากยังไม่มี"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # สร้างตาราง users (MODIFIED: profile_img เป็น TEXT)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT_NULL UNIQUE,
        password TEXT NOT NULL,
        first_name TEXT,
        last_name TEXT,
        gender TEXT,
        email TEXT NOT NULL UNIQUE,
        phone TEXT,
        address TEXT,
        role TEXT NOT NULL,
        profile_img TEXT
    )
    """)
    
    # สร้าง user 'admin' เริ่มต้น (หากยังไม่มี)
    try:
        # (MODIFIED: ใส่ "data" ลงไปตรงๆ)
        cursor.execute("""
        INSERT OR IGNORE INTO users (username, password, role, email, profile_img) 
        VALUES (?, ?, ?, ?, ?)
        """, ("data6189", "data", "admin", "admin@example.com", None))
        
        conn.commit()
        print("Database initialized successfully (Passwords stored as plain text).")
    except sqlite3.Error as e:
        print(f"Error initializing database: {e}")
    finally:
        conn.close()

initialize_database() 