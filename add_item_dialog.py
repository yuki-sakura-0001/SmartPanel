# add_item_dialog.py

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QFileDialog, QMessageBox
from PyQt6.QtCore import Qt, QObject, pyqtSignal
import os
import logging

class SignalEmitter(QObject):
    item_saved = pyqtSignal(dict)

class AddItemDialog(QDialog):
    def __init__(self, parent=None, item_data=None):
        super().__init__(parent)
        self.setWindowTitle("添加/編輯啟動項")
        self.setFixedSize(400, 200)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self.emitter = SignalEmitter()
        self.item_data = item_data if item_data else {}

        self.setup_ui()
        self.load_item_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 名稱輸入
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("名稱:"))
        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("輸入啟動項名稱")
        name_layout.addWidget(self.name_input)
        main_layout.addLayout(name_layout)

        # 路徑輸入和瀏覽按鈕
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("路徑:"))
        self.path_input = QLineEdit(self)
        self.path_input.setPlaceholderText("輸入程式路徑或網址")
        path_layout.addWidget(self.path_input)
        self.browse_button = QPushButton("瀏覽", self)
        self.browse_button.clicked.connect(self.browse_file)
        path_layout.addWidget(self.browse_button)
        main_layout.addLayout(path_layout)

        # 圖標路徑輸入和瀏覽按鈕
        icon_layout = QHBoxLayout()
        icon_layout.addWidget(QLabel("圖標:"))
        self.icon_input = QLineEdit(self)
        self.icon_input.setPlaceholderText("輸入圖標路徑 (可選)")
        icon_layout.addWidget(self.icon_input)
        self.browse_icon_button = QPushButton("瀏覽", self)
        self.browse_icon_button.clicked.connect(self.browse_icon)
        icon_layout.addWidget(self.browse_icon_button)
        main_layout.addLayout(icon_layout)

        # 按鈕區
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        self.cancel_button = QPushButton("取消", self)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        self.save_button = QPushButton("保存", self)
        self.save_button.clicked.connect(self.save_item)
        button_layout.addWidget(self.save_button)
        main_layout.addLayout(button_layout)

    def load_item_data(self):
        if self.item_data:
            self.name_input.setText(self.item_data.get("name", ""))
            self.path_input.setText(self.item_data.get("path", ""))
            self.icon_input.setText(self.item_data.get("icon", ""))

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "選擇程式或文件", "", "所有文件 (*);;可執行文件 (*.exe);;腳本文件 (*.py)")
        if file_path:
            self.path_input.setText(file_path)

    def browse_icon(self):
        icon_path, _ = QFileDialog.getOpenFileName(self, "選擇圖標文件", "", "圖片文件 (*.png *.jpg *.jpeg *.ico);;所有文件 (*)")
        if icon_path:
            self.icon_input.setText(icon_path)

    def save_item(self):
        name = self.name_input.text().strip()
        path = self.path_input.text().strip()
        icon = self.icon_input.text().strip()

        if not name or not path:
            QMessageBox.warning(self, "輸入錯誤", "名稱和路徑不能為空。")
            return

        # 驗證路徑是否存在 (如果是本地文件)
        if not path.startswith(("http://", "https://")) and not os.path.exists(path):
            QMessageBox.warning(self, "路徑錯誤", "指定的路徑不存在，請檢查。")
            return

        # 驗證圖標路徑是否存在 (如果提供了)
        if icon and not os.path.exists(icon):
            QMessageBox.warning(self, "圖標錯誤", "指定的圖標路徑不存在，請檢查。")
            return

        item_data = {
            "name": name,
            "path": path,
            "icon": icon
        }
        self.emitter.item_saved.emit(item_data)
        self.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = None
            event.accept()

if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    dialog = AddItemDialog()
    if dialog.exec() == QDialog.DialogCode.Accepted:
        logging.info("對話框已關閉，項目已保存。")
    sys.exit(app.exec())

