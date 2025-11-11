import sys
import os
import sqlite3
import re
import random
import smtplib  # --- (1) เพิ่ม import ---
import ssl      # --- (2) เพิ่ม import ---
from email.message import EmailMessage # --- (3) เพิ่ม import ---
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

# --- (!!!) การตั้งค่าการส่งอีเมล (!!!) ---
# (!!!) IMPORTNAT: กรุณากรอกข้อมูลนี้
# (!!!) หากใช้ Gmail แนะนำให้ใช้ "App Password" (ดูวิธีทำใน Google)
# (!!!) https://support.google.com/accounts/answer/185833
SMTP_SENDER_EMAIL = "oarzer35@gmail.com"  # <--- (ต้องแก้) ใส่อีเมลผู้ส่ง
SMTP_SENDER_PASSWORD = "egij kvcl nbdh khnw"  # <--- (ต้องแก้) ใส่รหัสผ่าน App Password 16 หลัก
SMTP_SENDER_NAME = "BEYOND COMICS"
SMTP_SERVER = "smtp.gmail.com"  # (นี่คือของ Gmail)
SMTP_PORT = 587 # (สำหรับ TLS/STARTTLS)
# --- (!!!) สิ้นสุดการตั้งค่า (!!!) ---


# --- Database Setup ---
DB_PATH = "src/database/thisshop.db"

def validate_password(email, password):
    """Validates the password against complex rules."""
    WEAK_PASSWORDS = ["12345678", "password", "qwerty"]
    
    if password in WEAK_PASSWORDS:
        return False, "รหัสผ่านง่ายต่อการคาดเดาเกินไป"
    
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
    
    email_local_part = email.split('@')[0].lower()
    if email_local_part and email_local_part in password.lower():
        return False, "รหัสผ่านห้ามมีอีเมล (Email) เป็นส่วนประกอบ"

    return True, "Success"

