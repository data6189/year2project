from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import sys


class SignupPage(QMainWindow):
    def __init__(self):
        super().__init__()
        self.showMaximized()

        # โหลด stylesheet
        self.load_stylesheet("src/styles/signup.qss")
        
        # === (ADDED) ตั้งค่าไอคอนสำหรับแสดง/ซ่อนรหัสผ่าน ===
        self.eye_open_icon_path = "src/img/icon/angryeye.png"
        self.eye_closed_icon_path = "src/img/icon/noneye.png"
        self.icon_size = QSize(25, 25)
        try:
            self.eye_open_icon = QIcon(self.eye_open_icon_path)
            self.eye_closed_icon = QIcon(self.eye_closed_icon_path)
        except Exception as e:
            print(f"Error loading icons: {e}")
            # สร้างไอคอนเปล่าๆ ไว้แทน_
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
        
        # === (ADDED) เพิ่ม Action (ไอคอนตา) ให้ช่อง Password ===
        self.password_visible = False # <--- (ADDED) สร้าง state เก็บสถานะ
        self.toggle_password_action = QAction(self.eye_closed_icon, "Show/Hide Password", self) # <--- (ADDED)
        self.toggle_password_action.triggered.connect(self.toggle_password_visibility) # <--- (ADDED)
        self.password.addAction(self.toggle_password_action, QLineEdit.ActionPosition.TrailingPosition) # <--- (ADDED)

        # === Label Confirm Password ===
        self.confirm_label = QLabel("Confirm Password", self.bg_label)
        self.confirm_label.setObjectName("confirmLabel")
        self.confirm_label.setGeometry(550, 560, 300, 40)

        # === Confirm Password Input ===
        self.confirm_password = QLineEdit(self.bg_label)
        self.confirm_password.setPlaceholderText("Confirm Password")
        self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password.setGeometry(550, 610, 400, 50)
        
        # === (ADDED) เพิ่ม Action (ไอคอนตา) ให้ช่อง Confirm Password ===
        self.confirm_visible = False # <--- (ADDED) สร้าง state เก็บสถานะ
        self.toggle_confirm_action = QAction(self.eye_closed_icon, "Show/Hide Password", self) # <--- (ADDED)
        self.toggle_confirm_action.triggered.connect(self.toggle_confirm_visibility) # <--- (ADDED)
        self.confirm_password.addAction(self.toggle_confirm_action, QLineEdit.ActionPosition.TrailingPosition) # <--- (ADDED)

        # === ปุ่ม Sign Up ===
        self.signup_btn = QPushButton("SIGN UP", self.bg_label)
        self.signup_btn.setObjectName("signupBtn")
        self.signup_btn.setGeometry(550, 690, 180, 50)
        self.signup_btn.clicked.connect(self.signup_clicked)

        # === ปุ่ม Back to Login ===
        self.back_btn = QPushButton("BACK TO LOGIN", self.bg_label)
        self.back_btn.setObjectName("backBtn")
        self.back_btn.setGeometry(770, 690, 180, 50)
        self.back_btn.clicked.connect(self.back_clicked)
    
    def load_stylesheet(self, filepath):
        """โหลด QSS stylesheet จากไฟล์"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print(f"Warning: Stylesheet file '{filepath}' not found")
    
    # === (ADDED) ฟังก์ชันสำหรับสลับการแสดงผลรหัสผ่าน ===
    def toggle_password_visibility(self):
        if not self.password_visible:
            self.password.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_password_action.setIcon(self.eye_open_icon)
            self.password_visible = True
        else:
            self.password.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_password_action.setIcon(self.eye_closed_icon)
            self.password_visible = False
            
    # === (ADDED) ฟังก์ชันสำหรับสลับการแสดงผลรหัสผ่าน (ช่องยืนยัน) ===
    def toggle_confirm_visibility(self):
        if not self.confirm_visible:
            self.confirm_password.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_confirm_action.setIcon(self.eye_open_icon)
            self.confirm_visible = True
        else:
            self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_confirm_action.setIcon(self.eye_closed_icon)
            self.confirm_visible = False

    def signup_clicked(self):
        """ฟังก์ชันเมื่อกด Sign Up"""
        username = self.username.text()
        email = self.email.text()
        password = self.password.text()
        confirm = self.confirm_password.text()
        
        # ตรวจสอบข้อมูล
        if not username or not email or not password:
            print("Error: Please fill all fields")
            return
            
        if password != confirm:
            print("Error: Passwords do not match")
            return
        
        print(f"Sign Up - Username: {username}, Email: {email}")
        # TODO: เชื่อมต่อกับ database

    def back_clicked(self):
        """กลับไปหน้า Login"""
        from login import LoginPage
        # ส่วนนี้คุณต้องจัดการการสลับหน้าต่างเอง (เช่น self.close() และเปิดหน้าใหม่)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SignupPage()
    window.show()
    sys.exit(app.exec())