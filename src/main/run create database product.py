import sqlite3

# === (ADDED) ส่วนสำหรับจัดการฐานข้อมูล ===
DB_NAME = "account.db"

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
        Price,
        profile_img TEXT
    )
    """)