# mouse_gesture.py - 滑鼠手勢識別模組

import math
import time
import json
import logging
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QPoint
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QApplication

class GesturePoint:
    """手勢點"""
    
    def __init__(self, x: int, y: int, timestamp: float = None):
        self.x = x
        self.y = y
        self.timestamp = timestamp or time.time()
        
    def distance_to(self, other: 'GesturePoint') -> float:
        """計算到另一個點的距離"""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
        
    def angle_to(self, other: 'GesturePoint') -> float:
        """計算到另一個點的角度（弧度）"""
        return math.atan2(other.y - self.y, other.x - self.x)

class GestureRecognizer:
    """手勢識別器"""
    
    def __init__(self, sensitivity: int = 5):
        self.sensitivity = sensitivity
        self.min_distance = 20 + (10 - sensitivity) * 5  # 根據靈敏度調整最小距離
        self.points: List[GesturePoint] = []
        self.directions: List[str] = []
        
    def add_point(self, x: int, y: int):
        """添加手勢點"""
        point = GesturePoint(x, y)
        self.points.append(point)
        
        # 如果有足夠的點，分析方向
        if len(self.points) >= 2:
            self._analyze_direction()
            
    def _analyze_direction(self):
        """分析手勢方向"""
        if len(self.points) < 2:
            return
            
        last_point = self.points[-1]
        prev_point = self.points[-2]
        
        # 檢查距離是否足夠
        distance = prev_point.distance_to(last_point)
        if distance < self.min_distance:
            return
            
        # 計算角度
        angle = prev_point.angle_to(last_point)
        direction = self._angle_to_direction(angle)
        
        # 避免重複方向
        if not self.directions or self.directions[-1] != direction:
            self.directions.append(direction)
            
    def _angle_to_direction(self, angle: float) -> str:
        """將角度轉換為方向"""
        # 將角度轉換為度數
        degrees = math.degrees(angle)
        if degrees < 0:
            degrees += 360
            
        # 根據角度範圍確定方向
        if 315 <= degrees or degrees < 45:
            return "→"  # 右
        elif 45 <= degrees < 135:
            return "↓"  # 下
        elif 135 <= degrees < 225:
            return "←"  # 左
        elif 225 <= degrees < 315:
            return "↑"  # 上
        else:
            return "?"
            
    def get_pattern(self) -> str:
        """獲取手勢模式"""
        if not self.directions:
            return ""
            
        # 檢查是否為圓形手勢
        if len(self.directions) >= 4 and self._is_circle():
            return "○"
            
        # 返回方向序列
        return "".join(self.directions)
        
    def _is_circle(self) -> bool:
        """檢查是否為圓形手勢"""
        if len(self.directions) < 4:
            return False
            
        # 簡單的圓形檢測：包含所有四個方向
        required_directions = {"↑", "↓", "←", "→"}
        return required_directions.issubset(set(self.directions))
        
    def reset(self):
        """重置手勢識別器"""
        self.points.clear()
        self.directions.clear()

