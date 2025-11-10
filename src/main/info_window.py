import sys
import sqlite3
import os
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *


class FeedbackOverlay(QWidget):
    go_back_signal = pyqtSignal()

    def __init__(self, user_id="guest", parent=None):
        super().__init__(parent)
        self.db_path = "src/database/thisshop.db"
        self.current_user_id = user_id
        self.setObjectName("FeedbackOverlay")
        self.init_ui()

    def init_ui(self):
        # ตั้งค่าให้โปร่งใส เพื่อให้พื้นหลังจาก InfoWindow แสดงทะลุขึ้นมา
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        main_layout = QVBoxLayout(self)
        # ปรับ layout margins (left, top, right, bottom)
        main_layout.setContentsMargins(800, 280, 130, 100)
        main_layout.setSpacing(15)

        feedback_title = QLabel("Feedback")
        feedback_title.setFont(QFont("Comic Sans MS", 32, QFont.Weight.Bold))
        feedback_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        feedback_title.setObjectName("feedback_title")

        title_layout = QHBoxLayout()
        title_layout.addStretch()
        title_layout.addWidget(feedback_title)
        title_layout.addStretch()
        main_layout.addLayout(title_layout)

        self.feedback_input = QTextEdit()
        self.feedback_input.setPlaceholderText("เขียนข้อเสนอแนะของคุณที่นี่...")
        self.feedback_input.setObjectName("feedback_input")
        self.feedback_input.setMinimumSize(400, 200)

        main_layout.addWidget(self.feedback_input)
        main_layout.addSpacing(20)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)

        self.btn_back = QPushButton("BACK")
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.setObjectName("btn_back")
        self.btn_back.setProperty("class", "feedback_btn") 
        self.btn_back.clicked.connect(self.go_back)

        self.btn_send = QPushButton("SEND")
        self.btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send.setObjectName("btn_send")
        self.btn_send.setProperty("class", "feedback_btn")
        self.btn_send.clicked.connect(self.send_feedback)

        button_layout.addStretch()
        button_layout.addWidget(self.btn_back)
        button_layout.addWidget(self.btn_send)
        button_layout.addStretch()

        main_layout.addLayout(button_layout)
        main_layout.addStretch()

    def go_back(self):
        self.go_back_signal.emit()

    def send_feedback(self):
        text = self.feedback_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "แจ้งเตือน", "กรุณาพิมพ์ข้อความก่อนส่ง")
            return

        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    feedback_text TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("INSERT INTO feedback (user_id, feedback_text) VALUES (?, ?)", 
                           (self.current_user_id, text))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "สำเร็จ", "ส่ง Feedback เรียบร้อย ขอบคุณครับ!")
            self.feedback_input.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"เกิดข้อผิดพลาด: {e}")

class InfoWindow(QMainWindow):
    def __init__(self, user_id="guest", parent_window=None):
        super().__init__()
        self.parent_window = parent_window
        self.setWindowTitle("Beyond Comics - About")
        self.setObjectName("InfoWindow")

        # --- [MERGED] โหลด Stylesheet ที่ต้องการจากที่นี่ ---
        self.load_stylesheet("src/styles/info_window.qss")

        self.feedback_overlay = FeedbackOverlay(user_id=user_id, parent=self)
        self.feedback_overlay.go_back_signal.connect(self.handle_go_back)
        
        self.showMaximized()

    def resizeEvent(self, event):
        # ปรับขนาด Overlay ให้เต็มจอเสมอ
        self.feedback_overlay.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    def handle_go_back(self):
        if self.parent_window:
            self.parent_window.show()
        self.close()

    # --- [MERGED] เพิ่มเมธอดสำหรับโหลด Stylesheet เข้ามาในคลาส ---
    def load_stylesheet(self, path):
        """โหลดไฟล์ QSS และนำมาใช้กับ Widget นี้ (self)"""
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    # ใช้ self.setStyleSheet() เพื่อให้สไตล์มีผลแค่กับหน้าต่างนี้
                    self.setStyleSheet(f.read())
            else:
                print(f"Warning: ไม่พบไฟล์ Stylesheet ที่ {path}")
        except Exception as e:
             print(f"Error loading stylesheet: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # --- [MERGED] ลบการเรียก load_stylesheet(app, ...) จากตรงนี้ ---
    # เพราะ InfoWindow จะโหลดสไตล์ของมันเองแล้ว

    win = InfoWindow(user_id="test_admin")
    sys.exit(app.exec())