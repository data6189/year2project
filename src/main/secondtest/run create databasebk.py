import sys
import os
import sqlite3
import re # สำหรับการตรวจสอบ Regex
# (ลบ import hashlib ออกแล้ว)
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

# === (ADDED) ส่วนสำหรับจัดการฐานข้อมูล ===
DB_NAME = "src/database/thisshop.db"

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

# === (ADDED) ฟังก์ชันตรวจสอบความถูกต้อง ===

def validate_username(username):
    """ตรวจสอบ Username ตามกฎ"""
    FORBIDDEN_NAMES = ["admin", "root", "support"]
    FORBIDDEN_WORDS = ["fuck", "shit", "admin"] # (ตัวอย่างคำหยาบ/คำต้องห้าม)

    if not (6 <= len(username) <= 20):
        return "Username ต้องมีความยาว 6-20 ตัวอักษร"
        
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return "Username ต้องเป็น a-z, A-Z, 0-9, และ _ เท่านั้น (ห้ามมีเว้นวรรค)"
        
    if username.lower() in FORBIDDEN_NAMES:
        return f"ไม่สามารถใช้ชื่อ {username} ได้"
        
    if any(word in username.lower() for word in FORBIDDEN_WORDS):
        return "Username มีคำที่ไม่เหมาะสม"
        
    return None #
    
def validate_password(password, username, email):
    """ตรวจสอบ Password ตามกฎ"""
    WEAK_PASSWORDS = ["123456", "password", "qwerty"]
    
    if len(password) < 8:
        return "รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร"
    if not re.search(r"[a-z]", password):
        return "รหัสผ่านต้องมีตัวพิมพ์เล็ก (a-z) อย่างน้อย 1 ตัว"
    if not re.search(r"[A-Z]", password):
        return "รหัสผ่านต้องมีตัวพิมพ์ใหญ่ (A-Z) อย่างน้อย 1 ตัว"
    if not re.search(r"[0-9]", password):
        return "รหัสผ่านต้องมีตัวเลข (0-9) อย่างน้อย 1 ตัว"
    if not re.search(r"[!@#$%^&*]", password): 
        return "รหัสผ่านต้องมีอักขระพิเศษ (!@#$%^&*) อย่างน้อย 1 ตัว"
        
    if username and username.lower() in password.lower():
        return "รหัสผ่านห้ามมีชื่อผู้ใช้ (Username) เป็นส่วนประกอบ"
        
    if email and email.lower().split('@')[0] in password.lower():
        return "รหัสผ่านห้ามมีอีเมล (Email) เป็นส่วนประกอบ"
        
    if password in WEAK_PASSWORDS:
        return "รหัสผ่านง่ายต่อการคาดเดาเกินไป"
        
    return None


# === คลาสหน้า Sign Up (ฉบับสมบูรณ์) ===

