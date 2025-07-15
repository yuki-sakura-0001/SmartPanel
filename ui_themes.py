# ui_themes.py - UI 主題和美化模組

import json
import logging
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QPalette, QColor, QFont
from PyQt6.QtWidgets import QApplication

class ThemeManager(QObject):
    """主題管理器"""
    
    theme_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.current_theme = "系統預設"
        self.themes = self.load_themes()
        
    def load_themes(self):
        """載入主題配置"""
        return {
            "系統預設": {
                "name": "系統預設",
                "colors": {
                    "primary": "#4CAF50",
                    "accent": "#2196F3",
                    "background": "#FFFFFF",
                    "surface": "#F5F5F5",
                    "text": "#212121",
                    "text_secondary": "#757575",
                    "border": "#E0E0E0",
                    "hover": "#EEEEEE",
                    "selected": "#E3F2FD"
                },
                "fonts": {
                    "family": "Microsoft YaHei UI",
                    "size": 12,
                    "title_size": 16,
                    "small_size": 10
                },
                "effects": {
                    "border_radius": 8,
                    "shadow": True,
                    "animations": True,
                    "opacity": 0.95
                }
            },
            "淺色主題": {
                "name": "淺色主題",
                "colors": {
                    "primary": "#6200EA",
                    "accent": "#03DAC6",
                    "background": "#FAFAFA",
                    "surface": "#FFFFFF",
                    "text": "#1C1C1C",
                    "text_secondary": "#666666",
                    "border": "#E1E1E1",
                    "hover": "#F0F0F0",
                    "selected": "#E8F5E8"
                },
                "fonts": {
                    "family": "Microsoft YaHei UI",
                    "size": 12,
                    "title_size": 16,
                    "small_size": 10
                },
                "effects": {
                    "border_radius": 12,
                    "shadow": True,
                    "animations": True,
                    "opacity": 0.98
                }
            },
            "深色主題": {
                "name": "深色主題",
                "colors": {
                    "primary": "#BB86FC",
                    "accent": "#03DAC6",
                    "background": "#121212",
                    "surface": "#1E1E1E",
                    "text": "#FFFFFF",
                    "text_secondary": "#AAAAAA",
                    "border": "#333333",
                    "hover": "#2C2C2C",
                    "selected": "#3700B3"
                },
                "fonts": {
                    "family": "Microsoft YaHei UI",
                    "size": 12,
                    "title_size": 16,
                    "small_size": 10
                },
                "effects": {
                    "border_radius": 8,
                    "shadow": True,
                    "animations": True,
                    "opacity": 0.95
                }
            }
        }
        
    def get_theme(self, theme_name: str = None):
        """獲取主題配置"""
        if theme_name is None:
            theme_name = self.current_theme
        return self.themes.get(theme_name, self.themes["系統預設"])
        
    def set_theme(self, theme_name: str):
        """設置主題"""
        if theme_name in self.themes:
            self.current_theme = theme_name
            self.apply_theme()
            self.theme_changed.emit()
            
    def apply_theme(self):
        """應用主題到應用程式"""
        theme = self.get_theme()
        app = QApplication.instance()
        
        if app:
            # 設置應用程式樣式
            stylesheet = self.generate_stylesheet(theme)
            app.setStyleSheet(stylesheet)
            
            # 設置字體
            font = QFont(theme["fonts"]["family"], theme["fonts"]["size"])
            app.setFont(font)
            
    def generate_stylesheet(self, theme):
        """生成樣式表"""
        colors = theme["colors"]
        fonts = theme["fonts"]
        effects = theme["effects"]
        
        return f"""
        /* 全局樣式 */
        QWidget {{
            background-color: {colors["background"]};
            color: {colors["text"]};
            font-family: "{fonts["family"]}";
            font-size: {fonts["size"]}px;
        }}
        
        /* 主視窗樣式 */
        QMainWindow {{
            background-color: {colors["background"]};
            border: 1px solid {colors["border"]};
            border-radius: {effects["border_radius"]}px;
        }}
        
        /* 按鈕樣式 */
        QPushButton {{
            background-color: {colors["primary"]};
            color: white;
            border: none;
            border-radius: {effects["border_radius"]}px;
            padding: 8px 16px;
            font-weight: bold;
            font-size: {fonts["size"]}px;
        }}
        
        QPushButton:hover {{
            background-color: {self.darken_color(colors["primary"], 0.1)};
        }}
        
        QPushButton:pressed {{
            background-color: {self.darken_color(colors["primary"], 0.2)};
        }}
        
        QPushButton:disabled {{
            background-color: {colors["border"]};
            color: {colors["text_secondary"]};
        }}
        
        /* 次要按鈕樣式 */
        QPushButton.secondary {{
            background-color: {colors["surface"]};
            color: {colors["text"]};
            border: 1px solid {colors["border"]};
        }}
        
        QPushButton.secondary:hover {{
            background-color: {colors["hover"]};
        }}
        
        /* 輸入框樣式 */
        QLineEdit {{
            background-color: {colors["surface"]};
            border: 2px solid {colors["border"]};
            border-radius: {effects["border_radius"]}px;
            padding: 8px 12px;
            font-size: {fonts["size"]}px;
        }}
        
        QLineEdit:focus {{
            border-color: {colors["primary"]};
        }}
        
        /* 列表樣式 */
        QListWidget {{
            background-color: {colors["surface"]};
            border: 1px solid {colors["border"]};
            border-radius: {effects["border_radius"]}px;
            outline: none;
        }}
        
        QListWidget::item {{
            padding: 12px;
            border-bottom: 1px solid {colors["border"]};
        }}
        
        QListWidget::item:hover {{
            background-color: {colors["hover"]};
        }}
        
        QListWidget::item:selected {{
            background-color: {colors["selected"]};
            color: {colors["text"]};
        }}
        
        /* 標籤樣式 */
        QLabel {{
            color: {colors["text"]};
            font-size: {fonts["size"]}px;
        }}
        
        QLabel.title {{
            font-size: {fonts["title_size"]}px;
            font-weight: bold;
            color: {colors["text"]};
        }}
        
        QLabel.subtitle {{
            font-size: {fonts["size"] + 2}px;
            font-weight: 600;
            color: {colors["text"]};
        }}
        
        QLabel.caption {{
            font-size: {fonts["small_size"]}px;
            color: {colors["text_secondary"]};
        }}
        
        /* 複選框樣式 */
        QCheckBox {{
            color: {colors["text"]};
            font-size: {fonts["size"]}px;
        }}
        
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {colors["border"]};
            border-radius: 3px;
            background-color: {colors["surface"]};
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {colors["primary"]};
            border-color: {colors["primary"]};
        }}
        
        /* 下拉框樣式 */
        QComboBox {{
            background-color: {colors["surface"]};
            border: 2px solid {colors["border"]};
            border-radius: {effects["border_radius"]}px;
            padding: 6px 12px;
            font-size: {fonts["size"]}px;
        }}
        
        QComboBox:focus {{
            border-color: {colors["primary"]};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {colors["text"]};
        }}
        
        /* 滑塊樣式 */
        QSlider::groove:horizontal {{
            border: 1px solid {colors["border"]};
            height: 6px;
            background: {colors["surface"]};
            border-radius: 3px;
        }}
        
        QSlider::handle:horizontal {{
            background: {colors["primary"]};
            border: 1px solid {colors["primary"]};
            width: 18px;
            height: 18px;
            border-radius: 9px;
            margin: -7px 0;
        }}
        
        QSlider::handle:horizontal:hover {{
            background: {self.darken_color(colors["primary"], 0.1)};
        }}
        
        /* 分組框樣式 */
        QGroupBox {{
            font-weight: bold;
            border: 2px solid {colors["border"]};
            border-radius: {effects["border_radius"]}px;
            margin-top: 10px;
            padding-top: 10px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 8px 0 8px;
            color: {colors["text"]};
            background-color: {colors["background"]};
        }}
        
        /* 標籤頁樣式 */
        QTabWidget::pane {{
            border: 1px solid {colors["border"]};
            border-radius: {effects["border_radius"]}px;
            background-color: {colors["surface"]};
        }}
        
        QTabBar::tab {{
            background-color: {colors["surface"]};
            border: 1px solid {colors["border"]};
            padding: 8px 16px;
            margin-right: 2px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {colors["primary"]};
            color: white;
        }}
        
        QTabBar::tab:hover {{
            background-color: {colors["hover"]};
        }}
        
        /* 對話框樣式 */
        QDialog {{
            background-color: {colors["background"]};
            border: 1px solid {colors["border"]};
            border-radius: {effects["border_radius"]}px;
        }}
        
        /* 分隔線樣式 */
        QFrame[frameShape="4"] {{
            color: {colors["border"]};
            background-color: {colors["border"]};
        }}
        
        /* 滾動條樣式 */
        QScrollBar:vertical {{
            background: {colors["surface"]};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background: {colors["border"]};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: {colors["text_secondary"]};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        """
        
    def darken_color(self, color_hex: str, factor: float = 0.1):
        """使顏色變暗"""
        try:
            # 移除 # 符號
            color_hex = color_hex.lstrip('#')
            
            # 轉換為 RGB
            r = int(color_hex[0:2], 16)
            g = int(color_hex[2:4], 16)
            b = int(color_hex[4:6], 16)
            
            # 應用變暗因子
            r = max(0, int(r * (1 - factor)))
            g = max(0, int(g * (1 - factor)))
            b = max(0, int(b * (1 - factor)))
            
            # 轉換回十六進制
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return color_hex
            
    def lighten_color(self, color_hex: str, factor: float = 0.1):
        """使顏色變亮"""
        try:
            # 移除 # 符號
            color_hex = color_hex.lstrip('#')
            
            # 轉換為 RGB
            r = int(color_hex[0:2], 16)
            g = int(color_hex[2:4], 16)
            b = int(color_hex[4:6], 16)
            
            # 應用變亮因子
            r = min(255, int(r + (255 - r) * factor))
            g = min(255, int(g + (255 - g) * factor))
            b = min(255, int(b + (255 - b) * factor))
            
            # 轉換回十六進制
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return color_hex
            
    def load_settings(self):
        """從設定文件載入主題設定"""
        try:
            settings_path = Path("settings.json")
            if settings_path.exists():
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
                appearance = settings.get("appearance", {})
                theme_name = appearance.get("theme", "系統預設")
                
                if theme_name in self.themes:
                    self.current_theme = theme_name
                    
                # 如果是自定義主題，載入自定義設定
                if theme_name == "自定義":
                    self.load_custom_theme(appearance)
                    
        except Exception as e:
            logging.error(f"載入主題設定失敗: {e}")
            
    def load_custom_theme(self, appearance_settings):
        """載入自定義主題"""
        custom_theme = self.themes["系統預設"].copy()
        
        # 更新顏色
        if "primary_color" in appearance_settings:
            custom_theme["colors"]["primary"] = appearance_settings["primary_color"]
        if "accent_color" in appearance_settings:
            custom_theme["colors"]["accent"] = appearance_settings["accent_color"]
            
        # 更新字體
        if "font_family" in appearance_settings:
            custom_theme["fonts"]["family"] = appearance_settings["font_family"]
        if "font_size" in appearance_settings:
            custom_theme["fonts"]["size"] = appearance_settings["font_size"]
            
        # 更新透明度
        if "opacity" in appearance_settings:
            custom_theme["effects"]["opacity"] = appearance_settings["opacity"] / 100.0
            
        self.themes["自定義"] = custom_theme

# 全局主題管理器實例
theme_manager = ThemeManager()

def apply_theme_to_widget(widget, theme_name: str = None):
    """將主題應用到特定控件"""
    theme = theme_manager.get_theme(theme_name)
    colors = theme["colors"]
    effects = theme["effects"]
    
    # 設置控件透明度
    widget.setWindowOpacity(effects["opacity"])
    
    # 應用樣式
    stylesheet = theme_manager.generate_stylesheet(theme)
    widget.setStyleSheet(stylesheet)

def get_current_theme():
    """獲取當前主題"""
    return theme_manager.get_theme()

def set_theme(theme_name: str):
    """設置主題"""
    theme_manager.set_theme(theme_name)

# 使用示例
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
    
    class TestWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("主題測試")
            self.resize(400, 300)
            
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            layout = QVBoxLayout(central_widget)
            
            title = QLabel("主題測試")
            title.setProperty("class", "title")
            layout.addWidget(title)
            
            button1 = QPushButton("主要按鈕")
            layout.addWidget(button1)
            
            button2 = QPushButton("次要按鈕")
            button2.setProperty("class", "secondary")
            layout.addWidget(button2)
            
            # 應用主題
            apply_theme_to_widget(self, "深色主題")
    
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())

