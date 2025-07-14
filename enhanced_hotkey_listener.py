# enhanced_hotkey_listener.py - 增強版熱鍵監聽器，支援多個熱鍵組合

import threading
import logging
import json 
import os   
from pynput import keyboard
from PyQt6.QtCore import QObject, pyqtSignal, Qt 

# --- 設定檔路徑與預設值 ---
SETTINGS_FILE = "settings.json"
DEFAULT_SETTINGS = {
  "hotkey": {
    "main_panel": {
      "use_ctrl": True,
      "use_alt": True,
      "use_shift": False,
      "trigger_key": "f12" 
    },
    "search_panel": {
      "use_ctrl": True,
      "use_alt": False,
      "use_shift": False,
      "trigger_key": "space"
    }
  }
}

# --- Log 設定 ---
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s',
                    filename='smartpanel.log',
                    filemode='w')

console_logger = logging.StreamHandler()
console_logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')
console_logger.setFormatter(formatter)
logging.getLogger('').addHandler(console_logger)

# --- 熱鍵相關常量定義 ---
CTRL_KEYS_SET = {keyboard.Key.ctrl_l, keyboard.Key.ctrl_r}
ALT_KEYS_SET = {keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr} 
SHIFT_KEYS_SET = {keyboard.Key.shift_l, keyboard.Key.shift_r}

# --- SettingsManager 類別 ---
class SettingsManager:
    def __init__(self):
        self.settings = DEFAULT_SETTINGS
        self.load_settings()

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    # 深度合併設定
                    self.settings = self._deep_merge(DEFAULT_SETTINGS, loaded_data)
                    logging.info(f"成功從 {SETTINGS_FILE} 載入設定。")
            except json.JSONDecodeError:
                logging.error(f"無法解析 {SETTINGS_FILE}，使用預設設定。")
                self.settings = DEFAULT_SETTINGS
            except Exception as e:
                logging.error(f"載入 {SETTINGS_FILE} 時發生錯誤: {e}，使用預設設定。")
                self.settings = DEFAULT_SETTINGS
        else:
            logging.warning(f"{SETTINGS_FILE} 不存在，將使用預設設定並創建文件。")
            self.save_settings() 

    def _deep_merge(self, default, loaded):
        """深度合併字典"""
        result = default.copy()
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
                logging.info(f"成功將設定保存到 {SETTINGS_FILE}。")
        except Exception as e:
            logging.error(f"保存設定到 {SETTINGS_FILE} 時發生錯誤: {e}")

    def get_hotkey_settings(self):
        return self.settings.get("hotkey", DEFAULT_SETTINGS["hotkey"])

# --- 熱鍵配置類別 ---
class HotkeyConfig:
    def __init__(self, config_dict):
        self.use_ctrl = config_dict.get("use_ctrl", False)
        self.use_alt = config_dict.get("use_alt", False)
        self.use_shift = config_dict.get("use_shift", False)
        self.trigger_key_char = config_dict.get("trigger_key", "")
        self.trigger_key = self._get_pynput_key_from_char(self.trigger_key_char)
        
    def _get_pynput_key_from_char(self, key_char):
        if not key_char:
            return None
        
        key_char_lower = key_char.lower()

        special_keys = {
            'f1': keyboard.Key.f1, 'f2': keyboard.Key.f2, 'f3': keyboard.Key.f3, 'f4': keyboard.Key.f4,
            'f5': keyboard.Key.f5, 'f6': keyboard.Key.f6, 'f7': keyboard.Key.f7, 'f8': keyboard.Key.f8,
            'f9': keyboard.Key.f9, 'f10': keyboard.Key.f10, 'f11': keyboard.Key.f11, 'f12': keyboard.Key.f12,
            'space': keyboard.Key.space, 'enter': keyboard.Key.enter, 'esc': keyboard.Key.esc,
            'tab': keyboard.Key.tab, 'backspace': keyboard.Key.backspace, 'delete': keyboard.Key.delete,
        }
        
        if key_char_lower in special_keys:
            return special_keys[key_char_lower]
        
        try:
            return keyboard.KeyCode.from_char(key_char_lower)
        except ValueError:
            logging.error(f"無法將字串 '{key_char}' 轉換為 pynput 鍵對象。")
            return None
    
    def matches(self, pressed_keys):
        """檢查當前按鍵是否匹配此熱鍵配置"""
        if self.trigger_key is None:
            return False
            
        # 檢查觸發鍵是否被按下
        if self.trigger_key not in pressed_keys:
            return False
            
        # 檢查修飾鍵
        ctrl_pressed = any(k in pressed_keys for k in CTRL_KEYS_SET)
        alt_pressed = any(k in pressed_keys for k in ALT_KEYS_SET)
        shift_pressed = any(k in pressed_keys for k in SHIFT_KEYS_SET)

        return (self.use_ctrl == ctrl_pressed and 
                self.use_alt == alt_pressed and 
                self.use_shift == shift_pressed)
    
    def get_display_name(self):
        """獲取熱鍵的顯示名稱"""
        parts = []
        if self.use_ctrl: parts.append("Ctrl")
        if self.use_alt: parts.append("Alt")
        if self.use_shift: parts.append("Shift")
        
        if isinstance(self.trigger_key, keyboard.KeyCode):
            parts.append(f"'{self.trigger_key.char}'")
        elif isinstance(self.trigger_key, keyboard.Key):
            parts.append(f"'{self.trigger_key.name}'")
        else:
            parts.append(f"'{self.trigger_key_char}'")
            
        return " + ".join(parts)

