import sqlite3

# === (ADDED) ส่วนสำหรับจัดการฐานข้อมูล ===
DB_NAME = "src/database/thisshop.db"

def initialize_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cart (
    CartID TEXT PRIMARY KEY,
    UserID TEXT NOT NULL,
    volume_issue TEXT,
    writer TEXT,
    rated TEXT,
    description TEXT,
    price REAL DEFAULT 0.0,
    stock INTEGER DEFAULT 0,
    cover_img TEXT,
    category TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
initialize_database() 