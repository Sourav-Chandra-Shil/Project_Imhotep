import sys
import mysql.connector
from mysql.connector import Error
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QTextEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import QGraphicsDropShadowEffect

# -------------------- DATABASE CONFIGURATION --------------------
DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = ""  # Replace with your MySQL password
DB_NAME = "imhotep"

DB_CONFIG = {
    "host": DB_HOST,
    "user": DB_USER,
    "password": DB_PASS,
    "database": DB_NAME,
    "port": 3306
}

# --- SQL Statements for Doctor Portal Only ---
SQL_TABLES = [
    """CREATE TABLE IF NOT EXISTS Prescription (
        Pr_ID INT AUTO_INCREMENT PRIMARY KEY,
        Patient_UID VARCHAR(50),
        Condition_Notes TEXT,
        Prescription TEXT,
        Doctor_Name VARCHAR(100),
        Created_At DATETIME DEFAULT CURRENT_TIMESTAMP
    );""",
    """CREATE TABLE IF NOT EXISTS Doctor_Portal (
        Doctor_ID INT AUTO_INCREMENT PRIMARY KEY,
        Patient_UID VARCHAR(50),
        Doctor_Name VARCHAR(100),
        Pr_ID INT,
        FOREIGN KEY (Pr_ID) REFERENCES Prescription(Pr_ID)
    );"""
]

