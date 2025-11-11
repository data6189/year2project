import sys
import os
import sqlite3
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

DB_PATH = "src/database/thisshop.db" 
now = datetime.now()

# --- IMPORT สำหรับ Info Window ---
feedbackWindow = None  # กำหนดค่าเริ่มต้นเป็น None ป้องกัน NameError
try:
    from feedback_window import feedbackWindow
except ImportError:
    print("Warning: ไม่สามารถ import feedbackWindow ได้ กรุณาตรวจสอบว่าไฟล์ feedback_window.py อยู่ในโฟลเดอร์เดียวกัน")
# --------------------------------


class MainAdminWindow(QMainWindow):
    logout_requested = pyqtSignal()
    
    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.current_username = username 
        
        self.new_profile_img_path = None
        self.current_profile_img_path = None
        self.editable_profile_fields = []

        self.is_in_edit_mode = False

        self.current_category = "ALL"
        self.current_search_term = ""
        self.current_sort_order = "Newest"
        
        self.current_detail_product_id = None 
        self.current_detail_stock = 0
        
        self.new_comic_img_path = None
        
        # --- เพิ่มส่วนนี้สำหรับ Product Detail Edit ---
        self.is_product_edit_mode = False
        self.detail_new_img_path = None
        self.current_detail_img_path = None
        # -------------------------------------------

        self.setWindowTitle(f"Beyond Comics - Admin : {self.current_username}") 
        self.showMaximized()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.header_frame = self.create_header()
        self.main_layout.addWidget(self.header_frame)
        self.create_feedback_button()

        self.body_widget = QWidget()
        self.body_layout = QHBoxLayout(self.body_widget)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(0)

        self.sidebar_stack = QStackedWidget()
        self.sidebar_stack.setFixedWidth(260)
        
        self.browse_sidebar = self.create_browse_sidebar()
        self.profile_sidebar = self.create_profile_sidebar()
        self.detail_sidebar = self.create_detail_sidebar() 
        self.add_comic_sidebar = self.create_add_comic_sidebar()
        self.orders_sidebar = self.create_orders_sidebar()
        self.order_details_sidebar = self.create_order_details_sidebar()
        self.sales_sidebar = self.create_sales_sidebar() # [NEW]
        
        self.sidebar_stack.addWidget(self.browse_sidebar)       # Index 0
        self.sidebar_stack.addWidget(self.profile_sidebar)      # Index 1
        self.sidebar_stack.addWidget(self.detail_sidebar)       # Index 2
        self.sidebar_stack.addWidget(self.add_comic_sidebar)    # Index 3
        self.sidebar_stack.addWidget(self.orders_sidebar)       # Index 4
        self.sidebar_stack.addWidget(self.order_details_sidebar) # Index 5
        self.sidebar_stack.addWidget(self.sales_sidebar)         # Index 6 [NEW]
        
        self.body_layout.addWidget(self.sidebar_stack) 

        self.main_content_stack = QStackedWidget()
        self.browse_page = self.create_browse_page()
        self.profile_page = self.create_profile_page()
        self.product_detail_page = self.create_product_detail_page() 
        self.add_comic_page = self.create_add_comic_page()
        self.orders_page = self.create_orders_page()
        self.order_details_page = self.create_order_details_page()
        self.sales_page = self.create_sales_page() # [NEW]

        self.main_content_stack.addWidget(self.browse_page)         # Index 0
        self.main_content_stack.addWidget(self.profile_page)        # Index 1
        self.main_content_stack.addWidget(self.product_detail_page) # Index 2
        self.main_content_stack.addWidget(self.add_comic_page)      # Index 3
        self.main_content_stack.addWidget(self.orders_page)         # Index 4
        self.main_content_stack.addWidget(self.order_details_page)  # Index 5
        self.main_content_stack.addWidget(self.sales_page)          # Index 6 [NEW]
        
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

    # (!!! แก้ไข Header: ปรับเป็น 2x3 !!!)
    def create_header(self):
        header_frame = QFrame()
        header_frame.setObjectName("Header")
        header_frame.setFixedHeight(185) # ปรับความสูงกลับมาปกติเพราะเหลือแค่ 2 แถว
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(50, 10, 200, 10)
        header_layout.addStretch() 

        right_buttons_widget = QWidget()
        # (ใช้ GridLayout 2x3)
        right_grid = QGridLayout(right_buttons_widget)
        right_grid.setSpacing(15) 
        right_grid.setContentsMargins(0, 20, 0, 20)

        button_height = 55 
        button_width = 180 
        
        # --- แถวที่ 0 ---
        # (คอลัมน์ 0: Manage Account)

        # (คอลัมน์ 1: Sales Summary)
        self.btn_sales_summary = QPushButton("Sales Summary")
        self.btn_sales_summary.setObjectName("navButton")
        self.btn_sales_summary.setFixedSize(button_width, button_height)
        self.btn_sales_summary.clicked.connect(self.show_sales_page) # [EDITED]
        right_grid.addWidget(self.btn_sales_summary, 0, 1)


        # (คอลัมน์ 2: PROFILE)
        profile_icon = QIcon("src/img/icon/profile.png") 
        self.btn_profile = QPushButton(" PROFILE")
        self.btn_profile.setIcon(profile_icon)
        self.btn_profile.setIconSize(QSize(50, 50))
        self.btn_profile.setObjectName("navButton")
        self.btn_profile.setFixedSize(button_width, button_height)
        self.btn_profile.clicked.connect(self.show_profile_page)
        right_grid.addWidget(self.btn_profile, 0, 2)

        # --- แถวที่ 1 ---
        # (คอลัมน์ 0: Manage Comics)
        self.btn_manage_comics = QPushButton("Manage Comics")
        self.btn_manage_comics.setObjectName("navButton")
        self.btn_manage_comics.setFixedSize(button_width, button_height)
        self.btn_manage_comics.clicked.connect(self.show_browse_page)
        right_grid.addWidget(self.btn_manage_comics, 1, 0)
        

        # (คอลัมน์ 1: Orders)
        self.btn_orders = QPushButton("Orders")
        self.btn_orders.setObjectName("navButton")
        self.btn_orders.setFixedSize(button_width, button_height)
        self.btn_orders.clicked.connect(self.show_orders_page)
        right_grid.addWidget(self.btn_orders, 1, 1)
        
        # (คอลัมน์ 2: LOGOUT)
        self.btn_logout = QPushButton("LOGOUT")
        self.btn_logout.setObjectName("navButton")
        self.btn_logout.setFixedSize(button_width, button_height)
        self.btn_logout.clicked.connect(self.handle_logout)
        right_grid.addWidget(self.btn_logout, 1, 2)

        header_layout.addWidget(right_buttons_widget)

        return header_frame

    def create_feedback_button(self):
        self.btn_feedback = QPushButton(self.central_widget)
        self.btn_feedback.setObjectName("btn_info")
        self.btn_feedback.setCursor(Qt.CursorShape.PointingHandCursor)
        # กำหนดขนาดและตำแหน่ง (ปรับ x, y ตามต้องการเพื่อให้ตรงกับดีไซน์)
        self.btn_feedback.setGeometry(368, 75, 60, 60) 
        self.btn_feedback.raise_() # ดึงปุ่มขึ้นมาไว้บนสุด
        self.btn_feedback.clicked.connect(self.open_feedback_window)
        
    def open_feedback_window(self):
        # ตรวจสอบว่าคลาส InfoWindow ถูก import มาสำเร็จหรือไม่
        if feedbackWindow is None:
              QMessageBox.warning(self, "Error", "ไม่พบไฟล์ feedback_window.py")
              return

        # ส่ง self (ตัวหน้าต่าง MainUserWindow นี้) ไปด้วย เพื่อให้ InfoWindow เรียกกลับมาได้
        self.feedback_window_instance = feedbackWindow(user_id=self.current_username, parent_window=self)
        self.feedback_window_instance.show()
        self.hide() # ซ่อนหน้าต่าง Main นี้ไว้ก่อ

    def create_browse_sidebar(self):
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("Sidebar")
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(20, 30, 20, 20)
        sidebar_layout.setSpacing(25)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        button_height = 55
        
        # 1. MARVEL
        btn_marvel = QPushButton("MARVEL")
        btn_marvel.setObjectName("sidebarButton")
        btn_marvel.setFixedHeight(button_height)
        btn_marvel.clicked.connect(lambda: self.filter_products_by_category("MARVEL"))
        sidebar_layout.addWidget(btn_marvel)

        # 2. DC
        btn_dc = QPushButton("DC")
        btn_dc.setObjectName("sidebarButton")
        btn_dc.setFixedHeight(button_height)
        btn_dc.clicked.connect(lambda: self.filter_products_by_category("DC"))
        sidebar_layout.addWidget(btn_dc)

        # 3. Image Comics
        btn_image = QPushButton("Image Comics")
        btn_image.setObjectName("sidebarButton")
        btn_image.setFixedHeight(button_height)
        btn_image.clicked.connect(lambda: self.filter_products_by_category("Image Comics"))
        sidebar_layout.addWidget(btn_image)

        # 4. ALL
        btn_all = QPushButton("ALL")
        btn_all.setObjectName("sidebarButton")
        btn_all.setFixedHeight(button_height)
        btn_all.clicked.connect(lambda: self.filter_products_by_category("ALL"))
        sidebar_layout.addWidget(btn_all)

        # --- เพิ่มปุ่ม Add Comic ---
        # 5. Add Comic
        btn_add_comic = QPushButton("Add Comic")
        btn_add_comic.setObjectName("sidebarButton")  # ใช้ Style เดียวกับปุ่มอื่น
        btn_add_comic.setFixedHeight(button_height)
        # เชื่อม signal clicked ไปยังฟังก์ชัน show_add_comic_page ที่มีอยู่แล้ว
        btn_add_comic.clicked.connect(self.show_add_comic_page)
        sidebar_layout.addWidget(btn_add_comic)
        # ------------------------

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

    def create_add_comic_sidebar(self):
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("Sidebar") 
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(20, 30, 20, 20)
        sidebar_layout.setSpacing(25)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        button_height = 55

        btn_manage = QPushButton("Add Comic")
        btn_manage.setObjectName("profilesidebarButton")
        btn_manage.setFixedHeight(button_height)
        btn_manage.setEnabled(False) 
        sidebar_layout.addWidget(btn_manage)

        btn_back = QPushButton("Back")
        btn_back.setObjectName("backsidebarButton")
        btn_back.setFixedHeight(button_height)
        btn_back.clicked.connect(self.show_browse_page) 
        sidebar_layout.addWidget(btn_back)
        
        sidebar_layout.addStretch()
        return sidebar_frame
        
    # --- [NEW] SIDEBAR FOR SALES SUMMARY ---
    # --- [NEW] SIDEBAR FOR SALES SUMMARY ---
    def create_sales_sidebar(self):
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("Sidebar")
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(20, 30, 20, 20)
        sidebar_layout.setSpacing(25)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        button_height = 55

        # 1. Daily Sales
        btn_daily_sales = QPushButton("Daily Sales")
        btn_daily_sales.setObjectName("sidebarButton") 
        btn_daily_sales.setFixedHeight(button_height)
        btn_daily_sales.clicked.connect(self.show_daily_sales_view)
        sidebar_layout.addWidget(btn_daily_sales)

        # 2. Monthly Sales
        btn_monthly_sales = QPushButton("Monthly Sales")
        btn_monthly_sales.setObjectName("sidebarButton")
        btn_monthly_sales.setFixedHeight(button_height)
        btn_monthly_sales.clicked.connect(self.show_monthly_sales_view) 
        sidebar_layout.addWidget(btn_monthly_sales)

        # 3. Yearly Sales
        btn_yearly_sales = QPushButton("Yearly Sales")
        btn_yearly_sales.setObjectName("sidebarButton")
        btn_yearly_sales.setFixedHeight(button_height)
        btn_yearly_sales.clicked.connect(self.show_yearly_sales_view) 
        sidebar_layout.addWidget(btn_yearly_sales)

        # --- [EDITED] 4. All-Time Sales (ย้ายมาตำแหน่งนี้) ---
        btn_all_time_sales = QPushButton("All-Time Sales")
        btn_all_time_sales.setObjectName("sidebarButton")
        btn_all_time_sales.setFixedHeight(button_height)
        btn_all_time_sales.clicked.connect(self.show_all_time_sales_view)
        sidebar_layout.addWidget(btn_all_time_sales)
        # ----------------------------------------------------

        # 5. Bestseller
        btn_bestseller = QPushButton("Bestseller")
        btn_bestseller.setObjectName("sidebarButton")
        btn_bestseller.setFixedHeight(button_height)
        # --- [EDITED] แก้ไขบรรทัดนี้ ---
        btn_bestseller.clicked.connect(self.show_bestseller_view) 
        # -------------------------------
        sidebar_layout.addWidget(btn_bestseller)
        
        # 6. Back
        btn_back = QPushButton("Back")
        btn_back.setObjectName("backsidebarButton")
        btn_back.setFixedHeight(button_height)
        btn_back.clicked.connect(self.show_browse_page)
        sidebar_layout.addWidget(btn_back)
        
        sidebar_layout.addStretch()
        return sidebar_frame
    
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
        
        self.add_comic_upload_button = QPushButton(" Upload Cover image")
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

        # --- ส่วนขวา: ฟอร์มข้อมูล ---
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setSpacing(15)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        right_form_frame = QFrame()
        right_form_frame.setObjectName("addComicFormFrame")
        form_layout = QFormLayout(right_form_frame)
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

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
        
        form_layout.addRow(QLabel("Name :"), self.add_comic_name)
        form_layout.addRow(QLabel("Volume/Issue :"), self.add_comic_volume)
        form_layout.addRow(QLabel("Description :"), self.add_comic_desc)
        form_layout.addRow(QLabel("Writer :"), self.add_comic_writer)
        form_layout.addRow(QLabel("Rated :"), self.add_comic_rated)
        form_layout.addRow(QLabel("ISBN :"), self.add_comic_isbn)
        form_layout.addRow(QLabel("Category :"), self.add_comic_category)
        form_layout.addRow(QLabel("Stock :"), self.add_comic_stock)
        form_layout.addRow(QLabel("Price :"), self.add_comic_price)
        
        right_layout.addWidget(right_form_frame)

        self.add_product_button = QPushButton("Add Comic")
        self.add_product_button.setObjectName("addProductButton")
        self.add_product_button.setFixedHeight(50)
        self.add_product_button.clicked.connect(self.save_new_comic)
        self.add_product_button.setFixedWidth(200) 
        
        right_layout.addWidget(self.add_product_button, 0, Qt.AlignmentFlag.AlignRight)
        right_layout.addStretch(1)
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
        
    # --- [NEW] SALES SUMMARY PAGE (Container) ---
    # --- [NEW] SALES SUMMARY PAGE (Container) ---
    def create_sales_page(self):
        page_frame = QWidget()
        main_layout = QVBoxLayout(page_frame)
        main_layout.setContentsMargins(0, 0, 0, 0) # ชิดขอบ
        main_layout.setSpacing(0)
        
        # สร้าง StackedWidget ภายในสำหรับสลับหน้า Daily, Monthly, etc.
        self.sales_content_stack = QStackedWidget()
        
        # สร้างหน้า Daily Sales
        self.daily_sales_page = self.create_daily_sales_page()
        self.sales_content_stack.addWidget(self.daily_sales_page) # Index 0
        
        self.monthly_sales_page = self.create_monthly_sales_page()
        self.sales_content_stack.addWidget(self.monthly_sales_page) # Index 1

        self.yearly_sales_page = self.create_yearly_sales_page()
        self.sales_content_stack.addWidget(self.yearly_sales_page) # Index 2
        
        # --- [NEW] เพิ่มหน้า All-Time ---
        self.all_time_sales_page = self.create_all_time_sales_page()
        self.sales_content_stack.addWidget(self.all_time_sales_page) # Index 3
        # -------------------------------
        
        # --- [NEW] เพิ่มหน้า Bestseller ---
        self.bestseller_page = self.create_bestseller_page()
        self.sales_content_stack.addWidget(self.bestseller_page) # Index 4
        # ----------------------------------
        
        main_layout.addWidget(self.sales_content_stack)
        return page_frame

    # --- [NEW] DAILY SALES PAGE (UI) ---
    def create_daily_sales_page(self):
        page_frame = QFrame()
        # ตั้งชื่อ ObjectName ให้ตรงกับ QSS ในรูป (Orders.jpg)
        page_frame.setObjectName("MainContent") # ใช้ชื่อเดียวกับ Browse Page เพื่อให้ได้พื้นหลังสีอ่อน
        
        main_layout = QVBoxLayout(page_frame)
        # ตั้งค่า Margins ให้มีพื้นที่ว่างรอบข้าง
        main_layout.setContentsMargins(300, 40, 50, 40)
        main_layout.setSpacing(20)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop) # จัดชิดบน

        # Frame สีครีมตรงกลางตามภาพ
        content_frame = QFrame()
        content_frame.setObjectName("salesReportFrame") # ตั้งชื่อเฉพาะสำหรับ QSS
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(40, 30, 40, 30)
        content_layout.setSpacing(15)
        
        # --- 1. Title ---
        title_label = QLabel("Daily Sales")
        title_label.setObjectName("salesReportTitle") # ตั้งชื่อเฉพาะสำหรับ QSS
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(title_label)
        
        content_layout.addSpacing(20)

        # --- 2. Results Area ---
        results_layout = QFormLayout()
        results_layout.setSpacing(10)
        results_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        total_amount_label = QLabel("Details :")
        total_amount_label.setObjectName("salesReportHeader")
        
        self.sales_orders_label = QLabel("0 orders")
        self.sales_orders_label.setObjectName("salesReportValue")
        
        self.sales_quantity_label = QLabel("0 books")
        self.sales_quantity_label.setObjectName("salesReportValue")
        
        self.sales_total_label = QLabel("0.00 THB")
        self.sales_total_label.setObjectName("salesReportTotalValue")

        # เพิ่มแถวข้อมูล
        results_layout.addRow(total_amount_label)
        orders_label = QLabel("orders:")
        orders_label.setObjectName("salesReportLabelText") # เพิ่ม ObjectName
        results_layout.addRow(orders_label, self.sales_orders_label)

        quantity_label = QLabel("quantity:")
        quantity_label.setObjectName("salesReportLabelText") # เพิ่ม ObjectName
        results_layout.addRow(quantity_label, self.sales_quantity_label)
        
        content_layout.addLayout(results_layout)
        content_layout.addSpacing(10)
        
        # เส้นคั่น
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        content_layout.addWidget(line)
        content_layout.addSpacing(10)

        # แถว Total
        total_layout = QHBoxLayout()
        total_label_text = QLabel("Total :")
        total_label_text.setObjectName("salesReportTotalLabel")
        total_layout.addWidget(total_label_text)
        total_layout.addWidget(self.sales_total_label)
        total_layout.addStretch(1)
        content_layout.addLayout(total_layout)
        
        content_layout.addStretch(1) # ดันส่วนล่างลงไป

        # --- 3. Date Input Area ---
        date_input_layout = QHBoxLayout()
        date_input_layout.setSpacing(10)
        date_input_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Days
        days_label = QLabel("Days")
        days_label.setObjectName("salesDateLabel")
        date_input_layout.addWidget(days_label)
        self.sales_day_input = QComboBox()
        self.sales_day_input.setObjectName("salesDateInput")
        self.sales_day_input.setFixedWidth(60)
        self.sales_day_input.addItems([str(i) for i in range(1, 32)])  # 1-31
        date_input_layout.addWidget(self.sales_day_input)

        # Months
        months_label = QLabel("Months")
        months_label.setObjectName("salesDateLabel")
        date_input_layout.addWidget(months_label)
        self.sales_month_input = QComboBox()
        self.sales_month_input.setObjectName("salesDateInput")
        self.sales_month_input.setFixedWidth(60)
        self.sales_month_input.addItems([str(i) for i in range(1, 13)])  # 1-12
        date_input_layout.addWidget(self.sales_month_input)

        # Years
        years_label = QLabel("Years")
        years_label.setObjectName("salesDateLabel") # <--- ตั้งชื่อเฉพาะ
        date_input_layout.addWidget(years_label)
        # date_input_layout.setObjectName("salesDateInputLayout") # ไม่จำเป็นต้องทำแบบนี้กับ layout
        self.sales_year_input = QLineEdit()
        self.sales_year_input.setObjectName("salesDateInput")
        self.sales_year_input.setFixedWidth(80)
        date_input_layout.addWidget(self.sales_year_input)

        date_input_layout.addSpacing(10)

        self.sales_apply_button = QPushButton("apply")
        self.sales_apply_button.setObjectName("salesApplyButton")
        self.sales_apply_button.setFixedSize(80, 35)
        self.sales_apply_button.clicked.connect(self.calculate_daily_sales)
        date_input_layout.addWidget(self.sales_apply_button)
        
        date_input_layout.addStretch()

        content_layout.addLayout(date_input_layout)
        
        # เพิ่ม content_frame ลงใน main_layout
        main_layout.addWidget(content_frame)
        main_layout.addStretch() # ดัน Frame ขึ้นบน

        return page_frame

    # --- [NEW] LOGIC FOR DAILY SALES ---
    # --- [NEW] LOGIC FOR DAILY SALES ---
    def calculate_daily_sales(self):
        try:
            day = int(self.sales_day_input.currentText())
            month = int(self.sales_month_input.currentText())
            year = int(self.sales_year_input.text())
            
            selected_date = datetime(year, month, day)
            
            # [EDITED] สร้างสตริงวันที่ทั้ง 2 รูปแบบ
            # รูปแบบที่ 1: 'YYYY-MM-DD' (สำหรับฟังก์ชัน DATE())
            date_sql_format = selected_date.strftime("%Y-%m-%d")
            # รูปแบบที่ 2: 'DD-Mon-YYYY' (สำหรับ LIKE)
            date_custom_format = selected_date.strftime("%d-%b-%Y") # เช่น '11-Nov-2025'
            
        except ValueError:
            QMessageBox.warning(self, "Invalid Date", "Please enter valid numbers for Day, Month, and Year.")
            self.sales_orders_label.setText("Invalid Date")
            self.sales_quantity_label.setText("Invalid Date")
            self.sales_total_label.setText("Invalid Date")
            return
        except Exception as e:
            QMessageBox.warning(self, "Date Error", f"An error occurred with the date: {e}")
            return
            
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # --- [EDITED] แก้ไข Query ทั้ง 3 ส่วน ---

            # Query 1: นับจำนวนออเดอร์ (orders) ที่ "มีสินค้า"
            cursor.execute("""
                SELECT
                    COUNT(DISTINCT oi.order_id)
                FROM
                    order_items oi
                JOIN
                    orders o ON oi.order_id = o.order_id
                WHERE
                    (DATE(o.order_date) = ? OR o.order_date LIKE ?)
                    AND o.status != 'cancelled' -- <--- [KEPT] คงไว้ตามที่ขอ
                    AND o.status IN ('paid', 'dispatched') -- <--- [ADDED] เพิ่มเงื่อนไข
            """, (date_sql_format, f"{date_custom_format}%"))
            
            order_data = cursor.fetchone()
            num_orders = order_data[0] if order_data[0] is not None else 0

            # Query 2: นับจำนวนสินค้า (quantity)
            cursor.execute("""
                SELECT
                    SUM(oi.quantity)
                FROM
                    order_items oi
                JOIN
                    orders o ON oi.order_id = o.order_id
                WHERE
                    (DATE(o.order_date) = ? OR o.order_date LIKE ?)
                    AND o.status != 'cancelled' -- <--- [KEPT] คงไว้ตามที่ขอ
                    AND o.status IN ('paid', 'dispatched') -- <--- [ADDED] เพิ่มเงื่อนไข
            """, (date_sql_format, f"{date_custom_format}%"))
            
            quantity_data = cursor.fetchone()
            total_quantity = quantity_data[0] if quantity_data[0] is not None else 0
            
            # Query 3: หายอดรวม (Total THB) 
            cursor.execute("""
                SELECT
                    SUM(total)
                FROM
                    orders
                WHERE
                    (DATE(order_date) = ? OR order_date LIKE ?)
                    AND status != 'cancelled' -- <--- [KEPT] คงไว้ตามที่ขอ
                    AND status IN ('paid', 'dispatched') -- <--- [ADDED] เพิ่มเงื่อนไข
            """, (date_sql_format, f"{date_custom_format}%"))
            
            sales_data = cursor.fetchone()
            total_sales = sales_data[0] if sales_data[0] is not None else 0.0
            
            conn.close()

            # อัปเดตหน้า UI
            self.sales_orders_label.setText(f"{num_orders} orders")
            self.sales_quantity_label.setText(f"{total_quantity} books")
            self.sales_total_label.setText(f"{total_sales:,.2f} THB")

        except sqlite3.Error as e:
            print(f"SQL Error: {e}")
            QMessageBox.warning(self, "Database Error", f"Could not retrieve sales data: {e}")
        except Exception as e:
            print(f"Error calculating sales: {e}")
            QMessageBox.warning(self, "Error", f"An unexpected error occurred: {e}")

    # --- [NEW] FUNCTION TO SHOW SALES PAGE ---
    def show_sales_page(self):
        print("Showing Sales Summary Page")
        self.sidebar_stack.setCurrentIndex(6)
        self.main_content_stack.setCurrentIndex(6)
        # แสดงหน้า Daily Sales เป็นค่าเริ่มต้น
        self.show_daily_sales_view()
        
    def show_daily_sales_view(self):
        print("Showing Daily Sales View")
        # สลับ StackedWidget ภายในไปที่หน้า Daily (Index 0)
        self.sales_content_stack.setCurrentIndex(0) 
        
        # --- [EDITED] ---
        
        # 1. ตั้งค่าวันที่ในช่องค้นหาเป็น "วันนี้"
        today = datetime.now()
        self.sales_day_input.setCurrentText(str(today.day))
        self.sales_month_input.setCurrentText(str(today.month))
        self.sales_year_input.setText(str(today.year))
        
        # 2. [เพิ่มบรรทัดนี้] เรียกใช้การคำนวณทันที
        # เพื่อให้ยอดขายของ "วันนี้" แสดงผลเลย โดยไม่ต้องกด Apply
        self.calculate_daily_sales()
        
    # --- [NEW] MONTHLY SALES PAGE (UI) ---
    def create_monthly_sales_page(self):
        page_frame = QFrame()
        page_frame.setObjectName("MainContent")
        
        main_layout = QVBoxLayout(page_frame)
        main_layout.setContentsMargins(300, 40, 50, 40)
        main_layout.setSpacing(20)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        content_frame = QFrame()
        content_frame.setObjectName("salesReportFrame")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(40, 30, 40, 30)
        content_layout.setSpacing(15)
        
        # --- 1. Title ---
        title_label = QLabel("Monthly Sales")
        title_label.setObjectName("salesReportTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(title_label)
        
        content_layout.addSpacing(20)

        # --- 2. Results Area ---
        results_layout = QFormLayout()
        results_layout.setSpacing(10)
        results_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        total_amount_label = QLabel("Details :")
        total_amount_label.setObjectName("salesReportHeader")
        
        # สร้าง Label ใหม่สำหรับ Monthly
        self.monthly_orders_label = QLabel("0 orders")
        self.monthly_orders_label.setObjectName("salesReportValue")
        
        self.monthly_quantity_label = QLabel("0 books")
        self.monthly_quantity_label.setObjectName("salesReportValue")
        
        self.monthly_total_label = QLabel("0.00 THB")
        self.monthly_total_label.setObjectName("salesReportTotalValue")

        results_layout.addRow(total_amount_label)
        orders_label = QLabel("orders:")
        orders_label.setObjectName("salesReportLabelText")
        results_layout.addRow(orders_label, self.monthly_orders_label)

        quantity_label = QLabel("quantity:")
        quantity_label.setObjectName("salesReportLabelText")
        results_layout.addRow(quantity_label, self.monthly_quantity_label)
        
        content_layout.addLayout(results_layout)
        content_layout.addSpacing(10)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        content_layout.addWidget(line)
        content_layout.addSpacing(10)

        total_layout = QHBoxLayout()
        total_label_text = QLabel("Total :")
        total_label_text.setObjectName("salesReportTotalLabel")
        total_layout.addWidget(total_label_text)
        total_layout.addWidget(self.monthly_total_label)
        total_layout.addStretch(1)
        content_layout.addLayout(total_layout)
        
        content_layout.addStretch(1)

        # --- 3. Date Input Area (ตัด Day ออก) ---
        date_input_layout = QHBoxLayout()
        date_input_layout.setSpacing(10)
        date_input_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Months
        months_label = QLabel("Months")
        months_label.setObjectName("salesDateLabel")
        date_input_layout.addWidget(months_label)
        self.monthly_month_input = QComboBox() # <--- ชื่อใหม่
        self.monthly_month_input.setObjectName("salesDateInput")
        self.monthly_month_input.setFixedWidth(60)
        self.monthly_month_input.addItems([str(i) for i in range(1, 13)])
        date_input_layout.addWidget(self.monthly_month_input)

        # Years
        years_label = QLabel("Years")
        years_label.setObjectName("salesDateLabel")
        date_input_layout.addWidget(years_label)
        self.monthly_year_input = QLineEdit() # <--- ชื่อใหม่
        self.monthly_year_input.setObjectName("salesDateInput")
        self.monthly_year_input.setFixedWidth(80)
        date_input_layout.addWidget(self.monthly_year_input)

        date_input_layout.addSpacing(10)

        self.monthly_apply_button = QPushButton("apply")
        self.monthly_apply_button.setObjectName("salesApplyButton")
        self.monthly_apply_button.setFixedSize(80, 35)
        self.monthly_apply_button.clicked.connect(self.calculate_monthly_sales)
        date_input_layout.addWidget(self.monthly_apply_button)
        
        date_input_layout.addStretch()
        content_layout.addLayout(date_input_layout)
        
        main_layout.addWidget(content_frame)
        main_layout.addStretch()

        return page_frame

    # --- [NEW] LOGIC FOR MONTHLY SALES ---
    def calculate_monthly_sales(self):
        try:
            month = int(self.monthly_month_input.currentText())
            year = int(self.monthly_year_input.text())
            
            # สร้าง Format สำหรับ Query
            # 1. 'YYYY-MM' (สำหรับ strftime)
            year_month_sql_format = f"{year}-{month:02d}"
            # 2. '%-Mon-YYYY%' (สำหรับ LIKE)
            month_abbr = datetime(year, month, 1).strftime('%b') # เช่น 'Nov'
            like_format = f"%-{month_abbr}-{year}%" # เช่น '%-Nov-2025%'

        except ValueError:
            QMessageBox.warning(self, "Invalid Date", "Please enter a valid Year.")
            self.monthly_orders_label.setText("Invalid Year")
            self.monthly_quantity_label.setText("Invalid Year")
            self.monthly_total_label.setText("Invalid Year")
            return
            
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # --- [EDITED] แก้ไข Query ทั้ง 3 ส่วน ---
            # ใช้ strftime('%Y-%m', o.order_date) และ LIKE

            # Query 1: นับจำนวนออเดอร์
            cursor.execute("""
                SELECT COUNT(DISTINCT oi.order_id)
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.order_id
                WHERE
                    (strftime('%Y-%m', o.order_date) = ? OR o.order_date LIKE ?)
                    AND o.status IN ('paid', 'dispatched')
            """, (year_month_sql_format, like_format))
            
            order_data = cursor.fetchone()
            num_orders = order_data[0] if order_data[0] is not None else 0

            # Query 2: นับจำนวนสินค้า
            cursor.execute("""
                SELECT SUM(oi.quantity)
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.order_id
                WHERE
                    (strftime('%Y-%m', o.order_date) = ? OR o.order_date LIKE ?)
                    AND o.status IN ('paid', 'dispatched')
            """, (year_month_sql_format, like_format))
            
            quantity_data = cursor.fetchone()
            total_quantity = quantity_data[0] if quantity_data[0] is not None else 0
            
            # Query 3: หายอดรวม
            cursor.execute("""
                SELECT SUM(total)
                FROM orders
                WHERE
                    (strftime('%Y-%m', order_date) = ? OR order_date LIKE ?)
                    AND status IN ('paid', 'dispatched')
            """, (year_month_sql_format, like_format))
            
            sales_data = cursor.fetchone()
            total_sales = sales_data[0] if sales_data[0] is not None else 0.0
            
            conn.close()

            # อัปเดตหน้า UI (ใช้ Label ของ Monthly)
            self.monthly_orders_label.setText(f"{num_orders} orders")
            self.monthly_quantity_label.setText(f"{total_quantity} books")
            self.monthly_total_label.setText(f"{total_sales:,.2f} THB")

        except sqlite3.Error as e:
            print(f"SQL Error: {e}")
            QMessageBox.warning(self, "Database Error", f"Could not retrieve sales data: {e}")
        except Exception as e:
            print(f"Error calculating sales: {e}")
            QMessageBox.warning(self, "Error", f"An unexpected error occurred: {e}")

    # --- [NEW] FUNCTION TO SHOW MONTHLY SALES VIEW ---
    def show_monthly_sales_view(self):
        print("Showing Monthly Sales View")
        self.sales_content_stack.setCurrentIndex(1) # <--- เปลี่ยน Index เป็น 1
        
        today = datetime.now()
        self.monthly_month_input.setCurrentText(str(today.month))
        self.monthly_year_input.setText(str(today.year))
        
        self.calculate_monthly_sales()


    # --- [NEW] YEARLY SALES PAGE (UI) ---
    def create_yearly_sales_page(self):
        page_frame = QFrame()
        page_frame.setObjectName("MainContent")
        
        main_layout = QVBoxLayout(page_frame)
        main_layout.setContentsMargins(300, 40, 50, 40)
        main_layout.setSpacing(20)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        content_frame = QFrame()
        content_frame.setObjectName("salesReportFrame")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(40, 30, 40, 30)
        content_layout.setSpacing(15)
        
        # --- 1. Title ---
        title_label = QLabel("Yearly Sales")
        title_label.setObjectName("salesReportTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(title_label)
        
        content_layout.addSpacing(20)

        # --- 2. Results Area ---
        results_layout = QFormLayout()
        results_layout.setSpacing(10)
        results_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        total_amount_label = QLabel("Details :")
        total_amount_label.setObjectName("salesReportHeader")
        
        # สร้าง Label ใหม่สำหรับ Yearly
        self.yearly_orders_label = QLabel("0 orders")
        self.yearly_orders_label.setObjectName("salesReportValue")
        
        self.yearly_quantity_label = QLabel("0 books")
        self.yearly_quantity_label.setObjectName("salesReportValue")
        
        self.yearly_total_label = QLabel("0.00 THB")
        self.yearly_total_label.setObjectName("salesReportTotalValue")

        results_layout.addRow(total_amount_label)
        orders_label = QLabel("orders:")
        orders_label.setObjectName("salesReportLabelText")
        results_layout.addRow(orders_label, self.yearly_orders_label)

        quantity_label = QLabel("quantity:")
        quantity_label.setObjectName("salesReportLabelText")
        results_layout.addRow(quantity_label, self.yearly_quantity_label)
        
        content_layout.addLayout(results_layout)
        content_layout.addSpacing(10)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        content_layout.addWidget(line)
        content_layout.addSpacing(10)

        total_layout = QHBoxLayout()
        total_label_text = QLabel("Total :")
        total_label_text.setObjectName("salesReportTotalLabel")
        total_layout.addWidget(total_label_text)
        total_layout.addWidget(self.yearly_total_label)
        total_layout.addStretch(1)
        content_layout.addLayout(total_layout)
        
        content_layout.addStretch(1)

        # --- 3. Date Input Area (ตัด Day และ Month ออก) ---
        date_input_layout = QHBoxLayout()
        date_input_layout.setSpacing(10)
        date_input_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Years
        years_label = QLabel("Years")
        years_label.setObjectName("salesDateLabel")
        date_input_layout.addWidget(years_label)
        self.yearly_year_input = QLineEdit() # <--- ชื่อใหม่
        self.yearly_year_input.setObjectName("salesDateInput")
        self.yearly_year_input.setFixedWidth(80)
        date_input_layout.addWidget(self.yearly_year_input)

        date_input_layout.addSpacing(10)

        self.yearly_apply_button = QPushButton("apply")
        self.yearly_apply_button.setObjectName("salesApplyButton")
        self.yearly_apply_button.setFixedSize(80, 35)
        self.yearly_apply_button.clicked.connect(self.calculate_yearly_sales)
        date_input_layout.addWidget(self.yearly_apply_button)
        
        date_input_layout.addStretch()
        content_layout.addLayout(date_input_layout)
        
        main_layout.addWidget(content_frame)
        main_layout.addStretch()

        return page_frame

    # --- [NEW] LOGIC FOR YEARLY SALES ---
    def calculate_yearly_sales(self):
        try:
            year = int(self.yearly_year_input.text())
            
            # สร้าง Format สำหรับ Query
            # 1. 'YYYY' (สำหรับ strftime)
            year_sql_format = str(year)
            # 2. '%-YYYY%' (สำหรับ LIKE)
            like_format = f"%-{year}%" # เช่น '%-2025%'

        except ValueError:
            QMessageBox.warning(self, "Invalid Date", "Please enter a valid Year.")
            self.yearly_orders_label.setText("Invalid Year")
            self.yearly_quantity_label.setText("Invalid Year")
            self.yearly_total_label.setText("Invalid Year")
            return
            
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # --- [EDITED] แก้ไข Query ทั้ง 3 ส่วน ---
            # ใช้ strftime('%Y', o.order_date) และ LIKE

            # Query 1: นับจำนวนออเดอร์
            cursor.execute("""
                SELECT COUNT(DISTINCT oi.order_id)
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.order_id
                WHERE
                    (strftime('%Y', o.order_date) = ? OR o.order_date LIKE ?)
                    AND o.status IN ('paid', 'dispatched')
            """, (year_sql_format, like_format))
            
            order_data = cursor.fetchone()
            num_orders = order_data[0] if order_data[0] is not None else 0

            # Query 2: นับจำนวนสินค้า
            cursor.execute("""
                SELECT SUM(oi.quantity)
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.order_id
                WHERE
                    (strftime('%Y', o.order_date) = ? OR o.order_date LIKE ?)
                    AND o.status IN ('paid', 'dispatched')
            """, (year_sql_format, like_format))
            
            quantity_data = cursor.fetchone()
            total_quantity = quantity_data[0] if quantity_data[0] is not None else 0
            
            # Query 3: หายอดรวม
            cursor.execute("""
                SELECT SUM(total)
                FROM orders
                WHERE
                    (strftime('%Y', order_date) = ? OR order_date LIKE ?)
                    AND status IN ('paid', 'dispatched')
            """, (year_sql_format, like_format))
            
            sales_data = cursor.fetchone()
            total_sales = sales_data[0] if sales_data[0] is not None else 0.0
            
            conn.close()

            # อัปเดตหน้า UI (ใช้ Label ของ Yearly)
            self.yearly_orders_label.setText(f"{num_orders} orders")
            self.yearly_quantity_label.setText(f"{total_quantity} books")
            self.yearly_total_label.setText(f"{total_sales:,.2f} THB")

        except sqlite3.Error as e:
            print(f"SQL Error: {e}")
            QMessageBox.warning(self, "Database Error", f"Could not retrieve sales data: {e}")
        except Exception as e:
            print(f"Error calculating sales: {e}")
            QMessageBox.warning(self, "Error", f"An unexpected error occurred: {e}")

    # --- [NEW] FUNCTION TO SHOW YEARLY SALES VIEW ---
    def show_yearly_sales_view(self):
        print("Showing Yearly Sales View")
        self.sales_content_stack.setCurrentIndex(2) # <--- เปลี่ยน Index เป็น 2
        
        today = datetime.now()
        self.yearly_year_input.setText(str(today.year))
        
        self.calculate_yearly_sales()

    # --- [NEW] ALL-TIME SALES PAGE (UI) ---
    def create_all_time_sales_page(self):
        page_frame = QFrame()
        page_frame.setObjectName("MainContent")
        
        main_layout = QVBoxLayout(page_frame)
        main_layout.setContentsMargins(300, 40, 50, 40)
        main_layout.setSpacing(20)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        content_frame = QFrame()
        content_frame.setObjectName("salesReportFrame")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(40, 30, 40, 30)
        content_layout.setSpacing(15)
        
        # --- 1. Title ---
        title_label = QLabel("All-Time Sales")
        title_label.setObjectName("salesReportTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(title_label)
        
        content_layout.addSpacing(20)

        # --- 2. Results Area ---
        results_layout = QFormLayout()
        results_layout.setSpacing(10)
        results_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        total_amount_label = QLabel("Details (All-Time) :")
        total_amount_label.setObjectName("salesReportHeader")
        
        # สร้าง Label ใหม่สำหรับ All-Time
        self.all_time_orders_label = QLabel("0 orders")
        self.all_time_orders_label.setObjectName("salesReportValue")
        
        self.all_time_quantity_label = QLabel("0 books")
        self.all_time_quantity_label.setObjectName("salesReportValue")
        
        self.all_time_total_label = QLabel("0.00 THB")
        self.all_time_total_label.setObjectName("salesReportTotalValue")

        results_layout.addRow(total_amount_label)
        orders_label = QLabel("orders:")
        orders_label.setObjectName("salesReportLabelText")
        results_layout.addRow(orders_label, self.all_time_orders_label)

        quantity_label = QLabel("quantity:")
        quantity_label.setObjectName("salesReportLabelText")
        results_layout.addRow(quantity_label, self.all_time_quantity_label)
        
        content_layout.addLayout(results_layout)
        content_layout.addSpacing(10)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        content_layout.addWidget(line)
        content_layout.addSpacing(10)

        total_layout = QHBoxLayout()
        total_label_text = QLabel("Total :")
        total_label_text.setObjectName("salesReportTotalLabel")
        total_layout.addWidget(total_label_text)
        total_layout.addWidget(self.all_time_total_label)
        total_layout.addStretch(1)
        content_layout.addLayout(total_layout)
        
        content_layout.addStretch(1)

        # --- 3. ไม่มี Date Input Area ---
        # (ลบส่วนนี้ออกไปเลย)
        
        main_layout.addWidget(content_frame)
        main_layout.addStretch()

        return page_frame

    # --- [NEW] LOGIC FOR ALL-TIME SALES ---
    def calculate_all_time_sales(self):
        # ไม่มีการ parse date เพราะเป็นการรวมยอดทั้งหมด
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # --- [EDITED] แก้ไข Query ทั้ง 3 ส่วน ---
            # (ตัด WHERE ที่เกี่ยวกับวันที่ออกทั้งหมด)

            # Query 1: นับจำนวนออเดอร์
            cursor.execute("""
                SELECT COUNT(DISTINCT oi.order_id)
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.order_id
                WHERE
                    o.status IN ('paid', 'dispatched')
            """)
            
            order_data = cursor.fetchone()
            num_orders = order_data[0] if order_data[0] is not None else 0

            # Query 2: นับจำนวนสินค้า
            cursor.execute("""
                SELECT SUM(oi.quantity)
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.order_id
                WHERE
                    o.status IN ('paid', 'dispatched')
            """)
            
            quantity_data = cursor.fetchone()
            total_quantity = quantity_data[0] if quantity_data[0] is not None else 0
            
            # Query 3: หายอดรวม
            cursor.execute("""
                SELECT SUM(total)
                FROM orders
                WHERE
                    status IN ('paid', 'dispatched')
            """)
            
            sales_data = cursor.fetchone()
            total_sales = sales_data[0] if sales_data[0] is not None else 0.0
            
            conn.close()

            # อัปเดตหน้า UI (ใช้ Label ของ All-Time)
            self.all_time_orders_label.setText(f"{num_orders} orders")
            self.all_time_quantity_label.setText(f"{total_quantity} books")
            self.all_time_total_label.setText(f"{total_sales:,.2f} THB")

        except sqlite3.Error as e:
            print(f"SQL Error: {e}")
            QMessageBox.warning(self, "Database Error", f"Could not retrieve sales data: {e}")
        except Exception as e:
            print(f"Error calculating sales: {e}")
            QMessageBox.warning(self, "Error", f"An unexpected error occurred: {e}")

    # --- [NEW] FUNCTION TO SHOW ALL-TIME SALES VIEW ---
    def show_all_time_sales_view(self):
        print("Showing All-Time Sales View")
        self.sales_content_stack.setCurrentIndex(3) # <--- เปลี่ยน Index เป็น 3
        
        # ไม่ต้องตั้งค่าวันที่
        
        self.calculate_all_time_sales()

    # --- [NEW] BESTSELLER PAGE (UI) ---
    def create_bestseller_page(self):
        page_frame = QFrame()
        page_frame.setObjectName("MainContent") # ใช้พื้นหลังเดียวกับหน้า Browse
        
        main_layout = QVBoxLayout(page_frame)
        main_layout.setContentsMargins(300, 40, 50, 40) # ปรับ Margins ตามความเหมาะสม
        main_layout.setSpacing(20)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- ส่วน Filter ---
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)
        
        category_label = QLabel("Filter by Category:")
        category_label.setObjectName("salesDateLabel") # ใช้สไตล์เดียวกับ Label อื่น
        
        self.bestseller_category_combo = QComboBox()
        self.bestseller_category_combo.setObjectName("salesDateInput") # ใช้สไตล์เดียวกับ ComboBox อื่น
        self.bestseller_category_combo.addItems(["ALL", "MARVEL", "DC", "Image Comics"])
        self.bestseller_category_combo.setFixedWidth(150)
        # เชื่อม Signal เมื่อมีการเปลี่ยนแปลง
        self.bestseller_category_combo.currentTextChanged.connect(self.load_bestseller_data)

        filter_layout.addWidget(category_label)
        filter_layout.addWidget(self.bestseller_category_combo)
        filter_layout.addStretch()
        
        main_layout.addLayout(filter_layout)

        # --- ตาราง Bestseller ---
        self.bestseller_table = QTableWidget()
        self.bestseller_table.setObjectName("ordersTable") # ใช้สไตล์เดียวกับตาราง Order
        self.bestseller_table.setColumnCount(4)
        self.bestseller_table.setHorizontalHeaderLabels(["NO.", "ITEM", "Category", "Quantity"])
        
        header = self.bestseller_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed) # NO.
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # ITEM
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # Category
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Quantity
        
        self.bestseller_table.setColumnWidth(0, 50) # NO.
        
        self.bestseller_table.verticalHeader().setVisible(False)
        self.bestseller_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.bestseller_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.bestseller_table.setShowGrid(True)
        
        main_layout.addWidget(self.bestseller_table, 1) # ให้ตารางยืดขยาย

        return page_frame
    
    # --- [NEW] LOGIC FOR BESTSELLER (แก้ไข) ---
    def load_bestseller_data(self):
        self.bestseller_table.setRowCount(0)
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            selected_category = self.bestseller_category_combo.currentText()
            
            # 1. สร้าง Query หลัก
            base_query = """
                SELECT 
                    p.id, 
                    p.name, 
                    p.cover_img, 
                    p.category, 
                    SUM(oi.quantity) as total_sold
                FROM 
                    order_items oi
                JOIN 
                    orders o ON oi.order_id = o.order_id
                JOIN 
                    product p ON oi.product_id = p.id
                WHERE 
                    o.status IN ('paid', 'dispatched') 
            """ # <-- [!!! EDITED !!!] แก้ไขจุดนี้
            
            params = []
            
            # 2. เพิ่มเงื่อนไข Category ถ้าไม่ได้เลือก "ALL"
            if selected_category != "ALL":
                base_query += " AND p.category = ? "
                params.append(selected_category)
                
            # 3. GROUP BY และ ORDER BY
            base_query += """
                GROUP BY 
                    p.id, p.name, p.cover_img, p.category
                ORDER BY 
                    total_sold DESC
            """
            
            cursor.execute(base_query, params)
            results = cursor.fetchall()
            conn.close()
            
            # 4. แสดงผลลัพธ์ในตาราง (ส่วนนี้เหมือนเดิม)
            self.bestseller_table.setRowCount(len(results))
            for i, (p_id, p_name, p_img, p_cat, total_sold) in enumerate(results):
                
                # --- Column 0: NO. ---
                num_item = QTableWidgetItem(str(i + 1))
                num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.bestseller_table.setItem(i, 0, num_item)

                # --- Column 1: ITEM (Image + Name) ---
                item_widget = QWidget()
                item_layout = QHBoxLayout(item_widget)
                item_layout.setContentsMargins(5, 5, 5, 5)
                
                img_label = QLabel()
                img_label.setFixedSize(60, 90) # ขนาดรูป
                img_label.setScaledContents(True)
                
                if p_img and os.path.exists(p_img):
                    img_label.setPixmap(QPixmap(p_img))
                else:
                    img_label.setPixmap(QPixmap("src/img/icon/profile.png")) # รูปสำรอง
                
                name_label = QLabel(p_name)
                name_label.setWordWrap(True)
                name_label.setObjectName("bestsellerItemName") # ใช้สไตล์เดียวกับตารางอื่น
                
                item_layout.addWidget(img_label)
                item_layout.addWidget(name_label, 1) # ให้ชื่อยืดได้
                self.bestseller_table.setCellWidget(i, 1, item_widget)
                
                # --- Column 2: Category ---
                cat_item = QTableWidgetItem(p_cat)
                cat_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.bestseller_table.setItem(i, 2, cat_item)
                
                # --- Column 3: Quantity ---
                qty_item = QTableWidgetItem(str(total_sold))
                qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.bestseller_table.setItem(i, 3, qty_item)
                
                # ตั้งค่าความสูงของแถว
                self.bestseller_table.setRowHeight(i, 100)

        except sqlite3.Error as e:
            print(f"SQL Error: {e}")
            QMessageBox.warning(self, "Database Error", f"Could not retrieve bestseller data: {e}")
        except Exception as e:
            print(f"Error loading bestseller data: {e}")

    # --- [NEW] FUNCTION TO SHOW BESTSELLER VIEW ---
    def show_bestseller_view(self):
        print("Showing Bestseller View")
        self.sales_content_stack.setCurrentIndex(4) # <--- Index 4 (เดี๋ยวเราจะเพิ่มใน create_sales_page)
        
        # ตั้งค่า Filter เป็น "ALL" ก่อนเสมอ
        self.bestseller_category_combo.setCurrentText("ALL")
        
        # โหลดข้อมูล (การตั้งค่า ComboBox ด้านบนจะ trigger signal นี้อยู่แล้ว
        # แต่เพื่อความแน่นอน, เราเรียกเองก็ได้)
        self.load_bestseller_data()



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
            error_label = QLabel(error_text)
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid_layout.addWidget(error_label, 0, 0)
            
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการโหลด comics: {e}")
            error_label = QLabel(f"Error loading comics:\n{e}")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid_layout.addWidget(error_label, 0, 0)

    # ... (imports และส่วนอื่นๆ ของ class MainAdminWindow)

    def create_product_detail_page(self):
        detail_frame = QFrame()
        detail_frame.setObjectName("ProductDetailPage")
        
        main_detail_layout = QHBoxLayout(detail_frame)
        # --- ห้ามแก้ไข ContentsMargins ---
        main_detail_layout.setContentsMargins(350, 40, 40, 40)
        main_detail_layout.setSpacing(30)
        main_detail_layout.setAlignment(Qt.AlignmentFlag.AlignRight) 

        main_detail_layout.addStretch(1) 

        # --- ส่วนซ้าย: รูปภาพ ---
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setSpacing(10)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        self.detail_cover_label = QLabel()
        self.detail_cover_label.setObjectName("detailCover") # ตรงกับ CSS
        self.detail_cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_cover_label.setFixedSize(250, 380) 
        
        self.detail_upload_button = QPushButton(" Change Cover")
        self.detail_upload_button.setObjectName("detailUploadButton") # ตรงกับ CSS
        self.detail_upload_button.setIcon(QIcon("src/img/icon/upload.png"))
        self.detail_upload_button.setIconSize(QSize(40, 40))
        self.detail_upload_button.setFixedHeight(40)
        self.detail_upload_button.setVisible(False)
        self.detail_upload_button.clicked.connect(self.select_detail_image)

        left_layout.addWidget(self.detail_cover_label)
        left_layout.addWidget(self.detail_upload_button)
        
        main_detail_layout.addWidget(left_container, 0, Qt.AlignmentFlag.AlignRight)

        main_detail_layout.addStretch(1) 

        # --- ส่วนขวา: ข้อมูล ---
        right_info_widget = QWidget()
        right_info_widget.setFixedWidth(500) 
        right_info_layout = QVBoxLayout(right_info_widget)
        right_info_layout.setContentsMargins(0, 0, 0, 0)
        right_info_layout.setSpacing(15)
        right_info_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight) 

        self.detail_name_field = QTextEdit()         # <--- ใช้ QTextEdit แทน
        self.detail_name_field.setObjectName("detailNameField")
        self.detail_name_field.setPlaceholderText("Product Name")
        self.detail_name_field.setFixedHeight(80)
        
        right_info_layout.addWidget(self.detail_name_field)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        right_info_layout.addWidget(line)

        self.detail_desc_field = QTextEdit()
        self.detail_desc_field.setObjectName("detailDescriptionField") # ตรงกับ CSS
        self.detail_desc_field.setFixedHeight(120)
        right_info_layout.addWidget(self.detail_desc_field)

        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setSpacing(8)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft) 
        
        self.detail_volume_field = QLineEdit()
        self.detail_writer_field = QLineEdit()
        self.detail_rated_field = QLineEdit()
        self.detail_isbn_field = QLineEdit()
        self.detail_category_field = QComboBox()
        self.detail_category_field.addItems(["MARVEL", "DC", "Image Comics"])
        self.detail_stock_field = QLineEdit()
        self.detail_price_field = QLineEdit()
        
        # กำหนด Object Name ให้เหมือนกันเพื่อใช้ CSS ร่วมกันได้ง่าย
        self.product_editable_fields = [
            self.detail_volume_field, self.detail_writer_field,
            self.detail_rated_field, self.detail_isbn_field,
            self.detail_category_field, self.detail_stock_field,
            self.detail_price_field
        ]
        for field in self.product_editable_fields:
            field.setObjectName("detailValueField")

        self.detail_price_field.setObjectName("detailPriceField") # แยกราคาออกมาเพื่อทำสีพิเศษ

        # เพิ่ม Label ที่มี Object Name ตรงกับ CSS
        def add_row(label_text, field):
            label = QLabel(label_text)
            label.setObjectName("detailFormLabel")
            form_layout.addRow(label, field)

        add_row("Volume/Issue :", self.detail_volume_field)
        add_row("Writer :", self.detail_writer_field)
        add_row("Rated :", self.detail_rated_field)
        add_row("ISBN (ID) :", self.detail_isbn_field)
        add_row("Category :", self.detail_category_field)
        add_row("Stock :", self.detail_stock_field)
        add_row("Price (THB) :", self.detail_price_field)

        right_info_layout.addWidget(form_widget)
        right_info_layout.addStretch() 

        # --- Buttons ---
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)

        self.btn_edit_product = QPushButton(" Edit")
        self.btn_edit_product.setObjectName("editButton") # หรือใช้ชื่อเดิมถ้ามี style อยู่แล้ว
        self.btn_edit_product.setIcon(QIcon("src/img/icon/edit.png"))
        self.btn_edit_product.setIconSize(QSize(50, 50))
        self.btn_edit_product.setFixedHeight(55)
        self.btn_edit_product.clicked.connect(self.toggle_product_edit_mode)

        self.btn_confirm_product = QPushButton(" Confirm")
        self.btn_confirm_product.setObjectName("confirmButton")
        self.btn_confirm_product.setIcon(QIcon("src/img/icon/confirm.png"))
        self.btn_confirm_product.setIconSize(QSize(50, 50))
        self.btn_confirm_product.setFixedHeight(55)
        self.btn_confirm_product.setVisible(False)
        self.btn_confirm_product.clicked.connect(self.save_product_changes)

        self.btn_cancel_edit = QPushButton(" Cancel")
        self.btn_cancel_edit.setObjectName("cancelButton")
        self.btn_cancel_edit.setIcon(QIcon("src/img/icon/delete.png")) # เปลี่ยนไอคอนตามเหมาะสม
        self.btn_cancel_edit.setIconSize(QSize(50, 50))
        self.btn_cancel_edit.setFixedHeight(55)
        self.btn_cancel_edit.setVisible(False)
        self.btn_cancel_edit.clicked.connect(self.cancel_product_edit)

        self.btn_delete_product = QPushButton(" Delete")
        self.btn_delete_product.setObjectName("deleteButton")
        self.btn_delete_product.setIcon(QIcon("src/img/icon/delete.png"))
        self.btn_delete_product.setIconSize(QSize(50, 50))
        self.btn_delete_product.setFixedHeight(55)
        self.btn_delete_product.clicked.connect(self.delete_product)

        buttons_layout.addWidget(self.btn_edit_product, 1)
        buttons_layout.addWidget(self.btn_cancel_edit, 1)
        buttons_layout.addWidget(self.btn_confirm_product, 1)
        buttons_layout.addWidget(self.btn_delete_product, 1)

        right_info_layout.addLayout(buttons_layout)
        main_detail_layout.addWidget(right_info_widget, 0, Qt.AlignmentFlag.AlignRight) 

        self.set_product_fields_read_only(True)
        return detail_frame

    def load_product_details(self, product_id):
        # รีเซ็ตสถานะการแก้ไขเมื่อโหลดสินค้าใหม่
        self.is_product_edit_mode = False
        self.set_product_fields_read_only(True)
        self.btn_edit_product.setVisible(True)
        self.btn_confirm_product.setVisible(False)
        self.btn_cancel_edit.setVisible(False) # ซ่อนปุ่ม Cancel
        self.btn_delete_product.setVisible(True) # แสดงปุ่ม Delete
        self.detail_upload_button.setVisible(False)
        self.detail_new_img_path = None

        self.current_detail_product_id = product_id
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            # เพิ่มการดึงข้อมูล category
            cursor.execute("""
                SELECT name, description, volume_issue, writer, rated, id, category, stock, price, cover_img 
                FROM product WHERE id = ?
            """, (product_id,))
            product_data = cursor.fetchone()
            conn.close()

            if product_data:
                (name, description, volume_issue, writer, rated, 
                 pid, category, stock, price, cover_img) = product_data
                
                self.detail_name_field.setText(name or "")
                self.detail_desc_field.setText(description or "")
                self.detail_volume_field.setText(volume_issue or "")
                self.detail_writer_field.setText(writer or "")
                self.detail_rated_field.setText(rated or "")
                self.detail_isbn_field.setText(str(pid) if pid is not None else "")
                
                # ตั้งค่า Category ComboBox
                cat_index = self.detail_category_field.findText(category or "", Qt.MatchFlag.MatchFixedString)
                if cat_index >= 0:
                    self.detail_category_field.setCurrentIndex(cat_index)

                self.detail_stock_field.setText(str(stock) if stock is not None else "0")
                self.detail_price_field.setText(f"{price:.2f}" if price is not None else "0.00")

                self.current_detail_stock = stock if stock is not None else 0
                self.current_detail_img_path = cover_img

                # โหลดรูปภาพ
                pixmap = QPixmap(cover_img) if cover_img and os.path.exists(cover_img) else QPixmap("src/img/icon/profile.png")
                if pixmap.isNull(): pixmap = QPixmap(250, 380); pixmap.fill(Qt.GlobalColor.gray)
                
                self.detail_cover_label.setPixmap(pixmap.scaled(
                    self.detail_cover_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                ))

            else:
                QMessageBox.warning(self, "Error", "Product not found.")
                self.show_browse_page()

        except Exception as e:
            print(f"Error loading product details: {e}")
            QMessageBox.warning(self, "Error", f"Could not load details: {e}")

    def show_product_detail_page(self, product_id):
        print(f"กำลังแสดงรายละเอียดสำหรับ ID: {product_id}")
        self.load_product_details(product_id)
        self.sidebar_stack.setCurrentIndex(2)
        self.main_content_stack.setCurrentIndex(2)

    # --- METHODS สำหรับการแก้ไขและลบสินค้า ---

    def set_product_fields_read_only(self, read_only):
        """ตั้งค่าสถานะ Read-Only ให้กับฟิลด์ข้อมูลสินค้า"""
        self.detail_name_field.setReadOnly(read_only)
        self.detail_desc_field.setReadOnly(read_only)
        for field in self.product_editable_fields:
            if isinstance(field, (QLineEdit, QTextEdit)):
                field.setReadOnly(read_only)
            elif isinstance(field, QComboBox):
                field.setEnabled(not read_only)

    def toggle_product_edit_mode(self):
        """สลับโหมดแก้ไขสินค้า"""
        self.is_product_edit_mode = True # เข้าสู่โหมดแก้ไขแน่นอนเมื่อกดปุ่ม Edit
        
        # เข้าสู่โหมดแก้ไข
        self.set_product_fields_read_only(False)
        # ไม่ต้องล็อก ISBN แล้วตามที่คุณต้องการ
        # self.detail_isbn_field.setReadOnly(True) 
        
        # จัดการการแสดงผลปุ่ม
        self.btn_edit_product.setVisible(False)
        self.btn_delete_product.setVisible(False) # ซ่อนปุ่ม Delete ขณะแก้ไขเพื่อป้องกันความสับสน
        self.btn_confirm_product.setVisible(True)
        self.btn_cancel_edit.setVisible(True) # แสดงปุ่ม Cancel
        self.detail_upload_button.setVisible(True)

    def cancel_product_edit(self):
        """ยกเลิกการแก้ไขและโหลดข้อมูลเดิมกลับมา"""
        self.is_product_edit_mode = False
        self.load_product_details(self.current_detail_product_id)

    def save_product_changes(self):
        """บันทึกการแก้ไขสินค้าลง Database (รวมถึงการแก้ ID)"""
        try:
            # ดึงข้อมูลจากฟิลด์
            new_id_str = self.detail_isbn_field.text().strip() # ดึง ID ใหม่
            name = self.detail_name_field.toPlainText().strip()
            desc = self.detail_desc_field.toPlainText().strip()
            volume = self.detail_volume_field.text().strip()
            writer = self.detail_writer_field.text().strip()
            rated = self.detail_rated_field.text().strip()
            category = self.detail_category_field.currentText()
            stock_str = self.detail_stock_field.text().strip()
            price_str = self.detail_price_field.text().strip()
            img_path = self.detail_new_img_path if self.detail_new_img_path else self.current_detail_img_path

            if not all([new_id_str, name, stock_str, price_str]):
                QMessageBox.warning(self, "Missing Info", "Please fill in ID, Name, Stock, and Price.")
                return

            new_id = int(new_id_str)
            stock = int(stock_str)
            price = float(price_str)

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # ถ้ามีการเปลี่ยน ID ต้องเช็คก่อนว่า ID ใหม่ซ้ำไหม
            if new_id != self.current_detail_product_id:
                cursor.execute("SELECT 1 FROM product WHERE id = ?", (new_id,))
                if cursor.fetchone():
                    QMessageBox.warning(self, "Duplicate ID", f"Product ID {new_id} already exists. Please use a unique ID.")
                    conn.close()
                    return

            # อัปเดตข้อมูล (รวมถึง ID)
            cursor.execute("""
                UPDATE product 
                SET id=?, name=?, description=?, volume_issue=?, writer=?, rated=?, category=?, stock=?, price=?, cover_img=?
                WHERE id=?
            """, (new_id, name, desc, volume, writer, rated, category, stock, price, img_path, self.current_detail_product_id))
            
            conn.commit()
            conn.close()

            QMessageBox.information(self, "Success", "Product updated successfully!")
            # โหลดข้อมูลใหม่โดยใช้ ID ใหม่ (ถ้ามีการเปลี่ยน)
            self.load_product_details(new_id) 

        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "ID and Stock must be integers, Price must be a number.")
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Database Error", "ID might already exist or other constraint failed.")
        except Exception as e:
            print(f"Error saving product: {e}")
            QMessageBox.warning(self, "Error", f"Could not save changes: {e}")

    def select_detail_image(self):
        """เลือกรูปภาพใหม่สำหรับสินค้าในหน้า Detail"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Cover Image", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.detail_new_img_path = os.path.normpath(file_path)
            pixmap = QPixmap(self.detail_new_img_path)
            self.detail_cover_label.setPixmap(pixmap.scaled(
                self.detail_cover_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            ))

    def delete_product(self):
        """ลบสินค้าออกจาก Database"""
        # ถามยืนยันก่อนลบ
        reply = QMessageBox.question(
            self, 'Confirm Delete', 
            f"Are you sure you want to delete this product?\n(ID: {self.current_detail_product_id})",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM product WHERE id = ?", (self.current_detail_product_id,))
                conn.commit()
                conn.close()

                QMessageBox.information(self, "Deleted", "Product has been deleted.")
                self.show_browse_page() # กลับไปหน้า Browse

            except Exception as e:
                print(f"Error deleting product: {e}")
                QMessageBox.warning(self, "Error", f"Could not delete product: {e}")
        
        
        
    # --- [NEW] SIDEBARS FOR ORDERS ---
    def create_orders_sidebar(self):
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("Sidebar")
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(20, 30, 20, 20)
        sidebar_layout.setSpacing(25)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        button_height = 55
        # คุณอาจจะอยากเพิ่มปุ่มกรอง Status ตรงนี้ในอนาคต (Pending, Paid, etc.)
        
        btn_back = QPushButton("Back")
        btn_back.setObjectName("backsidebarButton")
        btn_back.setFixedHeight(button_height)
        btn_back.clicked.connect(self.show_browse_page)
        sidebar_layout.addWidget(btn_back)

        sidebar_layout.addStretch()
        return sidebar_frame

    def create_order_details_sidebar(self):
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
        # กลับไปหน้ารายการ Orders
        btn_back.clicked.connect(self.show_orders_page)
        sidebar_layout.addWidget(btn_back)

        sidebar_layout.addStretch()
        return sidebar_frame

    # --- [NEW] ORDERS PAGE (ADMIN) ---
    def create_orders_page(self):
        page_frame = QFrame()
        main_layout = QVBoxLayout(page_frame)
        # [MARGINS] ตามต้นฉบับ mainuser.py ห้ามแก้ไข
        main_layout.setContentsMargins(250, 40, 50, 40)
        main_layout.setSpacing(20)

        self.orders_table = QTableWidget()
        self.orders_table.setObjectName("ordersTable")
        # [MODIFIED] เพิ่มเป็น 3 คอลัมน์เพื่อใส่ CUSTOMER
        self.orders_table.setColumnCount(3)
        self.orders_table.setHorizontalHeaderLabels(["Order Info", "CUSTOMER", "STATUS"])

        header = self.orders_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        # ปรับขนาดคอลัมน์ CUSTOMER และ STATUS
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.orders_table.setColumnWidth(2, 150)

        self.orders_table.verticalHeader().setVisible(False)
        self.orders_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.orders_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.orders_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.orders_table.setShowGrid(True)

        self.orders_table.cellClicked.connect(self.on_order_clicked)

        main_layout.addWidget(self.orders_table)

        return page_frame

    def show_orders_page(self):
        self.load_orders_data()
        self.sidebar_stack.setCurrentIndex(4)
        self.main_content_stack.setCurrentIndex(4)

    def load_orders_data(self):
        self.orders_table.setRowCount(0)
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            # [MODIFIED] Query สำหรับ Admin ดึงทั้งหมด และดึง user_id ด้วย
            cursor.execute("""
                SELECT order_id, order_date, status, user_id 
                FROM orders
                ORDER BY order_id DESC
            """)
            orders = cursor.fetchall()
            conn.close()

            self.orders_table.setRowCount(len(orders))
            for i, (order_id, order_date, status, user_id) in enumerate(orders):
                # --- Column 0: Order Info ---
                date_widget = QWidget()
                date_layout = QVBoxLayout(date_widget)
                date_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                date_layout.setSpacing(0)

                lbl_title = QLabel(f"Order ID: #{order_id}")
                lbl_title.setObjectName("orderDateTitle")
                lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
                date_layout.addWidget(lbl_title)

                # แยกวันที่และเวลา
                parts = order_date.split(' ')
                date_text = parts[0]
                time_text = parts[1] if len(parts) > 1 else ""

                lbl_date = QLabel(date_text)
                lbl_date.setObjectName("orderDateLabel")
                lbl_date.setAlignment(Qt.AlignmentFlag.AlignCenter)
                date_layout.addWidget(lbl_date)

                if time_text:
                    lbl_time = QLabel(time_text)
                    lbl_time.setObjectName("orderTimeLabel")
                    lbl_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    date_layout.addWidget(lbl_time)

                self.orders_table.setCellWidget(i, 0, date_widget)

                # --- [NEW] Column 1: CUSTOMER ---
                user_item = QTableWidgetItem(str(user_id))
                user_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                user_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.orders_table.setItem(i, 1, user_item)

                # --- Column 2: STATUS ---
                status_item = QTableWidgetItem(status)
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                status_item.setFont(QFont("Arial", 14, QFont.Weight.Bold)) # ปรับฟอนต์เล็กน้อยให้เหมาะกับ Admin
                
                # กำหนดสีสถานะ (Optional: เพื่อความสวยงามของ Admin)
                if status == 'pending':
                    status_item.setForeground(QBrush(QColor("#f39c12"))) # สีส้ม
                elif status == 'paid':
                    status_item.setForeground(QBrush(QColor("#2ecc71"))) # สีเขียว
                elif status == 'cancelled':
                    status_item.setForeground(QBrush(QColor("#ff0000"))) # สีเขียว
                elif status == 'dispatched':
                    status_item.setForeground(QBrush(QColor("#1aff00"))) # สีเขียว

                # เก็บ order_id ไว้ใน UserData ของ cell นี้เพื่อใช้ตอนคลิก
                status_item.setData(Qt.ItemDataRole.UserRole, order_id)
                status_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.orders_table.setItem(i, 2, status_item)

                self.orders_table.setRowHeight(i, 110) # ปรับความสูงแถวเล็กน้อย

        except Exception as e:
            print(f"Error loading orders: {e}")

    def on_order_clicked(self, row, col):
        # ดึง order_id ที่ซ่อนไว้ในคอลัมน์ Status (index 2)
        status_item = self.orders_table.item(row, 2)
        if status_item:
            order_id = status_item.data(Qt.ItemDataRole.UserRole)
            self.show_order_details_page(order_id)



    # --- [UPDATED] ORDER DETAILS PAGE (ADMIN) ---
    def create_order_details_page(self):
        # 1. สร้าง Widget หลักสำหรับหน้านี้
        page_widget = QWidget()
        page_layout = QVBoxLayout(page_widget)
        page_layout.setContentsMargins(290, 10, 20, 10)
        page_layout.setSpacing(0)

# 2. สร้าง Scroll Area หลัก (ครอบทั้งหน้าเผื่อจอเล็กมาก)
        main_scroll_area = QScrollArea()
        main_scroll_area.setObjectName("orderDetailScrollArea")
        main_scroll_area.setWidgetResizable(True)
        main_scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # 3. สร้าง Widget เนื้อหาข้างใน
        content_widget = QWidget()
        content_widget.setObjectName("orderDetailContentWidget")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(50, 30, 50, 30)
        content_layout.setSpacing(20)

        # --- Header ---
        self.order_details_header = QLabel("Order Details #...")
        self.order_details_header.setObjectName("detailsHeader")
        content_layout.addWidget(self.order_details_header)

        # --- ตารางสินค้า ---
        self.order_items_table = QTableWidget()
        self.order_items_table.setObjectName("cartTable")
        self.order_items_table.setColumnCount(4)
        self.order_items_table.setHorizontalHeaderLabels(["ITEM", "UNIT PRICE", "QUANTITY", "AMOUNT"])
        self.order_items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.order_items_table.verticalHeader().setVisible(False)
        self.order_items_table.setMinimumHeight(350)
        content_layout.addWidget(self.order_items_table)

        # --- ส่วนล่าง (แบ่งซ้าย-ขวา) ---
        bottom_split_layout = QHBoxLayout()
        bottom_split_layout.setSpacing(30)
        bottom_split_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # === [UPDATED] ฝั่งซ้าย: ที่อยู่จัดส่ง (มี Scrollbar เฉพาะส่วนนี้) ===
        # 1. สร้าง Scroll Area สำหรับฝั่งซ้าย
        left_scroll_area = QScrollArea()
        left_scroll_area.setWidgetResizable(True)
        left_scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        left_scroll_area.setMaximumHeight(400) # <-- กำหนดความสูงสูงสุด ถ้าเกินนี้จะเลื่อนได้

        # 2. สร้าง Frame ข้อมูลลูกค้า
        customer_info_frame = QFrame()
        customer_info_frame.setObjectName("customerInfoFrame")
        customer_layout = QVBoxLayout(customer_info_frame)
        customer_layout.setContentsMargins(20, 20, 20, 20)
        
        header_label = QLabel("ที่อยู่จัดส่ง :")
        header_label.setObjectName("customerInfoHeader")
        customer_layout.addWidget(header_label)
        customer_layout.addSpacing(10)

        info_form = QFormLayout()
        info_form.setSpacing(15)

        self.cust_username_label = QLabel("-")
        self.cust_firstname_label = QLabel("-")
        self.cust_lastname_label = QLabel("-")
        self.cust_tel_label = QLabel("-")
        self.cust_email_label = QLabel("-")
        self.cust_address_label = QLabel("-")
        self.cust_address_label.setWordWrap(True) # สำคัญ! ให้ตัดบรรทัด

        for lbl in [self.cust_username_label, self.cust_firstname_label, self.cust_lastname_label,
                    self.cust_tel_label, self.cust_email_label, self.cust_address_label]:
            lbl.setObjectName("customerInfoValue")

        def form_lbl(text):
            l = QLabel(text)
            l.setObjectName("customerInfoLabel")
            return l

        info_form.addRow(form_lbl("Customer ID:"), self.cust_username_label)
        info_form.addRow(form_lbl("First Name:"), self.cust_firstname_label)
        info_form.addRow(form_lbl("Last Name:"), self.cust_lastname_label)
        info_form.addRow(form_lbl("Tel:"), self.cust_tel_label)
        info_form.addRow(form_lbl("Email:"), self.cust_email_label)
        info_form.addRow(form_lbl("Address:"), self.cust_address_label)

        customer_layout.addLayout(info_form)
        
        # 3. นำ Frame ใส่ใน Scroll Area ฝั่งซ้าย
        left_scroll_area.setWidget(customer_info_frame)
        bottom_split_layout.addWidget(left_scroll_area, 60) # กว้าง 60%

        # === [ฝั่งขวา] สรุปยอดเงิน ===
        summary_widget = QWidget()
        summary_layout = QVBoxLayout(summary_widget)
        summary_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        summary_layout.setSpacing(10)

        def create_summary_row(text, val_label_obj_name, is_total=False):
            row = QWidget(); l = QHBoxLayout(row); l.setContentsMargins(0,0,0,0); l.setAlignment(Qt.AlignmentFlag.AlignRight)
            lbl_t = QLabel(text); lbl_t.setObjectName("cartSummaryLabel"); lbl_t.setAlignment(Qt.AlignmentFlag.AlignRight)
            lbl_v = QLabel("0.00 THB"); lbl_v.setObjectName(val_label_obj_name); lbl_v.setAlignment(Qt.AlignmentFlag.AlignRight)
            if is_total: lbl_v.setMinimumWidth(200)
            else: lbl_v.setFixedWidth(150)
            l.addWidget(lbl_t); l.addWidget(lbl_v)
            return row, lbl_v

        row_sub, self.ord_subtotal_label = create_summary_row("Subtotal :", "cartSummaryValue")
        row_ship, self.ord_shipping_label = create_summary_row("Shipping :", "cartSummaryValue")
        row_vat, self.ord_vat_label = create_summary_row("VAT 7% :", "cartSummaryValue")
        row_tot, self.ord_total_label = create_summary_row("Total :", "cartTotalValue", True)

        summary_layout.addWidget(row_sub)
        summary_layout.addWidget(row_ship)
        summary_layout.addWidget(row_vat)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Plain)
        line.setFixedWidth(300)
        line.setObjectName("summarySeparatorLine")
        summary_layout.addWidget(line, alignment=Qt.AlignmentFlag.AlignRight)
        
        summary_layout.addWidget(row_tot)
        bottom_split_layout.addWidget(summary_widget, 40) # กว้าง 40%

        content_layout.addLayout(bottom_split_layout)

        # --- ปุ่มกด ---
        buttons_layout = QHBoxLayout()
        #self.ord_back_button = QPushButton("Back to Orders")
        #self.ord_back_button.setObjectName("ordBackButton")
        #self.ord_back_button.setFixedSize(180, 50)
        #self.ord_back_button.clicked.connect(self.show_orders_page)
        
        self.ord_view_slip_button = QPushButton("View Payment Slip")
        self.ord_view_slip_button.setObjectName("confirmButton")
        self.ord_view_slip_button.setFixedSize(220, 50)
        self.ord_view_slip_button.clicked.connect(self.handle_view_slip_image_admin)

        #buttons_layout.addWidget(self.ord_back_button)
        buttons_layout.addStretch()
        
        # --- [ใหม่] ส่วนแก้ไขสถานะ ---
        # 1. ComboBox สำหรับเลือกสถานะ (ซ่อนไว้ก่อน)
        self.status_combo = QComboBox()
        # ใช้ lowercase เพื่อให้ตรงกับที่มักใช้ใน DB (ปรับแก้ได้ถ้า DB คุณเก็บตัวพิมพ์ใหญ่)
        self.status_combo.addItems(["pending", "paid", "dispatched", "cancelled"])
        self.status_combo.setFixedSize(150, 50)
        # ปรับสไตล์ให้ดูต่างจากปุ่มปกติเล็กน้อย
        self.status_combo.setObjectName("statusEditCombo")
        self.status_combo.setVisible(False)

        # 2. ปุ่ม Save สำหรับยืนยันการเปลี่ยนสถานะ (ซ่อนไว้ก่อน)
        self.btn_save_status = QPushButton("Save")
        self.btn_save_status.setObjectName("confirmButton") # ใช้สีเขียว
        self.btn_save_status.setFixedSize(50, 50)
        self.btn_save_status.setVisible(False)
        self.btn_save_status.clicked.connect(self.handle_save_status)

        # 3. ปุ่ม Cancel เล็กๆ สำหรับยกเลิกการ edit (ซ่อนไว้ก่อน)
        self.btn_cancel_status_edit = QPushButton("X")
        self.btn_cancel_status_edit.setFixedSize(40, 45)
        self.btn_cancel_status_edit.setObjectName("cancelStatusButton")
        self.btn_cancel_status_edit.setVisible(False)
        self.btn_cancel_status_edit.clicked.connect(self.toggle_status_edit_mode)

        # 4. ปุ่ม Edit Status (แสดงตอนแรก)
        self.btn_edit_status = QPushButton("Edit Status")
        self.btn_edit_status.setFixedSize(140, 50)
        self.btn_edit_status.setObjectName("editStatusButton")
        self.btn_edit_status.clicked.connect(self.toggle_status_edit_mode)

        # เพิ่มเข้า Layout
        buttons_layout.addWidget(self.status_combo)
        buttons_layout.addWidget(self.btn_cancel_status_edit)
        buttons_layout.addWidget(self.btn_save_status)
        buttons_layout.addWidget(self.btn_edit_status)
        buttons_layout.addSpacing(15)
        # ---------------------------
        
        buttons_layout.addWidget(self.ord_view_slip_button)
        
        # --- [ใหม่] เพิ่มปุ่ม Be Certified ต่อจากปุ่มดูสลิป ---
        self.btn_be_certified = QPushButton("Be Certified")
        # ใช้ ObjectName เดียวกับปุ่ม confirm เพื่อให้เป็นสีเขียว (ถ้าใน CSS มี)
        # หรือจะตั้งชื่อใหม่แล้วไปเขียน CSS เพิ่มก็ได้
        self.btn_be_certified.setObjectName("confirmButton")
        self.btn_be_certified.setFixedSize(180, 50)
        # เชื่อมกับฟังก์ชันที่จะสร้างในจุดที่ 2
        self.btn_be_certified.clicked.connect(self.handle_be_certified)
        
        buttons_layout.addSpacing(15) # เว้นระยะห่างนิดหน่อย
        buttons_layout.addWidget(self.btn_be_certified)
        # --------------------------------------------------
        
        
        content_layout.addSpacing(30)
        content_layout.addLayout(buttons_layout)

        # นำ Content ทั้งหมดใส่ใน Main Scroll Area
        main_scroll_area.setWidget(content_widget)
        page_layout.addWidget(main_scroll_area)

        return page_widget

    # --- [ใหม่] ฟังก์ชันสำหรับปุ่ม Be Certified ---
    def handle_be_certified(self):
        # ถามยืนยันก่อน
        reply = QMessageBox.question(
            self, 'Confirm Certification',
            f"Are you sure you want to certify Order #{self.current_viewing_order_id}?\nThis will record the current payment date.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # หาวันเวลาปัจจุบัน
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                # อัปเดต payment_date และเปลี่ยนสถานะเป็น paid
                cursor.execute("""
                    UPDATE orders 
                    SET payment_date = ?, status = 'paid' 
                    WHERE order_id = ?
                """, (current_time, self.current_viewing_order_id))
                conn.commit()
                conn.close()

                QMessageBox.information(self, "Success", f"Order #{self.current_viewing_order_id} has been certified.")
                
                # โหลดหน้า Order Details ใหม่เพื่อแสดงข้อมูลล่าสุด (ถ้าต้องการ)
                # หรือจะกลับไปหน้ารายการ Orders ก็ได้ โดยใช้ self.show_orders_page()
                self.show_orders_page() 

            except Exception as e:
                print(f"Error certifying order: {e}")
                QMessageBox.warning(self, "Error", f"Could not certify order: {e}")

    def show_order_details_page(self, order_id):
        self.load_order_details(order_id)
        self.sidebar_stack.setCurrentIndex(5)
        self.main_content_stack.setCurrentIndex(5)

    # --- [UPDATED] LOAD ORDER DETAILS ---
   # --- [UPDATED] LOAD ORDER DETAILS ---
    def load_order_details(self, order_id):
        self.current_viewing_order_id = order_id
        self.order_details_header.setText(f"Order Details #{order_id}")
        self.order_items_table.setRowCount(0)
        
        # รีเซ็ตข้อมูลลูกค้าก่อนโหลดใหม่
        for lbl in [self.cust_username_label, self.cust_firstname_label, self.cust_lastname_label,
                    self.cust_tel_label, self.cust_email_label, self.cust_address_label]:
            lbl.setText("Loading...")

        # รีเซ็ตปุ่ม Edit Status
        self.status_combo.setVisible(False)
        self.btn_save_status.setVisible(False)
        self.btn_cancel_status_edit.setVisible(False)
        
        # --- [EDITED] ---
        # ลบ self.btn_edit_status.setVisible(True) จากตรงนี้
        # เราจะไปกำหนดค่าที่ถูกต้องหลังจากดึง status ได้
        # self.btn_edit_status.setVisible(True) 
        # -------------------

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # 1. ดึงข้อมูลสรุปออเดอร์ (เพิ่ม status, payment_date)
            cursor.execute("""
                SELECT subtotal, shipping_fee, vat, total, user_id, slip_image, status, payment_date
                FROM orders WHERE order_id = ?
            """, (order_id,))
            order_summary = cursor.fetchone()
            
            if order_summary:
                sub, ship, vat, tot, user_id, slip_path, status, pay_date = order_summary
                
                self.ord_subtotal_label.setText(f"{sub:,.2f} THB")
                self.ord_shipping_label.setText(f"{ship:,.2f} THB")
                self.ord_vat_label.setText(f"{vat:,.2f} THB")
                self.ord_total_label.setText(f"{tot:,.2f} THB")
                self.current_slip_path_admin = slip_path
                
                # เก็บสถานะปัจจุบันไว้ใช้งาน
                self.current_order_status = status
                self.current_payment_date = pay_date

                # ตั้งค่า ComboBox ให้ตรงกับสถานะปัจจุบัน
                index = self.status_combo.findText(status, Qt.MatchFlag.MatchFixedString)
                if index >= 0:
                    self.status_combo.setCurrentIndex(index)

                # --- [NEW LOGIC START] ---
                # ตรวจสอบสถานะเพื่อซ่อน/แสดงปุ่ม

                # 1. ตรวจสอบปุ่ม Edit Status
                if status == 'cancelled' or status == 'dispatched':
                    # ถ้าเป็น 'cancelled' หรือ 'dispatched' ให้ซ่อนปุ่ม Edit
                    self.btn_edit_status.setVisible(False)
                else:
                    # สถานะอื่น (pending, paid) ให้แสดงปุ่ม Edit
                    self.btn_edit_status.setVisible(True)

                # 2. ตรวจสอบปุ่ม Be Certified
                # (ซ่อนถ้าจ่ายเงินแล้ว/ส่งของแล้ว/ยกเลิกแล้ว)
                if status == 'paid' or status == 'dispatched' or status == 'cancelled':
                    self.btn_be_certified.setVisible(False)
                else:
                    # สถานะอื่น (เช่น pending) ให้แสดง
                    self.btn_be_certified.setVisible(True)
                # --- [NEW LOGIC END] ---

                # 2. ดึงข้อมูลลูกค้า
                cursor.execute("""
                    SELECT first_name, last_name, phone, email, address 
                    FROM users WHERE username = ?
                """, (user_id,))
                user_info = cursor.fetchone()
                
                self.cust_username_label.setText(str(user_id))
                if user_info:
                    fname, lname, phone, email, address = user_info
                    self.cust_firstname_label.setText(fname if fname else "-")
                    self.cust_lastname_label.setText(lname if lname else "-")
                    self.cust_tel_label.setText(phone if phone else "-")
                    self.cust_email_label.setText(email if email else "-")
                    self.cust_address_label.setText(address if address else "-")
                else:
                    for lbl in [self.cust_firstname_label, self.cust_lastname_label,
                                self.cust_tel_label, self.cust_email_label, self.cust_address_label]:
                        lbl.setText("User not found")

            # 3. ดึงรายการสินค้า
            cursor.execute("""
                SELECT p.name, p.cover_img, oi.unit_price, oi.quantity
                FROM order_items oi
                JOIN product p ON oi.product_id = p.id
                WHERE oi.order_id = ?
            """, (order_id,))
            items = cursor.fetchall()
            conn.close()

            self.order_items_table.setRowCount(len(items))
            for i, (p_name, p_img, unit_price, quantity) in enumerate(items):
                # (ส่วนการแสดงผล Item ในตาราง... เหมือนเดิม)
                item_widget = QWidget()
                item_layout = QHBoxLayout(item_widget)
                item_layout.setContentsMargins(5, 5, 5, 5)
                img_label = QLabel()
                img_label.setFixedSize(60, 90)
                img_label.setScaledContents(True)
                if p_img and os.path.exists(p_img):
                    img_label.setPixmap(QPixmap(p_img))
                else:
                    img_label.setPixmap(QPixmap("src/img/icon/profile.png"))
                name_label = QLabel(p_name)
                name_label.setWordWrap(True)
                name_label.setObjectName("cartItemName")
                item_layout.addWidget(img_label)
                item_layout.addWidget(name_label)
                self.order_items_table.setCellWidget(i, 0, item_widget)

                price_item = QTableWidgetItem(f"{unit_price:,.2f} THB")
                price_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                price_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.order_items_table.setItem(i, 1, price_item)

                qty_item = QTableWidgetItem(str(quantity))
                qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                qty_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.order_items_table.setItem(i, 2, qty_item)

                amount = unit_price * quantity
                amount_item = QTableWidgetItem(f"{amount:,.2f} THB")
                amount_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                amount_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.order_items_table.setItem(i, 3, amount_item)

                self.order_items_table.setRowHeight(i, 100)

        except Exception as e:
            print(f"Error loading order details: {e}")
            QMessageBox.warning(self, "Error", "Could not load order details.")


    def toggle_status_edit_mode(self):
        """สลับโหมดแสดง/ซ่อนปุ่มแก้ไขสถานะ"""
        is_editing = self.status_combo.isVisible()
        self.status_combo.setVisible(not is_editing)
        self.btn_save_status.setVisible(not is_editing)
        self.btn_cancel_status_edit.setVisible(not is_editing)
        self.btn_edit_status.setVisible(is_editing)

        if is_editing:
            # คืนค่า ComboBox เป็นค่าเดิมถ้ายกเลิก
            index = self.status_combo.findText(self.current_order_status, Qt.MatchFlag.MatchFixedString)
            if index >= 0:
                self.status_combo.setCurrentIndex(index)

    def handle_save_status(self):
        """บันทึกการเปลี่ยนแปลงสถานะพร้อมเงื่อนไขพิเศษ"""
        new_status = self.status_combo.currentText()
        old_status = self.current_order_status

        if new_status == old_status:
            self.toggle_status_edit_mode() # ปิดโหมดแก้ไขถ้าไม่มีอะไรเปลี่ยนแปลง
            return

        # --- [RULE 1: ตรวจสอบการเปลี่ยนเป็น "paid"] ---
        if new_status == "paid":
            if old_status == "dispatched":
                pass # อนุญาต (dispatched -> paid)
            else:
                # [Block] ห้ามเปลี่ยนสถานะอื่นเป็น "paid" ด้วยตนเอง
                QMessageBox.warning(self, "Invalid Action", 
                                    "Cannot manually set status to 'paid'.\n"
                                    "Please use the 'Be Certified' button to confirm payment.")
                
                index = self.status_combo.findText(old_status, Qt.MatchFlag.MatchFixedString)
                if index >= 0:
                    self.status_combo.setCurrentIndex(index)
                return 

        # --- [RULE 2: ตรวจสอบการเปลี่ยนเป็น "pending"] ---
        if new_status == "pending":
            
            # --- [EDITED] ---
            # [Block] ห้ามเปลี่ยนจาก "dispatched" หรือ "paid" กลับเป็น "pending"
            if old_status == "dispatched" or old_status == "paid": 
                
                msg = ""
                if old_status == "dispatched":
                    msg = "Cannot change 'dispatched' status back to 'pending'."
                elif old_status == "paid":
                    msg = "Cannot change a 'paid' order back to 'pending'."

                QMessageBox.warning(self, "Invalid Action", msg)
                
                index = self.status_combo.findText(old_status, Qt.MatchFlag.MatchFixedString)
                if index >= 0:
                    self.status_combo.setCurrentIndex(index)
                return
            # ------------------

        # --- [RULE 3: ตรวจสอบการเปลี่ยนเป็น "dispatched"] ---
        if new_status == "dispatched" and not self.current_payment_date:
            QMessageBox.warning(self, "Cannot Dispatch", 
                                "This order has not been paid yet (No payment date).")
            
            index = self.status_combo.findText(old_status, Qt.MatchFlag.MatchFixedString)
            if index >= 0:
                self.status_combo.setCurrentIndex(index)
            return

        # --- ยืนยันการเปลี่ยนแปลง ---
        reply = QMessageBox.question(
            self, 'Confirm Status Change',
            f"Change status from '{old_status}' to '{new_status}'?\n(This action may affect stock or records)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # --- [DB LOGIC] ---

                # (Logic คืนสต็อกเมื่อ Cancel - เหมือนเดิม)
                if new_status == "cancelled" and old_status != "cancelled":
                    cursor.execute("""
                        UPDATE orders 
                        SET status = ?, cancelled_date = ? 
                        WHERE order_id = ?
                    """, (new_status, current_time, self.current_viewing_order_id))

                    # คืนสต็อก (Code เหมือนเดิม)
                    cursor.execute("SELECT product_id, quantity FROM order_items WHERE order_id = ?", (self.current_viewing_order_id,))
                    items_to_restore = cursor.fetchall()
                    for pid, qty in items_to_restore:
                        cursor.execute("UPDATE product SET stock = stock + ? WHERE id = ?", (qty, pid))
                    print(f"Restored stock for Order #{self.current_viewing_order_id}")

                # --- [EDITED] ---
                # (ลบ elif ที่เช็ค new_status == "pending" and old_status == "paid" ออกไป)
                # ------------------
                else:
                    # กรณีอื่นๆ ที่ผ่านการตรวจสอบมาแล้ว
                    # (เช่น paid -> dispatched, dispatched -> paid)
                    cursor.execute("UPDATE orders SET status = ? WHERE order_id = ?", 
                                   (new_status, self.current_viewing_order_id))

                # --- [END DB LOGIC] ---

                conn.commit()
                conn.close()

                QMessageBox.information(self, "Success", f"Status changed to '{new_status}'.")
                self.load_order_details(self.current_viewing_order_id)

            except Exception as e:
                print(f"Error updating status: {e}")
                QMessageBox.warning(self, "Error", f"Could not update status: {e}")




    def handle_view_slip_image_admin(self):
        # ฟังก์ชันสำหรับดูสลิป (เหมือนของ User แต่ปรับปรุงเล็กน้อย)
        if not hasattr(self, 'current_slip_path_admin') or not self.current_slip_path_admin:
            QMessageBox.information(self, "No Slip", "คำสั่งซื้อนี้ไม่มีการแนบรูปภาพสลิป")
            return

        image_path = self.current_slip_path_admin
        if os.path.exists(image_path):
            if os.name == 'nt':
                os.startfile(image_path)
            else:
                import subprocess
                opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
                subprocess.call([opener, image_path])
        else:
            QMessageBox.warning(self, "File Not Found", f"ไม่พบไฟล์รูปภาพที่:\n{image_path}")
        
        
        
    
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
            self.disable_edit_mode()
            self.is_in_edit_mode = False
        else:
            self.enable_edit_mode()
            self.is_in_edit_mode = True

    def select_profile_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Profile Image", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.new_profile_img_path = os.path.normpath(file_path)
            target_size = 250
            scaled_pixmap = self.create_scaled_pixmap(self.new_profile_img_path, target_size)
            self.profile_pic_label.setPixmap(scaled_pixmap)

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
                SET first_name = ?, last_name = ?, gender = ?, email = ?, phone = ?, address = ?, profile_img = ?
                WHERE username = ?
            """, (fname, lname, gender, email, phone, address, image_to_save, self.current_username))
            conn.commit()
            conn.close()
            
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
        self.filter_products_by_category("ALL")

    def handle_logout(self):
        reply = QMessageBox.question(self, 'Logout', 'Are you sure you want to logout?',
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                      QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.logout_requested.emit()
            self.close()

    def show_add_comic_page(self):
        print("กำลังแสดงหน้า Add Comic")
        self.clear_add_comic_form()
        self.sidebar_stack.setCurrentIndex(3)
        self.main_content_stack.setCurrentIndex(3)

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
        self.add_comic_img_preview.clear()
        self.add_comic_img_preview.setText("Upload Cover")
        self.add_comic_img_preview.setStyleSheet("background-color: white; border: 1px solid #ccc;")

    def select_new_comic_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Comic Cover Image", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.new_comic_img_path = os.path.normpath(file_path)
            try:
                target_size = self.add_comic_img_preview.size()
                pixmap = QPixmap(self.new_comic_img_path)
                scaled_pixmap = pixmap.scaled(
                    target_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                )
                self.add_comic_img_preview.setPixmap(scaled_pixmap)
                self.add_comic_img_preview.setText("") 
            except Exception as e:
                print(f"Error loading new comic image: {e}")
                self.add_comic_img_preview.setText("Error loading image")
                self.new_comic_img_path = None

    def save_new_comic(self):
        try:
            name = self.add_comic_name.text().strip()
            volume = self.add_comic_volume.text().strip()
            desc = self.add_comic_desc.toPlainText().strip()
            writer = self.add_comic_writer.text().strip()
            rated = self.add_comic_rated.text().strip()
            isbn_str = self.add_comic_isbn.text().strip()
            category = self.add_comic_category.currentText()
            stock_str = self.add_comic_stock.text().strip()
            price_str = self.add_comic_price.text().strip()
            img_path = self.new_comic_img_path

            if not all([name, isbn_str, stock_str, price_str, img_path]):
                QMessageBox.warning(self, "Missing Information", 
                                    "Please fill in all fields (Name, ISBN, Stock, Price) and upload an image.")
                return

            try:
                id_val = int(isbn_str) 
                stock = int(stock_str)
                price = float(price_str)
                if stock < 0 or price < 0:
                    raise ValueError("Stock and Price cannot be negative.")
            except ValueError as e:
                QMessageBox.warning(self, "Invalid Input", 
                                    f"Please enter valid numbers for ISBN, Stock, and Price.\n(Error: {e})")
                return

            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM product WHERE id = ?", (id_val,))
            if cursor.fetchone():
                QMessageBox.warning(self, "Duplicate Entry", 
                                    "A product with this ISBN (ID) already exists. Please use a unique ID.")
                conn.close()
                return
            
            cursor.execute("""
                INSERT INTO product (
                    id, name, volume_issue, description, writer, rated, 
                    category, stock, price, cover_img, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (id_val, name, volume, desc, writer, rated, category, stock, price, img_path, created_at))
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "Success", "New comic added successfully!")
            self.show_browse_page()

        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Database Error", "An error occurred (IntegrityError). This ISBN (ID) might already exist.")
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการบันทึก comic: {e}")
            QMessageBox.warning(self, "Error", f"Could not save new comic: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainAdminWindow(username="data6189") 
    window.show()
    sys.exit(app.exec())