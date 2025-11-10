import sys
import os
import sqlite3
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

# --- IMPORT สำหรับ ReportLab (สร้าง PDF) ---
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
# ----------------------------------------

# --- ตั้งค่า PATH ต่างๆ ---
DB_PATH = "src/database/thisshop.db"
FONT_PATH = "src/font/THSarabunNew.ttf"
LOGO_PATH = "src/img/icon/logo.png"
PDF_OUTPUT_DIR = "receipts"
# -----------------------

# --- IMPORT สำหรับ Info Window ---
InfoWindow = None  # กำหนดค่าเริ่มต้นเป็น None ป้องกัน NameError
try:
    from info_window import InfoWindow
except ImportError:
    print("Warning: ไม่สามารถ import InfoWindow ได้ กรุณาตรวจสอบว่าไฟล์ info_window.py อยู่ในโฟลเดอร์เดียวกัน")
# --------------------------------


class MainUserWindow(QMainWindow):
    logout_requested = pyqtSignal()

    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.current_username = username

        self.new_profile_img_path = None
        self.current_profile_img_path = None
        self.editable_profile_fields = []

        self.is_in_edit_mode = False

        # สถานะสำหรับการกรองและเรียงลำดับ
        self.current_category = "ALL"
        self.current_search_term = ""
        self.current_sort_order = "Newest"

        # สถานะหน้ารายละเอียด
        self.current_detail_product_id = None
        self.current_detail_stock = 0

        # สถานะสำหรับหน้า Checkout
        self.current_slip_path = None

        # [NEW] สถานะสำหรับหน้า Order Details (เพื่อใช้ในการพิมพ์ใบเสร็จ)
        self.current_viewing_order_id = None

        # [NEW] เตรียมฟอนต์สำหรับ PDF
        self.init_receipt_font()

        self.setWindowTitle(f"Beyond Comics - Welcome : {self.current_username}")
        self.showMaximized()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.header_frame = self.create_header()
        self.main_layout.addWidget(self.header_frame)
        
        self.create_info_button()

        self.body_widget = QWidget()
        self.body_layout = QHBoxLayout(self.body_widget)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(0)

        self.sidebar_stack = QStackedWidget()
        self.sidebar_stack.setFixedWidth(260)

        self.browse_sidebar = self.create_browse_sidebar()
        self.profile_sidebar = self.create_profile_sidebar()
        self.detail_sidebar = self.create_detail_sidebar()
        self.cart_sidebar = self.create_cart_sidebar()
        self.checkout_sidebar = self.create_checkout_sidebar()
        self.orders_sidebar = self.create_orders_sidebar()
        self.order_details_sidebar = self.create_order_details_sidebar()

        self.sidebar_stack.addWidget(self.browse_sidebar)        # Index 0
        self.sidebar_stack.addWidget(self.profile_sidebar)       # Index 1
        self.sidebar_stack.addWidget(self.detail_sidebar)        # Index 2
        self.sidebar_stack.addWidget(self.cart_sidebar)          # Index 3
        self.sidebar_stack.addWidget(self.checkout_sidebar)      # Index 4
        self.sidebar_stack.addWidget(self.orders_sidebar)        # Index 5
        self.sidebar_stack.addWidget(self.order_details_sidebar) # Index 6

        self.body_layout.addWidget(self.sidebar_stack)

        self.main_content_stack = QStackedWidget()
        self.browse_page = self.create_browse_page()
        self.profile_page = self.create_profile_page()
        self.product_detail_page = self.create_product_detail_page()
        self.cart_page = self.create_cart_page()
        self.checkout_page = self.create_checkout_page()
        self.orders_page = self.create_orders_page()
        self.order_details_page = self.create_order_details_page()

        self.main_content_stack.addWidget(self.browse_page)         # Index 0
        self.main_content_stack.addWidget(self.profile_page)        # Index 1
        self.main_content_stack.addWidget(self.product_detail_page) # Index 2
        self.main_content_stack.addWidget(self.cart_page)           # Index 3
        self.main_content_stack.addWidget(self.checkout_page)       # Index 4
        self.main_content_stack.addWidget(self.orders_page)         # Index 5
        self.main_content_stack.addWidget(self.order_details_page)  # Index 6

        self.body_layout.addWidget(self.main_content_stack, 1)

        self.main_layout.addWidget(self.body_widget, 1)
        
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

    # --- HEADER ---
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
        cart_button.clicked.connect(self.show_cart_page)
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

    # --- INFO BUTTON METHODS ---
    def create_info_button(self):
        self.btn_info = QPushButton(self.central_widget)
        self.btn_info.setObjectName("btn_info")
        self.btn_info.setCursor(Qt.CursorShape.PointingHandCursor)
        # กำหนดขนาดและตำแหน่ง (ปรับ x, y ตามต้องการเพื่อให้ตรงกับดีไซน์)
        self.btn_info.setGeometry(368, 75, 60, 60) 
        self.btn_info.raise_() # ดึงปุ่มขึ้นมาไว้บนสุด
        self.btn_info.clicked.connect(self.open_info_window)

    def open_info_window(self):
        # ตรวจสอบว่าคลาส InfoWindow ถูก import มาสำเร็จหรือไม่
        if InfoWindow is None:
             QMessageBox.warning(self, "Error", "ไม่พบไฟล์ info_window.py")
             return

        # ส่ง self (ตัวหน้าต่าง MainUserWindow นี้) ไปด้วย เพื่อให้ InfoWindow เรียกกลับมาได้
        self.info_window_instance = InfoWindow(user_id=self.current_username, parent_window=self)
        self.info_window_instance.show()
        self.hide() # ซ่อนหน้าต่าง Main นี้ไว้ก่อ

    # --- SIDEBARS ---
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

    def create_cart_sidebar(self):
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("Sidebar")
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(20, 30, 20, 20)
        sidebar_layout.setSpacing(25)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        button_height = 55
        btn_cart = QPushButton("CART")
        btn_cart.setObjectName("sidebarButtonActive")
        btn_cart.setFixedHeight(button_height)
        btn_cart.clicked.connect(self.show_cart_page)
        sidebar_layout.addWidget(btn_cart)

        btn_orders = QPushButton("Your Orders")
        btn_orders.setObjectName("sidebarButtonActive")
        btn_orders.setFixedHeight(button_height)
        btn_orders.clicked.connect(self.show_orders_page)
        sidebar_layout.addWidget(btn_orders)

        btn_back = QPushButton("Back")
        btn_back.setObjectName("backsidebarButton")
        btn_back.setFixedHeight(button_height)
        btn_back.clicked.connect(self.show_browse_page)
        sidebar_layout.addWidget(btn_back)

        sidebar_layout.addStretch()
        return sidebar_frame

    def create_checkout_sidebar(self):
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("Sidebar")
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(20, 30, 20, 20)
        sidebar_layout.setSpacing(25)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        button_height = 55
        btn_cart = QPushButton("CART")
        btn_cart.setObjectName("sidebarButtonActive")
        btn_cart.setFixedHeight(button_height)
        btn_cart.clicked.connect(self.show_cart_page)
        sidebar_layout.addWidget(btn_cart)

        btn_orders = QPushButton("Your Orders")
        btn_orders.setObjectName("sidebarButtonActive")
        btn_orders.setFixedHeight(button_height)
        btn_orders.clicked.connect(self.show_orders_page)
        sidebar_layout.addWidget(btn_orders)

        btn_back = QPushButton("Back")
        btn_back.setObjectName("backsidebarButton")
        btn_back.setFixedHeight(button_height)
        btn_back.clicked.connect(self.show_browse_page)
        sidebar_layout.addWidget(btn_back)

        sidebar_layout.addStretch()
        return sidebar_frame

    def create_orders_sidebar(self):
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("Sidebar")
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(20, 30, 20, 20)
        sidebar_layout.setSpacing(25)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        button_height = 55
        btn_cart = QPushButton("CART")
        btn_cart.setObjectName("sidebarButtonActive")
        btn_cart.setFixedHeight(button_height)
        btn_cart.clicked.connect(self.show_cart_page)
        sidebar_layout.addWidget(btn_cart)

        btn_orders = QPushButton("Your Orders")
        btn_orders.setObjectName("sidebarButtonActive")
        btn_orders.setFixedHeight(button_height)
        btn_orders.clicked.connect(self.show_orders_page)
        sidebar_layout.addWidget(btn_orders)

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
        btn_cart = QPushButton("CART")
        btn_cart.setObjectName("sidebarButtonActive")
        btn_cart.setFixedHeight(button_height)
        btn_cart.clicked.connect(self.show_cart_page)
        sidebar_layout.addWidget(btn_cart)

        btn_orders = QPushButton("Your Orders")
        btn_orders.setObjectName("sidebarButtonActive")
        btn_orders.setFixedHeight(button_height)
        btn_orders.clicked.connect(self.show_orders_page)
        sidebar_layout.addWidget(btn_orders)

        btn_back = QPushButton("Back")
        btn_back.setObjectName("backsidebarButton")
        btn_back.setFixedHeight(button_height)
        btn_back.clicked.connect(self.show_browse_page)
        sidebar_layout.addWidget(btn_back)

        sidebar_layout.addStretch()
        return sidebar_frame

    # --- BROWSE PAGE ---
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

                    comic_card.clicked.connect(
                        lambda checked=False, p_id=id: self.show_product_detail_page(p_id)
                    )
                    self.grid_layout.addWidget(comic_card, row, col, Qt.AlignmentFlag.AlignTop)

                self.grid_layout.setRowStretch(len(products) // num_columns + 1, 1)
                self.grid_layout.setColumnStretch(num_columns, 1)

        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการโหลด comics: {e}")
            error_label = QLabel(f"Error loading comics:\n{e}")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid_layout.addWidget(error_label, 0, 0)

    # --- DETAIL PAGE ---
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
        main_detail_layout.addWidget(self.detail_cover_label, 0, Qt.AlignmentFlag.AlignTop)

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

        cart_layout = QHBoxLayout()
        cart_layout.setSpacing(10)
        cart_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        quantity_label = QLabel("QUANTITY :")
        quantity_label.setObjectName("quantityLabel")
        cart_layout.addWidget(quantity_label)

        self.detail_quantity_spinbox = QSpinBox()
        self.detail_quantity_spinbox.setLocale(QLocale("en_US"))
        self.detail_quantity_spinbox.setObjectName("quantitySpinBox")
        self.detail_quantity_spinbox.setMinimum(1)
        self.detail_quantity_spinbox.setFixedWidth(60)
        cart_layout.addWidget(self.detail_quantity_spinbox)

        self.detail_add_to_cart_button = QPushButton("Add to Cart")
        self.detail_add_to_cart_button.setObjectName("addToCartButton")
        self.detail_add_to_cart_button.setFixedHeight(60)
        self.detail_add_to_cart_button.clicked.connect(self.handle_add_to_cart)
        cart_layout.addWidget(self.detail_add_to_cart_button)

        right_info_layout.addLayout(cart_layout)
        right_info_layout.addStretch()
        main_detail_layout.addWidget(right_info_widget, 0, Qt.AlignmentFlag.AlignRight)

        return detail_frame

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
        self.detail_quantity_spinbox.setEnabled(False)
        self.detail_quantity_spinbox.setValue(1)
        self.detail_add_to_cart_button.setEnabled(False)
        self.detail_add_to_cart_button.setText("Loading...")

        placeholder_pixmap = QPixmap(self.detail_cover_label.size())
        placeholder_pixmap.fill(Qt.GlobalColor.white)
        self.detail_cover_label.setPixmap(placeholder_pixmap)

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name, description, volume_issue, writer, rated, id, stock, price, cover_img
                FROM product WHERE id = ?
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

                if stock_available > 0:
                    self.detail_quantity_spinbox.setMaximum(stock_available)
                    self.detail_quantity_spinbox.setValue(1)
                    self.detail_quantity_spinbox.setEnabled(True)
                    self.detail_add_to_cart_button.setEnabled(True)
                    self.detail_add_to_cart_button.setText("Add to Cart")
                else:
                    self.detail_quantity_spinbox.setMaximum(0)
                    self.detail_quantity_spinbox.setValue(0)
                    self.detail_quantity_spinbox.setEnabled(False)
                    self.detail_add_to_cart_button.setEnabled(False)
                    self.detail_add_to_cart_button.setText("Out of Stock")

                pixmap = None
                if cover_img and os.path.exists(cover_img):
                    pixmap = QPixmap(cover_img)
                else:
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
                self.detail_desc_label.setText(f"No product with ID '{product_id}' was found.")
                self.detail_quantity_spinbox.setEnabled(False)
                self.detail_add_to_cart_button.setEnabled(False)
                self.detail_add_to_cart_button.setText("Unavailable")

        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการโหลดรายละเอียดสินค้า: {e}")
            self.detail_name_label.setText(f"Error Loading Product")
            self.detail_add_to_cart_button.setText("Error")

    def show_product_detail_page(self, product_id):
        self.load_product_details(product_id)
        self.sidebar_stack.setCurrentIndex(2)
        self.main_content_stack.setCurrentIndex(2)

    def handle_add_to_cart(self):
        quantity = self.detail_quantity_spinbox.value()
        product_id = self.current_detail_product_id
        stock = self.current_detail_stock

        if product_id is None or quantity <= 0:
            QMessageBox.warning(self, "Error", "Invalid product or quantity.")
            return
        if quantity > stock:
            QMessageBox.warning(self, "Stock Error", "Not enough stock available.")
            return

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute("SELECT quantity FROM cart WHERE user_id = ? AND product_id = ?",
                           (self.current_username, product_id))
            existing_item = cursor.fetchone()

            if existing_item:
                new_qty = existing_item[0] + quantity
                if new_qty > stock:
                    new_qty = stock
                    QMessageBox.information(self, "Stock Limited", f"Adjusted total quantity to max stock ({stock}).")
                cursor.execute("UPDATE cart SET quantity = ? WHERE user_id = ? AND product_id = ?",
                               (new_qty, self.current_username, product_id))
            else:
                cursor.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)",
                               (self.current_username, product_id, quantity))

            conn.commit()
            conn.close()
            QMessageBox.information(self, "Success", f"Added to cart successfully!")
            self.detail_quantity_spinbox.setValue(1)

        except Exception as e:
            print(f"Database Error (Add to Cart): {e}")
            QMessageBox.critical(self, "Error", f"Could not add to cart: {e}")

    # --- CART PAGE ---
    def create_cart_page(self):
        cart_frame = QFrame()
        main_layout = QVBoxLayout(cart_frame)
        main_layout.setContentsMargins(250, 10, 20, 40)
        main_layout.setSpacing(10)

        self.cart_table = QTableWidget()
        self.cart_table.setObjectName("cartTable")
        self.cart_table.setColumnCount(5)
        self.cart_table.setHorizontalHeaderLabels(["ITEM", "UNIT PRICE", "QUANTITY", "AMOUNT", "DEL?"])

        header = self.cart_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.cart_table.setColumnWidth(4, 60)

        self.cart_table.verticalHeader().setVisible(False)
        self.cart_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.cart_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        main_layout.addWidget(self.cart_table, 1)

        footer_widget = QWidget()
        footer_layout = QVBoxLayout(footer_widget)
        footer_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        footer_layout.setSpacing(10)

        def create_summary_row(text, value_label_obj_name="cartSummaryValue", is_total=False):
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

            label_title = QLabel(text)
            label_title.setObjectName("cartSummaryLabel")
            label_title.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            label_value = QLabel("0.00 THB")
            label_value.setObjectName(value_label_obj_name)
            if is_total:
                label_value.setMinimumWidth(200)
            else:
                label_value.setFixedWidth(150)
            label_value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            row_layout.addWidget(label_title)
            row_layout.addWidget(label_value)
            return row_widget, label_value

        row_sub, self.subtotal_label = create_summary_row("Subtotal :")
        row_ship, self.shipping_label = create_summary_row("Shipping :")
        row_vat, self.vat_label = create_summary_row("VAT 7% :")
        row_total, self.total_label = create_summary_row("Total :", "cartTotalValue", is_total=True)

        
        footer_layout.addWidget(row_sub)  # SUBTOTAL
        footer_layout.addWidget(row_ship)  # SHIPPING
        footer_layout.addWidget(row_vat)  # VAT
        # --- เส้นคั่นสีดำ ---
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Plain)
        line.setFixedWidth(300)
        line.setStyleSheet("background-color: #000000; max-height: 1px; margin: 10px 0;")
        footer_layout.addWidget(line)
        footer_layout.addWidget(line, alignment=Qt.AlignmentFlag.AlignRight)

        footer_layout.addWidget(row_total)  # TOTAL
        
        self.checkout_button = QPushButton("Check out")
        self.checkout_button.setObjectName("checkoutButton")
        self.checkout_button.setFixedSize(200, 50)
        self.checkout_button.clicked.connect(self.show_checkout_page)

        checkout_container = QHBoxLayout()
        checkout_container.addStretch()
        checkout_container.addWidget(self.checkout_button)

        footer_layout.addSpacing(20)
        footer_layout.addLayout(checkout_container)
        main_layout.addWidget(footer_widget)

        return cart_frame

    def show_cart_page(self):
        self.load_cart_data()
        self.sidebar_stack.setCurrentIndex(3)
        self.main_content_stack.setCurrentIndex(3)

    def load_cart_data(self):
        self.cart_table.setRowCount(0)
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            query = """
                SELECT p.id, p.name, p.cover_img, p.price, c.quantity, p.stock
                FROM cart c
                JOIN product p ON c.product_id = p.id
                WHERE c.user_id = ?
            """
            cursor.execute(query, (self.current_username,))
            cart_items = cursor.fetchall()
            conn.close()

            self.cart_table.setRowCount(len(cart_items))

            for row_idx, (p_id, p_name, p_img, p_price, c_qty, p_stock) in enumerate(cart_items):
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
                self.cart_table.setCellWidget(row_idx, 0, item_widget)

                price_item = QTableWidgetItem(f"{p_price:.2f} THB")
                price_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                price_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                price_item.setData(Qt.ItemDataRole.UserRole, p_id)
                self.cart_table.setItem(row_idx, 1, price_item)

                qty_spinbox = QSpinBox()
                qty_spinbox.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))
                qty_spinbox.setRange(1, p_stock if p_stock > 0 else 1)
                qty_spinbox.setValue(c_qty)
                qty_spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
                qty_spinbox.setFixedWidth(80)
                qty_spinbox.valueChanged.connect(lambda val, pid=p_id: self.update_cart_quantity(pid, val))

                qty_container = QWidget()
                qty_layout = QHBoxLayout(qty_container)
                qty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                qty_layout.setContentsMargins(0, 0, 0, 0)
                qty_layout.addWidget(qty_spinbox)
                self.cart_table.setCellWidget(row_idx, 2, qty_container)

                amount = p_price * c_qty
                amount_item = QTableWidgetItem(f"{amount:.2f} THB")
                amount_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                amount_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.cart_table.setItem(row_idx, 3, amount_item)

                del_btn = QPushButton()
                del_btn.setFixedSize(30, 30)
                del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                if os.path.exists("src/img/icon/delete.png"):
                    del_btn.setIcon(QIcon("src/img/icon/delete.png"))
                else:
                    del_btn.setText("X")
                del_btn.clicked.connect(lambda checked=False, pid=p_id: self.delete_cart_item(pid))

                del_container = QWidget()
                del_layout = QHBoxLayout(del_container)
                del_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                del_layout.setContentsMargins(0, 0, 0, 0)
                del_layout.addWidget(del_btn)
                self.cart_table.setCellWidget(row_idx, 4, del_container)

                self.cart_table.setRowHeight(row_idx, 100)

            self.update_cart_totals()

        except Exception as e:
            print(f"Error loading cart: {e}")

    def update_cart_quantity(self, product_id, new_quantity):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("UPDATE cart SET quantity = ? WHERE user_id = ? AND product_id = ?",
                           (new_quantity, self.current_username, product_id))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error updating cart quantity: {e}")
            return

        for row in range(self.cart_table.rowCount()):
            price_item = self.cart_table.item(row, 1)
            if price_item and price_item.data(Qt.ItemDataRole.UserRole) == product_id:
                unit_price_text = price_item.text().replace(" THB", "").replace(",", "").strip()
                unit_price = float(unit_price_text)
                new_amount = unit_price * new_quantity
                amount_item = self.cart_table.item(row, 3)
                if amount_item:
                    amount_item.setText(f"{new_amount:,.2f} THB")
                break
        self.update_cart_totals()

    def delete_cart_item(self, product_id):
        reply = QMessageBox.question(self, 'Confirm Delete', 'Remove this item from cart?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM cart WHERE user_id = ? AND product_id = ?",
                               (self.current_username, product_id))
                conn.commit()
                conn.close()
                self.load_cart_data()
            except Exception as e:
                print(f"Error deleting cart item: {e}")

    def update_cart_totals(self):
        subtotal = 0.0
        for row in range(self.cart_table.rowCount()):
            item = self.cart_table.item(row, 3)
            if item:
                text = item.text().replace(" THB", "").replace(",", "").strip()
                try:
                    subtotal += float(text)
                except ValueError:
                    pass

        shipping = 80.0 if subtotal > 0 else 0.0
        vat = subtotal * 0.07
        total = subtotal + shipping + vat

        self.subtotal_label.setText(f"{subtotal:,.2f} THB")
        self.shipping_label.setText(f"{shipping:,.2f} THB")
        self.vat_label.setText(f"{vat:,.2f} THB")
        self.total_label.setText(f"{total:,.2f} THB")

    # --- CHECKOUT PAGE ---
    def create_checkout_page(self):
        checkout_frame = QFrame()
        main_layout = QVBoxLayout(checkout_frame)
        main_layout.setContentsMargins(250, 0, 50, 40)
        main_layout.setSpacing(30)

        top_content_widget = QWidget()
        top_content_layout = QHBoxLayout(top_content_widget)
        top_content_layout.setSpacing(40)

        left_qr_widget = QWidget()
        left_qr_layout = QVBoxLayout(left_qr_widget)
        left_qr_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)

        qr_title = QLabel("Scan to Pay")
        qr_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qr_title.setObjectName("qrTitleLabel")

        self.qr_code_label = QLabel()
        self.qr_code_label.setFixedSize(350, 450)
        self.qr_code_label.setScaledContents(True)
        self.qr_code_label.setObjectName("qrCodeLabel")
        self.qr_code_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_code_path = "src/img/icon/qrcodekbank.jpg"

        if os.path.exists(self.qr_code_path):
            self.qr_code_label.setPixmap(QPixmap(self.qr_code_path))
        else:
            self.qr_code_label.setText("QR Code Not Found\n(Please check path)")
            self.qr_code_label.setStyleSheet("border: 2px dashed #aaa; color: #aaa; font-size: 16px;")

        left_qr_layout.addWidget(qr_title)
        left_qr_layout.addWidget(self.qr_code_label)
        left_qr_layout.addStretch()

        right_content_widget = QWidget()
        right_content_layout = QVBoxLayout(right_content_widget)
        right_content_layout.setContentsMargins(0, 20, 0, 0)
        right_content_layout.setSpacing(25)
        right_content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        upload_label = QLabel("Upload Receipt")
        upload_label.setObjectName("uploadlabel")
        right_content_layout.addWidget(upload_label)

        upload_container = QHBoxLayout()
        upload_container.setSpacing(10)

        self.slip_path_field = QLineEdit()
        self.slip_path_field.setPlaceholderText(" Select Receipt image...")
        self.slip_path_field.setReadOnly(True)
        self.slip_path_field.setFixedHeight(45)
        self.slip_path_field.setObjectName("slipPathField")

        self.upload_slip_button = QPushButton()
        self.upload_slip_button.setFixedSize(50, 45)
        self.upload_slip_button.setObjectName("uploadSlipButton")
        try:
            self.upload_slip_button.setIcon(QIcon("src/img/icon/upload.png"))
            self.upload_slip_button.setIconSize(QSize(28, 28))
        except:
            self.upload_slip_button.setText("UP")
        self.upload_slip_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.upload_slip_button.clicked.connect(self.select_slip_image)

        upload_container.addWidget(self.slip_path_field)
        upload_container.addWidget(self.upload_slip_button)
        right_content_layout.addLayout(upload_container)

        instructions = """ขั้นตอนการโอนเงิน
1.) สแกน QR Code ทางด้านซ้ายมือ
2.) โอนเงินจากยอดรวมทั้งหมด (Total)
3.) อัพโหลดรูปภาพ ใบเสร็จของการโอนเงินครั้งนี้
4.) กดปุ่ม Payment เพื่อยืนยันการโอนเงินและรอตรวจสอบ"""
        instruction_label = QLabel(instructions)
        instruction_label.setObjectName("instructionLabel")
        right_content_layout.addWidget(instruction_label)

        right_content_layout.addStretch(1)

        summary_container = QWidget()
        summary_layout = QVBoxLayout(summary_container)
        summary_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        summary_layout.setSpacing(8)

        def create_checkout_summary_row(text, row_type):
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

            label_title = QLabel(text)
            label_title.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            label_title.setObjectName(f"checkout{row_type}Title")

            label_value = QLabel("... THB")
            label_value.setMinimumWidth(160)
            label_value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            label_value.setObjectName(f"checkout{row_type}Value")

            row_layout.addWidget(label_title)
            row_layout.addWidget(label_value)
            return row_widget, label_value

        row_sub, self.checkout_subtotal_label = create_checkout_summary_row("Subtotal : ", "Subtotal")
        row_ship, self.checkout_shipping_label = create_checkout_summary_row("Shipping : ", "Shipping")
        row_vat, self.checkout_vat_label = create_checkout_summary_row("VAT 7% : ", "Vat")
        row_tot, self.checkout_total_label = create_checkout_summary_row("Total : ", "Total")

        summary_layout.addWidget(row_sub)
        summary_layout.addWidget(row_ship)
        summary_layout.addWidget(row_vat)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #ccc; margin: 5px 0;")
        summary_layout.addWidget(line)

        summary_layout.addWidget(row_tot)
        right_content_layout.addWidget(summary_container)

        top_content_layout.addWidget(left_qr_widget, 45)
        top_content_layout.addWidget(right_content_widget, 55)

        main_layout.addWidget(top_content_widget, 1)

        bottom_buttons_container = QWidget()
        bottom_buttons_layout = QHBoxLayout(bottom_buttons_container)
        bottom_buttons_layout.setContentsMargins(0, 20, 0, 0)

        self.checkout_back_button = QPushButton("Back to Cart")
        self.checkout_back_button.setFixedHeight(50)
        self.checkout_back_button.setMinimumWidth(150)
        self.checkout_back_button.setObjectName("checkoutBackButton")
        self.checkout_back_button.clicked.connect(self.show_cart_page)

        self.payment_button = QPushButton("Payment")
        self.payment_button.setFixedHeight(50)
        self.payment_button.setMinimumWidth(180)
        self.payment_button.setEnabled(False)
        self.payment_button.setObjectName("confirmPaymentButton")
        self.payment_button.clicked.connect(self.handle_payment)

        bottom_buttons_layout.addWidget(self.checkout_back_button, alignment=Qt.AlignmentFlag.AlignLeft)
        bottom_buttons_layout.addStretch(1)
        bottom_buttons_layout.addWidget(self.payment_button, alignment=Qt.AlignmentFlag.AlignRight)

        main_layout.addWidget(bottom_buttons_container, 0)

        return checkout_frame

    def show_checkout_page(self):
        if self.cart_table.rowCount() == 0:
            QMessageBox.warning(self, "Cart Empty", "Your cart is empty.")
            return

        subtotal = 0.0
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT SUM(p.price * c.quantity)
                FROM cart c
                JOIN product p ON c.product_id = p.id
                WHERE c.user_id = ?
            """, (self.current_username,))
            result = cursor.fetchone()
            if result and result[0] is not None:
                subtotal = float(result[0])
            conn.close()
        except Exception as e:
            print(f"Error calculating checkout total: {e}")

        shipping = 80.0 if subtotal > 0 else 0.0
        vat = subtotal * 0.07
        total = subtotal + shipping + vat

        self.checkout_subtotal_label.setText(f"{subtotal:,.2f} THB")
        self.checkout_shipping_label.setText(f"{shipping:,.2f} THB")
        self.checkout_vat_label.setText(f"{vat:,.2f} THB")
        self.checkout_total_label.setText(f"{total:,.2f} THB")

        self.current_slip_path = None
        self.slip_path_field.clear()
        self.payment_button.setEnabled(False)

        self.sidebar_stack.setCurrentIndex(4)
        self.main_content_stack.setCurrentIndex(4)

    def select_slip_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Payment Slip",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )

        if file_path:
            self.current_slip_path = os.path.normpath(file_path)
            self.slip_path_field.setText(os.path.basename(self.current_slip_path))
            self.payment_button.setEnabled(True)

    def handle_payment(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            # ดึงข้อมูลที่จำเป็นต้องตรวจสอบ
            cursor.execute("""
                SELECT first_name, last_name, email, phone, address
                FROM users WHERE username = ?
            """, (self.current_username,))
            user_data = cursor.fetchone()
            conn.close()

            if user_data:
                # user_data จะเก็บ tuple ของ (first_name, last_name, email, phone, address)
                # ตรวจสอบว่ามีค่าใดเป็น None หรือ ค่าว่าง "" หรือไม่
                # (str(field).strip() ช่วยเช็คกรณีที่เป็น space bar อย่างเดียวด้วย)
                is_profile_complete = all(field and str(field).strip() for field in user_data)

                if not is_profile_complete:
                    QMessageBox.warning(
                        self,
                        "Profile Incomplete",
                        "ไม่สามารถชำระเงินได้\n\nกรุณากรอกข้อมูลโปรไฟล์ให้ครบถ้วนก่อนทำรายการ\n(ชื่อ, นามสกุล, อีเมล, เบอร์โทรศัพท์ และที่อยู่)"
                    )
                    # บังคับเด้งไปหน้า Profile เพื่อให้กรอกข้อมูล
                    self.show_profile_page()
                    # (Optional) ถ้าอยากให้เข้าโหมดแก้ไขเลย ให้ uncomment บรรทัดล่างนี้
                    # self.toggle_edit_mode()
                    return
            else:
                QMessageBox.critical(self, "Error", "ไม่พบฐานข้อมูลผู้ใช้")
                return

        except Exception as e:
            print(f"Database Error (Profile Check): {e}")
            QMessageBox.critical(self, "Error", f"เกิดข้อผิดพลาดในการตรวจสอบโปรไฟล์: {e}")
            return
        # ------------------------------------------------

        subtotal = 0.0
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT SUM(p.price * c.quantity)
                FROM cart c JOIN product p ON c.product_id = p.id
                WHERE c.user_id = ?
            """, (self.current_username,))
            result = cursor.fetchone()
            if result and result[0]:
                subtotal = float(result[0])
            conn.close()
        except Exception as e:
            print(f"Error calculating subtotal for order: {e}")
            return

        shipping_fee = 80.0 if subtotal > 0 else 0.0
        vat = subtotal * 0.07
        total = subtotal + shipping_fee + vat

        current_date = datetime.now().strftime("%d-%b-%Y %H:%M")

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # 1. ดึงรายการสินค้าในตะกร้า พร้อมราคาปัจจุบัน
            cursor.execute("""
                SELECT c.product_id, c.quantity, p.price
                FROM cart c
                JOIN product p ON c.product_id = p.id
                WHERE c.user_id = ?
            """, (self.current_username,))
            cart_items_full = cursor.fetchall()

            if not cart_items_full:
                QMessageBox.warning(self, "Error", "Cart is empty.")
                conn.close()
                return

            # 2. Insert ลงตาราง orders
            cursor.execute("""
                INSERT INTO orders (user_id, order_date, status, subtotal, vat, shipping_fee, total, slip_image)
                VALUES (?, ?, 'pending', ?, ?, ?, ?, ?)
            """, (self.current_username, current_date, subtotal, vat, shipping_fee, total, self.current_slip_path))

            new_order_id = cursor.lastrowid

            # 3. Insert ลงตาราง order_items และตัดสต็อก
            for product_id, quantity, unit_price in cart_items_full:
                cursor.execute("""
                    INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                    VALUES (?, ?, ?, ?)
                """, (new_order_id, product_id, quantity, unit_price))

                cursor.execute("""
                    UPDATE product
                    SET stock = MAX(0, stock - ?)
                    WHERE id = ?
                """, (quantity, product_id))

            # 4. ล้างตะกร้า
            cursor.execute("DELETE FROM cart WHERE user_id = ?", (self.current_username,))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Payment Success", "Your order has been placed successfully!")
            self.show_orders_page()

        except Exception as e:
            print(f"Database Error (Payment): {e}")
            QMessageBox.critical(self, "Payment Error", f"Could not process payment: {e}")

    # --- ORDERS PAGE ---
    def create_orders_page(self):
        page_frame = QFrame()
        main_layout = QVBoxLayout(page_frame)
        main_layout.setContentsMargins(250, 40, 50, 40)
        main_layout.setSpacing(20)

        self.orders_table = QTableWidget()
        self.orders_table.setObjectName("ordersTable")
        self.orders_table.setColumnCount(2)
        self.orders_table.setHorizontalHeaderLabels(["My Orders (Click for details)", "STATUS"])

        header = self.orders_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.orders_table.setColumnWidth(1, 200)

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
        self.sidebar_stack.setCurrentIndex(5)
        self.main_content_stack.setCurrentIndex(5)

    def load_orders_data(self):
        self.orders_table.setRowCount(0)
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT order_id, order_date, status FROM orders
                WHERE user_id = ?
                ORDER BY order_id DESC
            """, (self.current_username,))
            orders = cursor.fetchall()
            conn.close()

            self.orders_table.setRowCount(len(orders))
            for i, (order_id, order_date, status) in enumerate(orders):
                date_widget = QWidget()
                date_layout = QVBoxLayout(date_widget)
                date_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                date_layout.setSpacing(0)

                lbl_title = QLabel(f"Order ID: #{order_id}")
                # [MOVED TO CSS] ใช้ ObjectName: orderDateTitle
                lbl_title.setObjectName("orderDateTitle")
                lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter) # ย้ายไป qproperty-alignment ใน CSS ได้ หรือจะคงไว้ที่นี่ก็ได้

                date_layout.addWidget(lbl_title)

                parts = order_date.split(' ')
                date_text = parts[0]
                time_text = parts[1] if len(parts) > 1 else ""

                lbl_date = QLabel(date_text)
                # [MOVED TO CSS] ใช้ ObjectName: orderDateLabel
                lbl_date.setObjectName("orderDateLabel")
                lbl_date.setAlignment(Qt.AlignmentFlag.AlignCenter)

                date_layout.addWidget(lbl_date)

                if time_text:
                    lbl_time = QLabel(time_text)
                    # [MOVED TO CSS] ใช้ ObjectName: orderTimeLabel
                    lbl_time.setObjectName("orderTimeLabel")
                    lbl_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    date_layout.addWidget(lbl_time)

                self.orders_table.setCellWidget(i, 0, date_widget)

                status_item = QTableWidgetItem(status)
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                # Note: QFont สำหรับ QTableWidgetItem ยังคงไว้ใน Python จะสะดวกกว่าการใช้ CSS
                status_item.setFont(QFont("Arial", 16))
                status_item.setData(Qt.ItemDataRole.UserRole, order_id)
                status_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.orders_table.setItem(i, 1, status_item)

                self.orders_table.setRowHeight(i, 130)

        except Exception as e:
            print(f"Error loading orders: {e}")

    def on_order_clicked(self, row, col):
        status_item = self.orders_table.item(row, 1)
        if status_item:
            order_id = status_item.data(Qt.ItemDataRole.UserRole)
            self.show_order_details_page(order_id)

    # --- ORDER DETAILS PAGE ---
    def create_order_details_page(self):
        details_frame = QFrame()
        main_layout = QVBoxLayout(details_frame)
        main_layout.setContentsMargins(290, 10, 20, 10)
        main_layout.setSpacing(1)

        self.order_details_header = QLabel("Order Details #...")
        # [MOVED TO CSS] ใช้ ObjectName: detailsHeader
        self.order_details_header.setObjectName("detailsHeader")
        main_layout.addWidget(self.order_details_header)

        self.order_items_table = QTableWidget()
        self.order_items_table.setObjectName("cartTable") # ใช้ Style เดิมที่มีอยู่แล้ว
        self.order_items_table.setColumnCount(4)
        self.order_items_table.setHorizontalHeaderLabels(["ITEM", "UNIT PRICE", "QUANTITY", "AMOUNT"])

        # ... (ส่วนตั้งค่า Header ตาราง ยังคงเดิม) ...
        header = self.order_items_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.order_items_table.setColumnWidth(2, 100)

        self.order_items_table.verticalHeader().setVisible(False)
        self.order_items_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.order_items_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        main_layout.addWidget(self.order_items_table, 1)

        footer_widget = QWidget()
        footer_layout = QVBoxLayout(footer_widget)
        footer_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        footer_layout.setSpacing(1)

        def create_summary_row(text, is_total=False):
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

            label_title = QLabel(text)
            label_title.setObjectName("cartSummaryLabel") # ใช้ Style เดิม
            label_title.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            label_value = QLabel("0.00 THB")
            if is_total:
                label_value.setObjectName("cartTotalValue") # ใช้ Style เดิม
                label_value.setMinimumWidth(200)
            else:
                label_value.setObjectName("cartSummaryValue") # ใช้ Style เดิม
                label_value.setFixedWidth(150)
            label_value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            row_layout.addWidget(label_title)
            row_layout.addWidget(label_value)
            return row_widget, label_value

        row_sub, self.ord_subtotal_label = create_summary_row("Subtotal :")
        row_ship, self.ord_shipping_label = create_summary_row("Shipping :")
        row_vat, self.ord_vat_label = create_summary_row("VAT 7% :")
        row_tot, self.ord_total_label = create_summary_row("Total :", is_total=True)

        footer_layout.addWidget(row_sub)
        footer_layout.addWidget(row_ship)
        footer_layout.addWidget(row_vat)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Plain)
        line.setFixedWidth(300)
        # [MOVED TO CSS] ใช้ ObjectName: summarySeparator
        line.setObjectName("summarySeparator")

        footer_layout.addWidget(line)
        footer_layout.addWidget(line, alignment=Qt.AlignmentFlag.AlignRight)

        footer_layout.addWidget(row_tot)

        buttons_container = QHBoxLayout()
        self.ord_back_button = QPushButton("Back")
        self.ord_back_button.setObjectName("ordBackButton") # เพิ่ม ObjectName เผื่อต้องการ style ในอนาคต
        self.ord_back_button.setFixedSize(150, 50)
        self.ord_back_button.clicked.connect(self.show_orders_page)
        
        # --- [เพิ่มส่วนนี้] ปุ่มสำหรับดูรูปสลิป ---
        self.ord_view_slip_button = QPushButton("View Transfer Receipt")
        self.ord_view_slip_button.setObjectName("ordDownloadButton") # ตั้งชื่อเผื่อไปแก้ CSS
        self.ord_view_slip_button.setFixedSize(250, 50)
        self.ord_view_slip_button.clicked.connect(self.handle_view_slip_image)
        # ------------------------------------

        self.ord_download_button = QPushButton("Download Receipt")
        self.ord_download_button.setObjectName("ordDownloadButton") # เพิ่ม ObjectName
        self.ord_download_button.setFixedSize(200, 50)
        self.ord_download_button.clicked.connect(self.handle_download_receipt)

        buttons_container.addWidget(self.ord_back_button)
        buttons_container.addStretch()
        buttons_container.addWidget(self.ord_view_slip_button)
        buttons_container.addSpacing(15) # เว้นระยะห่างระหว่างปุ่มเล็กน้อย
        buttons_container.addWidget(self.ord_download_button)
        
        footer_layout.addSpacing(20)
        footer_layout.addLayout(buttons_container)

        main_layout.addWidget(footer_widget)

        return details_frame

    def show_order_details_page(self, order_id):
        self.load_order_details(order_id)
        self.sidebar_stack.setCurrentIndex(6)
        self.main_content_stack.setCurrentIndex(6)

    def load_order_details(self, order_id):
        # [MODIFIED] บันทึก ID ที่กำลังดูล่าสุด
        self.current_viewing_order_id = order_id
        self.order_details_header.setText(f"Order Details #{order_id}")
        self.order_items_table.setRowCount(0)

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT subtotal, shipping_fee, vat, total
                FROM orders WHERE order_id = ?
            """, (order_id,))
            order_summary = cursor.fetchone()
            if order_summary:
                sub, ship, vat, tot = order_summary
                self.ord_subtotal_label.setText(f"{sub:,.2f} THB")
                self.ord_shipping_label.setText(f"{ship:,.2f} THB")
                self.ord_vat_label.setText(f"{vat:,.2f} THB")
                self.ord_total_label.setText(f"{tot:,.2f} THB")

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

    # --- PROFILE PAGE ---
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
        left_pic_layout.setContentsMargins(0, 0, 0, 0)

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

                image_path_to_load = img_path if (
                        img_path and os.path.exists(img_path)) else "src/img/icon/profile.png"
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
            self.disable_edit_mode()
            self.is_in_edit_mode = False
        else:
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
                SET first_name = ?, last_name = ?, gender = ?,
                    email = ?, phone = ?, address = ?, profile_img = ?
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

    # --- [NEW] RECEIPT GENERATION METHODS ---
    def init_receipt_font(self):
        """ลงทะเบียนฟอนต์สำหรับ ReportLab"""
        self.main_pdf_font = 'Helvetica'
        if os.path.exists(FONT_PATH):
            try:
                pdfmetrics.registerFont(TTFont('ThaiFont', FONT_PATH))
                self.main_pdf_font = 'ThaiFont'
            except Exception as e:
                print(f"Warning: Could not register Thai font: {e}")
        else:
            print(f"Warning: Font not found at {FONT_PATH}")

    def handle_download_receipt(self):
        if self.current_viewing_order_id is None:
            QMessageBox.warning(self, "Error", "No order selected.")
            return
        self.generate_receipt_pdf(self.current_viewing_order_id)    

    def generate_receipt_pdf(self, order_id):
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
            order_info = cursor.fetchone()
            if not order_info:
                QMessageBox.warning(self, "Error", f"Order {order_id} not found.")
                conn.close()
                return

            cursor.execute("""
                SELECT oi.product_id, p.name, oi.unit_price, oi.quantity
                FROM order_items oi
                LEFT JOIN product p ON oi.product_id = p.id
                WHERE oi.order_id = ?
            """, (order_id,))
            items = cursor.fetchall()
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Could not fetch order data: {e}")
            return

        try:
            if not os.path.exists(PDF_OUTPUT_DIR):
                os.makedirs(PDF_OUTPUT_DIR)

            pdf_filename = os.path.join(PDF_OUTPUT_DIR, f"Receipt_{order_info['user_id']}_{order_id}.pdf")
            pdf_filename = os.path.abspath(pdf_filename)

            c = canvas.Canvas(pdf_filename, pagesize=A4)
            width, height = A4

            # --- HEADER ---
            # 1. หัวกระดาษ (ORDER ID)
            c.setFont("Helvetica", 20)
            c.drawCentredString(width / 2.0, height - 30 * mm, f"ORDER ID # {order_info['order_id']}")

            # 2. ข้อมูลร้านค้า
            # ปรับตำแหน่ง Logo เล็กน้อยไม่ให้ทับข้อความ (ถ้ามี)
            LOGO_X, LOGO_Y = width - 125 * mm, height - 30 * mm # ย้าย Logo ไปขวาบนแทน เพื่อไม่ให้เบียดซ้าย
            LOGO_W, LOGO_H = 40 * mm, 30 * mm
            if os.path.exists(LOGO_PATH):
                try:
                    c.drawImage(LOGO_PATH, LOGO_X, LOGO_Y, width=LOGO_W, height=LOGO_H, preserveAspectRatio=True, mask='auto')
                except:
                    pass

            c.setFont(self.main_pdf_font, 14)
            text_y = height - 50 * mm # เริ่มต้นเขียนที่ตำแหน่งนี้
            c.drawString(20 * mm, text_y, "Beyond Comics Inc.")
            text_y -= 7 * mm
            # ลดขนาดฟอนต์ที่อยู่ลงเล็กน้อยเพื่อให้ดูสวยงามขึ้นเมื่ออยู่รวมกัน (หรือจะใช้ 14 เท่าเดิมก็ได้ครับ)
            c.setFont(self.main_pdf_font, 12) 
            for line in ["หอพักนักศึกษาชายที่ 10 มหาวิทยาลัยขอนแก่น",
                         "ตำบล ศิลา อำเภอเมืองขอนแก่น จังหวัด ขอนแก่น 40000",
                         "เลขประจำตัวผู้เสียภาษี 3101103733",
                         "โทร. 098-106-9613"]:
                c.drawString(25 * mm, text_y, line) # ขยับเข้ามานิดนึง (Indentation)
                text_y -= 6 * mm

            # --- เส้นคั่น ---
            line_y = text_y - 2 * mm
            c.setLineWidth(0.5)
            c.line(20 * mm, line_y, width - 20 * mm, line_y)

            # 3. ข้อมูลลูกค้า (ย้ายมาอยู่ใต้เส้นคั่น)
            text_y = line_y - 8 * mm
            c.setFont(self.main_pdf_font, 14)
            c.drawString(20 * mm, text_y, "ข้อมูลลูกค้า :")
            
            text_y -= 7 * mm
            c.setFont(self.main_pdf_font, 12)
            # ใช้ f-string จัดข้อความให้ชิดกันสวยงาม
            c.drawString(25 * mm, text_y, f"Customer ID : {order_info['user_id']}")
            text_y -= 6 * mm
            c.drawString(25 * mm, text_y, f"Order Date : {order_info['order_date']}")

            # --- TABLE ---
            # ... (ส่วนการเตรียมข้อมูลตารางเหมือนเดิม) ...
            table_data = [['ID', 'ITEM', 'UNIT PRICE', 'QUANTITY', 'AMOUNT']]
            for idx, item in enumerate(items, 1):
                u_price = item['unit_price']
                qty = item['quantity']
                amount = u_price * qty
                table_data.append([
                    str(idx),
                    item['name'] if item['name'] else "Unknown Item",
                    f"{u_price:,.2f} THB",
                    str(qty),
                    f"{amount:,.2f} THB"
                ])

            table = Table(table_data, colWidths=[10 * mm, 70 * mm, 35 * mm, 20 * mm, 35 * mm])
            table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, -1), self.main_pdf_font, 12),
                ('ALIGN', (1, 1), (-1, 0), 'LEFT'),
                ('ALIGN', (5, 1), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
                ('WORDWRAP', (1, 1), (1, -1), True),
            ]))

            available_width = width - 40 * mm
            _, table_height = table.wrap(available_width, height)
            
            # *** จุดสำคัญ: ปรับตำแหน่งเริ่มตารางลงมา เพราะ Header ยาวขึ้น ***
            table_top_y = text_y - 15 * mm  # ให้ห่างจากบรรทัดสุดท้ายของลูกค้า 15mm
            table_y = table_top_y - table_height
            table.drawOn(c, 20 * mm, table_y)

            # --- FOOTER ---
            y_footer = table_y - 20 * mm
            c.setLineWidth(0.5)
            c.line(20 * mm, y_footer + 5 * mm, width - 20 * mm, y_footer + 5 * mm)

            c.setFont(self.main_pdf_font, 14)
            right_x = width - 25 * mm

            c.drawRightString(right_x - 40 * mm, y_footer - 5 * mm, "Subtotal :")
            c.drawRightString(right_x, y_footer - 5 * mm, f"{order_info['subtotal']:,.2f} THB")

            c.drawRightString(right_x - 40 * mm, y_footer - 12 * mm, "Shipping :")
            c.drawRightString(right_x, y_footer - 12 * mm, f"{order_info['shipping_fee']:,.2f} THB")

            c.drawRightString(right_x - 40 * mm, y_footer - 19 * mm, "VAT 7% :")
            c.drawRightString(right_x, y_footer - 19 * mm, f"{order_info['vat']:,.2f} THB")

            c.line(width - 80 * mm, y_footer - 24 * mm, width - 20 * mm, y_footer - 24 * mm)
            c.setFont("Helvetica", 16)
            c.drawRightString(right_x - 40 * mm, y_footer - 32 * mm, "Total :")
            c.drawRightString(right_x, y_footer - 32 * mm, f"{order_info['total']:,.2f} THB")

            c.setFont("Helvetica", 20)
            # ปรับตำแหน่งคำขอบคุณไม่ให้ทับ Footer ถ้าสินค้ายาว
            c.drawCentredString(width / 2.0, 30 * mm, "Thank bro, you are my hero!")

            c.save()

            if os.name == 'nt':
                os.startfile(pdf_filename)
            else:
                import subprocess
                opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
                subprocess.call([opener, pdf_filename])

        except Exception as e:
            QMessageBox.critical(self, "PDF Error", f"Could not create receipt PDF: {e}")
            import traceback
            traceback.print_exc()
    
    def handle_view_slip_image(self):
        order_id = self.current_viewing_order_id
        if order_id is None:
            QMessageBox.warning(self, "Error", "No order selected.")
            return

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            # ดึง path รูปภาพสลิปจากตาราง orders
            cursor.execute("SELECT slip_image FROM orders WHERE order_id = ?", (order_id,))
            result = cursor.fetchone()
            conn.close()

            if result and result[0]:
                image_path = result[0]
                # ตรวจสอบว่าไฟล์มีอยู่จริงหรือไม่
                if os.path.exists(image_path):
                    # เปิดไฟล์ภาพด้วยโปรแกรม Default ของเครื่อง (เหมือนที่ใช้เปิด PDF)
                    if os.name == 'nt': # สำหรับ Windows
                        os.startfile(image_path)
                    else: # สำหรับ macOS/Linux (เผื่อไว้)
                        import subprocess
                        opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
                        subprocess.call([opener, image_path])
                else:
                     QMessageBox.warning(self, "File Not Found", f"ไม่พบไฟล์รูปภาพที่:\n{image_path}\nไฟล์อาจถูกลบหรือย้ายไปแล้ว")
            else:
                QMessageBox.information(self, "No Slip", "คำสั่งซื้อนี้ไม่มีการแนบรูปภาพสลิป")

        except Exception as e:
            print(f"Error viewing slip image: {e}")
            QMessageBox.critical(self, "Error", f"เกิดข้อผิดพลาดในการเปิดรูปภาพ: {e}")
            

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainUserWindow(username="test")
    window.show()
    sys.exit(app.exec())