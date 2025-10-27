import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

# === Import Pages ===
# 1. Import ForgetPasswordPage
try:
    from forget_password import ForgetPasswordPage
except ImportError:
    print("Warning: 'forget_password.py' not found. Using mock class.")
    
# 2. Import SignupPage (แก้ไขตามคำขอ)
try:
    from signup import SignupPage 
    print("Successfully imported SignupPage from signup.py")
except ImportError:
    print("Error: 'signup.py' not found or SignupPage class not found.")

# === หน้า Login (เหมือนเดิม) ===
class LoginPage(QFrame): # <-- แก้ไขบรรทัดนี้
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # === โหลด Stylesheet (เหมือนเดิม) ===
        self.load_stylesheet("src/styles/login.qss")
        self.setObjectName("loginPage")
        
        self.user_label = QLabel("Username", self)
        self.user_label.setObjectName("userLabel")
        self.user_label.setGeometry(550, 200, 300, 40)

        self.username = QLineEdit(self)
        self.username.setPlaceholderText("Enter Username")
        self.username.setGeometry(550, 250, 400, 50)

        self.pass_label = QLabel("Password", self)
        self.pass_label.setObjectName("passLabel")
        self.pass_label.setGeometry(550, 320, 300, 40)

        self.password = QLineEdit(self)
        self.password.setPlaceholderText("Enter Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setGeometry(550, 370, 400, 50)

        self.login_btn = QPushButton("LOGIN", self)
        self.login_btn.setObjectName("loginBtn")
        self.login_btn.setGeometry(550, 480, 180, 50)

        self.signup_btn = QPushButton("SIGNUP", self)
        self.signup_btn.setObjectName("signupBtn")
        self.signup_btn.setGeometry(770, 480, 180, 50)

        self.forget_btn = QPushButton("FORGET PASSWORD?", self)
        self.forget_btn.setObjectName("forgetBtn")
        self.forget_btn.setGeometry(630, 560, 260, 50)

        self.animate_widgets([
            self.user_label, self.username,
            self.pass_label, self.password,
            self.login_btn, self.signup_btn,
            self.forget_btn
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


# === Main Window (เหมือนเดิม) ===
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Beyond Comics")
        self.showMaximized()
        
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # === สร้างและเพิ่มหน้า ===
        self.login_page = LoginPage()
        self.forget_page = ForgetPasswordPage()
        self.signup_page = SignupPage() # <-- ตอนนี้จะใช้คลาสจริงจาก signup.py

        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.forget_page)
        self.stack.addWidget(self.signup_page) 

        # === เชื่อมปุ่ม ===
        self.login_page.forget_btn.clicked.connect(self.slide_to_forget)
        self.login_page.signup_btn.clicked.connect(self.slide_to_signup) 

        # --- สำคัญ ---
        # ตรวจสอบว่าคลาส SignupPage ของคุณมีปุ่มชื่อ 'back_btn' หรือไม่
        # ถ้ามี โค้ดนี้จะเชื่อมต่อปุ่มนั้นให้
        if hasattr(self.signup_page, "back_btn"):
            self.signup_page.back_btn.clicked.connect(self.slide_to_login_from_signup)
        else:
            print("Warning: 'SignupPage' object from signup.py has no attribute 'back_btn'.")
            print("         (ปุ่ม 'Back' จากหน้า Signup จะยังไม่ทำงาน)")

        if hasattr(self.forget_page, "back_btn"):
            self.forget_page.back_btn.clicked.connect(self.slide_to_login_from_forget)
        else:
             print("Warning: 'ForgetPasswordPage' object has no attribute 'back_btn'.")

    # --- (เมธอด slide ทั้งหมดเหมือนเดิม) ---

    def slide_to_forget(self):
        self.animate_slide(self.login_page, self.forget_page, "right")

    def slide_to_signup(self):
        self.animate_slide(self.login_page, self.signup_page, "right")

    def slide_to_login_from_forget(self):
        self.animate_slide(self.forget_page, self.login_page, "left")

    def slide_to_login_from_signup(self):
        self.animate_slide(self.signup_page, self.login_page, "left")

    def animate_slide(self, current_widget, next_widget, direction="right"):
        """ทำแอนิเมชันเลื่อนหน้า"""
        current_index = self.stack.indexOf(current_widget)
        next_index = self.stack.indexOf(next_widget)

        if current_index == next_index:
            return 

        offset_x = self.stack.frameRect().width()
        if direction == "left":
            offset_x = -offset_x

        next_widget.setGeometry(offset_x, 0, self.stack.width(), self.stack.height())
        self.stack.setCurrentWidget(next_widget)

        anim_old = QPropertyAnimation(current_widget, b"pos")
        anim_new = QPropertyAnimation(next_widget, b"pos")

        for anim in (anim_old, anim_new):
            anim.setDuration(600)
            anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        anim_old.setStartValue(current_widget.pos())
        anim_old.setEndValue(QPoint(-offset_x, 0))

        anim_new.setStartValue(QPoint(offset_x, 0))
        anim_new.setEndValue(QPoint(0, 0))

        self.anim_old = anim_old
        self.anim_new = anim_new
        
        anim_old.start()
        anim_new.start()
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

