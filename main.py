# main.py (版本 9.10 - 集成啟動項管理基礎與設定檔讀寫)

import sys
import logging
import subprocess 
import webbrowser 
import json # 需要 json 來讀取和寫入啟動項列表
import os   # 需要 os 來檢查文件是否存在

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, 
    QFrame, QListWidget, QListWidgetItem, QAbstractItemView, QHBoxLayout, QSizePolicy,
    QFileDialog, QMessageBox, QDialog # 引入 QDialog
)
from PyQt6.QtCore import Qt, QTimer, QPoint, QRect, QObject, pyqtSignal, QSize 
from PyQt6.QtGui import QIcon # 引入 QIcon

from hotkey_listener import HotkeyListener
from enhanced_hotkey_listener import EnhancedHotkeyListener
from add_item_dialog import AddItemDialog # 引入添加啟動項的對話框
from search_panel import SearchPanel # 引入搜尋面板
from settings_dialog import SettingsDialog # 引入設定對話框
from mouse_gesture import MouseGestureHandler, GlobalMouseGestureFilter # 引入滑鼠手勢
from ui_themes import theme_manager, apply_theme_to_widget # 引入主題管理器

# --- Log 設定 ---
# 這裡使用已有的 logging 配置
# --- ---

# --- 全局配置路徑 ---
SETTINGS_FILE = "settings.json" # 啟動項列表也會保存在這裡
# 如果需要獨立的啟動項列表配置，可以再定義一個 STARTUP_ITEMS_FILE = "startup_items.json"

# --- 讀取啟動項列表 ---
def load_startup_items():
    """從 settings.json 載入啟動項列表"""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings_data = json.load(f)
                # 啟動項列表應該儲存在 settings_data["startup_items"] 中
                return settings_data.get("startup_items", [])
        else:
            # 如果 settings.json 不存在，返回空列表
            return []
    except (json.JSONDecodeError, Exception) as e:
        logging.error(f"載入啟動項列表時出錯: {e}，返回空列表。")
        return []

# --- 啟動項管理數據 ---
# 我們需要一個地方來儲存所有啟動項的數據，以便讀取和保存
# 目前暫時放在全局，後續可以考慮封裝到 SettingsManager 或單獨的 manager 中
CURRENT_STARTUP_ITEMS = []

