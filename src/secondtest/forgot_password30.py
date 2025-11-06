import sys
import os
import sqlite3
import re
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

# --- Database Setup ---
DB_PATH = "src/database/thisshop.db"

def validate_password(username, email, password):
    """Validates the password against complex rules."""
    WEAK_PASSWORDS = ["12345678", "password", "qwerty"]
    
    if password in WEAK_PASSWORDS:
        return "รหัสผ่านง่ายต่อการคาดเดาเกินไป"
    
    if len(password) < 8:
        return False, "รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร"
    if not re.search(r"[a-z]", password):
        return False, "รหัสผ่านต้องมีตัวพิมพ์เล็ก (a-z) อย่างน้อย 1 ตัว"
    if not re.search(r"[A-Z]", password):
        return False, "รหัสผ่านต้องมีตัวพิมพ์ใหญ่ (A-Z) อย่างน้อย 1 ตัว"
    if not re.search(r"[0-9]", password):
        return False, "รหัสผ่านต้องมีตัวเลข (0-9) อย่างน้อย 1 ตัว"
    if not re.search(r"[!@#$%^&*]", password):
        return False, "รหัสผ่านต้องมีอักขระพิเศษ (!@#$%^&*) อย่างน้อย 1 ตัว"
    
    if username.lower() in password.lower():
        return False, "รหัสผ่านห้ามมีชื่อผู้ใช้ (Username) เป็นส่วนประกอบ"
    email_local_part = email.split('@')[0].lower()
    if email_local_part in password.lower():
        return False, "รหัสผ่านห้ามมีอีเมล (Email) เป็นส่วนประกอบ"

    return True, "Success"

