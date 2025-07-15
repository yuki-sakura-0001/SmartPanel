# settings_dialog.py - 設定對話框模組

import os
import sys
import json
import logging
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QPushButton, QCheckBox, QComboBox,
    QGroupBox, QFormLayout, QSpinBox, QSlider, QColorDialog,
    QFileDialog, QMessageBox, QFrame, QScrollArea, QGridLayout,
    QButtonGroup, QRadioButton, QTextEdit, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QKeySequence

try:
    from startup_manager import startup_manager
    STARTUP_MANAGER_AVAILABLE = True
except ImportError:
    STARTUP_MANAGER_AVAILABLE = False
    logging.warning("開機啟動管理器不可用")

class HotkeyEdit(QLineEdit):
    """熱鍵編輯控件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setPlaceholderText("點擊此處設定熱鍵...")
        self.current_keys = []
        
    def keyPressEvent(self, event):
        """處理按鍵事件"""
        key = event.key()
        modifiers = event.modifiers()
        
        # 忽略單獨的修飾鍵
        if key in [Qt.Key.Key_Control, Qt.Key.Key_Alt, Qt.Key.Key_Shift, Qt.Key.Key_Meta]:
            return
            
        # 構建熱鍵字符串
        key_parts = []
        
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            key_parts.append("Ctrl")
        if modifiers & Qt.KeyboardModifier.AltModifier:
            key_parts.append("Alt")
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            key_parts.append("Shift")
        if modifiers & Qt.KeyboardModifier.MetaModifier:
            key_parts.append("Meta")
            
        # 添加主鍵
        key_name = QKeySequence(key).toString()
        if key_name:
            key_parts.append(key_name)
            
        hotkey_text = "+".join(key_parts)
        self.setText(hotkey_text)
        
        # 保存熱鍵信息
        self.current_keys = {
            "ctrl": bool(modifiers & Qt.KeyboardModifier.ControlModifier),
            "alt": bool(modifiers & Qt.KeyboardModifier.AltModifier),
            "shift": bool(modifiers & Qt.KeyboardModifier.ShiftModifier),
            "meta": bool(modifiers & Qt.KeyboardModifier.MetaModifier),
            "key": key_name.lower()
        }
        
    def get_hotkey_config(self):
        """獲取熱鍵配置"""
        return self.current_keys
        
    def set_hotkey_config(self, config):
        """設置熱鍵配置"""
        if not config:
            return
            
        self.current_keys = config
        key_parts = []
        
        if config.get("ctrl", False):
            key_parts.append("Ctrl")
        if config.get("alt", False):
            key_parts.append("Alt")
        if config.get("shift", False):
            key_parts.append("Shift")
        if config.get("meta", False):
            key_parts.append("Meta")
            
        key = config.get("key", "")
        if key:
            key_parts.append(key.upper())
            
        self.setText("+".join(key_parts))

class MouseGestureSettingsDialog(QDialog):
    """滑鼠手勢設定對話框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("滑鼠手勢設定")
        self.setModal(True)
        self.resize(600, 500)
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """設置 UI"""
        layout = QVBoxLayout(self)
        
        # 啟用滑鼠手勢
        self.enable_gesture_checkbox = QCheckBox("啟用滑鼠手勢")
        layout.addWidget(self.enable_gesture_checkbox)
        
        # 手勢靈敏度
        sensitivity_group = QGroupBox("手勢靈敏度")
        sensitivity_layout = QFormLayout(sensitivity_group)
        
        self.sensitivity_slider = QSlider(Qt.Orientation.Horizontal)
        self.sensitivity_slider.setRange(1, 10)
        self.sensitivity_slider.setValue(5)
        self.sensitivity_label = QLabel("5")
        self.sensitivity_slider.valueChanged.connect(
            lambda v: self.sensitivity_label.setText(str(v))
        )
        
        sensitivity_layout.addRow("靈敏度:", self.sensitivity_slider)
        sensitivity_layout.addRow("", self.sensitivity_label)
        layout.addWidget(sensitivity_group)
        
        # 手勢觸發按鈕
        trigger_group = QGroupBox("觸發按鈕")
        trigger_layout = QVBoxLayout(trigger_group)
        
        self.trigger_button_group = QButtonGroup()
        self.middle_button_radio = QRadioButton("滑鼠中鍵")
        self.right_button_radio = QRadioButton("滑鼠右鍵")
        self.middle_button_radio.setChecked(True)
        
        self.trigger_button_group.addButton(self.middle_button_radio, 0)
        self.trigger_button_group.addButton(self.right_button_radio, 1)
        
        trigger_layout.addWidget(self.middle_button_radio)
        trigger_layout.addWidget(self.right_button_radio)
        layout.addWidget(trigger_group)
        
        # 手勢動作設定
        gestures_group = QGroupBox("手勢動作")
        gestures_layout = QVBoxLayout(gestures_group)
        
        self.gestures_list = QListWidget()
        self.setup_gesture_list()
        gestures_layout.addWidget(self.gestures_list)
        
        # 手勢按鈕
        gesture_buttons_layout = QHBoxLayout()
        self.add_gesture_button = QPushButton("添加手勢")
        self.edit_gesture_button = QPushButton("編輯手勢")
        self.delete_gesture_button = QPushButton("刪除手勢")
        
        gesture_buttons_layout.addWidget(self.add_gesture_button)
        gesture_buttons_layout.addWidget(self.edit_gesture_button)
        gesture_buttons_layout.addWidget(self.delete_gesture_button)
        gestures_layout.addLayout(gesture_buttons_layout)
        
        layout.addWidget(gestures_group)
        
        # 對話框按鈕
        buttons_layout = QHBoxLayout()
        self.ok_button = QPushButton("確定")
        self.cancel_button = QPushButton("取消")
        self.apply_button = QPushButton("應用")
        
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.apply_button.clicked.connect(self.apply_settings)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.ok_button)
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.apply_button)
        
        layout.addLayout(buttons_layout)
        
    def setup_gesture_list(self):
        """設置手勢列表"""
        default_gestures = [
            {"pattern": "↑", "action": "顯示主面板", "description": "向上滑動顯示快速啟動面板"},
            {"pattern": "↓", "action": "隱藏面板", "description": "向下滑動隱藏當前面板"},
            {"pattern": "→", "action": "顯示搜尋面板", "description": "向右滑動顯示搜尋面板"},
            {"pattern": "←", "action": "返回", "description": "向左滑動返回上一個狀態"},
            {"pattern": "○", "action": "關閉應用", "description": "畫圓圈關閉當前應用"}
        ]
        
        for gesture in default_gestures:
            item = QListWidgetItem()
            item.setText(f"{gesture['pattern']} - {gesture['action']}")
            item.setData(Qt.ItemDataRole.UserRole, gesture)
            self.gestures_list.addItem(item)
            
    def load_settings(self):
        """載入設定"""
        try:
            settings_path = Path("settings.json")
            if settings_path.exists():
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
                mouse_gesture = settings.get("mouse_gesture", {})
                self.enable_gesture_checkbox.setChecked(mouse_gesture.get("enabled", False))
                self.sensitivity_slider.setValue(mouse_gesture.get("sensitivity", 5))
                
                trigger_button = mouse_gesture.get("trigger_button", "middle")
                if trigger_button == "right":
                    self.right_button_radio.setChecked(True)
                else:
                    self.middle_button_radio.setChecked(True)
                    
        except Exception as e:
            logging.error(f"載入滑鼠手勢設定失敗: {e}")
            
    def apply_settings(self):
        """應用設定"""
        try:
            settings_path = Path("settings.json")
            settings = {}
            
            if settings_path.exists():
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
            # 更新滑鼠手勢設定
            mouse_gesture = {
                "enabled": self.enable_gesture_checkbox.isChecked(),
                "sensitivity": self.sensitivity_slider.value(),
                "trigger_button": "right" if self.right_button_radio.isChecked() else "middle",
                "gestures": []
            }
            
            # 保存手勢列表
            for i in range(self.gestures_list.count()):
                item = self.gestures_list.item(i)
                gesture_data = item.data(Qt.ItemDataRole.UserRole)
                if gesture_data:
                    mouse_gesture["gestures"].append(gesture_data)
                    
            settings["mouse_gesture"] = mouse_gesture
            
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
                
            QMessageBox.information(self, "成功", "滑鼠手勢設定已保存")
            
        except Exception as e:
            logging.error(f"保存滑鼠手勢設定失敗: {e}")
            QMessageBox.critical(self, "錯誤", f"保存設定失敗: {str(e)}")

