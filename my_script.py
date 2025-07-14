# my_script.py
# 这是一个简单的示例腳本，用於測試 SmartPanel 的執行功能

import sys
import time
import logging

# 設定一個簡單的日誌，記錄腳本的運行情況
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='script_log.txt', # 腳本運行日誌
                    filemode='a') # 'a' 是追加模式，每次執行都追加到日誌

logging.info("示例腳本已啟動。")

# 簡單的輸出到控制台（這部分可能在 subprocess.Popen 中不可見）
print("Hello from my_script.py!")
logging.info("輸出了 'Hello from my_script.py!' 到標準輸出。")

# 模擬一個耗時的操作
logging.info("模擬一個 3 秒的延遲...")
print("模擬一個 3 秒的延遲...")
time.sleep(3)

# 腳本的退出信息
logging.info("示例腳本執行完畢，即將退出。")
print("示例腳本執行完畢，即將退出。")

# 腳本正常結束
sys.exit(0)