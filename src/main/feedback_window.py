import sys
import sqlite3
import os
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

# =========================================
# ส่วนหน้าแสดงรายละเอียด (Detail View)
# =========================================
class FeedbackDetailView(QWidget):
    go_back_signal = pyqtSignal()

    def __init__(self, db_path, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.current_feedback_id = None
        self.init_ui()

    def init_ui(self):
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(250, 220, 250, 100)
        main_layout.setSpacing(0)

        # --- TOP GRID ---
        grid_layout = QGridLayout()
        grid_layout.setSpacing(0)

        lbl_user_h = QLabel("Users")
        lbl_user_h.setProperty("header", True)
        lbl_user_h.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_user_h.setFixedHeight(40)

        lbl_msg_h = QLabel("Message")
        lbl_msg_h.setProperty("header", True)
        lbl_msg_h.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_msg_h.setFixedHeight(40)

        lbl_date_h = QLabel("Date")
        lbl_date_h.setProperty("header", True)
        lbl_date_h.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_date_h.setFixedHeight(40)

        grid_layout.addWidget(lbl_user_h, 0, 0)
        grid_layout.addWidget(lbl_msg_h, 0, 1)
        grid_layout.addWidget(lbl_date_h, 0, 2)

        self.lbl_user_val = QLabel("-")
        self.lbl_user_val.setProperty("data_cell", True)
        self.lbl_user_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_user_val.setFixedWidth(200)

        self.txt_msg_val = QTextEdit()
        self.txt_msg_val.setReadOnly(True)
        self.txt_msg_val.setProperty("data_cell", True)

        self.lbl_date_val = QLabel("-")
        self.lbl_date_val.setProperty("data_cell", True)
        self.lbl_date_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_date_val.setFixedWidth(200)

        grid_layout.addWidget(self.lbl_user_val, 1, 0)
        grid_layout.addWidget(self.txt_msg_val, 1, 1)
        grid_layout.addWidget(self.lbl_date_val, 1, 2)

        grid_layout.setColumnStretch(1, 1)
        grid_layout.setRowStretch(1, 2)

        main_layout.addLayout(grid_layout)
        main_layout.addSpacing(20)

        # --- NOTE SECTION ---
        lbl_note_h = QLabel("Note")
        lbl_note_h.setProperty("header", True)
        lbl_note_h.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_note_h.setFixedHeight(40)
        main_layout.addWidget(lbl_note_h)

        self.txt_note = QTextEdit()
        self.txt_note.setObjectName("note_edit")
        self.txt_note.setPlaceholderText("Type a note here...")
        self.txt_note.textChanged.connect(self.save_note_to_db)
        main_layout.addWidget(self.txt_note)

        main_layout.setStretchFactor(grid_layout, 3)
        main_layout.setStretchFactor(self.txt_note, 2)

        # --- BUTTON ---
        main_layout.addSpacing(20)
        btn_layout = QHBoxLayout()
        self.btn_back = QPushButton("BACK")
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.setMinimumHeight(50)
        self.btn_back.clicked.connect(self.go_back)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_back)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

    def load_detail(self, feedback_id, user, msg, date_str):
        self.current_feedback_id = feedback_id
        self.txt_note.blockSignals(True)

        self.lbl_user_val.setText(str(user))
        self.txt_msg_val.setText(str(msg))
        self.lbl_date_val.setText(date_str.replace(" ", "\n"))

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT note FROM feedback WHERE id = ?", (feedback_id,))
                row = cursor.fetchone()
                self.txt_note.setText(row[0] if row and row[0] else "")
            except sqlite3.OperationalError:
                 pass # Handle missing column if needed
            conn.close()
        except Exception as e:
            print(f"Error loading note: {e}")

        self.txt_note.blockSignals(False)

    def save_note_to_db(self):
        if self.current_feedback_id is None: return
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE feedback SET note = ? WHERE id = ?", (self.txt_note.toPlainText(), self.current_feedback_id))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error saving note: {e}")

    def go_back(self):
        self.go_back_signal.emit()