# --- Main Application Class ---
class ForgotPasswordPage(QMainWindow):
    def __init__(self):
        super().__init__()
        self.showMaximized()
        
        self.generated_otp = None
        self.verified_email = None

        try:
            self.conn = sqlite3.connect(DB_PATH)
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Could not connect to database: {e}")
            sys.exit(1)

        self.load_stylesheet("src/styles/forgot_password.qss")

        # (... ส่วน UI ที่เหลือเหมือนเดิม ...)
        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(True)
        self.setCentralWidget(self.bg_label)
        self.eye_open_icon_path = "src/img/icon/angryeye.png"
        self.eye_closed_icon_path = "src/img/icon/noneye.png"
        try:
            self.eye_open_icon = QIcon(self.eye_open_icon_path)
            self.eye_closed_icon = QIcon(self.eye_closed_icon_path)
        except Exception as e:
            print(f"Error loading icons: {e}")
            self.eye_open_icon = QIcon()
            self.eye_closed_icon = QIcon()
        self.title_label = QLabel("Reset Password", self.bg_label)
        self.title_label.setObjectName("titleLabel")
        self.title_label.setGeometry(550, 180, 400, 50)
        self.desc_label = QLabel("Enter your email to receive an OTP code", self.bg_label)
        self.desc_label.setObjectName("descLabel")
        self.desc_label.setGeometry(550, 240, 400, 30)
        self.email_label = QLabel("Email", self.bg_label)
        self.email_label.setObjectName("emailLabel")
        self.email_label.setGeometry(550, 280, 300, 40) 
        self.email = QLineEdit(self.bg_label)
        self.email.setPlaceholderText("Enter Email")
        self.email.setGeometry(550, 320, 400, 50)
        self.send_code_btn = QPushButton("SEND CODE", self.bg_label)
        self.send_code_btn.setObjectName("sendBtn")
        self.send_code_btn.setGeometry(550, 400, 180, 50)
        self.send_code_btn.clicked.connect(self.send_code_clicked)
        self.otp_label = QLabel("OTP Code", self.bg_label)
        self.otp_label.setObjectName("passLabel")
        self.otp_label.setGeometry(550, 280, 300, 40)
        self.otp_input = QLineEdit(self.bg_label)
        self.otp_input.setPlaceholderText("Enter 6-digit OTP")
        self.otp_input.setGeometry(550, 320, 400, 50)
        self.check_otp_btn = QPushButton("VERIFY OTP", self.bg_label)
        self.check_otp_btn.setObjectName("sendBtn")
        self.check_otp_btn.setGeometry(550, 400, 180, 50)
        self.check_otp_btn.clicked.connect(self.check_otp_clicked)
        self.pass_label = QLabel("New Password", self.bg_label)
        self.pass_label.setObjectName("passLabel")
        self.pass_label.setGeometry(550, 280, 300, 40)
        self.password = QLineEdit(self.bg_label)
        self.password.setPlaceholderText("Enter new password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setGeometry(550, 320, 400, 50)
        self.password_visible = False 
        self.toggle_password_action = QAction(self.eye_closed_icon, "Show/Hide Password", self) 
        self.toggle_password_action.triggered.connect(self.toggle_password_visibility) 
        self.password.addAction(self.toggle_password_action, QLineEdit.ActionPosition.TrailingPosition) 
        self.confirm_pass_label = QLabel("Confirm New Password", self.bg_label)
        self.confirm_pass_label.setObjectName("passLabel")
        self.confirm_pass_label.setGeometry(550, 380, 300, 40)
        self.confirm_password = QLineEdit(self.bg_label)
        self.confirm_password.setPlaceholderText("Confirm new password")
        self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password.setGeometry(550, 420, 400, 50)
        self.confirm_visible = False 
        self.toggle_confirm_action = QAction(self.eye_closed_icon, "Show/Hide Password", self) 
        self.toggle_confirm_action.triggered.connect(self.toggle_confirm_visibility) 
        self.confirm_password.addAction(self.toggle_confirm_action, QLineEdit.ActionPosition.TrailingPosition) 
        self.reset_btn = QPushButton("RESET PASSWORD", self.bg_label)
        self.reset_btn.setObjectName("resetBtn")
        self.reset_btn.setGeometry(550, 500, 180, 50)
        self.reset_btn.clicked.connect(self.reset_clicked)
        self.back_btn = QPushButton("BACK TO LOGIN", self.bg_label)
        self.back_btn.setObjectName("backBtn")
        self.back_btn.setGeometry(770, 400, 180, 50) 
        self.back_btn.clicked.connect(self.back_clicked)
        
        # --- ตั้งค่าหน้า UI เริ่มต้น ---
        self._show_stage1()
    
    
    def load_stylesheet(self, filepath):
        """Loads QSS stylesheet from file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print(f"Warning: Stylesheet file '{filepath}' not found")

    # --- UI State Management Functions (unchanged) ---
    def _show_stage1(self):
        """Resets UI to Stage 1 (Enter Email)"""
        self.desc_label.setText("Enter your email to receive an OTP code")
        self.desc_label.setGeometry(550, 240, 400, 30)
        self.email.clear()
        self.otp_input.clear()
        self.password.clear()
        self.confirm_password.clear()
        self.generated_otp = None
        self.verified_email = None
        self.email_label.show()
        self.email.show()
        self.send_code_btn.show()
        self.otp_label.hide()
        self.otp_input.hide()
        self.check_otp_btn.hide()
        self.pass_label.hide()
        self.password.hide()
        self.confirm_pass_label.hide()
        self.confirm_password.hide()
        self.reset_btn.hide()
        self.back_btn.setGeometry(770, 400, 180, 50)

    def _show_stage2(self):
        """Switches UI to Stage 2 (Enter OTP)"""
        self.desc_label.setText(f"Enter the OTP sent to {self.verified_email}")
        self.desc_label.setGeometry(550, 240, 400, 30)
        self.otp_input.clear()
        self.email_label.hide()
        self.email.hide()
        self.send_code_btn.hide()
        self.otp_label.show()
        self.otp_input.show()
        self.check_otp_btn.show()
        self.pass_label.hide()
        self.password.hide()
        self.confirm_pass_label.hide()
        self.confirm_password.hide()
        self.reset_btn.hide()
        self.back_btn.setGeometry(770, 400, 180, 50)


    def _show_stage3(self):
        """Switches UI to Stage 3 (New Password)"""
        self.desc_label.setText("Enter and confirm your new password")
        self.desc_label.setGeometry(550, 240, 400, 30)
        self.password.clear()
        self.confirm_password.clear()
        self.email_label.hide()
        self.email.hide()
        self.send_code_btn.hide()
        self.otp_label.hide()
        self.otp_input.hide()
        self.check_otp_btn.hide()
        self.pass_label.show()
        self.password.show()
        self.confirm_pass_label.show()
        self.confirm_password.show()
        self.reset_btn.show()
        self.back_btn.setGeometry(770, 500, 180, 50)

    # --- (!!!) แก้ไขฟังก์ชัน send_email_otp (!!!) ---
    def send_email_otp(self, recipient_email, otp_code):
        """
        ส่งอีเมล OTP ไปยังผู้รับ
        """
        try:
            msg = EmailMessage()
            msg['Subject'] = "Your OTP Code for Password Reset"
            
            # --- (2) แก้ไขบรรทัดนี้ ---
            # ตั้งค่าชื่อผู้ส่งและอีเมลผู้ส่ง
            msg['From'] = f"{SMTP_SENDER_NAME} <{SMTP_SENDER_EMAIL}>"
            
            msg['To'] = recipient_email
            
            # เนื้อหาอีเมล
            msg.set_content(f"""
            Hello,

            Your One-Time Password (OTP) code for resetting your password is:

            {otp_code}

            This code is valid for a short time. 
            If you did not request this, please ignore this email.
            """)

            # สร้างการเชื่อมต่อที่ปลอดภัย
            context = ssl.create_default_context()
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls(context=context)  # เริ่มโหมด TLS
                server.login(SMTP_SENDER_EMAIL, SMTP_SENDER_PASSWORD)
                server.send_message(msg)
                print(f"Successfully sent OTP to {recipient_email}")
            return True, "Success"

        except smtplib.SMTPAuthenticationError:
            print("Error: SMTP Authentication Failed. Check email/password (or App Password).")
            return False, "Authentication Error. Check server configuration."
        except Exception as e:
            print(f"Error sending email: {e}")
            return False, f"An error occurred while sending the email: {e}"
    # --- (!!!) สิ้นสุดการแก้ไข (!!!) ---


    def send_code_clicked(self):
        """
        Checks Email, sends real OTP, and switches to Stage 2
        """
        
        # Check if user has configured settings
        if SMTP_SENDER_EMAIL == "your-email@gmail.com" or SMTP_SENDER_PASSWORD == "your-app-password":
            QMessageBox.critical(self, "Configuration Error", 
                               "SMTP settings are not configured.\n\n"
                               "Please edit the script file (forgot_password_otp.py) "
                               "and fill in SMTP_SENDER_EMAIL and SMTP_SENDER_PASSWORD "
                               "at the top of the file.")
            return

        email = self.email.text()
        
        if not email or '@' not in email:
            QMessageBox.warning(self, "Input Error", "Please enter a valid email address.")
            return

        try:
            cursor = self.conn.cursor()
            query = "SELECT * FROM users WHERE email = ?"
            cursor.execute(query, (email,))
            result = cursor.fetchone()

            if result:
                self.generated_otp = str(random.randint(100000, 999999))
                self.verified_email = email
                
                print(f"Generated OTP for {email}: {self.generated_otp}") # For Debug

                # Show "Sending..." message
                loading_msg = QMessageBox(QMessageBox.Icon.Information, "Sending...", "Sending OTP, please wait...", QMessageBox.StandardButton.NoButton, self)
                loading_msg.show()
                QApplication.processEvents() # Force UI update
                
                success, message = self.send_email_otp(self.verified_email, self.generated_otp)
                
                loading_msg.close() # Close "Sending" box
                
                if success:
                    QMessageBox.information(self, "OTP Sent", 
                                          f"An OTP has been successfully sent to:\n{self.verified_email}\n\n"
                                          "Please check your inbox (and spam folder).")
                    
                    self._show_stage2() 
                else:
                    QMessageBox.critical(self, "Email Send Error", 
                                       f"Failed to send OTP.\n\nError: {message}")

            else:
                QMessageBox.critical(self, "Verification Failed", "This email is not registered to any account.")
        except Exception as e:
            if 'loading_msg' in locals():
                loading_msg.close()
            QMessageBox.critical(self, "Database Error", f"An error occurred while checking email: {e}")

    # --- Other functions (check_otp_clicked, toggles, reset_clicked, etc.) remain unchanged ---

    def check_otp_clicked(self):
        """Checks the entered OTP"""
        entered_otp = self.otp_input.text()
        
        if not entered_otp:
            QMessageBox.warning(self, "Input Error", "Please enter the OTP.")
            return
            
        if entered_otp == self.generated_otp:
            QMessageBox.information(self, "Success", "OTP Verified. Please set your new password.")
            self._show_stage3()
        else:
            QMessageBox.warning(self, "Error", "Invalid OTP. Please try again.")
            self.otp_input.clear()


    def toggle_password_visibility(self):
        """Toggles password visibility"""
        if not self.password_visible:
            self.password.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_password_action.setIcon(self.eye_open_icon)
            self.password_visible = True
        else:
            self.password.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_password_action.setIcon(self.eye_closed_icon)
            self.password_visible = False
            
    def toggle_confirm_visibility(self):
        """Toggles confirm password visibility"""
        if not self.confirm_visible:
            self.confirm_password.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_confirm_action.setIcon(self.eye_open_icon)
            self.confirm_visible = True
        else:
            self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_confirm_action.setIcon(self.eye_closed_icon)
            self.confirm_visible = False

    def reset_clicked(self):
        """Handles the password reset logic"""
        email = self.verified_email 
        
        if not email:
            QMessageBox.critical(self, "Error", "No verified email found. Please restart the process.")
            self._show_stage1()
            return
            
        new_password = self.password.text()
        confirm_password = self.confirm_password.text()
        
        if new_password != confirm_password:
            QMessageBox.warning(self, "Error", "Passwords do not match. Please try again.")
            return
            
        is_valid, message = validate_password(email, new_password)
        if not is_valid:
            QMessageBox.warning(self, "Password Error", message)
            return
            
        try:
            cursor = self.conn.cursor()
            query = "UPDATE users SET password = ? WHERE email = ?"
            cursor.execute(query, (new_password, email)) 
            self.conn.commit()
            
            QMessageBox.information(self, "Success", "Your password has been reset successfully.")
            self._show_stage1()
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred while updating password: {e}")

    def back_clicked(self):
        """Returns to Stage 1"""
        print("Returning to Stage 1...")
        self._show_stage1()

    def closeEvent(self, event):
        """Closes the database connection on exit"""
        self.conn.close()
        print("Database connection closed.")
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ForgotPasswordPage()
    window.show()
    sys.exit(app.exec())