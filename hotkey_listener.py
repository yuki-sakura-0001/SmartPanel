# hotkey_listener.py (版本 9.9 - 擴充修飾鍵支持 AltGr)

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
    "use_ctrl": True,
    "use_alt": True,
    "use_shift": False,
    "trigger_key": "f12" 
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
# --- Log 設定結束 ---

# --- 熱鍵相關常量定義 ---
use_ctrl = False
use_alt = False
use_shift = False
TRIGGER_KEY_CHAR = 'f12' 
TRIGGER_KEY = None 

CTRL_KEYS_SET = {keyboard.Key.ctrl_l, keyboard.Key.ctrl_r}
# !!! 關鍵修改：在 ALT_KEYS_SET 中加入 alt_gr !!!
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
                    self.settings = {**DEFAULT_SETTINGS, **loaded_data}
                    self.settings["hotkey"] = {**DEFAULT_SETTINGS["hotkey"], **loaded_data.get("hotkey", {})}
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

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
                logging.info(f"成功將設定保存到 {SETTINGS_FILE}。")
        except Exception as e:
            logging.error(f"保存設定到 {SETTINGS_FILE} 時發生錯誤: {e}")

    def get_hotkey_settings(self):
        return self.settings.get("hotkey", DEFAULT_SETTINGS["hotkey"])

# --- 全局實例與配置載入 ---
settings_manager = SettingsManager()
hotkey_config = settings_manager.get_hotkey_settings()

use_ctrl = hotkey_config.get("use_ctrl", False)
use_alt = hotkey_config.get("use_alt", False)
use_shift = hotkey_config.get("use_shift", False)
TRIGGER_KEY_CHAR = hotkey_config.get("trigger_key", 'f12')

def get_pynput_key_from_char(key_char):
    if not key_char:
        return None
    
    key_char_lower = key_char.lower()

    special_keys = {
        'f1': keyboard.Key.f1, 'f2': keyboard.Key.f2, 'f3': keyboard.Key.f3, 'f4': keyboard.Key.f4,
        'f5': keyboard.Key.f5, 'f6': keyboard.Key.f6, 'f7': keyboard.Key.f7, 'f8': keyboard.Key.f8,
        'f9': keyboard.Key.f9, 'f10': keyboard.Key.f10, 'f11': keyboard.Key.f11, 'f12': keyboard.Key.f12,
        'space': keyboard.Key.space, 'enter': keyboard.Key.enter, 'esc': keyboard.Key.esc,
        'tab': keyboard.Key.tab, 'backspace': keyboard.Key.backspace, 'delete': keyboard.Key.delete,
        'ctrl_l': keyboard.Key.ctrl_l, 'ctrl_r': keyboard.Key.ctrl_r,
        'alt_l': keyboard.Key.alt_l, 'alt_r': keyboard.Key.alt_r,
        'shift_l': keyboard.Key.shift_l, 'shift_r': keyboard.Key.shift_r,
        'cmd': keyboard.Key.cmd, 'cmd_l': keyboard.Key.cmd_l, 'cmd_r': keyboard.Key.cmd_r,
        'menu': keyboard.Key.menu, 'caps_lock': keyboard.Key.caps_lock, 
        'num_lock': keyboard.Key.num_lock, 'scroll_lock': keyboard.Key.scroll_lock,
        'print_screen': keyboard.Key.print_screen, 'pause': keyboard.Key.pause
    }
    
    if key_char_lower in special_keys:
        return special_keys[key_char_lower]
    
    try:
        return keyboard.KeyCode.from_char(key_char_lower)
    except ValueError:
        logging.error(f"無法將字串 '{key_char}' 轉換為 pynput 鍵對象。")
        return None

TRIGGER_KEY = get_pynput_key_from_char(TRIGGER_KEY_CHAR)
if TRIGGER_KEY is None:
    logging.error(f"無法解析設定檔中的觸發鍵 '{TRIGGER_KEY_CHAR}'。將使用預設的 't'。")
    TRIGGER_KEY = keyboard.KeyCode.from_char('t')

logging.info(f"熱鍵設定載入: Ctrl={use_ctrl}, Alt={use_alt}, Shift={use_shift}, Trigger='{TRIGGER_KEY_CHAR}'")

# --- 信號和監聽器類別 ---
class SignalEmitter(QObject):
    activated = pyqtSignal()

class HotkeyListener(threading.Thread):
    def __init__(self):
        super().__init__()
        self.emitter = SignalEmitter()
        self.daemon = True
        self.pressed_keys = set()
        self.pressed_keys_lock = threading.Lock() 
        self.is_active = True 
        
        self.use_ctrl = use_ctrl
        self.use_alt = use_alt
        self.use_shift = use_shift
        self.trigger_key = TRIGGER_KEY 
        
        self.key_display_name = self.get_key_display_name(self.trigger_key)

    def get_key_display_name(self, key):
        if isinstance(key, keyboard.KeyCode):
            return key.char
        elif isinstance(key, keyboard.Key):
            return key.name
        return str(key) 

    def check_and_trigger(self):
        """檢查當前的按鍵組合是否滿足我們的熱鍵要求"""
        with self.pressed_keys_lock:
            current_keys = self.pressed_keys 
        
        ctrl_pressed = any(k in current_keys for k in CTRL_KEYS_SET)
        alt_pressed = any(k in current_keys for k in ALT_KEYS_SET)
        shift_pressed = any(k in current_keys for k in SHIFT_KEYS_SET)

        modifiers_ok = (self.use_ctrl == ctrl_pressed) and \
                       (self.use_alt == alt_pressed) and \
                       (self.use_shift == shift_pressed)

        if modifiers_ok:
            logging.info("熱鍵觸發成功!")
            self.emitter.activated.emit()

    def on_press(self, key):
        """當有按鍵被按下時"""
        logging.debug(f"按鍵按下: {key}")
        
        if not self.is_active:
            return

        is_trigger_key = (key == self.trigger_key)
        
        with self.pressed_keys_lock:
            self.pressed_keys.add(key)
        
        if is_trigger_key:
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
        hotkey_str_parts = []
        if self.use_ctrl: hotkey_str_parts.append("Ctrl")
        if self.use_alt: hotkey_str_parts.append("Alt")
        if self.use_shift: hotkey_str_parts.append("Shift")
        hotkey_str_parts.append(f"'{self.key_display_name}'")
        hotkey_str = " + ".join(hotkey_str_parts)
        
        logging.info(f"熱鍵監聽已啟動。請按 <{hotkey_str}> 來開關面板。")
        
        try:
            with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
                self.listener = listener 
                listener.join() 
                
        except Exception as e:
            logging.error(f"熱鍵監聽器發生未預期錯誤: {e}", exc_info=True)
        finally:
            logging.info("熱鍵監聽器已停止。")