# --- MainWindow 類別 ---
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('SmartPanel')
        self.resize(400, 500) 
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        
        self.setup_ui()
        
        self.center() 
        self.show() 
        
        self.close_timer = QTimer(self)
        self.close_timer.setSingleShot(True) 
        self.close_timer.timeout.connect(self.safe_exit) 

        self._drag_pos = QPoint() 
        self._current_list_item = None # 當前選中的列表項

        # --- 載入啟動項列表 ---
        self.load_startup_items_from_settings()
        # --- ---
        
        # --- 初始化搜尋面板 ---
        self.search_panel = SearchPanel()
        # --- ---
        
        # --- 初始化設定對話框 ---
        self.settings_dialog = None
        # --- ---
        
        # --- 初始化滑鼠手勢 ---
        self.gesture_handler = MouseGestureHandler()
        self.gesture_handler.gesture_recognized.connect(self.handle_gesture)
        self.gesture_filter = GlobalMouseGestureFilter(self.gesture_handler)
        self.installEventFilter(self.gesture_filter)
        # --- ---
        
        # --- 初始化主題管理器 ---
        theme_manager.load_settings()
        theme_manager.theme_changed.connect(self.apply_current_theme)
        self.apply_current_theme()
        # --- ---

    def setup_ui(self):
        """設置窗口內的 UI 元素"""
        main_layout = QVBoxLayout(self) 
        main_layout.setContentsMargins(10, 10, 10, 10) 
        main_layout.setSpacing(10) 

        # --- 頂部標題、關閉按鈕和設置按鈕 ---
        title_label = QLabel("SmartPanel - 快速啟動", self)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        font = title_label.font()
        font.setPointSize(18)
        title_label.setFont(font)
        
        close_button = QPushButton("X", self)
        close_button.setFixedSize(30, 30)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #f00; 
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 15px; 
                border: none;
                padding: 0; 
            }
            QPushButton:hover { background-color: #c00; }
        """)
        close_button.clicked.connect(self.close)
        
        settings_button = QPushButton("設置", self)
        settings_button.clicked.connect(self.show_settings_dialog)
        settings_button.setFixedSize(80, 30)
        settings_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3; 
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 15px; 
                border: none;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        
        add_item_button = QPushButton("添加", self)
        add_item_button.clicked.connect(self.show_add_item_dialog)
        add_item_button.setFixedSize(80, 30)
        add_item_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 15px; 
                border: none;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        
        search_button = QPushButton("搜尋", self)
        search_button.clicked.connect(self.show_search_panel)
        search_button.setFixedSize(80, 30)
        search_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800; 
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 15px; 
                border: none;
            }
            QPushButton:hover { background-color: #F57C00; }
        """)
        
        title_hbox = QHBoxLayout()
        title_hbox.setContentsMargins(0,0,0,0)
        title_hbox.addWidget(title_label) 
        title_hbox.addStretch(1) 
        title_hbox.addWidget(search_button, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop) 
        title_hbox.addWidget(add_item_button, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        title_hbox.addWidget(settings_button, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop) 
        title_hbox.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop) 
        
        separator = QFrame(self)
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setFixedHeight(2)
        
        main_layout.addLayout(title_hbox)
        main_layout.addWidget(separator)

        # --- 快速啟動列表 ---
        self.list_widget = QListWidget(self)
        self.list_widget.setAlternatingRowColors(True) 
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection) 
        self.list_widget.setContentsMargins(0,0,0,0)
        self.list_widget.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel) 
        self.list_widget.setUniformItemSizes(True) 

        # 連接列表項點擊和鍵盤事件
        self.list_widget.itemClicked.connect(self.on_list_item_clicked)
        # 這裡為了讓列表控件能接收鍵盤事件，需要設置 focus policy
        self.list_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus) 

        # --- 底部提示區 ---
        bottom_label = QLabel("按熱鍵顯示/隱藏面板，按 Esc 退出，按 Ctrl+F 或 F3 搜尋", self)
        bottom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottom_label.setStyleSheet("font-size: 10px; color: grey;")
        main_layout.addWidget(bottom_label)

        self.setLayout(main_layout)
        
    def load_startup_items_from_settings(self):
        """從 settings.json 讀取並填充啟動項列表"""
        global CURRENT_STARTUP_ITEMS # 確保我們修改的是全局變量
        CURRENT_STARTUP_ITEMS = load_startup_items() # 獲取啟動項列表
        
        self.list_widget.clear() # 清空現有列表
        
        for item_data in CURRENT_STARTUP_ITEMS:
            self.add_item_to_list_widget(item_data) # 添加每個項目
        
        logging.info(f"已從設定檔載入 {len(CURRENT_STARTUP_ITEMS)} 個啟動項。")

    def save_startup_items_to_settings(self):
        """將當前的啟動項列表保存回 settings.json"""
        try:
            # 獲取當前列表的數據
            items_to_save = []
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                item_data = {
                    "name": item.text(),
                    "path": item.data(Qt.ItemDataRole.UserRole), # path 是 user role 的數據
                    "icon": item.data(Qt.ItemDataRole.UserRole + 1) # 假設 icon 是 UserRole+1
                }
                # 確保 icon 路徑不為空時才保存
                if item_data["icon"] is None or item_data["icon"] == "":
                    del item_data["icon"]
                items_to_save.append(item_data)
            
            # 讀取現有設定，只更新 startup_items 部分
            current_settings = {}
            if os.path.exists(SETTINGS_FILE):
                try:
                    with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                        current_settings = json.load(f)
                except (json.JSONDecodeError, Exception) as e:
                    logging.error(f"讀取 settings.json 失敗，無法保存啟動項: {e}")
                    return # 如果讀取失敗，則不保存

            # 更新 startup_items
            current_settings["startup_items"] = items_to_save
            
            # 保存回文件
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(current_settings, f, indent=2)
            
            global CURRENT_STARTUP_ITEMS
            CURRENT_STARTUP_ITEMS = items_to_save # 更新全局變量
            logging.info(f"已將 {len(items_to_save)} 個啟動項保存到設定檔。")

        except Exception as e:
            logging.error(f"保存啟動項到 settings.json 時發生錯誤: {e}")


    def add_item_to_list_widget(self, item_data):
        """將啟動項數據添加到 QListWidget 中"""
        item = QListWidgetItem()
        item.setText(item_data.get("name", "未命名項目"))
        item.setSizeHint(QSize(0, 45)) 
        item.setBackground(Qt.GlobalColor.white) 
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable) # 允許編輯
        
        # 儲存數據到 ItemDataRole
        item.setData(Qt.ItemDataRole.UserRole, item_data.get("path")) 
        if item_data.get("icon"):
            try:
                from PyQt6.QtGui import QIcon
                icon_path = item_data["icon"]
                if os.path.exists(icon_path):
                    item.setIcon(QIcon(icon_path))
                else:
                    logging.warning(f"圖標文件不存在: {icon_path}")
            except Exception as e:
                logging.warning(f"無法載入圖標 {item_data.get('icon')}: {e}")

        self.list_widget.addItem(item)
        self.list_widget.scrollToItem(item) # 滾動到新添加的項目

    def show_settings_dialog(self):
        """顯示設定對話框"""
        if self.settings_dialog is None:
            self.settings_dialog = SettingsDialog(self)
            self.settings_dialog.settings_changed.connect(self.on_settings_changed)
        
        self.settings_dialog.show()
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()
        
    def on_settings_changed(self):
        """設定變更時的處理"""
        # 重新載入設定
        self.load_startup_items_from_settings()
        
        # 更新滑鼠手勢設定
        self.gesture_handler.load_settings()
        
        # 重新載入主題設定
        theme_manager.load_settings()
        self.apply_current_theme()
        
        # 可以在這裡添加其他需要更新的設定
        logging.info("設定已更新")
        
    def apply_current_theme(self):
        """應用當前主題"""
        apply_theme_to_widget(self)
        
        # 同時應用到搜尋面板
        if hasattr(self, 'search_panel') and self.search_panel:
            apply_theme_to_widget(self.search_panel)
            
        # 應用到設定對話框
        if hasattr(self, 'settings_dialog') and self.settings_dialog:
            apply_theme_to_widget(self.settings_dialog)
        
    def handle_gesture(self, pattern):
        """處理手勢識別結果"""
        logging.info(f"處理手勢: {pattern}")
        self.gesture_handler.execute_gesture_action(pattern)
        
        # 根據手勢執行相應動作
        if pattern == "↑":
            self.show()
            self.raise_()
            self.activateWindow()
        elif pattern == "↓":
            self.hide()
        elif pattern == "→":
            self.show_search_panel()
        elif pattern == "←":
            # 返回操作
            if self.search_panel.isVisible():
                self.search_panel.hide()
            else:
                self.hide()
        elif pattern == "○":
            # 關閉應用
            self.close()
            
    def show_add_item_dialog(self):
        """打開添加/編輯啟動項對話框"""
        logging.info("打開啟動項管理對話框。")
        # 這裡我們只實現添加功能，如果需要編輯，需要傳入點擊的 item_data
        self.add_item_dialog = AddItemDialog(self) 
        
        self.add_item_dialog.emitter.item_saved.connect(self.add_new_item_to_list)
        
        self.add_item_dialog.exec() 

    def add_new_item_to_list(self, item_data):
        """從 AddItemDialog 接收新項目數據並添加到列表"""
        self.add_item_to_list_widget(item_data)
        self.save_startup_items_to_settings() # 保存到設定檔

    def show_search_panel(self):
        """顯示搜尋面板"""
        logging.info("顯示搜尋面板")
        self.search_panel.center()
        self.search_panel.show()
        self.search_panel.activateWindow()
        self.search_panel.raise_()

    # --- 繼承自 QDialog 的方法，需要重寫以讓對話框可拖動 ---
    # 這些方法應該放在 AddItemDialog 類別中，而不是 MainWindow 中
    # 但為了方便調用，我們可以在 MainWindow 中也添加它們，或者讓 MainWindow 代理調用
    # 現在已將滑鼠事件處理移至 AddItemDialog 中了。

    def mousePressEvent(self, event):
        """處理主窗口的滑鼠按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            clicked_widget = self.childAt(event.pos())
            # 判斷是否點擊了頂部標題區域 (Y < 70)，且不是關閉按鈕
            if event.pos().y() < 70 and str(clicked_widget) != "<QPushButton object at ...>": 
                self._drag_pos = event.pos() 
                logging.debug(f"主窗口準備拖動，按下位置: {self._drag_pos}")
                super().mousePressEvent(event) 
            else:
                self._drag_pos = QPoint() 
                super().mousePressEvent(event) 
        else:
            super().mousePressEvent(event) 

    def mouseMoveEvent(self, event):
        """處理主窗口的滑鼠移動事件"""
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            new_pos = event.pos() - self._drag_pos
            current_window_pos = self.geometry().topLeft()
            new_window_abs_pos = current_window_pos + new_pos
            self.move(new_window_abs_pos)
            logging.debug(f"主窗口拖動中，移動到: {new_window_abs_pos}")
        else:
            super().mouseMoveEvent(event) 

    def mouseReleaseEvent(self, event):
        """處理主窗口的滑鼠鬆開事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = QPoint() 
            logging.debug("主窗口滑鼠鬆開，清空拖動位置記錄。")
            
            # 檢查是否點擊了列表控件內的某個項目後鬆開了滑鼠
            clicked_item = self.list_widget.currentItem()
            if clicked_item and self.list_widget.visualItemRect(clicked_item).contains(event.pos()):
                logging.debug(f"滑鼠釋放於列表項: {clicked_item.text()}")
                self.execute_selected_item() 
            else:
                super().mouseReleaseEvent(event)
        else:
            super().mouseReleaseEvent(event)

    def toggle_visibility(self):
        """切換視窗的顯示/隱藏狀態"""
        if self.isVisible():
            logging.info("隱藏面板")
            self.hide()
        else:
            logging.info("顯示面板")
            self.center() 
            self.show()
            self.activateWindow()
            self.raise_() 

    def center(self):
        """將視窗移動到螢幕中央"""
        screen_geometry = self.screen().availableGeometry() 
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        x = max(0, x)
        y = max(0, y)
        self.move(x, y)
        logging.debug(f"視窗移動到: ({x}, {y})")

    def keyPressEvent(self, event):
        """處理鍵盤按下事件"""
        if event.key() == Qt.Key.Key_Escape:
            logging.info("偵測到 Esc 鍵按下，關閉面板。")
            self.close()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
             logging.debug("偵測到 Enter 鍵按下")
             self.execute_selected_item()
        elif event.key() == Qt.Key.Key_F3 or (event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_F):
            # Ctrl+F 或 F3 打開搜尋面板
            self.show_search_panel()
        elif event.key() == Qt.Key.Key_Down:
            self.move_list_selection(1) 
        elif event.key() == Qt.Key.Key_Up:
            self.move_list_selection(-1) 
        elif event.key() == Qt.Key.Key_Home:
            self.list_widget.setCurrentRow(0)
            if self.list_widget.currentItem(): self.list_widget.scrollToItem(self.list_widget.currentItem())
        elif event.key() == Qt.Key.Key_End:
            self.list_widget.setCurrentRow(self.list_widget.count() - 1)
            if self.list_widget.currentItem(): self.list_widget.scrollToItem(self.list_widget.currentItem())

    def move_list_selection(self, direction):
        """移動列表選擇"""
        current_row = self.list_widget.currentRow()
        new_row = current_row + direction
        
        if 0 <= new_row < self.list_widget.count():
            self.list_widget.setCurrentRow(new_row)
            self.list_widget.scrollToItem(self.list_widget.currentItem())
        elif new_row < 0 and current_row == 0: 
            self.list_widget.setCurrentRow(self.list_widget.count() - 1)
            if self.list_widget.currentItem(): self.list_widget.scrollToItem(self.list_widget.currentItem())
        elif new_row >= self.list_widget.count() and current_row == self.list_widget.count() - 1: 
            self.list_widget.setCurrentRow(0)
            if self.list_widget.currentItem(): self.list_widget.scrollToItem(self.list_widget.currentItem())

    def closeEvent(self, event):
        """處理窗口關閉事件"""
        logging.info("觸發窗口關閉事件。")
        self.close_timer.start(100) 
        event.accept() 

    def safe_exit(self):
        """安全退出應用程式"""
        logging.info("執行安全退出。")
        QApplication.quit() 

    def on_list_item_clicked(self, item):
        """處理列表項點擊事件"""
        logging.debug(f"列表項被點擊: {item.text()}")
        self.execute_selected_item()

    def execute_selected_item(self):
        """執行列表欄中當前選中的項目"""
        selected_item = self.list_widget.currentItem()
        if selected_item:
            item_text = selected_item.text()
            action_path = selected_item.data(Qt.ItemDataRole.UserRole) 
            
            logging.info(f"執行列表項目: {item_text} (Path: {action_path})")
            
            if not action_path:
                logging.warning("項目沒有設定執行路徑")
                return
            
            try:
                # 判斷是否為網址
                if action_path.startswith(("http://", "https://")):
                    logging.info(f"打開網址: {action_path}")
                    webbrowser.open(action_path)
                # 判斷是否為 Python 腳本
                elif action_path.endswith(".py"):
                    logging.info(f"執行 Python 腳本: {action_path}")
                    subprocess.Popen([sys.executable, action_path])
                # 其他文件或程式
                else:
                    logging.info(f"執行程式或打開文件: {action_path}")
                    if os.name == 'nt':  # Windows
                        subprocess.Popen([action_path], shell=True)
                    else:  # Linux/macOS
                        subprocess.Popen([action_path])
                        
                # 執行後隱藏面板
                self.hide()
                        
            except Exception as e:
                logging.error(f"執行項目時發生錯誤: {e}")
                QMessageBox.warning(self, "執行錯誤", f"無法執行 {item_text}:\n{str(e)}")
        else:
            logging.warning("沒有選中任何列表項目。")


# --- 程式主執行區塊 ---
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    window = MainWindow()

    # --- 熱鍵監聽設定 ---
    listener = EnhancedHotkeyListener()
    listener.emitter.main_panel_activated.connect(window.toggle_visibility)
    listener.emitter.search_panel_activated.connect(window.show_search_panel)
    listener.start()
    # --- 設定結束 ---

    sys.exit(app.exec())