# =========================================
# ส่วนหน้าตารางรวม (Overlay List View)
# =========================================
class FeedbackOverlay(QWidget):
    request_detail_signal = pyqtSignal(int, str, str, str)
    go_back_signal = pyqtSignal()

    def __init__(self, user_id="guest", parent=None):
        super().__init__(parent)
        self.db_path = "src/database/thisshop.db"
        self.current_user_id = user_id
        self.setObjectName("FeedbackOverlay")
        self.init_ui()
        self.load_feedback_data()

    def init_ui(self):
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(250, 220, 250, 100)
        main_layout.setSpacing(30)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Users", "Message", "Date"])
        self.table.setObjectName("feedback_table")
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(70)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 150)

        self.table.cellClicked.connect(self.on_table_clicked)
        main_layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        self.btn_back = QPushButton("BACK")
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.setObjectName("btn_back")
        self.btn_back.setMinimumWidth(200)
        self.btn_back.setMinimumHeight(50)
        self.btn_back.clicked.connect(self.go_back)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_back)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

    def load_feedback_data(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='feedback'")
            if not cursor.fetchone():
                 conn.close()
                 return

            cursor.execute("SELECT id, user_id, feedback_text, created_at FROM feedback ORDER BY created_at DESC")
            rows = cursor.fetchall()
            self.table.setRowCount(len(rows))
            for row_idx, row_data in enumerate(rows):
                fb_id, user_id, message, created_at_str = row_data
                try:
                    dt_obj = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S")
                    formatted_date = dt_obj.strftime("%d-%b-%Y\n%H:%M")
                except ValueError:
                    formatted_date = created_at_str

                item_user = QTableWidgetItem(str(user_id))
                item_user.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item_user.setData(Qt.ItemDataRole.UserRole, fb_id)
                self.table.setItem(row_idx, 0, item_user)

                self.table.setItem(row_idx, 1, QTableWidgetItem(str(message)))

                item_date = QTableWidgetItem(formatted_date)
                item_date.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row_idx, 2, item_date)

            self.table.resizeRowsToContents()
            conn.close()
        except Exception as e:
            print(f"Error loading feedback data: {e}")

    def on_table_clicked(self, row, column):
        fb_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.request_detail_signal.emit(
            fb_id,
            self.table.item(row, 0).text(),
            self.table.item(row, 1).text(),
            self.table.item(row, 2).text()
        )

    def go_back(self):
        self.go_back_signal.emit()

# =========================================
# Main Window
# =========================================
class feedbackWindow(QMainWindow):
    def __init__(self, user_id="guest", parent_window=None):
        super().__init__()
        self.parent_window = parent_window
        self.setWindowTitle("Beyond Comics - Feedback List")
        self.setObjectName("InfoWindow")
        
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.feedback_overlay = FeedbackOverlay(user_id=user_id, parent=self)
        self.stacked_widget.addWidget(self.feedback_overlay)

        self.detail_view = FeedbackDetailView(db_path=self.feedback_overlay.db_path, parent=self)
        self.stacked_widget.addWidget(self.detail_view)

        self.feedback_overlay.go_back_signal.connect(self.handle_main_go_back)
        self.feedback_overlay.request_detail_signal.connect(self.show_detail_view)
        self.detail_view.go_back_signal.connect(self.show_list_view)

        self.load_stylesheet("src/styles/feedback_window.qss")
        self.showMaximized()

    def show_detail_view(self, fb_id, user, msg, date_str):
        self.detail_view.load_detail(fb_id, user, msg, date_str)
        self.stacked_widget.setCurrentIndex(1)

    def show_list_view(self):
        self.stacked_widget.setCurrentIndex(0)

    def handle_main_go_back(self):
        if self.parent_window: self.parent_window.show()
        self.close()

    def load_stylesheet(self, path):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

if __name__ == '__main__':
    # Create dummy DB for testing
    if not os.path.exists("src/database"): os.makedirs("src/database")
    conn = sqlite3.connect("src/database/thisshop.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, feedback_text TEXT, created_at TEXT, note TEXT)")
    cursor.execute("SELECT COUNT(*) FROM feedback")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO feedback (user_id, feedback_text, created_at) VALUES (?, ?, ?)", ("TestUser", "Test Message Long enough specifically designed to test text wrapping features.", "2025-11-10 10:30:00"))
        conn.commit()
    conn.close()

    app = QApplication(sys.argv)
    win = feedbackWindow(user_id="test_admin")
    sys.exit(app.exec())