class SignupPage(QMainWindow):
    def __init__(self):
        super().__init__()
        self.showMaximized()
        
        self.profile_image_path = None 

        # โหลด stylesheet
        self.load_stylesheet("src/styles/signup.qss")
        
        # === ตั้งค่าไอคอนสำหรับแสดง/ซ่อนรหัสผ่าน ===
        self.eye_open_icon_path = "src/img/icon/angryeye.png"
        self.eye_closed_icon_path = "src/img/icon/noneye.png"

        try:
            self.eye_open_icon = QIcon(self.eye_open_icon_path)
            self.eye_closed_icon = QIcon(self.eye_closed_icon_path)
        except Exception as e:
            print(f"Error loading icons: {e}")
            self.eye_open_icon = QIcon()
            self.eye_closed_icon = QIcon()

        # === ตั้งค่าภาพพื้นหลัง ===
        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(True)
        self.setCentralWidget(self.bg_label)
        
        # === Title ===
        self.title_label = QLabel("Create Account", self.bg_label)
        self.title_label.setObjectName("titleLabel")
        self.title_label.setGeometry(550, 150, 400, 50)
        
        # === Label Username ===
        self.user_label = QLabel("Username", self.bg_label)
        self.user_label.setObjectName("userLabel")
        self.user_label.setGeometry(550, 200, 300, 40)
        
        # === Username Input ===
        self.username = QLineEdit(self.bg_label)
        self.username.setPlaceholderText("Enter Username")
        self.username.setGeometry(550, 250, 400, 50)

        # === Label Email ===
        self.email_label = QLabel("Email", self.bg_label)
        self.email_label.setObjectName("emailLabel")
        self.email_label.setGeometry(550, 320, 300, 40)
        
        # === Email Input ===
        self.email = QLineEdit(self.bg_label)
        self.email.setPlaceholderText("Enter Email")
        self.email.setGeometry(550, 370, 400, 50)

        # === Label Password ===
        self.pass_label = QLabel("Password", self.bg_label)
        self.pass_label.setObjectName("passLabel")
        self.pass_label.setGeometry(550, 440, 300, 40)

        # === Password Input ===
        self.password = QLineEdit(self.bg_label)
        self.password.setPlaceholderText("Enter Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setGeometry(550, 490, 400, 50)
        
        self.password_visible = False 
        self.toggle_password_action = QAction(self.eye_closed_icon, "Show/Hide Password", self) 
        self.toggle_password_action.triggered.connect(self.toggle_password_visibility) 
        self.password.addAction(self.toggle_password_action, QLineEdit.ActionPosition.TrailingPosition) 

        # === Label Confirm Password ===
        self.confirm_label = QLabel("Confirm Password", self.bg_label)
        self.confirm_label.setObjectName("confirmLabel")
        self.confirm_label.setGeometry(550, 560, 300, 40)

        # === Confirm Password Input ===
        self.confirm_password = QLineEdit(self.bg_label)
        self.confirm_password.setPlaceholderText("Confirm Password")
        self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password.setGeometry(550, 610, 400, 50)
        
        self.confirm_visible = False 
        self.toggle_confirm_action = QAction(self.eye_closed_icon, "Show/Hide Password", self) 
        self.toggle_confirm_action.triggered.connect(self.toggle_confirm_visibility) 
        self.confirm_password.addAction(self.toggle_confirm_action, QLineEdit.ActionPosition.TrailingPosition) 

        # === (ADDED) ส่วนอัปโหลดรูปโปรไฟล์ ===
        self.upload_label = QLabel("Profile Picture (Optional)", self.bg_label)
        self.upload_label.setObjectName("uploadLabel") 
        self.upload_label.setGeometry(550, 670, 150, 30)

        self.upload_btn = QPushButton("Upload Image", self.bg_label)
        self.upload_btn.setObjectName("uploadBtn")
        self.upload_btn.setGeometry(710, 670, 120, 30)
        self.upload_btn.clicked.connect(self.upload_profile_image) 

        self.profile_path_label = QLabel("No file selected", self.bg_label)
        self.profile_path_label.setObjectName("pathLabel")
        self.profile_path_label.setGeometry(840, 670, 110, 30)
        
        # === (MODIFIED) ขยับปุ่ม Sign Up และ Back ลงมา ===
        self.signup_btn = QPushButton("SIGN UP", self.bg_label)
        self.signup_btn.setObjectName("signupBtn")
        self.signup_btn.setGeometry(550, 720, 180, 50) 
        self.signup_btn.clicked.connect(self.signup_clicked)

        self.back_btn = QPushButton("BACK TO LOGIN", self.bg_label)
        self.back_btn.setObjectName("backBtn")
        self.back_btn.setGeometry(770, 720, 180, 50) 
        self.back_btn.clicked.connect(self.back_clicked)
    
    def load_stylesheet(self, filepath):
        """โหลด QSS stylesheet จากไฟล์"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print(f"Warning: Stylesheet file '{filepath}' not found")
    
    def toggle_password_visibility(self):
        """สลับการแสดงผลรหัสผ่าน"""
        if not self.password_visible:
            self.password.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_password_action.setIcon(self.eye_open_icon)
            self.password_visible = True
        else:
            self.password.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_password_action.setIcon(self.eye_closed_icon)
            self.password_visible = False
            
    def toggle_confirm_visibility(self):
        """สลับการแสดงผลรหัสผ่าน (ช่องยืนยัน)"""
        if not self.confirm_visible:
            self.confirm_password.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_confirm_action.setIcon(self.eye_open_icon)
            self.confirm_visible = True
        else:
            self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_confirm_action.setIcon(self.eye_closed_icon)
            self.confirm_visible = False

    def show_error_message(self, message):
        """แสดงหน้าต่าง Popup ข้อผิดพลาด"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Sign Up Failed")
        msg.setText(message)
        msg.exec()

    def upload_profile_image(self):
        """
        เปิด QFileDialog เพื่อเลือกไฟล์รูปภาพ
        และเก็บ Path ไว้ใน self.profile_image_path
        """
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Select Profile Image",
            "", 
            "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if filepath: 
            self.profile_image_path = filepath
            filename = os.path.basename(filepath)
            self.profile_path_label.setText(filename)
            print(f"Selected profile image: {filepath}")
        else:
            self.profile_image_path = None
            self.profile_path_label.setText("No file selected")

    def signup_clicked(self):
        """ฟังก์ชันเมื่อกด Sign Up (เชื่อมต่อ Database และตรวจสอบ)"""
        username = self.username.text().strip()
        email = self.email.text().strip()
        password = self.password.text() # <--- รับรหัสผ่าน (Plain Text)
        confirm = self.confirm_password.text()
        
        # 1. ตรวจสอบข้อมูลเบื้องต้น
        if not username or not email or not password:
            self.show_error_message("กรุณากรอกข้อมูล Username, Email และ Password ให้ครบถ้วน")
            return
            
        if password != confirm:
            self.show_error_message("รหัสผ่าน และ ยืนยันรหัสผ่าน ไม่ตรงกัน")
            return
            
        # 2. ตรวจสอบ Username ตามกฎ
        username_error = validate_username(username)
        if username_error:
            self.show_error_message(username_error)
            return

        # 3. ตรวจสอบ Password ตามกฎ
        password_error = validate_password(password, username, email)
        if password_error:
            self.show_error_message(password_error)
            return
            
        # 4. เชื่อมต่อและตรวจสอบข้อมูลซ้ำใน Database
        conn = None
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            
            # ตรวจสอบ Username ซ้ำ
            cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                self.show_error_message("Username นี้มีผู้ใช้งานแล้ว")
                return
                
            # ตรวจสอบ Email ซ้ำ
            cursor.execute("SELECT user_id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                self.show_error_message("Email นี้มีผู้ใช้งานแล้ว")
                return
                
            # 5. (MODIFIED) ถ้าทุกอย่างผ่าน = ลงทะเบียน
            # hashed_pass = hash_password(password) # <--- (REMOVED)
            role = "user" 
            
            # (MODIFIED: ใส่ 'password' (Plain Text) ลงไปตรงๆ)
            cursor.execute("""
            INSERT INTO users (username, email, password, role, profile_img) 
            VALUES (?, ?, ?, ?, ?)
            """, (username, email, password, role, self.profile_image_path))
            
            conn.commit()
            
            QMessageBox.information(self, "Success", f"บัญชี {username} ถูกสร้างเรียบร้อยแล้ว!")
            
            # (MODIFIED) ล้างค่าในช่องกรอก (รวมถึง path)
            self.username.clear()
            self.email.clear()
            self.password.clear()
            self.confirm_password.clear()
            self.profile_image_path = None 
            self.profile_path_label.setText("No file selected")
            
        except sqlite3.Error as e:
            self.show_error_message(f"เกิดข้อผิดพลาดกับฐานข้อมูล: {e}")
        finally:
            if conn:
                conn.close()


    def back_clicked(self):
        """กลับไปหน้า Login"""
        print("Switching to Login Page...")
        # from login import LoginPage
        # self.close()
        # self.login_window = LoginPage()
        # self.login_window.show()


if __name__ == "__main__":
    # (ADDED) เรียกใช้ฟังก์ชันสร้าง DB ก่อนเริ่มแอป
    initialize_database() 
    
    app = QApplication(sys.argv)
    window = SignupPage()
    window.show()
    sys.exit(app.exec())