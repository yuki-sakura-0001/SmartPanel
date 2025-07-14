# search_panel.py - 全局搜尋面板模組

import sys
import os
import logging
import subprocess
import webbrowser
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget, 
    QListWidgetItem, QLabel, QFrame, QPushButton
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QPoint
from PyQt6.QtGui import QIcon, QFont

class SearchThread(QThread):
    """搜尋執行緒，避免阻塞 UI"""
    results_ready = pyqtSignal(list)
    
    def __init__(self, query):
        super().__init__()
        self.query = query
        
    def run(self):
        """執行搜尋"""
        results = []
        
        if not self.query.strip():
            self.results_ready.emit(results)
            return
            
        # 基本文件搜尋 (使用 Python 內建功能)
        try:
            results.extend(self.search_files(self.query))
        except Exception as e:
            logging.error(f"文件搜尋錯誤: {e}")
            
        # 應用程式搜尋
        try:
            results.extend(self.search_applications(self.query))
        except Exception as e:
            logging.error(f"應用程式搜尋錯誤: {e}")
            
        # 限制結果數量
        results = results[:50]
        
        self.results_ready.emit(results)
        
    def search_files(self, query):
        """搜尋文件"""
        results = []
        query_lower = query.lower()
        
        # 搜尋常見目錄
        search_paths = [
            Path.home() / "Desktop",
            Path.home() / "Documents", 
            Path.home() / "Downloads",
            Path.home()
        ]
        
        for search_path in search_paths:
            if not search_path.exists():
                continue
                
            try:
                for item in search_path.rglob("*"):
                    if len(results) >= 30:  # 限制文件搜尋結果
                        break
                        
                    if item.is_file() and query_lower in item.name.lower():
                        results.append({
                            "name": item.name,
                            "path": str(item),
                            "type": "file",
                            "icon": self.get_file_icon(item)
                        })
            except (PermissionError, OSError):
                continue
                
        return results
        
    def search_applications(self, query):
        """搜尋應用程式"""
        results = []
        query_lower = query.lower()
        
        if os.name == 'nt':  # Windows
            # 搜尋開始選單
            start_menu_paths = [
                Path(os.environ.get('PROGRAMDATA', '')) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
                Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs"
            ]
            
            for start_path in start_menu_paths:
                if not start_path.exists():
                    continue
                    
                try:
                    for item in start_path.rglob("*.lnk"):
                        if query_lower in item.stem.lower():
                            results.append({
                                "name": item.stem,
                                "path": str(item),
                                "type": "application",
                                "icon": "app"
                            })
                except (PermissionError, OSError):
                    continue
                    
        return results
        
    def get_file_icon(self, file_path):
        """根據文件類型返回圖標類型"""
        suffix = file_path.suffix.lower()
        
        if suffix in ['.txt', '.md', '.log']:
            return "text"
        elif suffix in ['.py', '.js', '.html', '.css', '.cpp', '.java']:
            return "code"
        elif suffix in ['.jpg', '.png', '.gif', '.bmp', '.jpeg']:
            return "image"
        elif suffix in ['.mp4', '.avi', '.mkv', '.mov']:
            return "video"
        elif suffix in ['.mp3', '.wav', '.flac', '.aac']:
            return "audio"
        elif suffix in ['.pdf']:
            return "pdf"
        elif suffix in ['.doc', '.docx']:
            return "word"
        elif suffix in ['.xls', '.xlsx']:
            return "excel"
        else:
            return "file"

