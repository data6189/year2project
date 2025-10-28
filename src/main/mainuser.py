import sys
import os
import sqlite3
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

# (สำคัญ) ตรวจสอบให้แน่ใจว่าเส้นทางไปยังฐานข้อมูลถูกต้อง
DB_PATH = "src/database/thisshop.db" 

class MainUserWindow(QMainWindow):
    logout_requested = pyqtSignal()
    
    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.current_username = username 
        
        self.new_profile_img_path = None # เส้นทางรูปโปรไฟล์ใหม่ที่เลือก
        self.current_profile_img_path = None # เส้นทางรูปโปรไฟล์ปัจจุบันจาก DB
        self.editable_profile_fields = [] # รายการช่องที่แก้ไขได้

        self.is_in_edit_mode = False

        self.setWindowTitle(f"Beyond Comics - Welcome {self.current_username}") 
        self.setGeometry(100, 100, 1920, 1080)
        self.showMaximized()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.header_frame = self.create_header()
        self.main_layout.addWidget(self.header_frame)

        self.body_widget = QWidget()
        self.body_layout = QHBoxLayout(self.body_widget)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(0)

        self.sidebar_stack = QStackedWidget()
        self.sidebar_stack.setFixedWidth(260)
        
        self.browse_sidebar = self.create_browse_sidebar()
        self.profile_sidebar = self.create_profile_sidebar()
        
        self.sidebar_stack.addWidget(self.browse_sidebar)
        self.sidebar_stack.addWidget(self.profile_sidebar)
        
        self.body_layout.addWidget(self.sidebar_stack) 

        self.main_content_stack = QStackedWidget()
        self.browse_page = self.create_browse_page()
        self.profile_page = self.create_profile_page()

        self.main_content_stack.addWidget(self.browse_page)
        self.main_content_stack.addWidget(self.profile_page)
        
        self.body_layout.addWidget(self.main_content_stack, 1)

        self.main_layout.addWidget(self.body_widget, 1)

        # (แก้ไข) ตรวจสอบให้แน่ใจว่าโหลดไฟล์ QSS ที่ถูกต้อง
        self.load_stylesheet("src/styles/mainuser.qss")
        self.load_user_profile()
        
        self.set_profile_fields_read_only(True)


    def load_stylesheet(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print(f"คำเตือน: ไม่พบไฟล์ stylesheet '{filepath}'")
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการโหลด stylesheet: {e}")

    def create_header(self):
        header_frame = QFrame()
        header_frame.setObjectName("Header")
        header_frame.setFixedHeight(185)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(50, 10, 50, 10)
        header_layout.setSpacing(120)
        header_layout.addStretch()

        button_height = 60
        button_width = 190
        
        cart_icon = QIcon("src/img/icon/cart.png") 
        cart_button = QPushButton(" CART") 
        cart_button.setIcon(cart_icon)
        cart_button.setIconSize(QSize(50, 50)) 
        cart_button.setObjectName("navButton")
        cart_button.setFixedSize(button_width, button_height)
        header_layout.addWidget(cart_button)

        profile_icon = QIcon("src/img/icon/profile.png") 
        profile_button = QPushButton(" PROFILE")
        profile_button.setIcon(profile_icon)
        profile_button.setIconSize(QSize(50, 50))
        profile_button.setObjectName("navButton")
        profile_button.setFixedSize(button_width, button_height)
        profile_button.clicked.connect(self.show_profile_page)
        header_layout.addWidget(profile_button)

        logout_button = QPushButton("LOGOUT")
        logout_button.setObjectName("navButton")
        logout_button.setFixedSize(button_width, button_height)
        logout_button.clicked.connect(self.handle_logout)
        header_layout.addWidget(logout_button)

        return header_frame

    def create_browse_sidebar(self):
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("Sidebar") 
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(20, 30, 20, 20)
        sidebar_layout.setSpacing(25)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        button_height = 55

        btn_marvel = QPushButton("MARVEL")
        btn_marvel.setObjectName("sidebarButton")
        btn_marvel.setFixedHeight(button_height)
        btn_marvel.clicked.connect(self.show_browse_page) 
        sidebar_layout.addWidget(btn_marvel)

        btn_dc = QPushButton("DC")
        btn_dc.setObjectName("sidebarButton")
        btn_dc.setFixedHeight(button_height)
        btn_dc.clicked.connect(self.show_browse_page)
        sidebar_layout.addWidget(btn_dc)

        btn_image = QPushButton("Image Comics")
        btn_image.setObjectName("sidebarButton")
        btn_image.setFixedHeight(button_height)
        btn_image.clicked.connect(self.show_browse_page)
        sidebar_layout.addWidget(btn_image)
        sidebar_layout.addStretch()
        
        btn_image = QPushButton("ALL")
        btn_image.setObjectName("sidebarButton")
        btn_image.setFixedHeight(button_height)
        btn_image.clicked.connect(self.show_browse_page)
        sidebar_layout.addWidget(btn_image)
        sidebar_layout.addStretch()
        
        return sidebar_frame

    def create_profile_sidebar(self):
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("Sidebar") 
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(20, 30, 20, 20)
        sidebar_layout.setSpacing(25)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        button_height = 55

        btn_profile = QPushButton("PROFILE")
        btn_profile.setObjectName("profilesidebarButton")
        btn_profile.setFixedHeight(button_height)
        btn_profile.setEnabled(False)
        sidebar_layout.addWidget(btn_profile)

        btn_back = QPushButton("Back")
        btn_back.setObjectName("backsidebarButton")
        btn_back.setFixedHeight(button_height)
        btn_back.clicked.connect(self.show_browse_page)
        sidebar_layout.addWidget(btn_back)
        
        sidebar_layout.addStretch()
        return sidebar_frame

    def create_browse_page(self):
        main_content_frame = QFrame()
        main_content_frame.setObjectName("MainContent") 
        main_layout = QVBoxLayout(main_content_frame)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(300, 20, 20, 20)

        browse_header_layout = QHBoxLayout()
        browse_label = QLabel("BROWSE")
        browse_label.setObjectName("browseLabel")
        browse_header_layout.addWidget(browse_label)
        browse_header_layout.addStretch()
        sort_combo = QComboBox()
        sort_combo.setObjectName("sortCombo")
        sort_combo.addItems(["Newest", "Oldest", "A-Z"])
        sort_combo.setFixedHeight(35)
        browse_header_layout.addWidget(sort_combo)
        main_layout.addLayout(browse_header_layout)
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(10)
        search_input = QLineEdit()
        search_input.setObjectName("searchBox")
        search_input.setPlaceholderText("Search comics...")
        search_input.setFixedHeight(40)
        search_button = QPushButton("Search")
        search_button.setObjectName("searchButton")
        search_button.setFixedHeight(40)
        search_layout.addWidget(search_input, stretch=1)
        search_layout.addWidget(search_button)
        main_layout.addLayout(search_layout)
        scroll_area = QScrollArea()
        scroll_area.setObjectName("scrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content_widget = QWidget()
        scroll_content_widget.setObjectName("scrollContent")
        self.grid_layout = QGridLayout(scroll_content_widget)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setContentsMargins(20, 20, 20, 20)
        for i in range(20):
            row = i // 4
            col = i % 4
            comic_placeholder = QLabel(f"Comic Book {i+1}\n[Image Here]")
            comic_placeholder.setObjectName("comicPlaceholder")
            comic_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            comic_placeholder.setFixedSize(200, 300)
            self.grid_layout.addWidget(comic_placeholder, row, col)
        scroll_area.setWidget(scroll_content_widget)
        main_layout.addWidget(scroll_area, stretch=1)
        
        return main_content_frame

    def create_profile_page(self):
        profile_frame = QFrame()
        profile_frame.setObjectName("ProfilePage") 
        
        main_profile_layout = QVBoxLayout(profile_frame)
        main_profile_layout.setContentsMargins(300, 50, 50, 50)
        main_profile_layout.setSpacing(30)
        main_profile_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)
        top_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        left_container = QWidget()
        left_pic_layout = QVBoxLayout()
        left_pic_layout.setSpacing(10)
        left_pic_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        left_pic_layout.setContentsMargins(0,0,0,0)

        self.profile_pic_label = QLabel()
        self.profile_pic_label.setObjectName("profilePicLabel")
        # --- ขนาดของ Label รูปโปรไฟล์ (ปรับเป็น 250x250) ---
        self.profile_pic_label.setFixedSize(250, 250) 
        
        self.upload_button = QPushButton(" Upload Profile image")
        try:
            upload_icon = QIcon(QPixmap("src/img/icon/upload.png")) 
            self.upload_button.setIcon(upload_icon)
            self.upload_button.setIconSize(QSize(40, 40))
        except:
             print("คำเตือน: ไม่พบไอคอนอัปโหลด 'src/img/icon/upload.png'")
            
        self.upload_button.setObjectName("uploadButton") 
        self.upload_button.setFixedHeight(40)
        self.upload_button.clicked.connect(self.select_profile_image)
        self.upload_button.setVisible(False)
        
        left_pic_layout.addWidget(self.profile_pic_label)
        left_pic_layout.addWidget(self.upload_button)
        
        left_container.setLayout(left_pic_layout)
        top_layout.addWidget(left_container, 0, alignment=Qt.AlignmentFlag.AlignTop)
        
        info_frame = QFrame()
        info_frame.setObjectName("profileInfoFrame")
        info_layout = QFormLayout(info_frame) 
        info_layout.setSpacing(15)
        info_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft) 

        self.profile_username_field = QLineEdit()
        self.profile_fname_field = QLineEdit()
        self.profile_lname_field = QLineEdit()
        self.profile_gender_field = QComboBox() 
        self.profile_gender_field.addItems(["ชาย", "หญิง", "อื่น ๆ"])
        self.profile_gender_field.setObjectName("profileDataField") 
        
        self.profile_email_field = QLineEdit()
        self.profile_phone_field = QLineEdit()
        self.profile_address_field = QTextEdit() 
        
        self.editable_profile_fields = [
            self.profile_fname_field, self.profile_lname_field,
            self.profile_gender_field,
            self.profile_email_field,
            self.profile_phone_field, self.profile_address_field
        ]
        
        self.profile_username_field.setReadOnly(True)
        self.profile_username_field.setObjectName("profileDataField")
        
        for field in self.editable_profile_fields:
            if isinstance(field, (QLineEdit, QTextEdit)):
                field.setReadOnly(True)
            elif isinstance(field, QComboBox):
                field.setEnabled(False)
                
            field.setObjectName("profileDataField") 

        self.profile_address_field.setFixedHeight(100) 

        info_layout.addRow(QLabel("Username :"), self.profile_username_field)
        info_layout.addRow(QLabel("First Name :"), self.profile_fname_field) 
        info_layout.addRow(QLabel("Last Name :"), self.profile_lname_field)
        info_layout.addRow(QLabel("Gender :"), self.profile_gender_field)
        info_layout.addRow(QLabel("Email :"), self.profile_email_field)
        info_layout.addRow(QLabel("Phone :"), self.profile_phone_field) 
        info_layout.addRow(QLabel("Address :"), self.profile_address_field)

        top_layout.addWidget(info_frame, 1) 
        main_profile_layout.addLayout(top_layout)

        self.bottom_button_layout = QHBoxLayout()
        self.bottom_button_layout.setSpacing(10)
        
        edit_icon = QIcon("src/img/icon/edit.png") 
        self.edit_button = QPushButton(" Edit profile")
        self.edit_button.setIcon(edit_icon)
        self.edit_button.setIconSize(QSize(50, 50))
        self.edit_button.setObjectName("editProfileButton") 
        self.edit_button.setFixedSize(190, 60)
        
        self.edit_button.clicked.connect(self.toggle_edit_mode) 
        
        self.bottom_button_layout.addWidget(self.edit_button, 0)
        
        confirm_icon = QIcon("src/img/icon/confirm.png") 
        self.confirm_button = QPushButton(" Confirm")
        self.confirm_button.setIcon(confirm_icon)
        self.confirm_button.setIconSize(QSize(50, 50))
        self.confirm_button.setObjectName("confirmProfileButton") 
        self.confirm_button.setFixedSize(190, 60)
        self.confirm_button.clicked.connect(self.save_profile_changes)
        self.confirm_button.setVisible(False)
        
        self.bottom_button_layout.addWidget(self.confirm_button, 0)
        
        self.bottom_button_layout.addStretch(1)
        
        main_profile_layout.addLayout(self.bottom_button_layout)
        main_profile_layout.addStretch()

        return profile_frame

    # --- (แก้ไข) ---
    # เปลี่ยนชื่อจาก create_circular_pixmap เป็น create_scaled_pixmap
    # และลบโค้ดส่วนที่ทำให้เป็นวงกลม (QPainter, QPainterPath)
    def create_scaled_pixmap(self, image_path, size):
        """
        สร้าง QPixmap สี่เหลี่ยมที่สเกลแล้วจาก image_path ที่กำหนด
        """
        try:
            source_pixmap = QPixmap(image_path)
            if source_pixmap.isNull():
                # ถ้า path ไม่ถูกต้อง หรือไฟล์เสียหาย ให้ใช้รูป default
                print(f"คำเตือน: ไม่พบไฟล์รูปภาพที่ '{image_path}', ใช้รูปโปรไฟล์เริ่มต้น")
                source_pixmap = QPixmap("src/img/icon/profile.png")
                if source_pixmap.isNull():
                        # ถ้าไฟล์ default ก็ไม่มี ให้สร้าง pixmap สีเทาขึ้นมาแทน
                    print("คำเตือน: ไม่พบรูปโปรไฟล์เริ่มต้น 'src/img/icon/profile.png'")
                    source_pixmap = QPixmap(size, size)
                    source_pixmap.fill(Qt.GlobalColor.gray)

        except Exception as e:
            print(f"เกิดข้อผิดพลาดขณะโหลด QPixmap: {e}")
            source_pixmap = QPixmap(size, size)
            source_pixmap.fill(Qt.GlobalColor.gray)

        # 1. สเกลภาพให้เป็นสี่เหลี่ยมจัตุรัสขนาดที่กำหนด
        # (ใช้ IgnoreAspectRatio เพื่อบังคับให้ภาพพอดีกับกรอบ 250x250)
        scaled_pixmap = source_pixmap.scaled(
            size, size, 
            Qt.AspectRatioMode.IgnoreAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )

        # 8. คืนค่า pixmap ที่สเกลแล้ว
        return scaled_pixmap
    # --- (สิ้นสุดการแก้ไข) ---

    def load_user_profile(self):
        try:
            target_size = 250 # ขนาดที่ตรงกับ QLabel (250x250)
            
            if not os.path.exists(DB_PATH):
                print(f"ข้อผิดพลาด: ไม่พบไฟล์ DB ขณะโหลดโปรไฟล์: {DB_PATH}")
                self.profile_username_field.setText(self.current_username)
                self.profile_fname_field.setText("N/A (DB not found)")
                
                # --- (แก้ไข) เรียกใช้ create_scaled_pixmap ---
                default_pixmap = self.create_scaled_pixmap("src/img/icon/profile.png", target_size)
                self.profile_pic_label.setPixmap(default_pixmap)
                return

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT first_name, last_name, gender, email, phone, address, profile_img 
                FROM users 
                WHERE username = ?
            """, (self.current_username,))
            
            user_data = cursor.fetchone()
            conn.close()

            if user_data:
                fname, lname, gender, email, phone, address, img_path = user_data
                
                self.profile_username_field.setText(self.current_username)
                self.profile_fname_field.setText(fname or "")
                self.profile_lname_field.setText(lname or "")
                
                gender_value = gender or ""
                index = self.profile_gender_field.findText(gender_value, Qt.MatchFlag.MatchFixedString)
                if index >= 0:
                    self.profile_gender_field.setCurrentIndex(index)
                else:
                    self.profile_gender_field.setCurrentIndex(0)
                    if gender_value not in ["", "N/A"]:
                            print(f"คำเตือน: เพศ '{gender_value}' จาก DB ไม่ตรงกับตัวเลือก, ตั้งเป็นค่าเริ่มต้น")
                
                self.profile_email_field.setText(email or "")
                self.profile_phone_field.setText(phone or "") 
                self.profile_address_field.setText(address or "")
                
                self.current_profile_img_path = img_path
                self.new_profile_img_path = None

                # --- (แก้ไข) เรียกใช้ create_scaled_pixmap ---
                image_path_to_load = img_path if (img_path and os.path.exists(img_path)) else "src/img/icon/profile.png"
                scaled_pixmap = self.create_scaled_pixmap(image_path_to_load, target_size)
                self.profile_pic_label.setPixmap(scaled_pixmap)
                
            else:
                print(f"ไม่พบผู้ใช้: {self.current_username}")
                self.profile_username_field.setText(self.current_username)
                self.profile_fname_field.setText("N/A")
                self.profile_lname_field.setText("N/A")
                self.profile_gender_field.setCurrentIndex(0)
                
                # --- (แก้ไข) เรียกใช้ create_scaled_pixmap ---
                default_pixmap = self.create_scaled_pixmap("src/img/icon/profile.png", target_size)
                self.profile_pic_label.setPixmap(default_pixmap)

        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการโหลดโปรไฟล์: {e}")
            QMessageBox.warning(self, "Error", f"ไม่สามารถโหลดข้อมูลโปรไฟล์ได้: {e}")

    def set_profile_fields_read_only(self, read_only):
        for field in self.editable_profile_fields:
            
            is_read_only_widget = isinstance(field, (QLineEdit, QTextEdit))
            is_combo_box = isinstance(field, QComboBox)

            if is_read_only_widget:
                field.setReadOnly(read_only)
            elif is_combo_box:
                field.setEnabled(not read_only)

            field.setProperty("readOnly", read_only) 
            self.style().polish(field)


    def enable_edit_mode(self):
        self.set_profile_fields_read_only(False)
        self.upload_button.setVisible(True)
        self.confirm_button.setVisible(True)

    def disable_edit_mode(self):
        self.set_profile_fields_read_only(True)
        self.upload_button.setVisible(False)
        self.confirm_button.setVisible(False)
        self.edit_button.setVisible(True)
        self.load_user_profile()

    def toggle_edit_mode(self):
        if self.is_in_edit_mode:
            print("ยกเลิกการแก้ไขโปรไฟล์")
            self.disable_edit_mode()
            self.is_in_edit_mode = False
        else:
            print("เปิดใช้งานการแก้ไขโปรไฟล์")
            self.enable_edit_mode()
            self.is_in_edit_mode = True

    def select_profile_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Profile Image", 
            "",
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if file_path:
            self.new_profile_img_path = os.path.normpath(file_path)
            
            # --- (แก้ไข) เรียกใช้ create_scaled_pixmap ---
            target_size = 250 # ขนาดที่ตรงกับ QLabel (250x250)
            scaled_pixmap = self.create_scaled_pixmap(self.new_profile_img_path, target_size)
            self.profile_pic_label.setPixmap(scaled_pixmap)
            
            print(f"เลือกรูปโปรไฟล์ใหม่: {self.new_profile_img_path}")

    def save_profile_changes(self):
        try:
            fname = self.profile_fname_field.text()
            lname = self.profile_lname_field.text()
            gender = self.profile_gender_field.currentText() 
            email = self.profile_email_field.text()
            phone = self.profile_phone_field.text()
            address = self.profile_address_field.toPlainText()
            
            image_to_save = self.new_profile_img_path if self.new_profile_img_path else self.current_profile_img_path

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users 
                SET 
                    first_name = ?, 
                    last_name = ?, 
                    gender = ?, 
                    email = ?, 
                    phone = ?, 
                    address = ?, 
                    profile_img = ?
                WHERE 
                    username = ?
            """, (fname, lname, gender, email, phone, address, image_to_save, self.current_username))
            
            conn.commit()
            conn.close()
            
            print(f"อัปเดตโปรไฟล์สำหรับ {self.current_username} สำเร็จ")
            QMessageBox.information(self, "Success", "Profile updated successfully!")

            self.disable_edit_mode()
            
            self.is_in_edit_mode = False 

        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการบันทึกโปรไฟล์: {e}")
            QMessageBox.warning(self, "Error", f"ไม่สามารถบันทึกการเปลี่ยนแปลงโปรไฟล์ได้: {e}")


    def show_profile_page(self):
        self.disable_edit_mode()
        self.load_user_profile()
        
        self.is_in_edit_mode = False 
        
        self.sidebar_stack.setCurrentIndex(1)
        self.main_content_stack.setCurrentIndex(1)

    def show_browse_page(self):
        self.sidebar_stack.setCurrentIndex(0)
        self.main_content_stack.setCurrentIndex(0)

    def handle_logout(self):
        reply = QMessageBox.question(self, 'Logout', 'Are you sure you want to logout?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.logout_requested.emit()
            self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainUserWindow(username="test")
    window.show()
    sys.exit(app.exec())
