from PyQt6.QtWidgets import QApplication, QMainWindow, QLineEdit, QPushButton, QLabel, QGraphicsOpacityEffect
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
        pixmap = QPixmap("src\img\LoginSystem.jpg") 
        self.bg_label.setPixmap(pixmap)
        self.bg_label.setScaledContents(True)  # scale ตามหน้าต่าง
        self.setCentralWidget(self.bg_label)
        
        # === Label Username ===
        self.user_label = QLabel("Username", self.bg_label)
        self.user_label.setGeometry(550, 200, 300, 40)
        self.user_label.setStyleSheet("color: #FFD700;")
        self.user_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        
        # Username
        username_label = QLabel("Username")
        username_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        username_label.setStyleSheet("color: yellow;")
        self.username_input = QLineEdit()
        self.username_input.setFixedWidth(550)
        self.username_input.setFixedHeight(350)
        self.username_input.setStyleSheet("padding: 8px; border-radius: 20px; background: white;")

        # === Username Textbox ===
        self.username = QLineEdit(self.bg_label)
        self.username.setPlaceholderText("Enter Username")
        self.username.setGeometry(550, 250, 400, 50)  # (x, y, กว้าง, สูง)
        self.username.setStyleSheet("""
            QLineEdit {
                background: white;
                border-radius: 20px;
                padding-left: 15px;
                font-size: 18px;
                color: black;
            }
        """)

        # === Label Password ===
        self.pass_label = QLabel("Password", self.bg_label)
        self.pass_label.setGeometry(550, 320, 300, 40)
        self.pass_label.setStyleSheet("color: #FFD700;")
        self.pass_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))

        # === Password Textbox ===
        self.password = QLineEdit(self.bg_label)
        self.password.setPlaceholderText("Enter Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setGeometry(550, 370, 400, 50)
        self.password.setStyleSheet("""
            QLineEdit {
                background: white;
                border-radius: 20px;
                padding-left: 15px;
                font-size: 18px;
                color: black;
            }
        """)

        # === ปุ่ม Login ===
        self.login_btn = QPushButton("LOGIN", self.bg_label)
        self.login_btn.setGeometry(550, 480, 180, 50)
        self.login_btn.setStyleSheet(self.button_style())
        self.login_btn.clicked.connect(self.login_clicked)

        # === ปุ่ม Signup ===
        self.signup_btn = QPushButton("SIGNUP", self.bg_label)
        self.signup_btn.setGeometry(770, 480, 180, 50)
        self.signup_btn.setStyleSheet(self.button_style())
        self.signup_btn.clicked.connect(self.signup_clicked)

        # === ปุ่ม Forget Password ===
        self.forget_btn = QPushButton("FORGET PASSWORD?", self.bg_label)
        self.forget_btn.setGeometry(630, 560, 260, 50)
        self.forget_btn.setStyleSheet(self.button_style())
        self.forget_btn.clicked.connect(self.forget_clicked)

        # === เรียก animation ===
        self.animate_widgets([
            self.user_label, self.username,
            self.pass_label, self.password,
            self.login_btn, self.signup_btn, self.forget_btn
        ])
        
    def button_style(self):
        return """
            QPushButton {
                color: #FFD700;
                border: 1px solid #FFD700;
                font-size: 16px;
                padding: 8px;
                border-radius: 5px;
                background-color: rgba(0,0,0,0);
            }
            QPushButton:hover {
                background-color: #FFD700;
                color: black;
            }
        """
        
    def animate_widgets(self, widgets):
        """ ทำ fade-in + slide-up ให้แต่ละ widget """
        for i, widget in enumerate(widgets):
            opacity_effect = QGraphicsOpacityEffect()
            widget.setGraphicsEffect(opacity_effect)
            opacity_effect.setOpacity(0)

            # กำหนดตำแหน่งเริ่มจากด้านล่าง
            start_pos = widget.pos() + QPoint(0, 50)
            end_pos = widget.pos()
            widget.move(start_pos)

            def start_animation(w=widget, oe=opacity_effect, sp=start_pos, ep=end_pos):
                # fade animation
                fade_anim = QPropertyAnimation(oe, b"opacity")
                fade_anim.setDuration(1000)
                fade_anim.setStartValue(0)
                fade_anim.setEndValue(1)
                fade_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

                # slide animation
                slide_anim = QPropertyAnimation(w, b"pos")
                slide_anim.setDuration(1000)
                slide_anim.setStartValue(sp)
                slide_anim.setEndValue(ep)
                slide_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

                # กัน GC
                w.fade_anim = fade_anim
                w.slide_anim = slide_anim

                fade_anim.start()
                slide_anim.start()

            # ใช้ QTimer delay ทีละชิ้น
            QTimer.singleShot(i * 150, start_animation)


    # === ฟังก์ชันที่ปุ่มกด (ยังไม่ทำอะไร แค่ print) ===
    def login_clicked(self):
        print("Login clicked:", self.username.text(), self.password.text())

    def signup_clicked(self):
        print("Signup clicked")

    def forget_clicked(self):
        print("Forget Password clicked")

##-- Run --##
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginPage()
    window.show()
    sys.exit(app.exec())