class MouseGestureHandler(QObject):
    """滑鼠手勢處理器"""
    
    gesture_recognized = pyqtSignal(str)  # 手勢識別信號
    
    def __init__(self):
        super().__init__()
        self.enabled = False
        self.sensitivity = 5
        self.trigger_button = "middle"  # middle 或 right
        self.gestures: Dict[str, Dict[str, Any]] = {}
        
        self.recognizer = GestureRecognizer(self.sensitivity)
        self.is_recording = False
        self.start_pos = QPoint()
        
        self.load_settings()
        
    def load_settings(self):
        """載入設定"""
        try:
            settings_path = Path("settings.json")
            if settings_path.exists():
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
                mouse_gesture = settings.get("mouse_gesture", {})
                self.enabled = mouse_gesture.get("enabled", False)
                self.sensitivity = mouse_gesture.get("sensitivity", 5)
                self.trigger_button = mouse_gesture.get("trigger_button", "middle")
                
                # 載入手勢動作
                self.gestures = {}
                for gesture in mouse_gesture.get("gestures", []):
                    pattern = gesture.get("pattern", "")
                    if pattern:
                        self.gestures[pattern] = gesture
                        
                # 更新識別器靈敏度
                self.recognizer = GestureRecognizer(self.sensitivity)
                
        except Exception as e:
            logging.error(f"載入滑鼠手勢設定失敗: {e}")
            
    def handle_mouse_press(self, event: QMouseEvent) -> bool:
        """處理滑鼠按下事件"""
        if not self.enabled:
            return False
            
        # 檢查是否為觸發按鈕
        if self.trigger_button == "middle" and event.button() == Qt.MouseButton.MiddleButton:
            self.start_recording(event.pos())
            return True
        elif self.trigger_button == "right" and event.button() == Qt.MouseButton.RightButton:
            self.start_recording(event.pos())
            return True
            
        return False
        
    def handle_mouse_move(self, event: QMouseEvent) -> bool:
        """處理滑鼠移動事件"""
        if not self.enabled or not self.is_recording:
            return False
            
        # 添加手勢點
        self.recognizer.add_point(event.pos().x(), event.pos().y())
        return True
        
    def handle_mouse_release(self, event: QMouseEvent) -> bool:
        """處理滑鼠釋放事件"""
        if not self.enabled or not self.is_recording:
            return False
            
        # 檢查是否為觸發按鈕
        trigger_released = False
        if self.trigger_button == "middle" and event.button() == Qt.MouseButton.MiddleButton:
            trigger_released = True
        elif self.trigger_button == "right" and event.button() == Qt.MouseButton.RightButton:
            trigger_released = True
            
        if trigger_released:
            self.stop_recording()
            return True
            
        return False
        
    def start_recording(self, pos: QPoint):
        """開始記錄手勢"""
        self.is_recording = True
        self.start_pos = pos
        self.recognizer.reset()
        self.recognizer.add_point(pos.x(), pos.y())
        
    def stop_recording(self):
        """停止記錄手勢"""
        if not self.is_recording:
            return
            
        self.is_recording = False
        
        # 獲取手勢模式
        pattern = self.recognizer.get_pattern()
        if pattern and pattern in self.gestures:
            logging.info(f"識別到手勢: {pattern}")
            self.gesture_recognized.emit(pattern)
        else:
            logging.debug(f"未識別的手勢: {pattern}")
            
    def execute_gesture_action(self, pattern: str):
        """執行手勢動作"""
        if pattern not in self.gestures:
            return
            
        gesture = self.gestures[pattern]
        action = gesture.get("action", "")
        
        try:
            if action == "顯示主面板":
                self._show_main_panel()
            elif action == "顯示搜尋面板":
                self._show_search_panel()
            elif action == "隱藏面板":
                self._hide_panels()
            elif action == "返回":
                self._go_back()
            elif action == "關閉應用":
                self._close_application()
            else:
                logging.warning(f"未知的手勢動作: {action}")
                
        except Exception as e:
            logging.error(f"執行手勢動作失敗: {e}")
            
    def _show_main_panel(self):
        """顯示主面板"""
        # 這裡需要與主程式通信
        # 可以通過信號或直接調用主視窗方法
        pass
        
    def _show_search_panel(self):
        """顯示搜尋面板"""
        pass
        
    def _hide_panels(self):
        """隱藏面板"""
        pass
        
    def _go_back(self):
        """返回"""
        pass
        
    def _close_application(self):
        """關閉應用程式"""
        QApplication.quit()

class GlobalMouseGestureFilter(QObject):
    """全局滑鼠手勢過濾器"""
    
    def __init__(self, gesture_handler: MouseGestureHandler):
        super().__init__()
        self.gesture_handler = gesture_handler
        
    def eventFilter(self, obj, event):
        """事件過濾器"""
        if event.type() == event.Type.MouseButtonPress:
            if self.gesture_handler.handle_mouse_press(event):
                return True
        elif event.type() == event.Type.MouseMove:
            if self.gesture_handler.handle_mouse_move(event):
                return True
        elif event.type() == event.Type.MouseButtonRelease:
            if self.gesture_handler.handle_mouse_release(event):
                return True
                
        return super().eventFilter(obj, event)

# 使用示例
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
    
    class TestWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("滑鼠手勢測試")
            self.resize(400, 300)
            
            label = QLabel("在視窗中使用滑鼠中鍵拖拽來測試手勢", self)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setCentralWidget(label)
            
            # 設置手勢處理器
            self.gesture_handler = MouseGestureHandler()
            self.gesture_handler.enabled = True
            self.gesture_handler.gesture_recognized.connect(self.on_gesture)
            
            # 安裝事件過濾器
            self.gesture_filter = GlobalMouseGestureFilter(self.gesture_handler)
            self.installEventFilter(self.gesture_filter)
            
        def on_gesture(self, pattern):
            print(f"識別到手勢: {pattern}")
            self.centralWidget().setText(f"識別到手勢: {pattern}")
    
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())

