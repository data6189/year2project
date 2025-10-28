import sqlite3
import re # สำหรับการตรวจสอบ Regex
# (ลบ import hashlib ออกแล้ว)
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

# === (ADDED) ส่วนสำหรับจัดการฐานข้อมูล ===
DB_NAME = "account.db"

# === (REMOVED) ฟังก์ชัน hash_password ถูกลบออกแล้ว ===

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