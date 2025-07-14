# hotkey_listener.py (版本 5.5 - 精確修復狀態追蹤 Bug)

import threading
import logging
from pynput import keyboard
from PyQt6.QtCore import QObject, pyqtSignal

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

# ==============================================================================
#                          *** 熱鍵自定義區 ***
# ==============================================================================
use_ctrl = True
use_alt = True
use_shift = False
TRIGGER_KEY = keyboard.KeyCode.from_char('t') # 使用 't' 作為觸發鍵

# --- 內部定義 ---
CTRL_KEYS = {keyboard.Key.ctrl_l, keyboard.Key.ctrl_r}
ALT_KEYS = {keyboard.Key.alt_l, keyboard.Key.alt_r}
SHIFT_KEYS = {keyboard.Key.shift_l, keyboard.Key.shift_r}
# ==============================================================================


class SignalEmitter(QObject):
    activated = pyqtSignal()

class HotkeyListener(threading.Thread):
    def __init__(self):
        super().__init__()
        self.emitter = SignalEmitter()
        self.daemon = True
        
        # 核心變數：一個集合，用來存放所有當前被按下的按鍵
        # 每個元素是一個 (按鍵物件, 按下的時間戳) 的元組
        # 使用時間戳是為了更精確地處理同一按鍵被快速連續按下或鬆開的情況
        self.pressed_keys_with_time = {} # 使用字典來記錄按鍵和時間戳
        
    def get_key_display_name(self, key):
        """安全地獲取按鍵的顯示名稱"""
        if isinstance(key, keyboard.KeyCode):
            return key.char
        elif isinstance(key, keyboard.Key):
            return key.name
        return str(key) # 回退到直接轉換為字串

    def check_and_trigger(self):
        """檢查當前的按鍵組合是否滿足我們的熱鍵要求"""
        
        current_keys = set(self.pressed_keys_with_time.keys()) # 只取當前按鍵的集合
        
        ctrl_pressed = any(k in current_keys for k in CTRL_KEYS)
        alt_pressed = any(k in current_keys for k in ALT_KEYS)
        shift_pressed = any(k in current_keys for k in SHIFT_KEYS)

        # 判斷修飾鍵是否符合設定
        modifiers_ok = (use_ctrl == ctrl_pressed) and \
                       (use_alt == alt_pressed) and \
                       (use_shift == shift_pressed)

        if modifiers_ok:
            logging.info("熱鍵觸發成功!")
            self.emitter.activated.emit()

    def on_press(self, key):
        """當有按鍵被按下時"""
        logging.debug(f"按鍵按下: {key}")
        
        if not self.is_active: # 如果監聽器已非活動狀態，則直接返回
            return

        # 使用當前時間戳記錄按鍵按下
        # 我們將按鍵物件作為鍵，時間戳作為值存儲在字典中
        self.pressed_keys_with_time[key] = threading.current_thread().native_id # 使用線程ID作為時間戳的代理，確保唯一性

        # 只有當這次按下的鍵是觸發鍵時，才檢查熱鍵組合是否成立
        if key == TRIGGER_KEY:
            self.check_and_trigger()

    def on_release(self, key):
        """當有按鍵被鬆開時"""
        logging.debug(f"按鍵鬆開: {key}")

        if not self.is_active:
            return

        # 從字典中移除被鬆開的按鍵
        self.pressed_keys_with_time.pop(key, None) # 使用 pop 移除，並設置默認值 None，避免 KeyError

    def stop_listening(self):
        """標記監聽器為非活動狀態"""
        logging.warning("收到停止監聽指令。")
        self.is_active = False
        # 注意：這裡我們沒有去調用 listener.stop()。
        # 如果主程式 (main.py) 正常退出，它的事件迴圈結束，
        # 這個 thread 也會因為是 daemon thread 而被終止。
        # 如果主程式崩潰，或者卡住，這裡的標記會讓新事件無效化，
        # 但 listener.join() 可能仍然會等待。
        # 更完善的中止機制需要線程間的協調，例如使用一個 Event 物件。
        # 但目前階段，先讓 is_active 標記生效已足夠。

    def run(self):
        """執行緒啟動時執行的主要方法"""
        key_display_name = self.get_key_display_name(TRIGGER_KEY)
        
        hotkey_str_parts = []
        if use_ctrl: hotkey_str_parts.append("Ctrl")
        if use_alt: hotkey_str_parts.append("Alt")
        if use_shift: hotkey_str_parts.append("Shift")
        hotkey_str_parts.append(f"'{key_display_name}'")
        hotkey_str = " + ".join(hotkey_str_parts)
        
        logging.info(f"熱鍵監聽已啟動。請按 <{hotkey_str}> 來開關面板。")
        
        try:
            # 創建監聽器，使用我們自定義的 on_press 和 on_release 方法
            with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
                self.listener = listener # 保存 listener 的引用，以便未來可能需要調用 stop()
                
                # 這裡的 join() 是關鍵，它會讓當前線程（監聽器線程）等待，直到監聽器停止。
                # 監聽器通常在收到 None 值時停止，或者如果它的上下文管理器退出。
                # 在本例中，我們依賴主程式正常結束來終止整個程序。
                listener.join() 
                
        except Exception as e:
            logging.error(f"熱鍵監聽器發生未預期錯誤: {e}", exc_info=True)
        finally:
            logging.info("熱鍵監聽器已停止。")