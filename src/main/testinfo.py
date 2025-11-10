import sys
import os
import subprocess
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QLabel
from PyQt6.QtGui import QPixmap, QCursor
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Beyond Comics - Main App")
        
        # ล็อกขนาดหน้าต่างไว้ก่อนเพื่อความแม่นยำในการวางตำแหน่ง
        self.setFixedSize(1280, 720)
        # self.showMaximized() # ปิดไว้ชั่วคราวระหว่างปรับตำแหน่ง

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # --- ส่วนพื้นหลัง ---
        self.bg_label = QLabel(self.central_widget)
        pixmap = QPixmap("src/img/user/userbg.png")
        if pixmap.isNull():
             self.bg_label.setText("Error: ไม่พบไฟล์รูปภาพ")
             self.bg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
             # ใส่สีพื้นหลังแทนถ้าไม่เจอรูป จะได้เห็นปุ่มชัดๆ
             self.bg_label.setStyleSheet("background-color: lightgray;")
        else:
            self.bg_label.setPixmap(pixmap)
            self.bg_label.setScaledContents(True)
        self.bg_label.resize(1280, 720)

        # --- ส่วนปุ่ม Info ---
        self.btn_info = QPushButton(self.central_widget)
        
        # *** เปลี่ยน Style Sheet ชั่วคราวเพื่อแสดงขอบสีแดง ***
        # border: 2px solid red;  <- เพิ่มขอบสีแดงหนา 2px
        # background-color: rgba(255, 0, 0, 50); <- เพิ่มสีพื้นแดงจางๆ ให้เห็นพื้นที่คลิกชัดขึ้น
        self.btn_info.setStyleSheet("""
            QPushButton {
                border: 2px solid red;
                background-color: rgba(255, 0, 0, 50);
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 100);
            }
        """)
        
        self.btn_info.setCursor(Qt.CursorShape.PointingHandCursor)

        # ตำแหน่งเริ่มต้น (ลองปรับค่าพวกนี้ดูครับ)
        # x=245, y=80, กว้าง=60, สูง=60
        self.btn_info.setGeometry(245, 80, 60, 60)
        
        # ดึงปุ่มขึ้นมาไว้บนสุดเสมอ
        self.btn_info.raise_()

        self.btn_info.clicked.connect(self.open_info_window)

    def open_info_window(self):
        filename = "src/main/info.py"
        if os.path.exists(filename):
            print(f"Opening {filename}...")
            subprocess.Popen([sys.executable, filename])
        else:
            print(f"Error: ไม่พบไฟล์ {filename} ในโฟลเดอร์ปัจจุบัน")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())