class SettingsDialog(QDialog):
    """主設定對話框"""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SmartPanel - 設定")
        self.setModal(True)
        self.resize(700, 600)
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """設置 UI"""
        layout = QVBoxLayout(self)
        
        # 創建標籤頁
        self.tab_widget = QTabWidget()
        
        # 一般設定標籤頁
        self.general_tab = self.create_general_tab()
        self.tab_widget.addTab(self.general_tab, "一般設定")
        
        # 熱鍵設定標籤頁
        self.hotkey_tab = self.create_hotkey_tab()
        self.tab_widget.addTab(self.hotkey_tab, "熱鍵設定")
        
        # 外觀設定標籤頁
        self.appearance_tab = self.create_appearance_tab()
        self.tab_widget.addTab(self.appearance_tab, "外觀設定")
        
        # 進階設定標籤頁
        self.advanced_tab = self.create_advanced_tab()
        self.tab_widget.addTab(self.advanced_tab, "進階設定")
        
        layout.addWidget(self.tab_widget)
        
        # 對話框按鈕
        buttons_layout = QHBoxLayout()
        
        # 滑鼠手勢設定按鈕
        self.mouse_gesture_button = QPushButton("滑鼠手勢設定")
        self.mouse_gesture_button.clicked.connect(self.open_mouse_gesture_settings)
        
        self.ok_button = QPushButton("確定")
        self.cancel_button = QPushButton("取消")
        self.apply_button = QPushButton("應用")
        
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.apply_button.clicked.connect(self.apply_settings)
        
        buttons_layout.addWidget(self.mouse_gesture_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.ok_button)
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.apply_button)
        
        layout.addLayout(buttons_layout)
        
    def create_general_tab(self):
        """創建一般設定標籤頁"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 開機啟動設定
        startup_group = QGroupBox("開機啟動")
        startup_layout = QFormLayout(startup_group)
        
        self.auto_start_checkbox = QCheckBox("開機時自動啟動 SmartPanel")
        self.auto_start_checkbox.stateChanged.connect(self.on_auto_start_changed)
        self.minimize_to_tray_checkbox = QCheckBox("啟動時最小化到系統托盤")
        
        # 檢查開機啟動狀態
        if STARTUP_MANAGER_AVAILABLE:
            self.auto_start_checkbox.setChecked(startup_manager.is_startup_enabled())
        else:
            self.auto_start_checkbox.setEnabled(False)
            self.auto_start_checkbox.setToolTip("開機啟動管理器不可用")
        
        startup_layout.addRow(self.auto_start_checkbox)
        startup_layout.addRow(self.minimize_to_tray_checkbox)
        layout.addWidget(startup_group)
        
        # 面板行為設定
        behavior_group = QGroupBox("面板行為")
        behavior_layout = QFormLayout(behavior_group)
        
        self.auto_hide_checkbox = QCheckBox("失去焦點時自動隱藏面板")
        self.remember_position_checkbox = QCheckBox("記住面板位置")
        self.show_animations_checkbox = QCheckBox("顯示動畫效果")
        
        behavior_layout.addRow(self.auto_hide_checkbox)
        behavior_layout.addRow(self.remember_position_checkbox)
        behavior_layout.addRow(self.show_animations_checkbox)
        layout.addWidget(behavior_group)
        
        # 搜尋設定
        search_group = QGroupBox("搜尋設定")
        search_layout = QFormLayout(search_group)
        
        self.enable_everything_checkbox = QCheckBox("啟用 Everything 高速搜尋 (Windows)")
        self.search_delay_spinbox = QSpinBox()
        self.search_delay_spinbox.setRange(100, 2000)
        self.search_delay_spinbox.setValue(300)
        self.search_delay_spinbox.setSuffix(" ms")
        
        self.max_results_spinbox = QSpinBox()
        self.max_results_spinbox.setRange(10, 200)
        self.max_results_spinbox.setValue(50)
        
        search_layout.addRow(self.enable_everything_checkbox)
        search_layout.addRow("搜尋延遲:", self.search_delay_spinbox)
        search_layout.addRow("最大結果數:", self.max_results_spinbox)
        layout.addWidget(search_group)
        
        layout.addStretch()
        return tab
        
    def create_hotkey_tab(self):
        """創建熱鍵設定標籤頁"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 全局熱鍵設定
        hotkey_group = QGroupBox("全局熱鍵")
        hotkey_layout = QFormLayout(hotkey_group)
        
        self.main_panel_hotkey = HotkeyEdit()
        self.search_panel_hotkey = HotkeyEdit()
        
        hotkey_layout.addRow("快速啟動面板:", self.main_panel_hotkey)
        hotkey_layout.addRow("搜尋面板:", self.search_panel_hotkey)
        layout.addWidget(hotkey_group)
        
        # 面板內熱鍵設定
        panel_hotkey_group = QGroupBox("面板內熱鍵")
        panel_hotkey_layout = QFormLayout(panel_hotkey_group)
        
        self.escape_action_combo = QComboBox()
        self.escape_action_combo.addItems(["隱藏面板", "關閉應用程式", "無動作"])
        
        self.enter_action_combo = QComboBox()
        self.enter_action_combo.addItems(["執行選中項目", "打開文件位置", "複製路徑"])
        
        panel_hotkey_layout.addRow("Esc 鍵動作:", self.escape_action_combo)
        panel_hotkey_layout.addRow("Enter 鍵動作:", self.enter_action_combo)
        layout.addWidget(panel_hotkey_group)
        
        # 熱鍵說明
        help_label = QLabel("""
        <b>熱鍵設定說明:</b><br>
        • 點擊輸入框後按下想要的熱鍵組合<br>
        • 支援 Ctrl、Alt、Shift、Meta 修飾鍵<br>
        • 建議使用不常用的組合避免衝突<br>
        • 設定後需要重啟應用程式才能生效
        """)
        help_label.setWordWrap(True)
        help_label.setStyleSheet("color: #666; font-size: 12px; padding: 10px;")
        layout.addWidget(help_label)
        
        layout.addStretch()
        return tab
        
    def create_appearance_tab(self):
        """創建外觀設定標籤頁"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 主題設定
        theme_group = QGroupBox("主題")
        theme_layout = QFormLayout(theme_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["系統預設", "淺色主題", "深色主題", "自定義"])
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        
        theme_layout.addRow("主題:", self.theme_combo)
        layout.addWidget(theme_group)
        
        # 字體設定
        font_group = QGroupBox("字體")
        font_layout = QFormLayout(font_group)
        
        self.font_family_combo = QComboBox()
        self.font_family_combo.addItems(["系統預設", "微軟正黑體", "新細明體", "Arial", "Consolas"])
        
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 24)
        self.font_size_spinbox.setValue(12)
        
        font_layout.addRow("字體:", self.font_family_combo)
        font_layout.addRow("大小:", self.font_size_spinbox)
        layout.addWidget(font_group)
        
        # 顏色設定
        color_group = QGroupBox("顏色")
        color_layout = QFormLayout(color_group)
        
        self.primary_color_button = QPushButton()
        self.primary_color_button.setFixedSize(50, 30)
        self.primary_color_button.setStyleSheet("background-color: #4CAF50;")
        self.primary_color_button.clicked.connect(lambda: self.choose_color(self.primary_color_button))
        
        self.accent_color_button = QPushButton()
        self.accent_color_button.setFixedSize(50, 30)
        self.accent_color_button.setStyleSheet("background-color: #2196F3;")
        self.accent_color_button.clicked.connect(lambda: self.choose_color(self.accent_color_button))
        
        color_layout.addRow("主要顏色:", self.primary_color_button)
        color_layout.addRow("強調顏色:", self.accent_color_button)
        layout.addWidget(color_group)
        
        # 透明度設定
        opacity_group = QGroupBox("透明度")
        opacity_layout = QFormLayout(opacity_group)
        
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(50, 100)
        self.opacity_slider.setValue(95)
        self.opacity_label = QLabel("95%")
        self.opacity_slider.valueChanged.connect(
            lambda v: self.opacity_label.setText(f"{v}%")
        )
        
        opacity_layout.addRow("面板透明度:", self.opacity_slider)
        opacity_layout.addRow("", self.opacity_label)
        layout.addWidget(opacity_group)
        
        layout.addStretch()
        return tab
        
    def create_advanced_tab(self):
        """創建進階設定標籤頁"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 性能設定
        performance_group = QGroupBox("性能")
        performance_layout = QFormLayout(performance_group)
        
        self.enable_cache_checkbox = QCheckBox("啟用搜尋結果快取")
        self.cache_size_spinbox = QSpinBox()
        self.cache_size_spinbox.setRange(10, 1000)
        self.cache_size_spinbox.setValue(100)
        self.cache_size_spinbox.setSuffix(" MB")
        
        performance_layout.addRow(self.enable_cache_checkbox)
        performance_layout.addRow("快取大小:", self.cache_size_spinbox)
        layout.addWidget(performance_group)
        
        # 日誌設定
        logging_group = QGroupBox("日誌")
        logging_layout = QFormLayout(logging_group)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText("INFO")
        
        self.log_file_path_edit = QLineEdit()
        self.log_file_path_edit.setText("logs/smartpanel.log")
        self.log_file_browse_button = QPushButton("瀏覽...")
        self.log_file_browse_button.clicked.connect(self.browse_log_file)
        
        log_file_layout = QHBoxLayout()
        log_file_layout.addWidget(self.log_file_path_edit)
        log_file_layout.addWidget(self.log_file_browse_button)
        
        logging_layout.addRow("日誌級別:", self.log_level_combo)
        logging_layout.addRow("日誌文件:", log_file_layout)
        layout.addWidget(logging_group)
        
        # 備份與還原
        backup_group = QGroupBox("備份與還原")
        backup_layout = QVBoxLayout(backup_group)
        
        backup_buttons_layout = QHBoxLayout()
        self.backup_button = QPushButton("備份設定")
        self.restore_button = QPushButton("還原設定")
        self.reset_button = QPushButton("重置為預設值")
        
        self.backup_button.clicked.connect(self.backup_settings)
        self.restore_button.clicked.connect(self.restore_settings)
        self.reset_button.clicked.connect(self.reset_settings)
        
        backup_buttons_layout.addWidget(self.backup_button)
        backup_buttons_layout.addWidget(self.restore_button)
        backup_buttons_layout.addWidget(self.reset_button)
        
        backup_layout.addLayout(backup_buttons_layout)
        layout.addWidget(backup_group)
        
        layout.addStretch()
        return tab
        
    def choose_color(self, button):
        """選擇顏色"""
        color = QColorDialog.getColor()
        if color.isValid():
            button.setStyleSheet(f"background-color: {color.name()};")
            
    def browse_log_file(self):
        """瀏覽日誌文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "選擇日誌文件", self.log_file_path_edit.text(),
            "日誌文件 (*.log);;所有文件 (*)"
        )
        if file_path:
            self.log_file_path_edit.setText(file_path)
            
    def backup_settings(self):
        """備份設定"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "備份設定", "smartpanel_backup.json",
            "JSON 文件 (*.json);;所有文件 (*)"
        )
        if file_path:
            try:
                import shutil
                shutil.copy("settings.json", file_path)
                QMessageBox.information(self, "成功", "設定已備份")
            except Exception as e:
                QMessageBox.critical(self, "錯誤", f"備份失敗: {str(e)}")
                
    def restore_settings(self):
        """還原設定"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "還原設定", "",
            "JSON 文件 (*.json);;所有文件 (*)"
        )
        if file_path:
            try:
                import shutil
                shutil.copy(file_path, "settings.json")
                self.load_settings()
                QMessageBox.information(self, "成功", "設定已還原")
            except Exception as e:
                QMessageBox.critical(self, "錯誤", f"還原失敗: {str(e)}")
                
    def reset_settings(self):
        """重置設定"""
        reply = QMessageBox.question(
            self, "確認", "確定要重置所有設定為預設值嗎？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if os.path.exists("settings.json"):
                    os.remove("settings.json")
                self.load_settings()
                QMessageBox.information(self, "成功", "設定已重置")
            except Exception as e:
                QMessageBox.critical(self, "錯誤", f"重置失敗: {str(e)}")
                
    def open_mouse_gesture_settings(self):
        """打開滑鼠手勢設定"""
        dialog = MouseGestureSettingsDialog(self)
        dialog.exec()
        
    def on_theme_changed(self, theme_name):
        """主題變更時的處理"""
        # 即時預覽主題變更
        from ui_themes import theme_manager
        theme_manager.set_theme(theme_name)
        
    def on_auto_start_changed(self, state):
        """開機啟動設定變更時的處理"""
        if not STARTUP_MANAGER_AVAILABLE:
            return
            
        try:
            if state == Qt.CheckState.Checked.value:
                if not startup_manager.enable_startup():
                    QMessageBox.warning(self, "警告", "啟用開機啟動失敗")
                    self.auto_start_checkbox.setChecked(False)
            else:
                if not startup_manager.disable_startup():
                    QMessageBox.warning(self, "警告", "禁用開機啟動失敗")
                    self.auto_start_checkbox.setChecked(True)
        except Exception as e:
            logging.error(f"開機啟動設定變更失敗: {e}")
            QMessageBox.critical(self, "錯誤", f"開機啟動設定失敗: {str(e)}")
        
    def load_settings(self):
        """載入設定"""
        try:
            settings_path = Path("settings.json")
            if settings_path.exists():
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            else:
                settings = self.get_default_settings()
                
            # 載入一般設定
            general = settings.get("general", {})
            self.auto_start_checkbox.setChecked(general.get("auto_start", False))
            self.minimize_to_tray_checkbox.setChecked(general.get("minimize_to_tray", True))
            self.auto_hide_checkbox.setChecked(general.get("auto_hide", True))
            self.remember_position_checkbox.setChecked(general.get("remember_position", True))
            self.show_animations_checkbox.setChecked(general.get("show_animations", True))
            
            # 載入搜尋設定
            search = settings.get("search", {})
            self.enable_everything_checkbox.setChecked(search.get("enable_everything", True))
            self.search_delay_spinbox.setValue(search.get("delay", 300))
            self.max_results_spinbox.setValue(search.get("max_results", 50))
            
            # 載入熱鍵設定
            hotkey = settings.get("hotkey", {})
            main_panel = hotkey.get("main_panel", {})
            search_panel = hotkey.get("search_panel", {})
            
            self.main_panel_hotkey.set_hotkey_config(main_panel)
            self.search_panel_hotkey.set_hotkey_config(search_panel)
            
            # 載入外觀設定
            appearance = settings.get("appearance", {})
            theme = appearance.get("theme", "系統預設")
            if theme in ["系統預設", "淺色主題", "深色主題", "自定義"]:
                self.theme_combo.setCurrentText(theme)
                
            font_family = appearance.get("font_family", "系統預設")
            if font_family in ["系統預設", "微軟正黑體", "新細明體", "Arial", "Consolas"]:
                self.font_family_combo.setCurrentText(font_family)
                
            self.font_size_spinbox.setValue(appearance.get("font_size", 12))
            self.opacity_slider.setValue(appearance.get("opacity", 95))
            
            # 載入進階設定
            advanced = settings.get("advanced", {})
            self.enable_cache_checkbox.setChecked(advanced.get("enable_cache", True))
            self.cache_size_spinbox.setValue(advanced.get("cache_size", 100))
            
            log_level = advanced.get("log_level", "INFO")
            if log_level in ["DEBUG", "INFO", "WARNING", "ERROR"]:
                self.log_level_combo.setCurrentText(log_level)
                
            self.log_file_path_edit.setText(advanced.get("log_file", "logs/smartpanel.log"))
            
        except Exception as e:
            logging.error(f"載入設定失敗: {e}")
            
    def get_default_settings(self):
        """獲取預設設定"""
        return {
            "general": {
                "auto_start": False,
                "minimize_to_tray": True,
                "auto_hide": True,
                "remember_position": True,
                "show_animations": True
            },
            "search": {
                "enable_everything": True,
                "delay": 300,
                "max_results": 50
            },
            "hotkey": {
                "main_panel": {
                    "ctrl": True,
                    "alt": True,
                    "shift": False,
                    "meta": False,
                    "key": "f12"
                },
                "search_panel": {
                    "ctrl": True,
                    "alt": False,
                    "shift": False,
                    "meta": False,
                    "key": "space"
                }
            },
            "appearance": {
                "theme": "系統預設",
                "font_family": "系統預設",
                "font_size": 12,
                "primary_color": "#4CAF50",
                "accent_color": "#2196F3",
                "opacity": 95
            },
            "advanced": {
                "enable_cache": True,
                "cache_size": 100,
                "log_level": "INFO",
                "log_file": "logs/smartpanel.log"
            },
            "mouse_gesture": {
                "enabled": False,
                "sensitivity": 5,
                "trigger_button": "middle"
            }
        }
        
    def apply_settings(self):
        """應用設定"""
        try:
            settings = {
                "general": {
                    "auto_start": self.auto_start_checkbox.isChecked(),
                    "minimize_to_tray": self.minimize_to_tray_checkbox.isChecked(),
                    "auto_hide": self.auto_hide_checkbox.isChecked(),
                    "remember_position": self.remember_position_checkbox.isChecked(),
                    "show_animations": self.show_animations_checkbox.isChecked()
                },
                "search": {
                    "enable_everything": self.enable_everything_checkbox.isChecked(),
                    "delay": self.search_delay_spinbox.value(),
                    "max_results": self.max_results_spinbox.value()
                },
                "hotkey": {
                    "main_panel": self.main_panel_hotkey.get_hotkey_config(),
                    "search_panel": self.search_panel_hotkey.get_hotkey_config()
                },
                "appearance": {
                    "theme": self.theme_combo.currentText(),
                    "font_family": self.font_family_combo.currentText(),
                    "font_size": self.font_size_spinbox.value(),
                    "primary_color": self.primary_color_button.styleSheet().split(":")[1].strip().rstrip(";"),
                    "accent_color": self.accent_color_button.styleSheet().split(":")[1].strip().rstrip(";"),
                    "opacity": self.opacity_slider.value()
                },
                "advanced": {
                    "enable_cache": self.enable_cache_checkbox.isChecked(),
                    "cache_size": self.cache_size_spinbox.value(),
                    "log_level": self.log_level_combo.currentText(),
                    "log_file": self.log_file_path_edit.text()
                }
            }
            
            # 保留現有的滑鼠手勢設定
            try:
                with open("settings.json", 'r', encoding='utf-8') as f:
                    existing_settings = json.load(f)
                    if "mouse_gesture" in existing_settings:
                        settings["mouse_gesture"] = existing_settings["mouse_gesture"]
            except:
                pass
                
            with open("settings.json", 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
                
            self.settings_changed.emit()
            QMessageBox.information(self, "成功", "設定已保存")
            
        except Exception as e:
            logging.error(f"保存設定失敗: {e}")
            QMessageBox.critical(self, "錯誤", f"保存設定失敗: {str(e)}")

# 使用示例
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = SettingsDialog()
    dialog.show()
    sys.exit(app.exec())

