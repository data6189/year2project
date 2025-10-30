import sys
import os
import sqlite3
import datetime # (!!! ใหม่ !!!) เพิ่ม import นี้
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

# (สำคัญ) ตรวจสอบให้แน่ใจว่าเส้นทางไปยังฐานข้อมูลถูกต้อง
DB_PATH = "src/database/thisshop.db" 

# (!!! แก้ไข !!!) เปลี่ยนชื่อคลาสเป็น MainAdminWindow
class MainAdminWindow(QMainWindow):
    logout_requested = pyqtSignal()
    
    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.current_username = username 
        
        self.new_profile_img_path = None # เส้นทางรูปโปรไฟล์ใหม่ที่เลือก
        self.current_profile_img_path = None # เส้นทางรูปโปรไฟล์ปัจจุบันจาก DB
        self.editable_profile_fields = [] # รายการช่องที่แก้ไขได้

        self.is_in_edit_mode = False

        # สถานะสำหรับการกรองและเรียงลำดับ
        self.current_category = "ALL"
        self.current_search_term = ""
        self.current_sort_order = "Newest" # ค่าเริ่มต้นที่แสดงใน QComboBox
        
        self.current_detail_product_id = None 
        self.current_detail_stock = 0
        
        # (!!! ใหม่ !!!) ตัวแปรสำหรับเก็บที่อยู่รูป comic ที่จะเพิ่ม
        self.new_comic_img_path = None

        self.setWindowTitle(f"Beyond Comics - ADMIN PANEL - {self.current_username}") 
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
        self.detail_sidebar = self.create_detail_sidebar() 
        self.add_comic_sidebar = self.create_add_comic_sidebar() # (!!! ใหม่ !!!)
        
        self.sidebar_stack.addWidget(self.browse_sidebar)     # Index 0
        self.sidebar_stack.addWidget(self.profile_sidebar)    # Index 1
        self.sidebar_stack.addWidget(self.detail_sidebar)     # Index 2
        self.sidebar_stack.addWidget(self.add_comic_sidebar)  # Index 3 (!!! ใหม่ !!!)
        
        self.body_layout.addWidget(self.sidebar_stack) 

        self.main_content_stack = QStackedWidget()
        self.browse_page = self.create_browse_page()
        self.profile_page = self.create_profile_page()
        self.product_detail_page = self.create_product_detail_page() 
        self.add_comic_page = self.create_add_comic_page() # (!!! ใหม่ !!!)

        self.main_content_stack.addWidget(self.browse_page)         # Index 0
        self.main_content_stack.addWidget(self.profile_page)        # Index 1
        self.main_content_stack.addWidget(self.product_detail_page) # Index 2
        self.main_content_stack.addWidget(self.add_comic_page)      # Index 3 (!!! ใหม่ !!!)
        
        self.body_layout.addWidget(self.main_content_stack, 1)

        self.main_layout.addWidget(self.body_widget, 1)

        self.load_stylesheet("src/styles/mainadmin.qss") 
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

    # (!!! แก้ไข !!!)
    # ลบปุ่ม "CART" และเพิ่มปุ่ม "ADD COMIC"
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
        
        # --- (!!! ส่วนของปุ่ม CART ถูกลบออก !!!) ---
        
        # (!!! ใหม่ !!!) ปุ่ม ADD COMIC
        try:
            add_comic_icon = QIcon("src/img/icon/add.png") 
        except:
            add_comic_icon = QIcon() 
            
        add_comic_button = QPushButton(" ADD COMIC")
        add_comic_button.setIcon(add_comic_icon)
        add_comic_button.setIconSize(QSize(50, 50)) 
        add_comic_button.setObjectName("navButton")
        add_comic_button.setFixedSize(button_width, button_height)
        
        # (!!! แก้ไข !!!) เปลี่ยนจาก placeholder_add_comic
        add_comic_button.clicked.connect(self.show_add_comic_page) 
        
        header_layout.addWidget(add_comic_button) 

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
        btn_marvel.clicked.connect(lambda: self.filter_products_by_category("MARVEL")) 
        sidebar_layout.addWidget(btn_marvel)

        btn_dc = QPushButton("DC")
        btn_dc.setObjectName("sidebarButton")
        btn_dc.setFixedHeight(button_height)
        btn_dc.clicked.connect(lambda: self.filter_products_by_category("DC"))
        sidebar_layout.addWidget(btn_dc)

        btn_image = QPushButton("Image Comics")
        btn_image.setObjectName("sidebarButton")
        btn_image.setFixedHeight(button_height)
        btn_image.clicked.connect(lambda: self.filter_products_by_category("Image Comics"))
        sidebar_layout.addWidget(btn_image)
        sidebar_layout.addStretch()
        
        btn_all = QPushButton("ALL")
        btn_all.setObjectName("sidebarButton")
        btn_all.setFixedHeight(button_height)
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

    def create_detail_sidebar(self):
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("Sidebar") 
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(20, 30, 20, 20)
        sidebar_layout.setSpacing(25)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        button_height = 55

        btn_back = QPushButton("Back")
        btn_back.setObjectName("backsidebarButton")
        btn_back.setFixedHeight(button_height)
        btn_back.clicked.connect(self.show_browse_page)
        sidebar_layout.addWidget(btn_back)
        
        sidebar_layout.addStretch()
        return sidebar_frame

    # (!!! ใหม่ !!!)
    # สร้าง Sidebar สำหรับหน้า Add Comic
    def create_add_comic_sidebar(self):
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("Sidebar") 
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(20, 30, 20, 20)
        sidebar_layout.setSpacing(25)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        button_height = 55

        # (ปุ่ม Add comic นี้จะกดไม่ได้ มีไว้โชว์เฉยๆ)
        btn_add_comic = QPushButton("Add comic")
        btn_add_comic.setObjectName("profilesidebarButton") # (ใช้ style เดียวกับปุ่ม profile)
        btn_add_comic.setFixedHeight(button_height)
        btn_add_comic.setEnabled(False) 
        sidebar_layout.addWidget(btn_add_comic)

        # (ปุ่ม Back เพื่อกลับไปหน้า Browse)
        btn_back = QPushButton("Back")
        btn_back.setObjectName("backsidebarButton")
        btn_back.setFixedHeight(button_height)
        btn_back.clicked.connect(self.show_browse_page) 
        sidebar_layout.addWidget(btn_back)
        
        sidebar_layout.addStretch()
        return sidebar_frame

    # (!!! ใหม่ !!!)
    # สร้างหน้า UI สำหรับ Add Comic
    def create_add_comic_page(self):
        add_comic_frame = QFrame()
        add_comic_frame.setObjectName("AddComicPage") 
        
        main_layout = QHBoxLayout(add_comic_frame)
        main_layout.setContentsMargins(300, 50, 50, 50) 
        main_layout.setSpacing(30)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- ส่วนซ้าย: อัปโหลดรูป ---
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setSpacing(10)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.add_comic_img_preview = QLabel("Upload Comic image")
        self.add_comic_img_preview.setObjectName("addComicImgPreview")
        self.add_comic_img_preview.setFixedSize(250, 380) 
        self.add_comic_img_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.add_comic_img_preview.setStyleSheet("background-color: white; border: 1px solid #ccc;") 
        
        self.add_comic_upload_button = QPushButton(" Upload Comic image")
        try:
            upload_icon = QIcon(QPixmap("src/img/icon/upload.png")) 
            self.add_comic_upload_button.setIcon(upload_icon)
            self.add_comic_upload_button.setIconSize(QSize(40, 40))
        except:
            pass
        self.add_comic_upload_button.setObjectName("uploadButton") 
        self.add_comic_upload_button.setFixedHeight(40)
        self.add_comic_upload_button.clicked.connect(self.select_new_comic_image)
        
        left_layout.addWidget(self.add_comic_img_preview)
        left_layout.addWidget(self.add_comic_upload_button)
        main_layout.addWidget(left_container, 0)

        # --- ส่วนขวา: ฟอร์มข้อมูล (ปรับ Layout) ---
        
        # (1. สร้าง Container หลักด้านขวา ให้ใช้ QVBoxLayout)
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container) # (Layout แนวตั้ง)
        right_layout.setSpacing(15)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # (2. สร้าง Frame สำหรับ QFormLayout โดยเฉพาะ)
        right_form_frame = QFrame()
        right_form_frame.setObjectName("addComicFormFrame")
        form_layout = QFormLayout(right_form_frame) # (เอา Form ใส่ใน Frame นี้)
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        # (สร้าง Widgets สำหรับฟอร์ม - เหมือนเดิม)
        self.add_comic_name = QLineEdit()
        self.add_comic_volume = QLineEdit()
        self.add_comic_desc = QTextEdit()
        self.add_comic_writer = QLineEdit()
        self.add_comic_rated = QLineEdit()
        self.add_comic_isbn = QLineEdit()
        self.add_comic_category = QComboBox()
        self.add_comic_category.addItems(["MARVEL", "DC", "Image Comics"])
        self.add_comic_stock = QLineEdit()
        self.add_comic_price = QLineEdit()
        
        self.add_comic_desc.setFixedHeight(120)
        
        fields_to_style = [
            self.add_comic_name, self.add_comic_volume, self.add_comic_desc,
            self.add_comic_writer, self.add_comic_rated, self.add_comic_isbn,
            self.add_comic_category, self.add_comic_stock, self.add_comic_price
        ]
        
        for field in fields_to_style:
            field.setObjectName("addComicField")

        self.add_comic_name.setPlaceholderText("Enter comic name")
        self.add_comic_volume.setPlaceholderText("Enter volume or issue #")
        self.add_comic_writer.setPlaceholderText("Enter writer(s)")
        self.add_comic_rated.setPlaceholderText("Enter rating (e.g., T+)")
        self.add_comic_isbn.setPlaceholderText("Enter ISBN (must be unique ID)")
        self.add_comic_stock.setPlaceholderText("Enter stock quantity")
        self.add_comic_price.setPlaceholderText("Enter price (e.g., 150.00)")
        
        # (เพิ่มแถวใน Form - เหมือนเดิม)
        form_layout.addRow(QLabel("Name :"), self.add_comic_name)
        form_layout.addRow(QLabel("Volume/Issue :"), self.add_comic_volume)
        form_layout.addRow(QLabel("Description :"), self.add_comic_desc)
        form_layout.addRow(QLabel("Writer :"), self.add_comic_writer)
        form_layout.addRow(QLabel("Rated :"), self.add_comic_rated)
        form_layout.addRow(QLabel("ISBN :"), self.add_comic_isbn)
        form_layout.addRow(QLabel("Category :"), self.add_comic_category)
        form_layout.addRow(QLabel("Stock :"), self.add_comic_stock)
        form_layout.addRow(QLabel("Price :"), self.add_comic_price)
        
        # (3. เพิ่ม Frame ที่มี Form ลงใน right_layout)
        right_layout.addWidget(right_form_frame)

        # (4. สร้างปุ่ม Add Product)
        self.add_product_button = QPushButton("Add Product")
        self.add_product_button.setObjectName("addProductButton")
        self.add_product_button.setFixedHeight(50)
        self.add_product_button.clicked.connect(self.save_new_comic)
        
        # (กำหนดความกว้างคงที่ให้ปุ่ม)
        self.add_product_button.setFixedWidth(200) 
        
        # (5. เพิ่มปุ่ม Add Product เข้าไปใน right_layout)
        
        # (!!! นี่คือการแก้ไขที่สำคัญ: เปลี่ยนจาก AlignLeft เป็น AlignRight !!!)
        right_layout.addWidget(self.add_product_button, 0, Qt.AlignmentFlag.AlignRight)

        # (6. เพิ่ม Stretch เพื่อดันทุกอย่างขึ้นบน)
        right_layout.addStretch(1)

        # (7. เพิ่ม right_container (ที่มี VBox) เข้าไปใน main_layout)
        main_layout.addWidget(right_container, 1)

        return add_comic_frame


    def create_browse_page(self):
        main_content_frame = QFrame()
        main_content_frame.setObjectName("MainContent") 
        main_layout = QVBoxLayout(main_content_frame)
        main_layout.setSpacing(20)
        main_layout.addStretch()
        
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

    def on_search_text_changed(self, text):
        self.current_search_term = text.strip()
        self.refresh_comic_grid() 

    def on_search_button_clicked(self):
        self.current_search_term = self.search_input.text().strip()
        self.refresh_comic_grid() 

    def on_sort_order_changed(self, sort_text):
        self.current_sort_order = sort_text
        self.refresh_comic_grid() 

    def filter_products_by_category(self, category):
        print(f"กำลังกรองสำหรับ: {category}")
        if category == "ALL":
            self.browse_label.setText("BROWSE")
        else:
            self.browse_label.setText(f"BROWSE - {category.upper()}") 
            
        self.current_category = category
        self.current_search_term = ""
        self.search_input.setText("") 
        
        self.refresh_comic_grid()

    def refresh_comic_grid(self):
        try:
            while self.grid_layout.count():
                item = self.grid_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
        except Exception as e:
            print(f"เกิดข้อผิดพลาดขณะล้าง grid: {e}")

        try:
            if not os.path.exists(DB_PATH):
                print(f"ข้อผิดพลาด: ไม่พบไฟล์ DB ที่: {DB_PATH}")
                error_label = QLabel(f"Error: Database not found at\n{DB_PATH}")
                error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.grid_layout.addWidget(error_label, 0, 0)
                return 

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            base_query = "SELECT name, cover_img, volume_issue, id FROM product"
            where_clauses = []
            params = []

            if self.current_category != "ALL":
                where_clauses.append("category = ?")
                params.append(self.current_category)
            
            if self.current_search_term:
                where_clauses.append("name LIKE ?")
                params.append(f"{self.current_search_term}%")

            if where_clauses:
                base_query += " WHERE " + " AND ".join(where_clauses)
                
            if self.current_sort_order == "Newest":
                base_query += " ORDER BY created_at DESC"
            elif self.current_sort_order == "Oldest":
                base_query += " ORDER BY created_at ASC"
            elif self.current_sort_order == "A-Z":
                base_query += " ORDER BY name ASC"
                
            print(f"Executing Query: {base_query} with params: {tuple(params)}")

            cursor.execute(base_query, tuple(params))
            products = cursor.fetchall()
            conn.close()

            if not products:
                no_comics_label = QLabel(f"No comics found.")
                no_comics_label.setObjectName("noComicsLabel")
                no_comics_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.grid_layout.addWidget(no_comics_label, 0, 0)
            
            else:
                card_width = 200
                card_height = 340 
                image_height = 250
                name_height = 50
                volume_height = 25
                
                num_columns = 4 

                for i, (name, cover_img_path, volume_issue, id) in enumerate(products):
                    row = i // num_columns
                    col = i % num_columns

                    comic_card = QPushButton() 
                    comic_card.setObjectName("comicCard")
                    comic_card.setFixedSize(card_width, card_height)
                    comic_card.setCursor(Qt.CursorShape.PointingHandCursor) 
                    
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
                    card_layout.addSpacing(10)

                    name_label = QLabel() 
                    name_label.setObjectName("comicName")
                    name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    name_label.setFixedHeight(name_height)
                    name_label.setToolTip(name) 
                    name_label.setWordWrap(True) 
                    name_label.setText(name) 

                    volume_text = volume_issue if volume_issue else "N/A"
                    volume_label = QLabel(volume_text)
                    volume_label.setObjectName("comicVolume")
                    volume_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    volume_label.setFixedHeight(volume_height)

                    card_layout.addWidget(name_label)
                    card_layout.addWidget(volume_label)
                    
                    card_layout.addStretch(1) 
                    
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

    
    # (!!! แก้ไข !!!)
    # ลบส่วน "QUANTITY" และปุ่ม "Add to Cart"
    def create_product_detail_page(self):
        detail_frame = QFrame()
        detail_frame.setObjectName("ProductDetailPage")
        
        main_detail_layout = QHBoxLayout(detail_frame)
        main_detail_layout.setContentsMargins(350, 40, 40, 40)
        main_detail_layout.setSpacing(30)
        main_detail_layout.setAlignment(Qt.AlignmentFlag.AlignRight) 

        main_detail_layout.addStretch(1) 

        self.detail_cover_label = QLabel("Loading image...")
        self.detail_cover_label.setObjectName("detailCover")
        self.detail_cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_cover_label.setFixedSize(250, 380) 
        main_detail_layout.addWidget(self.detail_cover_label, 0, Qt.AlignmentFlag.AlignRight)

        main_detail_layout.addStretch(1) 

        right_info_widget = QWidget()
        right_info_widget.setFixedWidth(500) 
        right_info_layout = QVBoxLayout(right_info_widget)
        right_info_layout.setContentsMargins(0, 0, 0, 0)
        right_info_layout.setSpacing(15)
        right_info_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight) 

        self.detail_name_label = QLabel("Product Name")
        self.detail_name_label.setObjectName("detailName")
        self.detail_name_label.setWordWrap(True)
        self.detail_name_label.setAlignment(Qt.AlignmentFlag.AlignLeft) 
        right_info_layout.addWidget(self.detail_name_label)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        right_info_layout.addWidget(line)

        self.detail_desc_label = QTextEdit()
        self.detail_desc_label.setObjectName("detailDescription")
        self.detail_desc_label.setReadOnly(True)
        self.detail_desc_label.setText("Loading description...")
        self.detail_desc_label.setFixedHeight(150) 
        right_info_layout.addWidget(self.detail_desc_label)

        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setSpacing(5)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft) 
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter) 
        
        self.detail_volume_label = QLabel("N/A")
        self.detail_writer_label = QLabel("N/A")
        self.detail_rated_label = QLabel("N/A")
        self.detail_isbn_label = QLabel("N/A") 
        self.detail_stock_label = QLabel("N/A")
        
        for label in [self.detail_volume_label, self.detail_writer_label, 
                      self.detail_rated_label, self.detail_isbn_label, self.detail_stock_label]:
            label.setObjectName("detailFormValue") 
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        form_rows_data = [
            ("Volume/Issue :", self.detail_volume_label),
            ("Writer :", self.detail_writer_label),
            ("Rated :", self.detail_rated_label),
            ("ISBN :", self.detail_isbn_label),
            ("Stock :", self.detail_stock_label)
        ]

        for label_text, value_widget in form_rows_data:
            label_header = QLabel(label_text)
            label_header.setObjectName("detailFormLabel") 
            form_layout.addRow(label_header, value_widget)
        
        right_info_layout.addWidget(form_widget)
        
        self.detail_price_label = QLabel("Price : 0.00 THB")
        self.detail_price_label.setObjectName("detailPrice")
        self.detail_price_label.setAlignment(Qt.AlignmentFlag.AlignRight) 
        right_info_layout.addWidget(self.detail_price_label)
        
        # --- (!!! ส่วนของปุ่ม CART, QSpinBox, Label QUANTITY ถูกลบออก !!!) ---
        
        right_info_layout.addStretch() 
        
        main_detail_layout.addWidget(right_info_widget, 0, Qt.AlignmentFlag.AlignRight) 

        return detail_frame

    # (!!! แก้ไข !!!)
    # ลบ Logic ที่ควบคุมปุ่ม Cart และ Spinbox
    def load_product_details(self, product_id):
        self.detail_name_label.setText("Loading...")
        self.detail_desc_label.setText("Loading details...")
        self.detail_volume_label.setText("N/A")
        self.detail_writer_label.setText("N/A")
        self.detail_rated_label.setText("N/A")
        self.detail_isbn_label.setText("N/A") 
        self.detail_stock_label.setText("N/A")
        self.detail_price_label.setText("Price : N/A")
        
        self.current_detail_product_id = None
        self.current_detail_stock = 0
        
        # --- (!!! ลบส่วนที่ควบคุม UI ของ Cart !!!) ---
        
        placeholder_pixmap = QPixmap(self.detail_cover_label.size())
        placeholder_pixmap.fill(Qt.GlobalColor.white)
        self.detail_cover_label.setPixmap(placeholder_pixmap)
        
        try:
            if not os.path.exists(DB_PATH):
                raise FileNotFoundError(f"Database not found at {DB_PATH}")

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT name, description, volume_issue, writer, rated, id, stock, price, cover_img 
                FROM product 
                WHERE id = ?
            """, (product_id,))
            
            product_data = cursor.fetchone()
            conn.close()

            if product_data:
                (name, description, volume_issue, writer, rated, 
                 id, stock, price, cover_img) = product_data
                
                self.detail_name_label.setText(name or "N/A")
                self.detail_desc_label.setText(description or "No description available.")
                self.detail_volume_label.setText(volume_issue or "N/A")
                self.detail_writer_label.setText(writer or "N/A")
                self.detail_rated_label.setText(rated or "N/A")
                self.detail_isbn_label.setText(str(id) if id is not None else "N/A")
                
                stock_available = stock if stock is not None else 0
                self.detail_stock_label.setText(str(stock_available))
                self.detail_price_label.setText(f"Price : {price:.2f} THB" if price is not None else "Price : N/A")

                self.current_detail_product_id = id
                self.current_detail_stock = stock_available

                # --- (!!! ลบ Logic การควบคุมปุ่ม Cart/Spinbox ตาม Stock !!!) ---

                pixmap = None
                if cover_img and os.path.exists(cover_img):
                    pixmap = QPixmap(cover_img)
                else:
                    print(f"คำเตือน: ไม่พบรูป detail '{cover_img}' สำหรับ ID {product_id}. ใช้ placeholder")
                    pixmap = QPixmap("src/img/icon/profile.png") 
                
                if pixmap.isNull():
                    pixmap = QPixmap(self.detail_cover_label.size())
                    pixmap.fill(Qt.GlobalColor.gray) 

                scaled_pixmap = pixmap.scaled(
                    self.detail_cover_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.detail_cover_label.setPixmap(scaled_pixmap)

            else:
                self.detail_name_label.setText("Product Not Found")
                self.detail_desc_label.setText(f"No product with ID '{product_id}' was found in the database.")
                pixmap = QPixmap(self.detail_cover_label.size())
                pixmap.fill(Qt.GlobalColor.white) 
                self.detail_cover_label.setPixmap(pixmap)
                print(f"ไม่พบสินค้าที่มี ID: {product_id}")
                
                # --- (!!! ลบส่วนที่ควบคุม UI ของ Cart !!!) ---

        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการโหลดรายละเอียดสินค้า (ID: {product_id}): {e}")
            self.detail_name_label.setText(f"Error Loading Product")
            self.detail_desc_label.setText(f"An error occurred: {e}. Please try again or check the database.")
            pixmap = QPixmap(self.detail_cover_label.size())
            pixmap.fill(Qt.GlobalColor.lightGray) 
            self.detail_cover_label.setPixmap(pixmap)
            
            # --- (!!! ลบส่วนที่ควบคุม UI ของ Cart !!!) ---

    def show_product_detail_page(self, product_id):
        print(f"กำลังแสดงรายละเอียดสำหรับ ID: {product_id}")
        
        self.load_product_details(product_id)
        
        self.sidebar_stack.setCurrentIndex(2)
        self.main_content_stack.setCurrentIndex(2)
        
    # --- (!!! ลบฟังก์ชัน handle_add_to_cart ทั้งหมด !!!) ---

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
        
        # (แก้ไข) เปลี่ยนเป็น KeepAspectRatio เพื่อไม่ให้รูปบิดเบี้ยว
        # (หมายเหตุ: create_scaled_pixmap นี้ใช้สำหรับ profile ที่เป็นสี่เหลี่ยมจัตุรัส)
        # (เราจะใช้ logic ที่ต่างกันเล็กน้อยสำหรับปก comic)
        scaled_pixmap = source_pixmap.scaled(
            size, size, 
            Qt.AspectRatioMode.IgnoreAspectRatio, # (อันนี้สำหรับ profile ถูกแล้ว)
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
        self.filter_products_by_category("ALL") # (รีเฟรช grid ทุกครั้งที่กลับมา)


    def handle_logout(self):
        reply = QMessageBox.question(self, 'Logout', 'Are you sure you want to logout?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.logout_requested.emit()
            self.close()

    # (!!! ลบ !!!)
    # (ฟังก์ชัน Placeholder ถูกลบออก)
    # def placeholder_add_comic(self):
    #     ...

    # (!!! ใหม่ !!!)
    # ฟังก์ชันสำหรับสลับไปหน้า Add Comic
    def show_add_comic_page(self):
        print("กำลังแสดงหน้า Add Comic")
        self.clear_add_comic_form() # (ล้างฟอร์มทุกครั้งที่เปิด)
        self.sidebar_stack.setCurrentIndex(3)
        self.main_content_stack.setCurrentIndex(3)

    # (!!! ใหม่ !!!)
    # ฟังก์ชันสำหรับล้างฟอร์ม Add Comic
    def clear_add_comic_form(self):
        self.add_comic_name.clear()
        self.add_comic_volume.clear()
        self.add_comic_desc.clear()
        self.add_comic_writer.clear()
        self.add_comic_rated.clear()
        self.add_comic_isbn.clear()
        self.add_comic_category.setCurrentIndex(0)
        self.add_comic_stock.clear()
        self.add_comic_price.clear()
        
        self.new_comic_img_path = None
        self.add_comic_img_preview.clear() # (ล้างรูป)
        self.add_comic_img_preview.setText("Upload Comic image") # (ใส่ข้อความกลับไป)
        # (คืน style พื้นหลังสีขาว)
        self.add_comic_img_preview.setStyleSheet("background-color: white; border: 1px solid #ccc;")

    # (!!! ใหม่ !!!)
    # ฟังก์ชันสำหรับเลือกรูปปก Comic
    def select_new_comic_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Comic Cover Image", 
            "",
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if file_path:
            self.new_comic_img_path = os.path.normpath(file_path)
            
            try:
                target_size = self.add_comic_img_preview.size()
                pixmap = QPixmap(self.new_comic_img_path)
                
                # (ใช้ KeepAspectRatio เพื่อให้ปก comic ไม่บิดเบี้ยว)
                scaled_pixmap = pixmap.scaled(
                    target_size, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                
                self.add_comic_img_preview.setPixmap(scaled_pixmap)
                self.add_comic_img_preview.setText("") # (ลบข้อความ placeholder)
            except Exception as e:
                print(f"Error loading new comic image: {e}")
                self.add_comic_img_preview.setText("Error loading image")
                self.new_comic_img_path = None
                
            print(f"เลือกรูป comic ใหม่: {self.new_comic_img_path}")

    # (!!! ใหม่ !!!)
    # ฟังก์ชันสำหรับบันทึก Comic ใหม่ลง DB
    def save_new_comic(self):
        try:
            # 1. ดึงข้อมูลจากฟอร์ม
            name = self.add_comic_name.text().strip()
            volume = self.add_comic_volume.text().strip()
            desc = self.add_comic_desc.toPlainText().strip()
            writer = self.add_comic_writer.text().strip()
            rated = self.add_comic_rated.text().strip()
            isbn_str = self.add_comic_isbn.text().strip() # (นี่คือ ID)
            category = self.add_comic_category.currentText()
            stock_str = self.add_comic_stock.text().strip()
            price_str = self.add_comic_price.text().strip()
            img_path = self.new_comic_img_path

            # 2. ตรวจสอบข้อมูลเบื้องต้น
            if not all([name, isbn_str, stock_str, price_str, img_path]):
                QMessageBox.warning(self, "Missing Information", 
                                    "Please fill in all fields (Name, ISBN, Stock, Price) and upload an image.")
                return

            # 3. แปลงค่าและตรวจสอบตัวเลข
            try:
                # (ISBN/ID ควรเป็นตัวเลข ตามโครงสร้าง DB ที่มีอยู่)
                id_val = int(isbn_str) 
                stock = int(stock_str)
                price = float(price_str)
                
                if stock < 0 or price < 0:
                    raise ValueError("Stock and Price cannot be negative.")

            except ValueError as e:
                print(f"Validation Error: {e}")
                QMessageBox.warning(self, "Invalid Input", 
                                    f"Please enter valid numbers for ISBN, Stock, and Price.\n(Error: {e})")
                return

            # (ดึงเวลาปัจจุบัน)
            created_at = datetime.datetime.now().isoformat()

            # 4. เชื่อมต่อ DB และ INSERT
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # (ตรวจสอบว่า ID/ISBN ซ้ำหรือไม่)
            cursor.execute("SELECT 1 FROM product WHERE id = ?", (id_val,))
            if cursor.fetchone():
                QMessageBox.warning(self, "Duplicate Entry", 
                                    "A product with this ISBN (ID) already exists. Please use a unique ID.")
                conn.close()
                return

            # (INSERT ข้อมูลใหม่)
            cursor.execute("""
                INSERT INTO product (
                    id, name, volume_issue, description, writer, rated, 
                    category, stock, price, cover_img, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                id_val, name, volume, desc, writer, rated, 
                category, stock, price, img_path, created_at
            ))
            
            conn.commit()
            conn.close()
            
            # 5. แจ้งผลและกลับไปหน้า Browse
            print(f"เพิ่ม comic '{name}' (ID: {id_val}) สำเร็จ")
            QMessageBox.information(self, "Success", "New comic added successfully!")
            
            self.show_browse_page() # (กลับไปหน้า browse)

        except sqlite3.IntegrityError:
             QMessageBox.warning(self, "Database Error", 
                                 "An error occurred (IntegrityError). This ISBN (ID) might already exist.")
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการบันทึก comic: {e}")
            QMessageBox.warning(self, "Error", f"Could not save new comic: {e}")


# (!!! ใหม่ !!!)
# ฟังก์ชันสำหรับจำลองการตรวจสอบสิทธิ์ Admin
def check_admin_role(username):
    """
    (ฟังก์ชันตัวอย่าง) ตรวจสอบว่าผู้ใช้เป็น admin หรือไม่
    ในแอปจริง, หน้าต่าง Login จะเป็นผู้เรียกใช้ Logic นี้
    (และควรตรวจสอบรหัสผ่านด้วย)
    """
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}. Cannot verify admin role.")
        return False
        
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # (สำคัญ) ตรวจสอบทั้ง username และ role = 'admin'
        cursor.execute(
            "SELECT role FROM users WHERE username = ? AND role = 'admin'", 
            (username,)
        )
        admin_user = cursor.fetchone()
        
        if admin_user:
            print(f"Verification successful: {username} is an admin.")
            return True
        else:
            print(f"Verification failed: {username} is not an admin or does not exist.")
            return False
            
    except sqlite3.Error as e:
        print(f"Error checking admin role: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    
    window = MainAdminWindow(username="data6189") 
    window.show()
    sys.exit(app.exec())