def get_connection():
    """Create and return a MySQL database connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"DB Connection Error: {e}")
        return None

def initialize_db():
    """Create required tables for Doctor Portal if they do not exist."""
    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        for sql in SQL_TABLES:
            cur.execute(sql)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Doctor Portal tables initialized successfully.")
    except Exception as e:
        print(f"Error initializing tables: {e}")

# -------------------- UI STYLE UTILITIES --------------------
def apply_shadow(widget, blur_radius=20, x_offset=0, y_offset=4, color=QColor(0, 0, 0, 60)):
    """Apply drop shadow effect to a widget."""
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur_radius)
    shadow.setOffset(x_offset, y_offset)
    shadow.setColor(color)
    widget.setGraphicsEffect(shadow)

# -------------------- MAIN UI CLASS --------------------
class DoctorPortalUI(QWidget):
    """Doctor Portal — Main application window for managing patient prescriptions."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Imhotep — Doctor's Portal")
        self.setMinimumSize(980, 700)
        self.setStyleSheet("background-color:#eef1f4;")

        # State Variables 
        self.current_patient_uid = None
        self.registered_doctor_name = None
        self.last_condition = ""
        self.last_prescription = ""
        self.current_edit_prescription_id = None  # Holds prescription_id for edit mode

        self.init_ui()

    # -------------------- INITIAL UI SETUP --------------------
    def init_ui(self):
        """Initialize and layout all UI components."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(28, 20, 28, 18)
        main_layout.setSpacing(18)

        # Title Section 
        title_label = QLabel("Imhotep")
        title_font = QFont("Helvetica", 40, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Doctor's Portal")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666; font-size: 14px;")

        main_layout.addWidget(title_label)
        main_layout.addWidget(subtitle)

        # Main Container
        container = QFrame()
        container.setStyleSheet("background-color:white; border-radius:12px;")
        apply_shadow(container, blur_radius=30, y_offset=6)

        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(26, 22, 26, 22)
        container_layout.setSpacing(12)

        # TOP BAR SECTION
        top_h = QHBoxLayout()
        top_h.setSpacing(20)

        # Left Info 
        left_info = QFrame()
        left_layout = QVBoxLayout()
        left_layout.setSpacing(8)

        self.doctor_name_label = QLabel("Dr. Unknown")
        self.doctor_name_label.setFont(QFont("Helvetica", 18, QFont.Bold))
        left_layout.addWidget(self.doctor_name_label)

        placeholder_btn = QPushButton("Generated UI Placeholder")
        placeholder_btn.setEnabled(False)
        placeholder_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #bbb;
                border-radius: 6px;
                padding: 6px 10px;
                background: #f5f6f7;
                color: #333;
            }
        """)
        placeholder_btn.setMaximumWidth(220)
        left_layout.addWidget(placeholder_btn)
        left_layout.addStretch()

        left_info.setLayout(left_layout)
        left_info.setMaximumWidth(360)
        top_h.addWidget(left_info)

        # Back Button 
        back_btn = QPushButton("← Back")
        back_btn.setFixedWidth(100)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #333;
                border: 1px solid #ccc;
                border-radius: 6px;
                padding: 6px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e6e6e6;
            }
        """)
        back_btn.clicked.connect(self.on_back)

        top_h.addStretch()
        top_h.addWidget(back_btn, alignment=Qt.AlignRight)
        container_layout.addLayout(top_h)

        # BODY SECTION (Left + Right Panels)
        body_h = QHBoxLayout()
        body_h.setSpacing(18)

        # LEFT PANEL — PATIENT SEARCH & HISTORY
        left_card = QFrame()
        left_card.setStyleSheet("background: #fbfbfb; border-radius: 10px;")
        apply_shadow(left_card, blur_radius=18, y_offset=4)

        left_v = QVBoxLayout(left_card)
        left_v.setContentsMargins(18, 16, 18, 16)
        left_v.setSpacing(12)

        find_label = QLabel("Find Patient")
        find_label.setFont(QFont("Helvetica", 12, QFont.Bold))
        left_v.addWidget(find_label)

        self.uid_input = QLineEdit()
        self.uid_input.setPlaceholderText("Enter Patient UID")
        self.uid_input.setFixedHeight(36)
        self.uid_input.setStyleSheet("border:1px solid #e1e1e1; border-radius:6px; padding-left:8px;")
        left_v.addWidget(self.uid_input)

        self.notification_label = QLabel("")
        self.notification_label.setStyleSheet("color: #888; font-size: 11px;")
        left_v.addWidget(self.notification_label)

        self.load_btn = QPushButton("Load Patient")
        self.load_btn.setFixedHeight(40)
        self.load_btn.setStyleSheet("""
            QPushButton {
                background-color: #2b78f6;
                color: white;
                border-radius: 6px;
                font-weight: bold;
            }
        """)
        self.load_btn.clicked.connect(self.on_load_patient)
        left_v.addWidget(self.load_btn)

        hist_label = QLabel("Patient History")
        hist_label.setFont(QFont("Helvetica", 12, QFont.Bold))
        left_v.addWidget(hist_label)

        # History Scroll 
        self.history_scroll = QScrollArea()
        self.history_scroll.setWidgetResizable(True)
        self.history_scroll.setStyleSheet("border:1px solid #e9e9e9; border-radius:8px; background:#fff;")
        self.history_scroll.setFixedHeight(220)

        self.history_content = QWidget()
        self.history_layout = QVBoxLayout(self.history_content)
        self.history_layout.setContentsMargins(10, 10, 10, 10)
        self.history_layout.setSpacing(10)
        self.history_scroll.setWidget(self.history_content)

        left_v.addWidget(self.history_scroll)
        left_v.addStretch(1)

        # RIGHT PANEL — CONDITION & PRESCRIPTION
        right_card = QFrame()
        right_card.setStyleSheet("background: #fbfbfb; border-radius: 10px;")
        apply_shadow(right_card, blur_radius=18, y_offset=4)

        right_v = QVBoxLayout(right_card)
        right_v.setContentsMargins(18, 16, 18, 16)
        right_v.setSpacing(12)

        right_title = QLabel("Current Condition & Prescription")
        right_title.setFont(QFont("Helvetica", 12, QFont.Bold))
        right_v.addWidget(right_title)

        # Notes & Prescription Frame 
        bordered_frame = QFrame()
        bordered_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #ccc;
                border-radius: 8px;
                background: #fff;
            }
        """)
        bordered_layout = QVBoxLayout(bordered_frame)
        bordered_layout.setContentsMargins(10, 10, 10, 10)
        bordered_layout.setSpacing(8)

        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Doctor's notes & patient condition...")
        self.notes_edit.setFixedHeight(120)
        bordered_layout.addWidget(self.notes_edit)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        divider.setStyleSheet("color: #ccc; margin-top:6px; margin-bottom:6px;")
        bordered_layout.addWidget(divider)

        # Prescription
        self.prescription_edit = QTextEdit()
        self.prescription_edit.setPlaceholderText("Prescription details...")
        self.prescription_edit.setFixedHeight(100)
        bordered_layout.addWidget(self.prescription_edit)

        right_v.addWidget(bordered_frame)

        # Save Button 
        self.save_btn = QPushButton("Generate Prescription  Save")
        self.save_btn.setFixedHeight(44)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #20b54b;
                color: white;
                border-radius: 8px;
                font-weight: bold;
            }
        """)
        self.save_btn.clicked.connect(self.on_save_prescription)
        right_v.addWidget(self.save_btn)

        # Logout Button 
        right_v.addStretch(1)
        logout_row = QHBoxLayout()
        logout_row.addStretch()

        self.logout_btn = QPushButton("Log Out")
        self.logout_btn.setFixedSize(100, 36)
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #e05a4f;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #c94b41;
            }
        """)
        self.logout_btn.clicked.connect(self.on_logout)
        logout_row.addWidget(self.logout_btn)
        right_v.addLayout(logout_row)

        # Add Panels
        body_h.addWidget(left_card)
        body_h.addWidget(right_card)
        container_layout.addLayout(body_h)
        container.setLayout(container_layout)

        main_layout.addWidget(container)
        self.setLayout(main_layout)

    # -------------------- LOGIC & ACTIONS --------------------
    def show_notification(self, text, color="#888"):
        self.notification_label.setText(text)
        self.notification_label.setStyleSheet(f"color: {color}; font-size: 11px;")

    def _create_history_card(self, rec):
        card = QFrame()
        card.setStyleSheet("border: 1px solid #ddd; border-radius: 8px; background: #fff;")
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(10, 10, 10, 10)
        vbox.setSpacing(6)

        pid = rec.get("Pr_ID", "")
        date = rec.get("Created_At", "")
        note = (rec.get("Condition_Notes") or "")
        presc_full = (rec.get("Prescription") or "")

        note_preview = note[:120]
        presc_preview = presc_full[:120]

        info = QLabel(
            f"<b>ID:</b> {pid} | <b>Date:</b> {date}<br>"
            f"<b>Notes:</b> {note_preview}<br>"
            f"<b>Prescription:</b> {presc_preview}"
        )
        info.setWordWrap(True)
        vbox.addWidget(info)

        # Edit Button
        edit_btn = QPushButton("✏ Edit")
        edit_btn.setFixedWidth(68)
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #2b78f6;
                color: white;
                border-radius: 6px;
                padding: 4px 6px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #1f5fd6;
            }
        """)
        edit_btn.clicked.connect(lambda _, r=rec: self._on_edit_history_record(r))
        vbox.addWidget(edit_btn, alignment=Qt.AlignRight)

        return card

    def populate_history(self, records):
        for i in reversed(range(self.history_layout.count())):
            widget = self.history_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        if not records:
            no_data = QLabel("No patient data found.")
            no_data.setStyleSheet("color:#888;")
            self.history_layout.addWidget(no_data)
            return

        for rec in records:
            card = self._create_history_card(rec)
            self.history_layout.addWidget(card)

        self.history_layout.addStretch()

    def _on_edit_history_record(self, rec):
        try:
            self.current_edit_prescription_id = rec.get("Pr_ID")
            self.uid_input.setText(rec.get("Patient_UID") or "")
            presc = rec.get("Prescription") or ""
            presc_stripped = self._strip_doctor_signature(presc)
            self.notes_edit.setPlainText(rec.get("Condition_Notes") or "")
            self.prescription_edit.setPlainText(presc_stripped)
            self.show_notification(
                f"Loaded record ID {self.current_edit_prescription_id} for editing.",
                "#20b54b"
            )
        except Exception as e:
            print("Error loading record for edit:", e)

    def _strip_doctor_signature(self, presc_text):
        if not presc_text:
            return presc_text
        idx = presc_text.rfind("\n\n—")
        if idx != -1:
            return presc_text[:idx].rstrip()
        return presc_text

    def on_load_patient(self):
        self.current_edit_prescription_id = None
        uid = self.uid_input.text().strip()
        if not uid:
            return

        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT * FROM Prescription WHERE Patient_UID = %s ORDER BY Created_At DESC", (uid,)
            )
            records = cur.fetchall()
            cur.close()
            conn.close()

            self.populate_history(records)

            if records:
                latest = records[0]
                self.last_condition = latest.get("Condition_Notes") or ""
                self.last_prescription = self._strip_doctor_signature(latest.get("Prescription") or "")
                self.notes_edit.setPlainText(self.last_condition)
                self.prescription_edit.setPlainText(self.last_prescription)
                self.show_notification(
                    "Loaded latest record (not in edit-mode). Click Edit on a card to edit.", "#666"
                )
            else:
                self.last_condition = ""
                self.last_prescription = ""
                self.notes_edit.clear()
                self.prescription_edit.clear()
                self.show_notification("No patient data found — ready to create new.", "#666")

        except Exception as e:
            print(f"Error loading patient: {e}")

    def on_save_prescription(self):
        uid = self.uid_input.text().strip()
        notes = self.notes_edit.toPlainText().strip()
        presc = self.prescription_edit.toPlainText().strip()
        doctor_name = self.doctor_name_label.text().strip() or "Unknown"

        if not uid:
            self.show_notification("Enter a patient UID.", "#c00")
            return
        if not notes and not presc:
            self.show_notification("Please enter notes or prescription.", "#c00")
            return

        conn = get_connection()
        if not conn:
            return

        try:
            cur = conn.cursor()
            if self.current_edit_prescription_id:
                final_presc = presc + f"\n\n— {doctor_name}"
                cur.execute("""
                    UPDATE Prescription
                    SET Condition_Notes = %s, Prescription = %s, Doctor_Name = %s
                    WHERE Pr_ID = %s
                """, (notes, final_presc, doctor_name, self.current_edit_prescription_id))
                conn.commit()
                self.show_notification("Record updated successfully.", "#20b54b")
                self.current_edit_prescription_id = None
                self.on_load_patient()
            else:
                if notes == self.last_condition and presc == self.last_prescription and self.last_condition != "":
                    self.show_notification("No new changes — prescription not saved.", "#c00")
                else:
                    final_presc = presc + f"\n\n— {doctor_name}"
                    cur.execute("""
                        INSERT INTO Prescription (Patient_UID, Condition_Notes, Prescription, Doctor_Name)
                        VALUES (%s, %s, %s, %s)
                    """, (uid, notes, final_presc, doctor_name))
                    conn.commit()
                    self.show_notification("Prescription saved successfully.", "#20b54b")
                    self.on_load_patient()
                    self.last_condition = notes
                    self.last_prescription = presc

            cur.close()
            conn.close()

        except Exception as e:
            print(f"Error saving/updating record: {e}")

    def on_logout(self):
        self.close()

    def on_back(self):
        self.close()


# -------------------- EASY MERGE FUNCTION --------------------
def merge_with_external_module(module_path, class_name=None):
    """
    Dynamically merge an external Python file or class with this Doctor Portal UI.

    Usage:
        merge_with_external_module("patient_portal.py")
        merge_with_external_module("admin_panel.py", "AdminPanel")

    If class_name is provided, it returns that class for manual linking.
    """
    import importlib.util, os
    if not os.path.exists(module_path):
        print(f" Cannot merge: '{module_path}' not found.")
        return None

    spec = importlib.util.spec_from_file_location("merged_module", module_path)
    merged = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(merged)
    print(f"Successfully merged with: {module_path}")

    if class_name and hasattr(merged, class_name):
        return getattr(merged, class_name)
    return merged


#  ENTRY POINT 
def main():
    initialize_db()  # Ensure Doctor Portal tables exist before launching UI
    app = QApplication(sys.argv)
    window = DoctorPortalUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
