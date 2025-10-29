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

        # (เพิ่ม) สถานะสำหรับการกรองและเรียงลำดับ
        self.current_category = "ALL"
        self.current_search_term = ""
        self.current_sort_order = "Newest" # ค่าเริ่มต้นที่แสดงใน QComboBox

        self.setWindowTitle(f"Beyond Comics - Welcome {self.current_username}") 
        self.setGeometry(100, 100, 1920, 1080)
        self.showMaximized()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        #ตรงนี้คือ content พวกคอมมิคทั้งหลาย
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
        # (!!! ใหม่ !!!) สร้าง sidebar สำหรับหน้ารายละเอียด
        self.detail_sidebar = self.create_detail_sidebar() 
        
        self.sidebar_stack.addWidget(self.browse_sidebar)   # Index 0
        self.sidebar_stack.addWidget(self.profile_sidebar)  # Index 1
        # (!!! ใหม่ !!!) เพิ่ม sidebar ใหม่เข้าไปใน stack
        self.sidebar_stack.addWidget(self.detail_sidebar)   # Index 2
        
        self.body_layout.addWidget(self.sidebar_stack) 

        self.main_content_stack = QStackedWidget()
        self.browse_page = self.create_browse_page()
        self.profile_page = self.create_profile_page()
        # (!!! ใหม่ !!!) สร้างหน้าสำหรับรายละเอียดสินค้า
        self.product_detail_page = self.create_product_detail_page() 

        self.main_content_stack.addWidget(self.browse_page)         # Index 0
        self.main_content_stack.addWidget(self.profile_page)        # Index 1
        # (!!! ใหม่ !!!) เพิ่มหน้าใหม่เข้าไปใน stack
        self.main_content_stack.addWidget(self.product_detail_page) # Index 2
        
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
        # (แก้ไข) เชื่อมต่อปุ่มกับฟังก์ชัน filter_products_by_category
        btn_marvel.clicked.connect(lambda: self.filter_products_by_category("MARVEL")) 
        sidebar_layout.addWidget(btn_marvel)

        btn_dc = QPushButton("DC")
        btn_dc.setObjectName("sidebarButton")
        btn_dc.setFixedHeight(button_height)
        # (แก้ไข) เชื่อมต่อปุ่มกับฟังก์ชัน filter_products_by_category
        btn_dc.clicked.connect(lambda: self.filter_products_by_category("DC"))
        sidebar_layout.addWidget(btn_dc)

        btn_image = QPushButton("Image Comics")
        btn_image.setObjectName("sidebarButton")
        btn_image.setFixedHeight(button_height)
        # (แก้ไข) เชื่อมต่อปุ่มกับฟังก์ชัน filter_products_by_category
        # (หมายเหตุ) สมมติว่า category ใน DB คือ "Image Comics"
        btn_image.clicked.connect(lambda: self.filter_products_by_category("Image Comics"))
        sidebar_layout.addWidget(btn_image)
        sidebar_layout.addStretch()
        
        # (แก้ไข) แก้ไขชื่อตัวแปรปุ่ม 'ALL' จาก btn_image เป็น btn_all
        btn_all = QPushButton("ALL")
        btn_all.setObjectName("sidebarButton")
        btn_all.setFixedHeight(button_height)
        # (แก้ไข) เชื่อมต่อปุ่มกับฟังก์ชัน filter_products_by_category
        btn_all.clicked.connect(lambda: self.filter_products_by_category("ALL"))
        sidebar_layout.addWidget(btn_all)
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

    # (!!! ใหม่ !!!)
    # ฟังก์ชันสำหรับสร้าง Sidebar ของหน้า Detail
    def create_detail_sidebar(self):
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("Sidebar") 
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(20, 30, 20, 20)
        sidebar_layout.setSpacing(25)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        button_height = 55

        # ปุ่ม Back (เหมือนในหน้า Profile)
        btn_back = QPushButton("Back")
        btn_back.setObjectName("backsidebarButton")
        btn_back.setFixedHeight(button_height)
        # เชื่อมต่อกับ show_browse_page เพื่อกลับไปหน้า BROWSE
        btn_back.clicked.connect(self.show_browse_page)
        sidebar_layout.addWidget(btn_back)
        
        sidebar_layout.addStretch()
        return sidebar_frame


    def create_browse_page(self):
        main_content_frame = QFrame()
        main_content_frame.setObjectName("MainContent") 
        main_layout = QVBoxLayout(main_content_frame)
        main_layout.setSpacing(20)
        main_layout.addStretch()
        
        # อันนี้คือการปรับ maincontent พวกหน้าคอมมิค ไม่ให้ชิดขอบเกินไป
        main_layout.setContentsMargins(250, 20, 20, 20)
        
        browse_header_layout = QHBoxLayout()
        self.browse_label = QLabel("BROWSE")
        self.browse_label.setObjectName("browseLabel")
        browse_header_layout.addWidget(self.browse_label)
        browse_header_layout.addStretch()
        
        self.sort_combo = QComboBox()
        self.sort_combo.setObjectName("sortCombo")
        self.sort_combo.addItems(["Newest", "Oldest", "A-Z"])
        self.sort_combo.setFixedHeight(35)
        self.sort_combo.currentTextChanged.connect(self.on_sort_order_changed)
        browse_header_layout.addWidget(self.sort_combo)
        
        main_layout.addLayout(browse_header_layout)
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(10)
        
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchBox")
        self.search_input.setPlaceholderText("Search comics...")
        self.search_input.setFixedHeight(40)
        self.search_input.textChanged.connect(self.on_search_text_changed)
        
        self.search_button = QPushButton("Search")
        self.search_button.setObjectName("searchButton")
        self.search_button.setFixedHeight(40)
        self.search_button.clicked.connect(self.on_search_button_clicked)
        
        search_layout.addWidget(self.search_input, stretch=1)
        search_layout.addWidget(self.search_button)
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
        
        self.refresh_comic_grid()
        
        scroll_area.setWidget(scroll_content_widget)
        main_layout.addWidget(scroll_area, stretch=1)
        
        return main_content_frame

    # (ฟังก์ชันใหม่) สำหรับจัดการเมื่อพิมพ์ในช่อง search
    def on_search_text_changed(self, text):
        self.current_search_term = text.strip()
        self.refresh_comic_grid() # เรียกอัปเดต grid

    # (ฟังก์ชันใหม่) สำหรับจัดการเมื่อกดปุ่ม search
    def on_search_button_clicked(self):
        # ดึงค่าล่าสุดจาก search_input (เผื่อ)
        self.current_search_term = self.search_input.text().strip()
        self.refresh_comic_grid() # เรียกอัปเดต grid

    # (ฟังก์ชันใหม่) สำหรับจัดการเมื่อเปลี่ยนการเรียงลำดับ
    def on_sort_order_changed(self, sort_text):
        self.current_sort_order = sort_text
        self.refresh_comic_grid() # เรียกอัปเดต grid

    # (ฟังก์ชันแก้ไข) สำหรับการกรอง category
    def filter_products_by_category(self, category):
        print(f"กำลังกรองสำหรับ: {category}")
        if category == "ALL":
            self.browse_label.setText("BROWSE")
        else:
            # ใช้ .title() หรือ .upper() เพื่อความสวยงาม
            self.browse_label.setText(f"BROWSE - {category.upper()}") 
            
        # (แก้ไข) อัปเดต state และเรียก refresh
        self.current_category = category
        # (เพิ่ม) เมื่อเปลี่ยน category, ให้ล้างช่อง search
        self.current_search_term = ""
        self.search_input.setText("") # อัปเดต UI ช่อง search
        
        self.refresh_comic_grid()

    # (!!! อัปเดต !!!)
    # แก้ไข Query ให้ดึง id และเปลี่ยน QFrame เป็น QPushButton
    def refresh_comic_grid(self):
        # 1. ล้าง grid_layout เก่า
        try:
            while self.grid_layout.count():
                item = self.grid_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
        except Exception as e:
            print(f"เกิดข้อผิดพลาดขณะล้าง grid: {e}")

        # 2. ดึงข้อมูลใหม่ตาม state
        try:
            if not os.path.exists(DB_PATH):
                print(f"ข้อผิดพลาด: ไม่พบไฟล์ DB ที่: {DB_PATH}")
                error_label = QLabel(f"Error: Database not found at\n{DB_PATH}")
                error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.grid_layout.addWidget(error_label, 0, 0)
                return 

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # (อัปเดต Query) 
            base_query = "SELECT name, cover_img, volume_issue, id FROM product"
            where_clauses = []
            params = []

            # 2.1 เพิ่ม Category filter
            if self.current_category != "ALL":
                where_clauses.append("category = ?")
                params.append(self.current_category)
            
            # 2.2 เพิ่ม Search filter (ค้นหาจาก 'name')
            if self.current_search_term:
                where_clauses.append("name LIKE ?")
                params.append(f"{self.current_search_term}%")

            # 2.3 รวม WHERE clauses
            if where_clauses:
                base_query += " WHERE " + " AND ".join(where_clauses)
                
            # 2.4 เพิ่ม Sort order
            if self.current_sort_order == "Newest":
                base_query += " ORDER BY created_at DESC"
            elif self.current_sort_order == "Oldest":
                base_query += " ORDER BY created_at ASC"
            elif self.current_sort_order == "A-Z":
                base_query += " ORDER BY name ASC"
                
            # Debugging: พิมพ์ query ที่จะรัน
            print(f"Executing Query: {base_query} with params: {tuple(params)}")

            cursor.execute(base_query, tuple(params))
            products = cursor.fetchall()
            conn.close()

            # 3. แสดงผลข้อมูล
            if not products:
                no_comics_label = QLabel(f"No comics found.")
                no_comics_label.setObjectName("noComicsLabel")
                no_comics_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.grid_layout.addWidget(no_comics_label, 0, 0)
            
            else:
                card_width = 200
                card_height = 340 
                image_height = 250
                # ปรับ name_height ให้สูงขึ้นสำหรับ Word Wrap (จาก 35 เป็น 50)
                name_height = 50
                volume_height = 25
                
                num_columns = 4 

                for i, (name, cover_img_path, volume_issue, id) in enumerate(products):
                    row = i // num_columns
                    col = i % num_columns

                    # เปลี่ยนจาก QFrame เป็น QPushButton เพื่อให้คลิกได้
                    comic_card = QPushButton() 
                    comic_card.setObjectName("comicCard")
                    comic_card.setFixedSize(card_width, card_height)
                    comic_card.setCursor(Qt.CursorShape.PointingHandCursor) 
                    
                    # สร้าง Layout และใส่ลงใน QPushButton (comic_card)
                    card_layout = QVBoxLayout(comic_card) 
                    card_layout.setContentsMargins(5, 5, 5, 5) 
                    card_layout.setSpacing(5) 

                    card_layout.addStretch(1) 

                    image_label = QLabel()
                    image_label.setObjectName("comicImage")
                    image_label.setAlignment(Qt.AlignmentFlag.AlignCenter) 
                    image_label.setFixedSize(card_width - 10, image_height) 
                    
                    pixmap = None
                    if cover_img_path and os.path.exists(cover_img_path):
                        pixmap = QPixmap(cover_img_path)
                    else:
                        print(f"คำเตือน: ไม่พบรูป comic '{cover_img_path}' สำหรับ '{name}'. ใช้ placeholder")
                        pixmap = QPixmap("src/img/icon/profile.png") 
                        if pixmap.isNull():
                            pixmap = QPixmap(card_width - 10, image_height)
                            pixmap.fill(Qt.GlobalColor.gray)
                    
                    scaled_pixmap = pixmap.scaled(
                        image_label.size(), 
                        Qt.AspectRatioMode.KeepAspectRatio, 
                        Qt.TransformationMode.SmoothTransformation
                    )
                    image_label.setPixmap(scaled_pixmap)
                    
                    card_layout.addWidget(image_label)
                    card_layout.addSpacing(10) # ช่องว่าง 10px ระหว่างรูปภาพกับชื่อ

                    # --- (แก้ไขเพื่อรองรับ Word Wrap) ---
                    name_label = QLabel() 
                    name_label.setObjectName("comicName")
                    name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    name_label.setFixedHeight(name_height)
                    
                    # (สำคัญ) 1. เพิ่ม Tooltip เพื่อให้แสดงชื่อเต็มเมื่อ hover
                    name_label.setToolTip(name) 
                    
                    # (เพิ่ม) 2. เปิดใช้งานการตัดคำ
                    name_label.setWordWrap(True) 
                    
                    # (ตั้งค่า) 3. ตั้งค่าข้อความชื่อเต็ม (ไม่ต้องตัด)
                    name_label.setText(name) 
                    # --- (จบการแก้ไข) ---

                    volume_text = volume_issue if volume_issue else "N/A"
                    volume_label = QLabel(volume_text)
                    volume_label.setObjectName("comicVolume")
                    volume_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    volume_label.setFixedHeight(volume_height)

                    card_layout.addWidget(name_label)
                    card_layout.addWidget(volume_label)
                    
                    card_layout.addStretch(1) 
                    
                    # เชื่อมต่อ Clicked Signal กับฟังก์ชัน show_product_detail_page
                    product_id = id 
                    comic_card.clicked.connect(
                        lambda checked=False, p_id=product_id: self.show_product_detail_page(p_id)
                    )
                    
                    self.grid_layout.addWidget(comic_card, row, col, Qt.AlignmentFlag.AlignTop)

                self.grid_layout.setRowStretch(len(products) // num_columns + 1, 1)
                self.grid_layout.setColumnStretch(num_columns, 1)

        except sqlite3.OperationalError as e:
            print(f"เกิดข้อผิดพลาด SQL: {e}")
            error_text = f"Error executing query: {e}\n"
            if "no such column: id" in str(e):
                error_text += "Please ensure the 'product' table has an 'id' column."
            elif "no such column: created_at" in str(e):
                error_text += "Please ensure the 'product' table has a 'created_at' column."
            elif "no such column: category" in str(e):
                error_text += "Please ensure the 'product' table has a 'category' column."
            
            error_label = QLabel(error_text)
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid_layout.addWidget(error_label, 0, 0)
            
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการโหลด comics: {e}")
            error_label = QLabel(f"Error loading comics:\n{e}")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid_layout.addWidget(error_label, 0, 0)

    
    # (!!! ใหม่ !!!)
    # ฟังก์ชันสร้างหน้า UI สำหรับรายละเอียดสินค้า
    def create_product_detail_page(self):
        detail_frame = QFrame()
        detail_frame.setObjectName("ProductDetailPage")
        
        # ใช้ Layout หลักเป็น QHBoxLayout เพื่อแบ่งซ้าย (รูป) ขวา (ข้อมูล)
        main_detail_layout = QHBoxLayout(detail_frame)
        main_detail_layout.setContentsMargins(350, 40, 40, 40)
        main_detail_layout.setSpacing(30)
        # (!!! แก้ไข !!!) จัดทุกอย่างไปทางขวาใน layout หลัก
        main_detail_layout.setAlignment(Qt.AlignmentFlag.AlignRight) 

        # --- ส่วนด้านซ้าย (รูป) ---
        # (!!! แก้ไข !!!) (เพิ่ม) addStretch เพื่อดันรูปไปทางขวา
        main_detail_layout.addStretch(1) 

        self.detail_cover_label = QLabel("Loading image...")
        self.detail_cover_label.setObjectName("detailCover")
        self.detail_cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # (!!! แก้ไข !!!) ลดขนาดรูปอีก
        self.detail_cover_label.setFixedSize(250, 380) # ขนาดใหม่ที่เล็กลง
        main_detail_layout.addWidget(self.detail_cover_label, 0, Qt.AlignmentFlag.AlignRight) # จัดรูปไปทางขวา

        # --- ส่วนด้านขวา (ข้อมูล) ---
        # (!!! แก้ไข !!!) (เพิ่ม) addStretch เพื่อดัน widget ข้อมูลไปทางขวา (ถ้ามีพื้นที่เหลือ)
        main_detail_layout.addStretch(1) 

        right_info_widget = QWidget()
        # (!!! แก้ไข !!!) กำหนดความกว้างของ Widget ข้อมูล
        right_info_widget.setFixedWidth(500) # กำหนดความกว้างของส่วนข้อมูล
        right_info_layout = QVBoxLayout(right_info_widget)
        right_info_layout.setContentsMargins(0, 0, 0, 0)
        right_info_layout.setSpacing(15)
        # (!!! แก้ไข !!!) จัดชิดขวาในส่วนข้อมูล
        right_info_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight) 

        # ชื่อเรื่อง
        self.detail_name_label = QLabel("Product Name")
        self.detail_name_label.setObjectName("detailName")
        self.detail_name_label.setWordWrap(True)
        # (!!! แก้ไข !!!) จัดชื่อชิดขวา
        self.detail_name_label.setAlignment(Qt.AlignmentFlag.AlignRight) 
        right_info_layout.addWidget(self.detail_name_label)
        
        # เส้นคั่น
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        # (!!! แก้ไข !!!)
        # แก้ไขจาก QFrame.Shape.Sunken เป็น QFrame.Shadow.Sunken
        line.setFrameShadow(QFrame.Shadow.Sunken)
        right_info_layout.addWidget(line)

        # รายละเอียด (Description)
        self.detail_desc_label = QTextEdit()
        self.detail_desc_label.setObjectName("detailDescription")
        self.detail_desc_label.setReadOnly(True)
        self.detail_desc_label.setText("Loading description...")
        self.detail_desc_label.setFixedHeight(250) # จำกัดความสูง
        right_info_layout.addWidget(self.detail_desc_label)

        # ข้อมูลอื่นๆ (ใช้ QFormLayout)
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setSpacing(10)
        # (!!! แก้ไข !!!) จัด Label ไปทางขวา
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight) 
        # (!!! แก้ไข !!!) (เพิ่ม) จัด Field ไปทางขวา
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter) 
        
        self.detail_volume_label = QLabel("N/A")
        self.detail_writer_label = QLabel("N/A")
        self.detail_rated_label = QLabel("N/A")
        self.detail_isbn_label = QLabel("N/A") # เราจะยังใช้ตัวแปรนี้ แต่เปลี่ยนชื่อ Label
        self.detail_stock_label = QLabel("N/A")
        
        # (!!! แก้ไข !!!) (เพิ่ม) จัด Alignment ให้ QLabel เหล่านี้ชิดขวา
        for label in [self.detail_volume_label, self.detail_writer_label, 
                       self.detail_rated_label, self.detail_isbn_label, self.detail_stock_label]:
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        form_layout.addRow(QLabel("Volume/Issue :"), self.detail_volume_label)
        form_layout.addRow(QLabel("Writer :"), self.detail_writer_label)
        form_layout.addRow(QLabel("Rated :"), self.detail_rated_label)
        # (!!! แก้ไข !!!) เปลี่ยนป้ายชื่อจาก "ISBN :" เป็น "ID :"
        form_layout.addRow(QLabel("ID :"), self.detail_isbn_label)
        form_layout.addRow(QLabel("Stock :"), self.detail_stock_label)
        
        right_info_layout.addWidget(form_widget)
        
        # ราคา
        self.detail_price_label = QLabel("Price : 0.00 Bath")
        self.detail_price_label.setObjectName("detailPrice")
        # (!!! แก้ไข !!!) จัดชิดขวา
        self.detail_price_label.setAlignment(Qt.AlignmentFlag.AlignRight) 
        right_info_layout.addWidget(self.detail_price_label)
        
        # ปุ่ม Add to Cart
        self.detail_add_to_cart_button = QPushButton("Add Cart")
        self.detail_add_to_cart_button.setObjectName("addToCartButton")
        self.detail_add_to_cart_button.setFixedHeight(60)
        # (ยังไม่ต้องใส่ฟังก์ชัน)
        # self.detail_add_to_cart_button.clicked.connect(self.add_to_cart_function) 
        right_info_layout.addWidget(self.detail_add_to_cart_button, 0, Qt.AlignmentFlag.AlignRight)

        right_info_layout.addStretch() # ดันทุกอย่างขึ้นไปด้านบน
        
        # (!!! แก้ไข !!!) จัด widget ข้อมูลไปทางขวา
        main_detail_layout.addWidget(right_info_widget, 0, Qt.AlignmentFlag.AlignRight) 

        return detail_frame

    # (!!! ใหม่ !!!)
    # ฟังก์ชันสำหรับโหลดข้อมูลสินค้าจาก DB มาแสดง
    # (!!! แก้ไข !!!) เปลี่ยน product_isbn เป็น product_id และแก้ไขการจัดการ Error
    def load_product_details(self, product_id):
        # รีเซ็ต UI ก่อนโหลดข้อมูลใหม่
        self.detail_name_label.setText("Loading...")
        self.detail_desc_label.setText("Loading details...")
        self.detail_volume_label.setText("N/A")
        self.detail_writer_label.setText("N/A")
        self.detail_rated_label.setText("N/A")
        self.detail_isbn_label.setText("N/A") 
        self.detail_stock_label.setText("N/A")
        self.detail_price_label.setText("Price : N/A")
        
        # (เพิ่ม) ตั้งค่าพื้นหลังเป็นสีขาวทันที
        placeholder_pixmap = QPixmap(self.detail_cover_label.size())
        placeholder_pixmap.fill(Qt.GlobalColor.white)
        self.detail_cover_label.setPixmap(placeholder_pixmap)
        
        try:
            if not os.path.exists(DB_PATH):
                raise FileNotFoundError(f"Database not found at {DB_PATH}")

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # (!!! แก้ไข !!!) เปลี่ยน isbn เป็น id ทั้งใน SELECT และ WHERE
            cursor.execute("""
                SELECT name, description, volume_issue, writer, rated, id, stock, price, cover_img 
                FROM product 
                WHERE id = ?
            """, (product_id,))
            
            product_data = cursor.fetchone()
            conn.close()

            if product_data:
                # (!!! แก้ไข !!!) เปลี่ยน isbn เป็น id
                (name, description, volume_issue, writer, rated, 
                 id, stock, price, cover_img) = product_data
                
                # อัปเดต UI
                self.detail_name_label.setText(name or "N/A")
                self.detail_desc_label.setText(description or "No description available.")
                self.detail_volume_label.setText(volume_issue or "N/A")
                self.detail_writer_label.setText(writer or "N/A")
                self.detail_rated_label.setText(rated or "N/A")
                # (!!! แก้ไข !!!) เปลี่ยนเป็น str(id)
                self.detail_isbn_label.setText(str(id) if id is not None else "N/A")
                self.detail_stock_label.setText(str(stock) if stock is not None else "N/A")
                self.detail_price_label.setText(f"Price : {price:.2f} Bath" if price is not None else "Price : N/A")

                # โหลดรูปภาพปก
                pixmap = None
                if cover_img and os.path.exists(cover_img):
                    pixmap = QPixmap(cover_img)
                else:
                    print(f"คำเตือน: ไม่พบรูป detail '{cover_img}' สำหรับ ID {product_id}. ใช้ placeholder")
                    pixmap = QPixmap("src/img/icon/profile.png") 
                
                if pixmap.isNull():
                    pixmap = QPixmap(self.detail_cover_label.size())
                    pixmap.fill(Qt.GlobalColor.gray) # ถ้า placeholder ก็ยังโหลดไม่ได้ ก็ใช้สีเทา

                # สเกลรูปภาพให้พอดีกับ Label
                scaled_pixmap = pixmap.scaled(
                    self.detail_cover_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.detail_cover_label.setPixmap(scaled_pixmap)

            else:
                # (!!! แก้ไข !!!) ไม่โยน Exception แต่แสดงข้อความแจ้งเตือน
                self.detail_name_label.setText("Product Not Found")
                self.detail_desc_label.setText(f"No product with ID '{product_id}' was found in the database.")
                # ตั้งรูปเป็น placeholder สีขาว
                pixmap = QPixmap(self.detail_cover_label.size())
                pixmap.fill(Qt.GlobalColor.white) # พื้นหลังขาว
                self.detail_cover_label.setPixmap(pixmap)
                print(f"ไม่พบสินค้าที่มี ID: {product_id}")


        except Exception as e:
            # (!!! แก้ไข !!!) ไม่โยน Exception แต่แสดงข้อความแจ้งเตือน
            print(f"เกิดข้อผิดพลาดในการโหลดรายละเอียดสินค้า (ID: {product_id}): {e}")
            self.detail_name_label.setText(f"Error Loading Product")
            self.detail_desc_label.setText(f"An error occurred: {e}. Please try again or check the database.")
            pixmap = QPixmap(self.detail_cover_label.size())
            pixmap.fill(Qt.GlobalColor.lightGray) # สำหรับ Error ทั่วไปใช้สีเทาอ่อน
            self.detail_cover_label.setPixmap(pixmap)


    # (!!! ใหม่ !!!)
    # ฟังก์ชันสำหรับสลับไปหน้า Product Detail
    # (!!! แก้ไข !!!) เปลี่ยน product_isbn เป็น product_id
    def show_product_detail_page(self, product_id):
        # (!!! แก้ไข !!!) อัปเดตข้อความ Print
        print(f"กำลังแสดงรายละเอียดสำหรับ ID: {product_id}")
        
        # 1. โหลดข้อมูลมาก่อน
        # (!!! แก้ไข !!!) ส่ง product_id
        self.load_product_details(product_id)
        
        # 2. สลับ Stacked Widgets ไปยัง Index 2 (หน้าที่เราเพิ่มเข้าไปใหม่)
        self.sidebar_stack.setCurrentIndex(2)
        self.main_content_stack.setCurrentIndex(2)
        
        
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
        self.profile_pic_label.setFixedSize(250, 250) 
        
        self.upload_button = QPushButton("Upload Profile image")
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

    def create_scaled_pixmap(self, image_path, size):
        """
        สร้าง QPixmap สี่เหลี่ยมที่สเกลแล้วจาก image_path ที่กำหนด
        """
        try:
            source_pixmap = QPixmap(image_path)
            if source_pixmap.isNull():
                print(f"คำเตือน: ไม่พบไฟล์รูปภาพที่ '{image_path}', ใช้รูปโปรไฟล์เริ่มต้น")
                source_pixmap = QPixmap("src/img/icon/profile.png")
                if source_pixmap.isNull():
                    print("คำเตือน: ไม่พบรูปโปรไฟล์เริ่มต้น 'src/img/icon/profile.png'")
                    source_pixmap = QPixmap(size, size)
                    source_pixmap.fill(Qt.GlobalColor.gray)

        except Exception as e:
            print(f"เกิดข้อผิดพลาดขณะโหลด QPixmap: {e}")
            source_pixmap = QPixmap(size, size)
            source_pixmap.fill(Qt.GlobalColor.gray)

        scaled_pixmap = source_pixmap.scaled(
            size, size, 
            Qt.AspectRatioMode.IgnoreAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        return scaled_pixmap

    def load_user_profile(self):
        try:
            target_size = 250
            
            if not os.path.exists(DB_PATH):
                print(f"ข้อผิดพลาด: ไม่พบไฟล์ DB ขณะโหลดโปรไฟล์: {DB_PATH}")
                self.profile_username_field.setText(self.current_username)
                self.profile_fname_field.setText("N/A (DB not found)")
                
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

                image_path_to_load = img_path if (img_path and os.path.exists(img_path)) else "src/img/icon/profile.png"
                scaled_pixmap = self.create_scaled_pixmap(image_path_to_load, target_size)
                self.profile_pic_label.setPixmap(scaled_pixmap)
                
            else:
                print(f"ไม่พบผู้ใช้: {self.current_username}")
                self.profile_username_field.setText(self.current_username)
                self.profile_fname_field.setText("N/A")
                self.profile_lname_field.setText("N/A")
                self.profile_gender_field.setCurrentIndex(0)
                
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
            
            target_size = 250
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
        # (เพิ่ม) เมื่อกลับมาหน้า browse, ให้รีเซ็ตเป็น "ALL"
        # และล้างช่อง search
        # หมายเหตุ: หากคุณต้องการให้จำค่า filter/search เดิม ให้ลบบรรทัดล่างนี้
        self.filter_products_by_category("ALL")


    def handle_logout(self):
        reply = QMessageBox.question(self, 'Logout', 'Are you sure you want to logout?',
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                        QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.logout_requested.emit()
            self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # (สำคัญ) ตรวจสอบให้แน่ใจว่าตาราง 'product' ใน DB ของคุณ
    # มีคอลัมน์เหล่านี้ทั้งหมดเพื่อให้โค้ดทำงานได้:
    # - id (สำหรับระบุสินค้า)
    # - name (สำหรับ A-Z และ Search)
    # - category (สำหรับ MARVEL, DC, ...)
    # - created_at (สำหรับ Newest, Oldest)
    # - cover_img (สำหรับแสดงปก)
    # - volume_issue (สำหรับแสดงใน grid)
    # - description (สำหรับหน้ารายละเอียด)
    # - writer (สำหรับหน้ารายละเอียด)
    # - rated (สำหรับหน้ารายละเอียด)
    # - stock (สำหรับหน้ารายละเอียด)
    # - price (สำหรับหน้ารายละเอียด)
    #
    window = MainUserWindow(username="test") 
    window.show()
    sys.exit(app.exec())