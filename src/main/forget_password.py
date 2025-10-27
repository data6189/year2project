from PyQt6.QtWidgets import QApplication, QMainWindow, QLineEdit, QPushButton, QLabel, QGraphicsOpacityEffect
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt, QPropertyAnimation, QPoint, QEasingCurve, QTimer
import sys


class ForgetPasswordPage(QMainWindow):
    def __init__(self):
        super().__init__()
        self.showMaximized()

        # โหลด stylesheet
        self.load_stylesheet("src/styles/forget_password.qss")

        # === ตั้งค่าภาพพื้นหลัง ===
        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(True)
        self.setCentralWidget(self.bg_label)
        
        # === Title ===
        self.title_label = QLabel("Reset Password", self.bg_label)
        self.title_label.setObjectName("titleLabel")
        self.title_label.setGeometry(550, 180, 400, 50)
        
        # === Description ===
        self.desc_label = QLabel("Enter your email to receive reset instructions", self.bg_label)
        self.desc_label.setObjectName("descLabel")
        self.desc_label.setGeometry(550, 240, 400, 30)
        
        # === Label Email ===
        self.email_label = QLabel("Email", self.bg_label)
        self.email_label.setObjectName("emailLabel")
        self.email_label.setGeometry(550, 300, 300, 40)
        
        # === Email Input ===
        self.email = QLineEdit(self.bg_label)
        self.email.setPlaceholderText("Enter your email")
        self.email.setGeometry(550, 350, 400, 50)

        # === Label Verification Code (hidden initially) ===
        self.code_label = QLabel("Verification Code", self.bg_label)
        self.code_label.setObjectName("codeLabel")
        self.code_label.setGeometry(550, 420, 300, 40)
        self.code_label.hide()
        
        # === Verification Code Input (hidden initially) ===
        self.code = QLineEdit(self.bg_label)
        self.code.setPlaceholderText("Enter 6-digit code")
        self.code.setGeometry(550, 470, 400, 50)
        self.code.hide()

        # === Label New Password (hidden initially) ===
        self.pass_label = QLabel("New Password", self.bg_label)
        self.pass_label.setObjectName("passLabel")
        self.pass_label.setGeometry(550, 540, 300, 40)
        self.pass_label.hide()

        # === New Password Input (hidden initially) ===
        self.password = QLineEdit(self.bg_label)
        self.password.setPlaceholderText("Enter new password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setGeometry(550, 590, 400, 50)
        self.password.hide()

        # === ปุ่ม Send Code ===
        self.send_btn = QPushButton("SEND CODE", self.bg_label)
        self.send_btn.setObjectName("sendBtn")
        self.send_btn.setGeometry(550, 450, 180, 50)
        self.send_btn.clicked.connect(self.send_code_clicked)

        # === ปุ่ม Reset Password (hidden initially) ===
        self.reset_btn = QPushButton("RESET PASSWORD", self.bg_label)
        self.reset_btn.setObjectName("resetBtn")
        self.reset_btn.setGeometry(550, 680, 180, 50)
        self.reset_btn.clicked.connect(self.reset_clicked)
        self.reset_btn.hide()

        # === ปุ่ม Back to Login ===
        self.back_btn = QPushButton("BACK TO LOGIN", self.bg_label)
        self.back_btn.setObjectName("backBtn")
        self.back_btn.setGeometry(770, 450, 180, 50)
        self.back_btn.clicked.connect(self.back_clicked)

        # === Track state ===
        self.code_sent = False
    
    def load_stylesheet(self, filepath):
        """โหลด QSS stylesheet จากไฟล์"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print(f"Warning: Stylesheet file '{filepath}' not found")

    def send_code_clicked(self):
        """ฟังก์ชันเมื่อกด Send Code"""
        email = self.email.text()
        
        if not email:
            print("Error: Please enter email")
            return
        
        if '@' not in email:
            print("Error: Invalid email format")
            return
        
        print(f"Sending verification code to: {email}")
        # TODO: ส่ง email จริง
        
        # แสดงฟิลด์เพิ่มเติม
        self.code_label.show()
        self.code.show()
        self.pass_label.show()
        self.password.show()
        self.reset_btn.show()
        
        # ปรับตำแหน่งปุ่ม back
        self.back_btn.setGeometry(770, 680, 180, 50)
        
        # ซ่อนปุ่ม send
        self.send_btn.hide()
        
        self.code_sent = True


    def reset_clicked(self):
        """ฟังก์ชันเมื่อกด Reset Password"""
        email = self.email.text()
        code = self.code.text()
        new_password = self.password.text()
        
        if not code or not new_password:
            print("Error: Please fill all fields")
            return
        
        if len(code) != 6:
            print("Error: Verification code must be 6 digits")
            return
        
        if len(new_password) < 6:
            print("Error: Password must be at least 6 characters")
            return
        
        print(f"Reset Password - Email: {email}, Code: {code}")
        # TODO: ตรวจสอบ code และอัปเดต password ใน database
        
        # กลับไปหน้า Login
        self.back_clicked()

    def back_clicked(self):
        """กลับไปหน้า Login"""
        from login import LoginPage



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ForgetPasswordPage()
    window.show()
    sys.exit(app.exec())