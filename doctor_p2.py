import sys
import mysql.connector
from mysql.connector import Error
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QTextEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QScrollArea, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QCursor
from PyQt5.QtWidgets import QGraphicsDropShadowEffect

#  DATABASE CONFIGURATION
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "imhotep",
    "port": 3306
}

def get_connection(parent_widget=None):
    """Create and return a MySQL database connection. Shows a QMessageBox on failure."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            return conn
        else:
            raise Error("Unable to establish DB connection.")
    except Error as e:
        msg = f"Database connection error:\n{e}"
        if parent_widget is not None:
            QMessageBox.critical(parent_widget, "Database Error", msg)
        else:
            print(msg)
        return None

def apply_shadow(widget, blur_radius=20, x_offset=0, y_offset=4, color=QColor(0, 0, 0, 60)):
    """Apply drop shadow effect to a widget."""
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur_radius)
    shadow.setOffset(x_offset, y_offset)
    shadow.setColor(color)
    widget.setGraphicsEffect(shadow)

def style_button(btn, primary=False):
    """Apply consistent interactive styles to a button. primary=True gives stronger color."""
    # Use Qt-supported stylesheet properties (:hover, :pressed)
    if primary:
        # Strong primary button (e.g., Load, Save)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #2b78f6;
                color: white;
                border: 1px solid #1f5fd6;
                border-radius: 8px;
                padding: 8px 12px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #1a63d9; }
            QPushButton:pressed { background-color: #144fb8; }
            QPushButton:focus { outline: none; }
        """)
    else:
        # Secondary / neutral buttons (e.g., Back, Edit, Logout)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f6f7;
                color: #222;
                border: 1px solid #ccc;
                border-radius: 8px;
                padding: 6px 10px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #ececec; }
            QPushButton:pressed { background-color: #e0e0e0; }
            QPushButton:focus { outline: none; }
        """)
    # pointer cursor for clarity
    btn.setCursor(QCursor(Qt.PointingHandCursor))

class DoctorPortalUI(QWidget):
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
        self.current_edit_prescription_id = None

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(28, 20, 28, 18)
        main_layout.setSpacing(12)

        # --------------------
        # TOP ROW: Back button at top-left + Title centered
        # --------------------
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        # Back button placed at the very left (as requested)
        self.back_btn = QPushButton("← Back")
        self.back_btn.setFixedWidth(100)
        style_button(self.back_btn, primary=False)
        self.back_btn.clicked.connect(self.on_back)
        top_row.addWidget(self.back_btn, alignment=Qt.AlignLeft)

        # Title in center area - keep big
        title_container = QHBoxLayout()
        title_container.addStretch(1)
        title_label = QLabel("Imhotep")
        title_label.setFont(QFont("Helvetica", 40, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_container.addWidget(title_label)
        title_container.addStretch(1)
        top_row.addLayout(title_container)

        # keep a small spacer at right to balance
        top_row.addSpacing(100)

        main_layout.addLayout(top_row)

        # Subtitle under title (centered)
        subtitle = QLabel("Doctor's Portal")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666; font-size: 14px;")
        main_layout.addWidget(subtitle)

        # Main container (unchanged visually)
        container = QFrame()
        container.setStyleSheet("background-color:white; border-radius:12px;")
        apply_shadow(container, blur_radius=30, y_offset=6)
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(26, 22, 26, 22)
        container_layout.setSpacing(12)

        # BODY
        body_h = QHBoxLayout()
        body_h.setSpacing(18)

        # LEFT PANEL
        left_card = QFrame()
        left_card.setStyleSheet("background: #fbfbfb; border-radius: 10px;")
        apply_shadow(left_card, blur_radius=18, y_offset=4)
        left_v = QVBoxLayout(left_card)
        left_v.setContentsMargins(18, 16, 18, 16)
        left_v.setSpacing(12)
        left_v.addWidget(QLabel("Find Patient", font=QFont("Helvetica", 12, QFont.Bold)))
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
        style_button(self.load_btn, primary=True)   # stronger, clearer primary style
        self.load_btn.clicked.connect(self.on_load_patient)
        left_v.addWidget(self.load_btn)

        left_v.addWidget(QLabel("Patient History", font=QFont("Helvetica", 12, QFont.Bold)))
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

        # RIGHT PANEL
        right_card = QFrame()
        right_card.setStyleSheet("background: #fbfbfb; border-radius: 10px;")
        apply_shadow(right_card, blur_radius=18, y_offset=4)
        right_v = QVBoxLayout(right_card)
        right_v.setContentsMargins(18, 16, 18, 16)
        right_v.setSpacing(12)
        right_v.addWidget(QLabel("Current Condition & Prescription", font=QFont("Helvetica", 12, QFont.Bold)))

        bordered_frame = QFrame()
        bordered_frame.setStyleSheet("border: 1px solid #ccc; border-radius: 8px; background: #fff;")
        bordered_layout = QVBoxLayout(bordered_frame)
        bordered_layout.setContentsMargins(10, 10, 10, 10)
        bordered_layout.setSpacing(8)
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Doctor's notes & patient condition...")
        self.notes_edit.setFixedHeight(120)
        bordered_layout.addWidget(self.notes_edit)
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        divider.setStyleSheet("color: #ccc; margin-top:6px; margin-bottom:6px;")
        bordered_layout.addWidget(divider)
        self.prescription_edit = QTextEdit()
        self.prescription_edit.setPlaceholderText("Prescription details...")
        self.prescription_edit.setFixedHeight(100)
        bordered_layout.addWidget(self.prescription_edit)
        right_v.addWidget(bordered_frame)

        self.save_btn = QPushButton("Generate Prescription  Save")
        self.save_btn.setFixedHeight(44)
        style_button(self.save_btn, primary=True)
        self.save_btn.clicked.connect(self.on_save_prescription)
        right_v.addWidget(self.save_btn)

        logout_row = QHBoxLayout()
        logout_row.addStretch()
        self.logout_btn = QPushButton("Log Out")
        self.logout_btn.setFixedSize(100, 36)
        style_button(self.logout_btn, primary=False)
        self.logout_btn.clicked.connect(self.on_logout)
        logout_row.addWidget(self.logout_btn)
        right_v.addLayout(logout_row)

        body_h.addWidget(left_card)
        body_h.addWidget(right_card)
        container_layout.addLayout(body_h)
        container.setLayout(container_layout)
        main_layout.addWidget(container)
        self.setLayout(main_layout)

    # ---------- LOGIC ----------
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
        note = rec.get("Condition_Notes") or ""
        presc_full = rec.get("Prescription") or ""
        info = QLabel(f"<b>ID:</b> {pid}<br><b>Notes:</b> {note[:120]}<br><b>Prescription:</b> {presc_full[:120]}")
        info.setWordWrap(True)
        vbox.addWidget(info)

        # Edit button: uses secondary style but clear hover/pressed feedback
        edit_btn = QPushButton("✏ Edit")
        edit_btn.setFixedWidth(72)
        style_button(edit_btn, primary=False)
        edit_btn.clicked.connect(lambda _, r=rec: self._on_edit_history_record(r))
        vbox.addWidget(edit_btn, alignment=Qt.AlignRight)
        return card

    def _clear_layout(self, layout):
        """Safely remove widgets from a layout."""
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def populate_history(self, records):
        self._clear_layout(self.history_layout)
        if not records:
            no_data = QLabel("No patient data found.")
            no_data.setStyleSheet("color:#888;")
            self.history_layout.addWidget(no_data)
            self.history_layout.addStretch()
            return
        for rec in records:
            self.history_layout.addWidget(self._create_history_card(rec))
        self.history_layout.addStretch()

    def _on_edit_history_record(self, rec):
        self.current_edit_prescription_id = rec.get("Pr_ID")
        self.uid_input.setText(rec.get("Patient_UID") or "")
        self.notes_edit.setPlainText(rec.get("Condition_Notes") or "")
        self.prescription_edit.setPlainText(rec.get("Prescription") or "")
        self.show_notification(f"Loaded record ID {self.current_edit_prescription_id} for editing.", "#20b54b")

    def on_load_patient(self):
        """Load patient history using Patient_UID (not numeric Patient_ID)."""
        self.current_edit_prescription_id = None
        uid = self.uid_input.text().strip()
        if not uid:
            self.show_notification("Please enter Patient UID.", "#e05a4f")
            return

        conn = get_connection(parent_widget=self)
        if not conn:
            return
        cur = None
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT prescription.*, patient_portal.Patient_UID
                FROM prescription
                JOIN patient_portal ON prescription.Patient_ID = patient_portal.Patient_ID
                WHERE patient_portal.Patient_UID = %s
                ORDER BY prescription.Pr_ID DESC
            """, (uid,))
            records = cur.fetchall()
            self.populate_history(records)
            if records:
                latest = records[0]
                self.notes_edit.setPlainText(latest.get("Condition_Notes") or "")
                self.prescription_edit.setPlainText(latest.get("Prescription") or "")
                self.show_notification("Loaded latest record.", "#666")
            else:
                self.notes_edit.clear()
                self.prescription_edit.clear()
                self.show_notification("No patient data found.", "#666")
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Error loading patient data:\n{e}")
            print(f"Error loading patient: {e}")
        finally:
            if cur:
                cur.close()
            conn.close()

    def on_save_prescription(self):
        """Insert or update prescription depending on whether an edit id is set."""
        uid = self.uid_input.text().strip()
        notes = self.notes_edit.toPlainText().strip()
        presc = self.prescription_edit.toPlainText().strip()

        if not uid:
            self.show_notification("Please enter Patient UID.", "#e05a4f")
            return

        if not notes and not presc:
            self.show_notification("Notes or prescription must not be empty.", "#e05a4f")
            return

        conn = get_connection(parent_widget=self)
        if not conn:
            return

        cur = None
        try:
            cur = conn.cursor()

            # If editing existing prescription -> UPDATE
            if self.current_edit_prescription_id:
                cur.execute("""
                    UPDATE prescription
                    SET Condition_Notes = %s, Prescription = %s
                    WHERE Pr_ID = %s
                """, (notes, presc, self.current_edit_prescription_id))
                conn.commit()
                self.show_notification("Prescription updated successfully.", "#20b54b")
                self.current_edit_prescription_id = None
                self.on_load_patient()
                return

            # INSERT path: first verify patient exists and get numeric Patient_ID
            cur.execute("SELECT Patient_ID FROM patient_portal WHERE Patient_UID = %s", (uid,))
            patient_row = cur.fetchone()
            if not patient_row:
                self.show_notification("Invalid Patient UID — patient not found.", "#e05a4f")
                return
            patient_id = patient_row[0] if isinstance(patient_row, tuple) else patient_row

            # Insert new prescription
            cur.execute("""
                INSERT INTO prescription (Patient_ID, Condition_Notes, Prescription)
                VALUES (%s, %s, %s)
            """, (patient_id, notes, presc))
            conn.commit()
            self.show_notification("Prescription saved successfully.", "#20b54b")
            self.on_load_patient()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Save Error", f"Error saving prescription:\n{e}")
            print(f"Error saving prescription: {e}")
        finally:
            if cur:
                cur.close()
            conn.close()

    def on_logout(self): 
        self.close()
    def on_back(self): 
        self.close()

# ENTRY POINT
def main():
    app = QApplication(sys.argv)
    window = DoctorPortalUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
