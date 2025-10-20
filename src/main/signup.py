from PyQt6.QtWidgets import QApplication, QMainWindow, QLineEdit, QPushButton, QLabel, QGraphicsOpacityEffect
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt, QPropertyAnimation, QPoint, QEasingCurve, QTimer
import sys


class SignupPage(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Beyond Panels - Sign Up")
        self.showMaximized()

        # โหลด stylesheet
        self.load_stylesheet("src/styles/signup.qss")

        # === ตั้งค่าภาพพื้นหลัง ===
        self.bg_label = QLabel(self)
        pixmap = QPixmap("src/img/LoginSystem.jpg") 
        self.bg_label.setPixmap(pixmap)
        self.bg_label.setScaledContents(True)
        self.setCentralWidget(self.bg_label)
        
        # === Title ===
        self.title_label = QLabel("Create Account", self.bg_label)
        self.title_label.setObjectName("titleLabel")
        self.title_label.setGeometry(550, 120, 400, 50)
        
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

        # === Label Confirm Password ===
        self.confirm_label = QLabel("Confirm Password", self.bg_label)
        self.confirm_label.setObjectName("confirmLabel")
        self.confirm_label.setGeometry(550, 560, 300, 40)

        # === Confirm Password Input ===
        self.confirm_password = QLineEdit(self.bg_label)
        self.confirm_password.setPlaceholderText("Confirm Password")
        self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password.setGeometry(550, 610, 400, 50)

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

        # === เรียก animation ===
        self.animate_widgets([
            self.title_label,
            self.user_label, self.username,
            self.email_label, self.email,
            self.pass_label, self.password,
            self.confirm_label, self.confirm_password,
            self.signup_btn, self.back_btn
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

            QTimer.singleShot(i * 100, start_animation)

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
        self.login_window = LoginPage()
        self.login_window.show()
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SignupPage()
    window.show()
    sys.exit(app.exec())