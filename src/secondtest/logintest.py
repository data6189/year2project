import sys
import os  # มี import นี้อยู่แล้ว
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit,
    QPushButton, QGraphicsOpacityEffect, QStackedWidget
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QTimer

# === Import ForgetPasswordPage จาก path จริง ===
# หมายเหตุ: ในตัวอย่างนี้ เราจะสร้างคลาสจำลองขึ้นมาแทน
# เพื่อให้โค้ดสามารถรันได้โดยไม่ต้องมีไฟล์ forget_password.py จริง
# (ในการใช้งานจริง ให้ลบส่วนนี้ออก แล้วใช้ import เดิมของคุณ)
try:
    from forget_password import ForgetPasswordPage
except ImportError:
    print("Warning: 'forget_password.py' not found. Using mock class.")
    class ForgetPasswordPage(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.label = QLabel("นี่คือหน้าลืมรหัสผ่าน (จำลอง)", self)
            self.label.setGeometry(550, 200, 400, 50)
            self.back_btn = QPushButton("BACK TO LOGIN", self)
            self.back_btn.setGeometry(550, 300, 180, 50)


class LoginPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # === Label Username ===
        self.user_label = QLabel("Username", self)
        self.user_label.setGeometry(550, 200, 300, 40)

        # === Username Textbox ===
        self.username = QLineEdit(self)
        self.username.setPlaceholderText("Enter Username")
        self.username.setGeometry(550, 250, 400, 50)

        # === Label Password ===
        self.pass_label = QLabel("Password", self)
        self.pass_label.setGeometry(550, 320, 300, 40)

        # === Password Textbox ===
        self.password = QLineEdit(self)
        self.password.setPlaceholderText("Enter Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setGeometry(550, 370, 400, 50)

        # === ปุ่ม Login ===
        self.login_btn = QPushButton("LOGIN", self)
        self.login_btn.setGeometry(550, 480, 180, 50)

        # === ปุ่ม Forget Password ===
        self.forget_btn = QPushButton("FORGET PASSWORD?", self)
        self.forget_btn.setGeometry(770, 480, 180, 50)

        # === เรียก animation ตอนเริ่มต้น ===
        self.animate_widgets([
            self.user_label, self.username,
            self.pass_label, self.password,
            self.login_btn, self.forget_btn
        ])

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

                # เก็บ reference ของ animation ไว้ใน widget เพื่อป้องกัน GC
                w.fade_anim = fade_anim
                w.slide_anim = slide_anim

                fade_anim.start()
                slide_anim.start()

            QTimer.singleShot(i * 150, start_animation)


# === Main Window ใช้ QStackedWidget เพื่อเลื่อนระหว่างหน้า ===
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Beyond Panels")
        self.showMaximized()
        
        # === โหลด Stylesheet (ตามที่คุณถาม) ===
        self.load_stylesheet("src/styles/login.qss") 
        
        # === QStackedWidget ===
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # === สร้างและเพิ่มหน้า ===
        self.login_page = LoginPage()
        self.forget_page = ForgetPasswordPage()  # <-- จาก src/main/forget_password.py

        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.forget_page)

        # === เชื่อมปุ่ม ===
        self.login_page.forget_btn.clicked.connect(self.slide_to_forget)

        # (ถ้า ForgetPasswordPage มีปุ่ม Back ก็เชื่อมกลับได้)
        if hasattr(self.forget_page, "back_btn"):
            self.forget_page.back_btn.clicked.connect(self.slide_to_login)

    def load_stylesheet(self, filepath):
        """โหลดไฟล์ QSS และนำไปใช้กับหน้าต่างนี้"""
        try:
            # ใช้ os.path.join เพื่อความเข้ากันได้ของระบบ
            # สมมติว่า script นี้รันจาก root directory ที่มี src อยู่
            real_path = os.path.join(os.path.dirname(__file__), filepath)
            
            # ถ้าคุณรันจากที่อื่น อาจจะต้องเปลี่ยนเป็น path ตรงๆ
            # real_path = filepath 
            
            with open(real_path, "r", encoding="utf-8") as f:
                style = f.read()
                self.setStyleSheet(style)
                print(f"Stylesheet '{real_path}' loaded successfully.")
        except FileNotFoundError:
            print(f"Error: ไม่พบไฟล์ stylesheet ที่: {real_path}")
        except Exception as e:
            print(f"Error: เกิดปัญหาในการโหลด stylesheet: {e}")

    # --- Slide ไป Forget ---
    def slide_to_forget(self):
        self.animate_slide(self.login_page, self.forget_page, "right")

    # --- Slide กลับ Login ---
    def slide_to_login(self):
        self.animate_slide(self.forget_page, self.login_page, "left")

    def animate_slide(self, current_widget, next_widget, direction="right"):
        """ทำแอนิเมชันเลื่อนหน้า"""
        current_index = self.stack.indexOf(current_widget)
        next_index = self.stack.indexOf(next_widget)

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

        # ป้องกัน GC เก็บไว้ใน instance
        self.anim_old = anim_old
        self.anim_new = anim_new
        
        anim_old.start()
        anim_new.start()
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