# --- 信號發射器 ---
class SignalEmitter(QObject):
    main_panel_activated = pyqtSignal()
    search_panel_activated = pyqtSignal()

# --- 增強版熱鍵監聽器 ---
class EnhancedHotkeyListener(threading.Thread):
    def __init__(self):
        super().__init__()
        self.emitter = SignalEmitter()
        self.daemon = True
        self.pressed_keys = set()
        self.pressed_keys_lock = threading.Lock() 
        self.is_active = True 
        
        # 載入設定
        settings_manager = SettingsManager()
        hotkey_settings = settings_manager.get_hotkey_settings()
        
        # 初始化熱鍵配置
        self.main_panel_hotkey = HotkeyConfig(hotkey_settings.get("main_panel", {}))
        self.search_panel_hotkey = HotkeyConfig(hotkey_settings.get("search_panel", {}))
        
        logging.info(f"主面板熱鍵: {self.main_panel_hotkey.get_display_name()}")
        logging.info(f"搜尋面板熱鍵: {self.search_panel_hotkey.get_display_name()}")

    def check_and_trigger(self):
        """檢查當前的按鍵組合是否滿足任何熱鍵要求"""
        with self.pressed_keys_lock:
            current_keys = self.pressed_keys.copy()
        
        # 檢查主面板熱鍵
        if self.main_panel_hotkey.matches(current_keys):
            logging.info("主面板熱鍵觸發!")
            self.emitter.main_panel_activated.emit()
            return
            
        # 檢查搜尋面板熱鍵
        if self.search_panel_hotkey.matches(current_keys):
            logging.info("搜尋面板熱鍵觸發!")
            self.emitter.search_panel_activated.emit()
            return

    def on_press(self, key):
        """當有按鍵被按下時"""
        logging.debug(f"按鍵按下: {key}")
        
        if not self.is_active:
            return

        with self.pressed_keys_lock:
            self.pressed_keys.add(key)
        
        # 檢查是否為觸發鍵
        if (key == self.main_panel_hotkey.trigger_key or 
            key == self.search_panel_hotkey.trigger_key):
            self.check_and_trigger()

    def on_release(self, key):
        """當有按鍵被鬆開時"""
        logging.debug(f"按鍵鬆開: {key}")

        if not self.is_active:
            return
            
        with self.pressed_keys_lock:
            self.pressed_keys.discard(key)

    def stop_listening(self):
        logging.warning("收到停止監聽指令。")
        self.is_active = False

    def run(self):
        """執行緒啟動時執行的主要方法"""
        logging.info(f"增強版熱鍵監聽已啟動。")
        logging.info(f"主面板熱鍵: {self.main_panel_hotkey.get_display_name()}")
        logging.info(f"搜尋面板熱鍵: {self.search_panel_hotkey.get_display_name()}")
        
        try:
            with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
                self.listener = listener 
                listener.join() 
                
        except Exception as e:
            logging.error(f"熱鍵監聽器發生未預期錯誤: {e}", exc_info=True)
        finally:
            logging.info("增強版熱鍵監聽器已停止。")

if __name__ == '__main__':
    # 測試用
    import time
    
    def on_main_panel():
        print("主面板被觸發!")
        
    def on_search_panel():
        print("搜尋面板被觸發!")
    
    listener = EnhancedHotkeyListener()
    listener.emitter.main_panel_activated.connect(on_main_panel)
    listener.emitter.search_panel_activated.connect(on_search_panel)
    listener.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        listener.stop_listening()
        print("監聽器已停止")

