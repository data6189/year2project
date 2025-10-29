from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLineEdit, QPushButton, QLabel,
    QGraphicsOpacityEffect, QStackedWidget, QWidget
)
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt, QPropertyAnimation, QPoint, QEasingCurve, QTimer
import sys

class LoginPage(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Beyond Panels")
        self.showMaximized()

        # === ตั้งค่าภาพพื้นหลัง ===
        self.bg_label = QLabel(self)
        self.load_stylesheet("src/main/secondtest/styles/login.qss") # โหลด stylesheet จากไฟล์
        self.bg_label.setScaledContents(True)
        self.setCentralWidget(self.bg_label)
        
        # === Label Username ===
        self.user_label = QLabel("Username", self.bg_label)
        self.user_label.setObjectName("userLabel")
        self.user_label.setGeometry(550, 200, 300, 40)
        
        # === Username Textbox ===
        self.username = QLineEdit(self.bg_label)
        self.username.setPlaceholderText("Enter Username")
        self.username.setGeometry(550, 250, 400, 50)

        # === Label Password ===
        self.pass_label = QLabel("Password", self.bg_label)
        self.pass_label.setObjectName("passLabel")
        self.pass_label.setGeometry(550, 320, 300, 40)

        # === Password Textbox ===
        self.password = QLineEdit(self.bg_label)
        self.password.setPlaceholderText("Enter Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setGeometry(550, 370, 400, 50)

        # === ปุ่ม Login ===
        self.login_btn = QPushButton("LOGIN", self.bg_label)
        self.login_btn.setObjectName("loginBtn")
        self.login_btn.setGeometry(550, 480, 180, 50)
        self.login_btn.clicked.connect(self.login_clicked)

        # === ปุ่ม Signup ===
        self.signup_btn = QPushButton("SIGNUP", self.bg_label)
        self.signup_btn.setObjectName("signupBtn")
        self.signup_btn.setGeometry(770, 480, 180, 50)
        self.signup_btn.clicked.connect(self.signup_clicked)

        # === ปุ่ม Forget Password ===
        self.forget_btn = QPushButton("FORGET PASSWORD?", self.bg_label)
        self.forget_btn.setObjectName("forgetBtn")
        self.forget_btn.setGeometry(630, 560, 260, 50)
        self.forget_btn.clicked.connect(self.forget_clicked)

        # === เรียก animation ===
        self.animate_widgets([
            self.user_label, self.username,
            self.pass_label, self.password,
            self.login_btn, self.signup_btn, self.forget_btn
        ])
    
    def load_stylesheet(self, filepath):
        """โหลด QSS stylesheet จากไฟล์"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print(f"Warning: Stylesheet file '{filepath}' not found")
        
    def animate_widgets(self, widgets):
        """ทำ fade-in + slide-up ให้แต่ละ widget"""
        for i, widget in enumerate(widgets):
            opacity_effect = QGraphicsOpacityEffect()
            widget.setGraphicsEffect(opacity_effect)
            opacity_effect.setOpacity(0)

            start_pos = widget.pos() + QPoint(0, 50)
            end_pos = widget.pos()
            widget.move(start_pos)

            def start_animation(w=widget, oe=opacity_effect, sp=start_pos, ep=end_pos):
                fade_anim = QPropertyAnimation(oe, b"opacity")
                fade_anim.setDuration(1000)
                fade_anim.setStartValue(0)
                fade_anim.setEndValue(1)
                fade_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

                slide_anim = QPropertyAnimation(w, b"pos")
                slide_anim.setDuration(1000)
                slide_anim.setStartValue(sp)
                slide_anim.setEndValue(ep)
                slide_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

                w.fade_anim = fade_anim
                w.slide_anim = slide_anim

                fade_anim.start()
                slide_anim.start()

            QTimer.singleShot(i * 150, start_animation)

    def login_clicked(self):
        """ฟังก์ชันเมื่อกด Login"""
        username = self.username.text()
        password = self.password.text()
        
        if not username or not password:
            print("Error: Please fill all fields")
            return
            
        print("Login clicked:", username, password)
        # TODO: ตรวจสอบกับ database

    def signup_clicked(self):
        """เปิดหน้า Signup"""
        from signup import SignupPage
        self.signup_window = SignupPage()
        self.signup_window.show()
        self.close()

    def forget_clicked(self):
        """เปิดหน้า Forget Password"""
        from forget_password import ForgetPasswordPage
        self.forget_window = ForgetPasswordPage()
        self.forget_window.show()
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginPage()
    window.show()
    sys.exit(app.exec())