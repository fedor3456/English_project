import sys
import sqlite3
from datetime import datetime, timedelta
from functools import partial
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLineEdit, QComboBox, QWidget,
                             QTabWidget, QListWidget, QListWidgetItem, QFrame,
                             QLabel, QDialog, QMessageBox, QScrollArea)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIntValidator

# === ORGANIC DESIGN STYLE ===
STYLE_SHEET = """
QMainWindow { background-color: #f4f7f6; } 
QTabWidget::pane { border: 1px solid #2ecc71; background: #ffffff; top: -1px; border-radius: 12px; }
QTabBar::tab {
    background: #e8ecef; padding: 15px 35px; font-family: 'Segoe UI'; 
    font-weight: bold; color: black; border-top-left-radius: 12px; border-top-right-radius: 12px; margin-right: 4px;
    border: 1px solid #2ecc71; border-bottom: none;
}
QTabBar::tab:selected { background: #2ecc71; color: white; border: 2px solid #2ecc71; border-bottom: none; }
QListWidget { outline: 0; background: transparent; border: none; }
QListWidget::item:selected { background: transparent; }

QScrollBar:vertical { border: none; background: #f0f0f0; width: 10px; border-radius: 5px; }
QScrollBar::handle:vertical { background: #2ecc71; border-radius: 5px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { border: none; background: none; }
"""

CARD_STYLE = "QFrame { background-color: #f4fbf7; border: 2px solid #2ecc71; border-radius: 16px; }"
INPUT_BLACK_STYLE = "QLineEdit { border: 2px solid black; border-radius: 10px; padding: 10px 15px; font-size: 15px; color: black; background: #ffffff; }"
COMBO_GREEN_STYLE = """
QComboBox { border: 2px solid #2ecc71; border-radius: 10px; padding: 8px 15px; font-size: 15px; color: black; background: #ffffff; }
QComboBox:hover { border-color: #27ae60; }
QComboBox::drop-down { border: none; padding-right: 10px; }
QComboBox::down-arrow { width: 12px; height: 12px; }
QComboBox QAbstractItemView { border: 2px solid #2ecc71; border-radius: 8px; background-color: #ffffff; color: black; selection-background-color: #2ecc71; selection-color: white; outline: none; }
"""
BTN_STYLE = """
QPushButton { border: 2px solid #2ecc71; border-radius: 10px; padding: 12px; font-weight: bold; font-size: 14px; color: black; background-color: #ffffff; } 
QPushButton:hover { background-color: #2ecc71; color: white; }
"""


class ExpiryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GreenSrok v6.0 — English UI & New Storage Rules")
        self.resize(1200, 800)
        self.setStyleSheet(STYLE_SHEET)

        self.init_db()
        self.init_ui()

    def init_db(self):
        # New DB version to apply new default products and column schemas
        self.conn = sqlite3.connect('warehouse_v8.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute(
            'CREATE TABLE IF NOT EXISTS inventory (id INTEGER PRIMARY KEY, name TEXT, sku TEXT, storage TEXT, expiry_date TEXT)')
        self.cursor.execute(
            'CREATE TABLE IF NOT EXISTS catalog (id INTEGER PRIMARY KEY, name TEXT, sku TEXT, days_dark INTEGER, days_light INTEGER, days_fridge INTEGER)')

        self.cursor.execute("SELECT COUNT(*) FROM catalog")
        if self.cursor.fetchone()[0] == 0:
            # Default products (Name, SKU, Days on Dark shelf, Days in Light, Days in Fridge)
            defaults = [
                ("Orange", "001", 14, 7, 30),
                ("Potato", "002", 30, 7, 0),
                ("Peach", "003", 3, 1, 7),
                ("Red Sweet Pepper", "004", 0, 0, 14),
                ("Bread", "005", 7, 4, 14),
                ("Banana", "006", 5, 3, 0),
                ("Apple", "007", 14, 7, 30),
                ("Grape", "008", 2, 1, 14)
            ]
            self.cursor.executemany(
                "INSERT INTO catalog (name, sku, days_dark, days_light, days_fridge) VALUES (?, ?, ?, ?, ?)", defaults)
        self.conn.commit()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.tab_storage = QWidget()
        self.tab_search = QWidget()
        self.tab_catalog = QWidget()

        self.tabs.addTab(self.tab_storage, "📦 MY WAREHOUSE")
        self.tabs.addTab(self.tab_search, "🔍 RECEIVING (ADD)")
        self.tabs.addTab(self.tab_catalog, "⚙️ PRODUCT DATABASE")

        self.setup_storage_tab()
        self.setup_search_tab()
        self.setup_catalog_tab()

    def setup_storage_tab(self):
        layout = QVBoxLayout(self.tab_storage)
        self.storage_list = QListWidget()
        self.storage_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.storage_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.storage_list.setSpacing(25)
        layout.addWidget(self.storage_list)
        self.refresh_storage_cards()

    def refresh_storage_cards(self):
        self.storage_list.clear()
        self.cursor.execute("SELECT name, sku, COUNT(id) FROM inventory GROUP BY name, sku")
        for name, sku, count in self.cursor.fetchall():
            card = QFrame()
            card.setStyleSheet(CARD_STYLE)
            card.setFixedSize(300, 190)
            lay = QVBoxLayout(card)

            title = QLabel(name.upper())
            title.setStyleSheet(
                "color: black; font-size: 20px; font-weight: 900; border: none; background: transparent;")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title.setWordWrap(True)

            lbl_sku = QLabel(f"SKU: {sku}")
            lbl_sku.setStyleSheet(
                "color: #7f8c8d; font-size: 14px; font-weight: bold; border: none; background: transparent;")
            lbl_sku.setAlignment(Qt.AlignmentFlag.AlignCenter)

            badge = QLabel(f"BATCHES: {count}")
            badge.setStyleSheet(
                "color: #27ae60; font-weight: bold; font-size: 15px; border: none; background: transparent;")
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

            btn = QPushButton("DETAILS")
            btn.setStyleSheet(BTN_STYLE)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(partial(self.show_details, name, sku))

            lay.addWidget(title);
            lay.addWidget(lbl_sku);
            lay.addStretch();
            lay.addWidget(badge);
            lay.addWidget(btn)

            item = QListWidgetItem(self.storage_list)
            item.setSizeHint(QSize(310, 200))
            self.storage_list.setItemWidget(item, card)

    def show_details(self, product_name, sku):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Warehouse Batches: {product_name} (SKU: {sku})")
        dialog.resize(900, 600)
        dialog.setMinimumSize(700, 500)
        dialog.setStyleSheet("QDialog { background-color: #f4f7f6; }")

        lay = QVBoxLayout(dialog)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_lay = QVBoxLayout(content)
        content_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        content_lay.setSpacing(15)

        def populate():
            for i in reversed(range(content_lay.count())):
                widget = content_lay.itemAt(i).widget()
                if widget: widget.deleteLater()

            self.cursor.execute(
                "SELECT id, storage, expiry_date FROM inventory WHERE name = ? AND sku = ? ORDER BY expiry_date ASC",
                (product_name, sku))
            records = self.cursor.fetchall()

            if not records:
                empty_lbl = QLabel("All batches written off.")
                empty_lbl.setStyleSheet(
                    "font-size: 18px; color: #7f8c8d; font-weight: bold; border: none; margin-top: 20px;")
                empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                content_lay.addWidget(empty_lbl)
                return

            for batch_id, storage, expiry in records:
                b_card = QFrame()
                b_card.setStyleSheet(
                    "QFrame { background: #ebf9f1; border: 2px solid #2ecc71; border-radius: 12px; padding: 15px 20px; } QLabel { border: none; background: transparent; color: black; font-size: 16px; font-weight: bold; }")
                bl = QHBoxLayout(b_card)

                info = QLabel(f"📦 Storage: {storage}   |   ⏳ Expiry: {expiry}   |   🔖 Batch ID: {batch_id}")

                btn_del = QPushButton("Write-off")
                btn_del.setStyleSheet("""
                    QPushButton { border: 2px solid #ff7675; border-radius: 8px; padding: 8px 25px; font-weight: bold; font-size: 15px; color: #d63031; background-color: #ffffff; } 
                    QPushButton:hover { background-color: #ff7675; color: white; }
                """)
                btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_del.clicked.connect(partial(delete_batch, batch_id))

                bl.addWidget(info)
                bl.addStretch()
                bl.addWidget(btn_del)
                content_lay.addWidget(b_card)

        def delete_batch(batch_id):
            msg = QMessageBox(dialog)
            msg.setWindowTitle('Write-off')
            msg.setText("Are you sure you want to write off this batch?")
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg.setStyleSheet(
                f"QMessageBox {{ background-color: #ffffff; }} QLabel {{ color: black; font-size: 15px; }} {BTN_STYLE}")

            if msg.exec() == QMessageBox.StandardButton.Yes:
                self.cursor.execute("DELETE FROM inventory WHERE id = ?", (batch_id,))
                self.conn.commit()
                populate()
                self.refresh_storage_cards()

        populate()

        scroll.setWidget(content)
        lay.addWidget(scroll)

        btn_close = QPushButton("CLOSE WINDOW")
        btn_close.setStyleSheet(BTN_STYLE)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(dialog.accept)
        lay.addWidget(btn_close)

        dialog.exec()

    def setup_search_tab(self):
        layout = QVBoxLayout(self.tab_search)
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search by product name or SKU...")
        self.search_bar.setStyleSheet(INPUT_BLACK_STYLE)
        self.search_bar.textChanged.connect(self.refresh_search_results)
        layout.addWidget(self.search_bar)

        self.search_list = QListWidget()
        self.search_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.search_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.search_list.setSpacing(25)
        layout.addWidget(self.search_list)
        self.refresh_search_results()

    def refresh_search_results(self):
        self.search_list.clear()
        text = self.search_bar.text().lower()
        self.cursor.execute("SELECT id, name, sku, days_dark, days_light, days_fridge FROM catalog")
        for cat_id, name, sku, d_dark, d_light, d_fridge in self.cursor.fetchall():
            if text in name.lower() or text in sku.lower():
                card = QFrame()
                card.setStyleSheet(CARD_STYLE)
                card.setFixedSize(340, 230)
                v_lay = QVBoxLayout(card)

                title = QLabel(f"{name}\n(SKU: {sku})")
                title.setStyleSheet(
                    "color: black; font-size: 18px; font-weight: 900; border: none; background: transparent;")
                title.setAlignment(Qt.AlignmentFlag.AlignCenter)

                combo = QComboBox()
                combo.setStyleSheet(COMBO_GREEN_STYLE)
                combo.setCursor(Qt.CursorShape.PointingHandCursor)
                combo.addItem("Dark shelf", d_dark)
                combo.addItem("In the light", d_light)
                combo.addItem("Fridge", d_fridge)

                btn_lay = QHBoxLayout()
                btn_add = QPushButton("RECEIVE")
                btn_add.setStyleSheet(BTN_STYLE)
                btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_add.clicked.connect(partial(self.add_batch, name, sku, combo))

                btn_del = QPushButton("DELETE")
                btn_del.setStyleSheet(BTN_STYLE)
                btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_del.clicked.connect(partial(self.delete_product, cat_id, name))

                btn_lay.addWidget(btn_add);
                btn_lay.addWidget(btn_del)
                v_lay.addWidget(title);
                v_lay.addWidget(combo);
                v_lay.addStretch();
                v_lay.addLayout(btn_lay)

                item = QListWidgetItem(self.search_list)
                item.setSizeHint(QSize(350, 240))
                self.search_list.setItemWidget(item, card)

    def add_batch(self, name, sku, combo):
        storage_text = combo.currentText()
        days = combo.currentData()
        expiry = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

        self.cursor.execute("INSERT INTO inventory (name, sku, storage, expiry_date) VALUES (?, ?, ?, ?)",
                            (name, sku, storage_text, expiry))
        self.conn.commit()

        msg = QMessageBox(self)
        msg.setWindowTitle("Success")
        msg.setText(f"Product '{name}' (SKU: {sku}) successfully received!\nExpiry date: {expiry}")
        msg.setStyleSheet(
            f"QMessageBox {{ background-color: #ffffff; }} QLabel {{ color: black; font-size: 15px; }} {BTN_STYLE}")
        msg.exec()

        self.refresh_storage_cards()
        self.tabs.setCurrentIndex(0)

    def delete_product(self, cat_id, name):
        msg = QMessageBox(self)
        msg.setWindowTitle('Delete')
        msg.setText(f"Permanently delete '{name}' from the database?")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setStyleSheet(
            f"QMessageBox {{ background-color: #ffffff; }} QLabel {{ color: black; font-size: 15px; }} {BTN_STYLE}")

        if msg.exec() == QMessageBox.StandardButton.Yes:
            self.cursor.execute("DELETE FROM catalog WHERE id = ?", (cat_id,))
            self.conn.commit()
            self.refresh_search_results()

    def setup_catalog_tab(self):
        main_layout = QHBoxLayout(self.tab_catalog)
        main_layout.addStretch()

        center_widget = QWidget()
        v_lay = QVBoxLayout(center_widget)
        v_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        v_lay.setSpacing(20)

        title = QLabel("Add new product to database")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2ecc71; margin-bottom: 15px; border: none;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v_lay.addWidget(title)

        lbl_style = "font-size: 15px; font-weight: bold; color: black; border: none;"
        INPUT_WIDTH = 450

        self.new_name = QLineEdit()
        self.new_name.setPlaceholderText("e.g.: Pink Lady Apples")
        self.new_name.setStyleSheet(INPUT_BLACK_STYLE)
        self.new_name.setFixedWidth(INPUT_WIDTH)
        lbl1 = QLabel("1. Product Name:")
        lbl1.setStyleSheet(lbl_style)
        v_lay.addWidget(lbl1);
        v_lay.addWidget(self.new_name)

        self.new_sku = QLineEdit()
        self.new_sku.setPlaceholderText("e.g.: 101, ART-55, Grade A")
        self.new_sku.setStyleSheet(INPUT_BLACK_STYLE)
        self.new_sku.setFixedWidth(INPUT_WIDTH)
        lbl2 = QLabel("2. SKU / Number / Variety:")
        lbl2.setStyleSheet(lbl_style)
        v_lay.addWidget(lbl2);
        v_lay.addWidget(self.new_sku)

        only_int = QIntValidator(0, 9999)

        self.s_dark = QLineEdit("0")
        self.s_dark.setValidator(only_int)
        self.s_dark.setStyleSheet(INPUT_BLACK_STYLE)
        self.s_dark.setFixedWidth(INPUT_WIDTH)
        lbl3 = QLabel("3. Shelf life on a DARK SHELF (days, 0 if not allowed):")
        lbl3.setStyleSheet(lbl_style)
        v_lay.addWidget(lbl3);
        v_lay.addWidget(self.s_dark)

        self.s_light = QLineEdit("0")
        self.s_light.setValidator(only_int)
        self.s_light.setStyleSheet(INPUT_BLACK_STYLE)
        self.s_light.setFixedWidth(INPUT_WIDTH)
        lbl4 = QLabel("4. Shelf life IN THE LIGHT (days):")
        lbl4.setStyleSheet(lbl_style)
        v_lay.addWidget(lbl4);
        v_lay.addWidget(self.s_light)

        self.s_fridge = QLineEdit("0")
        self.s_fridge.setValidator(only_int)
        self.s_fridge.setStyleSheet(INPUT_BLACK_STYLE)
        self.s_fridge.setFixedWidth(INPUT_WIDTH)
        lbl5 = QLabel("5. Shelf life in the FRIDGE (days):")
        lbl5.setStyleSheet(lbl_style)
        v_lay.addWidget(lbl5);
        v_lay.addWidget(self.s_fridge)

        v_lay.addSpacing(15)

        save = QPushButton("SAVE TO DATABASE")
        save.setStyleSheet(BTN_STYLE)
        save.setFixedWidth(INPUT_WIDTH)
        save.setCursor(Qt.CursorShape.PointingHandCursor)
        save.clicked.connect(self.save_to_db)
        v_lay.addWidget(save)

        main_layout.addWidget(center_widget)
        main_layout.addStretch()

    def save_to_db(self):
        name = self.new_name.text().strip()
        sku = self.new_sku.text().strip()

        if not name or not sku:
            msg = QMessageBox(self)
            msg.setWindowTitle("Error")
            msg.setText("Please enter both Product Name and SKU!")
            msg.setStyleSheet(
                f"QMessageBox {{ background-color: #ffffff; }} QLabel {{ color: black; font-size: 15px; }} {BTN_STYLE}")
            msg.exec()
            return

        self.cursor.execute("SELECT id FROM catalog WHERE name = ? AND sku = ?", (name, sku))
        if self.cursor.fetchone():
            msg = QMessageBox(self)
            msg.setWindowTitle("Error")
            msg.setText("A product with this Name and SKU already exists!")
            msg.setStyleSheet(
                f"QMessageBox {{ background-color: #ffffff; }} QLabel {{ color: black; font-size: 15px; }} {BTN_STYLE}")
            msg.exec()
            return

        self.cursor.execute(
            "INSERT INTO catalog (name, sku, days_dark, days_light, days_fridge) VALUES (?, ?, ?, ?, ?)",
            (name, sku, int(self.s_dark.text()), int(self.s_light.text()), int(self.s_fridge.text())))
        self.conn.commit()
        self.refresh_search_results()

        msg = QMessageBox(self)
        msg.setWindowTitle("Success")
        msg.setText(f"Product '{name}' (SKU: {sku}) added to database!")
        msg.setStyleSheet(
            f"QMessageBox {{ background-color: #ffffff; }} QLabel {{ color: black; font-size: 15px; }} {BTN_STYLE}")
        msg.exec()

        self.new_name.clear()
        self.new_sku.clear()
        self.s_dark.setText("0")
        self.s_light.setText("0")
        self.s_fridge.setText("0")

        self.tabs.setCurrentIndex(1)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = ExpiryApp()
    ex.show()
    sys.exit(app.exec())