import sys
import os
import sqlite3
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

# === Database Connection ===
DB_PATH = "src/database/thisshop.db" 
if not os.path.exists(DB_PATH):
    print(f"Error: Database file not found at {DB_PATH}")
conn = sqlite3.connect(DB_PATH)


# === Import Pages ===
try:
    from forget_password import ForgetPasswordPage
except ImportError:
    print("Warning: 'forget_password.py' not found. Using mock class.")
    class ForgetPasswordPage(QFrame):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setObjectName("forgetPage")
            QLabel("Mock Forget Password Page", self).move(100, 100)
            self.back_btn = QPushButton("Mock Back", self) 
            self.back_btn.move(100, 150)
            
try:
    from signup import SignupPage 
    print("Successfully imported SignupPage from signup.py")
except ImportError:
    print("Error: 'signup.py' not found or SignupPage class not found.")
    class SignupPage(QFrame):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setObjectName("signupPage")
            QLabel("Mock Signup Page", self).move(100, 100)
            self.back_btn = QPushButton("Mock Back", self) 
            self.back_btn.move(100, 150)

# === (เพิ่ม) Import Main Windows (User, Mod, Admin) ===
# (ย้าย import มาไว้ตรงนี้ เพื่อให้หาไฟล์เจอ)
# (ถ้าไฟล์ยังไม่มีจริง จะใช้ Mock)
try:
    from mainuser import MainUserWindow
except ImportError:
    print("Warning: mainuser.py not found. Using Mock.")
    class MainUserWindow(QMainWindow):
        def __init__(self, username, parent=None):
            super().__init__(parent)
            QLabel(f"Mock User Window\nWelcome {username}", self).move(50,50)

try:
    from mainmod import MainModWindow
except ImportError:
    print("Warning: mainmod.py not found. Using Mock.")
    class MainModWindow(QMainWindow):
         def __init__(self, username, parent=None):
            super().__init__(parent)
            QLabel(f"Mock Mod Window\nWelcome {username}", self).move(50,50)

try:
    from mainadmin import MainAdminWindow
except ImportError:
    print("Warning: mainadmin.py not found. Using Mock.")
    class MainAdminWindow(QMainWindow):
         def __init__(self, username, parent=None):
            super().__init__(parent)
            QLabel(f"Mock Admin Window\nWelcome {username}", self).move(50,50)


