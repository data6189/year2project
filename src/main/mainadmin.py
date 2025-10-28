import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import QIcon

class MainAdminWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Beyond Comics") 
        self.setGeometry(100, 100, 1280, 720)
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

        self.sidebar_frame = self.create_sidebar()
        self.sidebar_frame.setFixedWidth(260)  # เพิ่มความกว้างให้พอดีกับภาพ
        self.body_layout.addWidget(self.sidebar_frame)

        self.main_content_frame = self.create_main_content()
        self.body_layout.addWidget(self.main_content_frame, 1)

        self.main_layout.addWidget(self.body_widget, 1)

        self.load_stylesheet("src/styles/mainuser.qss")

    def load_stylesheet(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print(f"Warning: Stylesheet file '{filepath}' not found")

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
        
        # --- 🛒 ปุ่ม CART ---
        cart_icon = QIcon("src/img/icon/cart.png") 
        cart_button = QPushButton(" CART") # เพิ่มเว้นวรรคหน้าข้อความ
        cart_button.setIcon(cart_icon)
        cart_button.setIconSize(QSize(50, 50)) # กำหนดขนาดไอคอน (กว้าง, สูง)
        cart_button.setObjectName("navButton")
        cart_button.setFixedSize(button_width, button_height)
        header_layout.addWidget(cart_button)

        # --- 👤 ปุ่ม PROFILE ---
        profile_icon = QIcon("src/img/icon/profile.png") 
        profile_button = QPushButton(" PROFILE") # เพิ่มเว้นวรรค
        profile_button.setIcon(profile_icon)
        profile_button.setIconSize(QSize(50, 50)) # กำหนดขนาดไอคอน
        profile_button.setObjectName("navButton")
        profile_button.setFixedSize(button_width, button_height)
        header_layout.addWidget(profile_button)

        # --- ปุ่ม LOGOUT (เหมือนเดิม) ---
        logout_button = QPushButton("LOGOUT")
        logout_button.setObjectName("navButton")
        logout_button.setFixedSize(button_width, button_height)
        header_layout.addWidget(logout_button)

        return header_frame

    def create_sidebar(self):
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
        sidebar_layout.addWidget(btn_marvel)

        btn_dc = QPushButton("DC")
        btn_dc.setObjectName("sidebarButton")
        btn_dc.setFixedHeight(button_height)
        sidebar_layout.addWidget(btn_dc)

        btn_image = QPushButton("Image Comics")
        btn_image.setObjectName("sidebarButton")
        btn_image.setFixedHeight(button_height)
        sidebar_layout.addWidget(btn_image)
        sidebar_layout.addStretch()
        return sidebar_frame

    def create_main_content(self):
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

         # --- 🔍 กล่องค้นหา ---
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
        self.grid_layout.setSpacing(20)              # ระยะห่างระหว่างการ์ด
        self.grid_layout.setContentsMargins(20, 20, 20, 20)  # ระยะรอบนอก

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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainAdminWindow()
    window.show()
    sys.exit(app.exec())