class SearchPanel(QWidget):
    """搜尋面板主類"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle('SmartPanel - 搜尋')
        self.resize(600, 400)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        
        self.search_thread = None
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
        
        self.setup_ui()
        self.center()
        
        self._drag_pos = QPoint()
        
    def setup_ui(self):
        """設置 UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 標題欄
        title_layout = QHBoxLayout()
        title_label = QLabel("SmartPanel - 全局搜尋", self)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title_label.font()
        font.setPointSize(16)
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
            }
            QPushButton:hover { background-color: #c00; }
        """)
        close_button.clicked.connect(self.close)
        
        title_layout.addWidget(title_label)
        title_layout.addStretch(1)
        title_layout.addWidget(close_button)
        
        # 分隔線
        separator = QFrame(self)
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        
        # 搜尋框
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("輸入關鍵字搜尋文件和應用程式...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                font-size: 16px;
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 5px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
        """)
        self.search_input.textChanged.connect(self.on_search_text_changed)
        self.search_input.returnPressed.connect(self.execute_selected_result)
        
        # 結果列表
        self.results_list = QListWidget(self)
        self.results_list.setAlternatingRowColors(True)
        self.results_list.setStyleSheet("""
            QListWidget {
                font-size: 14px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #4CAF50;
                color: white;
            }
        """)
        self.results_list.itemClicked.connect(self.execute_selected_result)
        
        # 狀態標籤
        self.status_label = QLabel("輸入關鍵字開始搜尋", self)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: grey; font-size: 12px;")
        
        # 組裝布局
        main_layout.addLayout(title_layout)
        main_layout.addWidget(separator)
        main_layout.addWidget(self.search_input)
        main_layout.addWidget(self.results_list)
        main_layout.addWidget(self.status_label)
        
        # 設置焦點
        self.search_input.setFocus()
        
    def center(self):
        """將視窗移動到螢幕中央"""
        screen_geometry = self.screen().availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
        
    def on_search_text_changed(self, text):
        """搜尋文字改變時的處理"""
        # 延遲搜尋，避免頻繁觸發
        self.search_timer.stop()
        self.search_timer.start(300)  # 300ms 延遲
        
    def perform_search(self):
        """執行搜尋"""
        query = self.search_input.text().strip()
        
        if not query:
            self.results_list.clear()
            self.status_label.setText("輸入關鍵字開始搜尋")
            return
            
        self.status_label.setText("搜尋中...")
        
        # 停止之前的搜尋執行緒
        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.terminate()
            self.search_thread.wait()
            
        # 開始新的搜尋
        self.search_thread = SearchThread(query)
        self.search_thread.results_ready.connect(self.display_results)
        self.search_thread.start()
        
    def display_results(self, results):
        """顯示搜尋結果"""
        self.results_list.clear()
        
        if not results:
            self.status_label.setText("未找到相關結果")
            return
            
        self.status_label.setText(f"找到 {len(results)} 個結果")
        
        for result in results:
            item = QListWidgetItem()
            item.setText(f"{result['name']}")
            item.setData(Qt.ItemDataRole.UserRole, result)
            
            # 設置工具提示
            item.setToolTip(result['path'])
            
            self.results_list.addItem(item)
            
        # 選中第一個結果
        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)
            
    def execute_selected_result(self):
        """執行選中的搜尋結果"""
        current_item = self.results_list.currentItem()
        if not current_item:
            return
            
        result = current_item.data(Qt.ItemDataRole.UserRole)
        if not result:
            return
            
        try:
            path = result['path']
            result_type = result['type']
            
            logging.info(f"執行搜尋結果: {result['name']} ({path})")
            
            if result_type == 'file':
                # 打開文件
                if os.name == 'nt':  # Windows
                    os.startfile(path)
                else:  # Linux/macOS
                    subprocess.Popen(['xdg-open', path])
            elif result_type == 'application':
                # 執行應用程式
                if os.name == 'nt' and path.endswith('.lnk'):
                    os.startfile(path)
                else:
                    subprocess.Popen([path])
            else:
                # 預設處理
                if os.name == 'nt':
                    os.startfile(path)
                else:
                    subprocess.Popen(['xdg-open', path])
                    
            # 執行後隱藏面板
            self.hide()
            
        except Exception as e:
            logging.error(f"執行搜尋結果時發生錯誤: {e}")
            
    def keyPressEvent(self, event):
        """處理鍵盤事件"""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() == Qt.Key.Key_Down:
            current_row = self.results_list.currentRow()
            if current_row < self.results_list.count() - 1:
                self.results_list.setCurrentRow(current_row + 1)
        elif event.key() == Qt.Key.Key_Up:
            current_row = self.results_list.currentRow()
            if current_row > 0:
                self.results_list.setCurrentRow(current_row - 1)
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.execute_selected_result()
        else:
            super().keyPressEvent(event)
            
    def mousePressEvent(self, event):
        """處理滑鼠按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            if event.pos().y() < 50:  # 標題欄區域
                self._drag_pos = event.pos()
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        """處理滑鼠移動事件"""
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            new_pos = event.pos() - self._drag_pos
            self.move(self.pos() + new_pos)
        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event):
        """處理滑鼠釋放事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = QPoint()
        super().mouseReleaseEvent(event)
        
    def showEvent(self, event):
        """顯示事件"""
        super().showEvent(event)
        self.search_input.setFocus()
        self.search_input.selectAll()

if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    panel = SearchPanel()
    panel.show()
    sys.exit(app.exec())

