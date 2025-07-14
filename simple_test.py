#!/usr/bin/env python3
# simple_test.py - 簡化版 SmartPanel 測試

import sys
import os
import json
import subprocess
import webbrowser
from pathlib import Path

try:
    from PyQt6.QtWidgets import (
        QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, 
        QFrame, QListWidget, QListWidgetItem, QHBoxLayout
    )
    from PyQt6.QtCore import Qt, QTimer, QPoint
    from PyQt6.QtGui import QIcon
    print("PyQt6 導入成功")
except ImportError as e:
    print(f"PyQt6 導入失敗: {e}")
    sys.exit(1)

class SimpleSmartPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('SmartPanel - 簡化測試版')
        self.resize(400, 300)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        
        self.setup_ui()
        self.center()
        
        # 添加一些測試項目
        self.add_test_items()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 標題
        title_label = QLabel("SmartPanel - 簡化測試版", self)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title_label.font()
        font.setPointSize(16)
        title_label.setFont(font)
        
        # 關閉按鈕
        close_button = QPushButton("關閉", self)
        close_button.clicked.connect(self.close)
        
        # 標題欄
        title_layout = QHBoxLayout()
        title_layout.addWidget(title_label)
        title_layout.addWidget(close_button)
        
        # 列表
        self.list_widget = QListWidget(self)
        self.list_widget.itemClicked.connect(self.execute_item)
        
        # 狀態標籤
        self.status_label = QLabel("按 Esc 退出，點擊項目執行", self)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        main_layout.addLayout(title_layout)
        main_layout.addWidget(self.list_widget)
        main_layout.addWidget(self.status_label)
        
    def add_test_items(self):
        """添加測試項目"""
        test_items = [
            {"name": "打開 Google", "path": "https://www.google.com", "type": "url"},
            {"name": "打開記事本", "path": "notepad", "type": "app"},
            {"name": "當前目錄", "path": ".", "type": "folder"}
        ]
        
        for item_data in test_items:
            item = QListWidgetItem()
            item.setText(item_data["name"])
            item.setData(Qt.ItemDataRole.UserRole, item_data)
            self.list_widget.addItem(item)
            
    def execute_item(self, item):
        """執行選中的項目"""
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return
            
        try:
            path = data["path"]
            item_type = data["type"]
            
            print(f"執行項目: {data['name']} ({path})")
            
            if item_type == "url":
                webbrowser.open(path)
            elif item_type == "app":
                if os.name == 'nt':  # Windows
                    subprocess.Popen([path], shell=True)
                else:  # Linux
                    subprocess.Popen([path])
            elif item_type == "folder":
                if os.name == 'nt':
                    subprocess.Popen(['explorer', path])
                else:
                    subprocess.Popen(['xdg-open', path])
                    
            self.status_label.setText(f"已執行: {data['name']}")
            
        except Exception as e:
            print(f"執行錯誤: {e}")
            self.status_label.setText(f"執行失敗: {str(e)}")
            
    def center(self):
        """將視窗移到螢幕中央"""
        screen_geometry = self.screen().availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
        
    def keyPressEvent(self, event):
        """處理鍵盤事件"""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

if __name__ == '__main__':
    print("啟動簡化版 SmartPanel...")
    
    app = QApplication(sys.argv)
    window = SimpleSmartPanel()
    window.show()
    
    print("視窗已顯示，按 Esc 關閉")
    sys.exit(app.exec())