# === หน้า Login (แก้ไข) ===
class LoginPage(QFrame):
    # 1. === (แก้ไข) === 
    # สร้าง signal ให้ส่ง string 2 ค่า (username, role)
    login_successful = pyqtSignal(str, str) 

    def __init__(self, eye_open_icon: QIcon, eye_closed_icon: QIcon, parent=None):
        super().__init__(parent)
        
        self.eye_open_icon = eye_open_icon
        self.eye_closed_icon = eye_closed_icon
        
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
        self.login_btn.clicked.connect(self.handle_login)
        self.password.returnPressed.connect(self.handle_login) 

        self.signup_btn = QPushButton("SIGNUP", self)
        self.signup_btn.setObjectName("signupBtn")
        self.signup_btn.setGeometry(770, 480, 180, 50)

        self.forget_btn = QPushButton("FORGET PASSWORD?", self)
        self.forget_btn.setObjectName("forgetBtn")
        self.forget_btn.setGeometry(630, 560, 260, 50)

        self.password_visible = False 
        self.toggle_password_action = QAction(self.eye_closed_icon, "Show/Hide Password", self) 
        self.toggle_password_action.triggered.connect(self.toggle_password_visibility) 
        self.password.addAction(self.toggle_password_action, QLineEdit.ActionPosition.TrailingPosition) 

        self.animate_widgets([
            self.user_label, self.username,
            self.pass_label, self.password,
            self.login_btn, self.signup_btn,
            self.forget_btn
        ])

    def handle_login(self):
        username_text = self.username.text()
        password_text = self.password.text()

        if not username_text or not password_text:
            QMessageBox.warning(self, "Login Error", "Username and password ห้ามเว้นช่องว่าง")
            return

        try:
            cursor = conn.cursor()
            
            # Query นี้จะค้นหาแถวที่ username และ password ตรงกัน
            # และดึงค่า 'role' ออกมาจากตาราง 'users'
            query = "SELECT role FROM users WHERE username = ? AND password = ?" 
            cursor.execute(query, (username_text, password_text))
            
            result = cursor.fetchone() 

            if result:
                # ถ้าเจอ -> ล็อกอินสำเร็จ
                role = result[0] # result คือ tuple เช่น ('user',)
                print(f"Login successful! User: {username_text}, Role: {role}")
                
                # 2. === (แก้ไข) ===
                # ส่ง Signal แจ้ง MainWindow ว่าสำเร็จ 
                # (ส่งทั้ง username_text และ role)
                self.login_successful.emit(username_text, role) 
                
            else:
                QMessageBox.warning(self, "Login Failed", "Invalid username or password.")
                self.password.clear()

        except sqlite3.Error as e:
            if "no such table: users" in str(e):
                QMessageBox.critical(self, "Database Error", "The 'users' table was not found. Please check database setup.")
            else:
                QMessageBox.critical(self, "Database Error", f"An error occurred while checking credentials: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")


    def load_stylesheet(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print(f"Warning: Stylesheet file '{filepath}' not found at '{os.path.abspath(filepath)}'")
        except Exception as e:
            print(f"Error loading stylesheet: {e}")
    
    def toggle_password_visibility(self):
        if not self.password_visible:
            self.password.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_password_action.setIcon(self.eye_open_icon)
            self.password_visible = True
        else:
            self.password.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_password_action.setIcon(self.eye_closed_icon)
            self.password_visible = False
    
    def animate_widgets(self, widgets):
        for i, widget in enumerate(widgets):
            try:
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

                    fade_anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
                    slide_anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

                QTimer.singleShot(i * 150, start_animation)
            except Exception as e:
                print(f"Error animating widget {widget}: {e}")


# === Main Window (แก้ไข) ===
class MainWindow(QMainWindow):
    def __init__(self):
        
        super().__init__()
        self.setWindowTitle("Beyond Comics")
        self.showFullScreen()
        #self.showMaximized()
        
        self.eye_open_icon_path = "src/img/icon/angryeye.png"
        self.eye_closed_icon_path = "src/img/icon/noneye.png"
        
        try:
            self.eye_open_icon = QIcon(self.eye_open_icon_path)
            self.eye_closed_icon = QIcon(self.eye_closed_icon_path)
            if self.eye_open_icon.isNull() or self.eye_closed_icon.isNull():
                print("Warning: Icons loaded but are null. Check paths.")
        except Exception as e:
            print(f"Error loading icons: {e}")
            self.eye_open_icon = QIcon()
            self.eye_closed_icon = QIcon()

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        self.login_page = LoginPage(
            eye_open_icon=self.eye_open_icon, 
            eye_closed_icon=self.eye_closed_icon,
            parent=self
        )
        self.forget_page = ForgetPasswordPage()
        self.signup_page = SignupPage() 

        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.forget_page)
        self.stack.addWidget(self.signup_page) 

        self.login_page.forget_btn.clicked.connect(self.slide_to_forget)
        self.login_page.signup_btn.clicked.connect(self.slide_to_signup) 

        if hasattr(self.signup_page, "back_btn"):
            self.signup_page.back_btn.clicked.connect(self.slide_to_login_from_signup)
        else:
            print("Warning: 'SignupPage' object has no attribute 'back_btn'.")

        if hasattr(self.forget_page, "back_btn"):
            self.forget_page.back_btn.clicked.connect(self.slide_to_login_from_forget)
        else:
            print("Warning: 'ForgetPasswordPage' object has no attribute 'back_btn'.")

        # (เชื่อม Signal จาก LoginPage)
        self.login_page.login_successful.connect(self.on_login_success)
        
        self.main_app_window = None


    # 3. === (แก้ไข) ===
    # ฟังก์ชันนี้จะรับ 2 ค่า (username, role)
    def on_login_success(self, username: str, role: str):
        try:
            # 4. === (แก้ไข) ===
            # ส่ง 'username=username' เข้าไปตอนสร้างหน้าต่างใหม่
            
            if role == 'user':
                # (import ถูกย้ายไปข้างบนแล้ว)
                self.main_app_window = MainUserWindow(username=username)
            elif role == 'moderator':
                # (import ถูกย้ายไปข้างบนแล้ว)
                self.main_app_window = MainModWindow(username=username)
            elif role == 'admin':
                # (import ถูกย้ายไปข้างบนแล้ว)
                self.main_app_window = MainAdminWindow(username=username)
            else:
                QMessageBox.critical(self, "Role Error", f"Unknown role received: {role}")
                return

            # (เพิ่ม) เชื่อมสัญญาณ Logout (ถ้าหน้าต่างนั้นมี)
            if hasattr(self.main_app_window, "logout_requested"):
                self.main_app_window.logout_requested.connect(self.handle_logout)
            
            self.main_app_window.show()
            self.close()
            
        except ImportError as e:
            # (โค้ดนี้อาจจะไม่ถูกเรียกแล้ว ถ้า import อยู่ข้างบน)
            QMessageBox.critical(self, "Import Error", f"Cannot open main window for role '{role}':\n{e}")
        except Exception as e:
            # (เพิ่ม) ดักจับ error อื่นๆ เช่น TypeError ถ้า class __init__ ไม่ตรง
             QMessageBox.critical(self, "Window Error", f"Error creating window for role '{role}':\n{e}")


    # (เพิ่ม) ฟังก์ชันสำหรับจัดการเมื่อ main_app_window กด Logout
    def handle_logout(self):
        print("Logout signal received from main app. Showing login page.")
        # (ล้างค่า username/password ในหน้า login ถ้าต้องการ)
        self.login_page.username.clear()
        self.login_page.password.clear()
        
        # (แสดงหน้า login)
        self.show()
        # (ทำ animation ให้ login page (ถ้าต้องการ))
        self.login_page.animate_widgets([
             self.login_page.user_label, self.login_page.username,
             self.login_page.pass_label, self.login_page.password,
             self.login_page.login_btn, self.login_page.signup_btn,
             self.login_page.forget_btn
        ])


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
        
        anim_old.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        anim_new.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