# --- Main Application Class ---
class ForgotPasswordPage(QMainWindow):
    def __init__(self):
        super().__init__()
        self.showMaximized()

        try:
            self.conn = sqlite3.connect(DB_PATH)
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Could not connect to database: {e}")
            sys.exit(1)

        self.load_stylesheet("src/styles/forgot_password.qss")

        # === ตั้งค่าภาพพื้นหลัง ===
        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(True)
        self.setCentralWidget(self.bg_label)
        
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
        
        # === Title ===
        self.title_label = QLabel("Reset Password", self.bg_label)
        self.title_label.setObjectName("titleLabel")
        self.title_label.setGeometry(550, 180, 400, 50)
        
        # === Description ===
        self.desc_label = QLabel("Enter your username and email to verify your account", self.bg_label)
        self.desc_label.setObjectName("descLabel")
        self.desc_label.setGeometry(550, 240, 400, 30)
        
        # === --- Stage 1 Widgets (Check User) --- ===
        
        self.user_label = QLabel("Username", self.bg_label)
        self.user_label.setObjectName("userLabel")
        self.user_label.setGeometry(550, 280, 300, 40)
        
        self.username = QLineEdit(self.bg_label)
        self.username.setPlaceholderText("Enter Username")
        self.username.setGeometry(550, 320, 400, 50)

        self.email_label = QLabel("Email", self.bg_label)
        self.email_label.setObjectName("emailLabel")
        self.email_label.setGeometry(550, 380, 300, 40)
        
        self.email = QLineEdit(self.bg_label)
        self.email.setPlaceholderText("Enter Email")
        self.email.setGeometry(550, 420, 400, 50)

        self.check_btn = QPushButton("CHECK USER", self.bg_label)
        self.check_btn.setObjectName("sendBtn")
        self.check_btn.setGeometry(550, 500, 180, 50)
        self.check_btn.clicked.connect(self.check_user_clicked)

        # === --- Stage 2 Widgets (Reset Password) --- ===

        self.pass_label = QLabel("New Password", self.bg_label)
        self.pass_label.setObjectName("passLabel")
        self.pass_label.setGeometry(550, 280, 300, 40)
        self.pass_label.hide()

        self.password = QLineEdit(self.bg_label)
        self.password.setPlaceholderText("Enter new password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setGeometry(550, 320, 400, 50)
        self.password.hide()

        self.password_visible = False 
        self.toggle_password_action = QAction(self.eye_closed_icon, "Show/Hide Password", self) 
        self.toggle_password_action.triggered.connect(self.toggle_password_visibility) 
        self.password.addAction(self.toggle_password_action, QLineEdit.ActionPosition.TrailingPosition) 

        self.confirm_pass_label = QLabel("Confirm New Password", self.bg_label)
        self.confirm_pass_label.setObjectName("passLabel")
        self.confirm_pass_label.setGeometry(550, 380, 300, 40)
        self.confirm_pass_label.hide()

        self.confirm_password = QLineEdit(self.bg_label)
        self.confirm_password.setPlaceholderText("Confirm new password")
        self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password.setGeometry(550, 420, 400, 50)
        self.confirm_password.hide()

        self.confirm_visible = False 
        self.toggle_confirm_action = QAction(self.eye_closed_icon, "Show/Hide Password", self) 
        self.toggle_confirm_action.triggered.connect(self.toggle_confirm_visibility) 
        self.confirm_password.addAction(self.toggle_confirm_action, QLineEdit.ActionPosition.TrailingPosition) 

        self.reset_btn = QPushButton("RESET PASSWORD", self.bg_label)
        self.reset_btn.setObjectName("resetBtn")
        self.reset_btn.setGeometry(550, 500, 180, 50)
        self.reset_btn.clicked.connect(self.reset_clicked)
        self.reset_btn.hide()

        # === --- Common Widgets --- ===

        self.back_btn = QPushButton("BACK TO LOGIN", self.bg_label)
        self.back_btn.setObjectName("backBtn")
        self.back_btn.setGeometry(770, 500, 180, 50)
        self.back_btn.clicked.connect(self.back_clicked)
    
    
    def load_stylesheet(self, filepath):
        """โหลด QSS stylesheet จากไฟล์"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print(f"Warning: Stylesheet file '{filepath}' not found")

    # --- (ฟังก์ชัน _show_stage1 และ _show_stage2 ที่เพิ่มเข้ามา) ---

    def _show_stage1(self):
        """
        รีเซ็ต UI กลับไปหน้ากรอก Username/Email (Stage 1)
        และล้างข้อมูลในช่องกรอกทั้งหมด
        """
        # อัปเดตข้อความ
        self.desc_label.setText("Enter your username and email to verify your account")
        self.desc_label.setGeometry(550, 240, 400, 30)

        # ล้างข้อมูลในช่องกรอก
        self.username.clear()
        self.email.clear()
        self.password.clear()
        self.confirm_password.clear()

        # ซ่อน Stage 2
        self.pass_label.hide()
        self.password.hide()
        self.confirm_pass_label.hide()
        self.confirm_password.hide()
        self.reset_btn.hide()

        # แสดง Stage 1
        self.user_label.show()
        self.username.show()
        self.email_label.show()
        self.email.show()
        self.check_btn.show()
        
        # ปรับตำแหน่งปุ่ม Back (ถ้าจำเป็น)
        self.back_btn.setGeometry(770, 500, 180, 50)

    def _show_stage2(self):
        """
        สลับ UI ไปหน้าตั้งรหัสผ่านใหม่ (Stage 2)
        """
        # อัปเดตข้อความ
        self.desc_label.setText("Enter and confirm your new password")
        self.desc_label.setGeometry(550, 240, 400, 30)

        # ล้างช่องรหัสผ่าน (เผื่อไว้)
        self.password.clear()
        self.confirm_password.clear()

        # ซ่อน Stage 1
        self.user_label.hide()
        self.username.hide()
        self.email_label.hide()
        self.email.hide()
        self.check_btn.hide()
        
        # แสดง Stage 2
        self.pass_label.show()
        self.password.show()
        self.confirm_pass_label.show()
        self.confirm_password.show()
        self.reset_btn.show()
        
        # ปรับตำแหน่งปุ่ม Back (ถ้าจำเป็น)
        self.back_btn.setGeometry(770, 500, 180, 50)

    # --- (ฟังก์ชันที่แก้ไข) ---

    def check_user_clicked(self):
        """ตรวจสอบ Username และ Email กับฐานข้อมูล"""
        username = self.username.text()
        email = self.email.text()
        
        if not username or not email:
            QMessageBox.warning(self, "Input Error", "Please enter both username and email.")
            return

        try:
            cursor = self.conn.cursor()
            query = "SELECT * FROM users WHERE username = ? AND email = ?"
            cursor.execute(query, (username, email))
            result = cursor.fetchone()

            if result:
                QMessageBox.information(self, "Success", "User verified. Please enter your new password.")
                # --- (เปลี่ยนไปใช้ helper) ---
                self._show_stage2() 
            else:
                QMessageBox.critical(self, "Verification Failed", "Username and Email do not match any account.")
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred while checking user: {e}")

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

    def reset_clicked(self):
        """ฟังก์ชันเมื่อกด Reset Password"""
        username = self.username.text() 
        email = self.email.text()
        new_password = self.password.text()
        confirm_password = self.confirm_password.text()
        
        if new_password != confirm_password:
            QMessageBox.warning(self, "Error", "Passwords do not match. Please try again.")
            return
            
        is_valid, message = validate_password(username, email, new_password)
        if not is_valid:
            QMessageBox.warning(self, "Password Error", message)
            return
            
        try:
            cursor = self.conn.cursor()
            query = "UPDATE users SET password = ? WHERE username = ?"
            # ส่ง new_password (plain text) เข้าไปแทน
            cursor.execute(query, (new_password, username)) 
            self.conn.commit()
            
            QMessageBox.information(self, "Success", "Your password has been reset successfully.")
            
            # --- (เปลี่ยนจาก self.back_clicked() เป็นการวนกลับไป Stage 1) ---
            self._show_stage1()
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred while updating password: {e}")

    def back_clicked(self):
        """กลับไปหน้า Login"""
        print("Switching to Login Page...")
        # ในแอปจริง ส่วนนี้อาจจะ self.close() และเปิดหน้าต่าง Login
        # หรือส่ง signal ให้ main controller สลับหน้าต่าง

    def closeEvent(self, event):
        """Close the database connection when the window is closed."""
        self.conn.close()
        print("Database connection closed.")
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ForgotPasswordPage()
    window.show()
    sys.exit(app.exec())

