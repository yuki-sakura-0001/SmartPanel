# SmartPanel - 智慧桌面面板

SmartPanel 是一個結合 Quicker 快速啟動面板和 uTools 搜尋功能的開源桌面工具，旨在提供高效、便捷的桌面操作體驗。

## 功能特色

### 🚀 快速啟動面板 (類似 Quicker)
- **全局熱鍵觸發**: 預設使用 `Ctrl+Alt+F12` 呼叫快速啟動面板
- **可視化操作**: 直觀的圖形化介面，支援圖標顯示
- **自定義啟動項**: 支援添加應用程式、網址、Python 腳本等
- **鍵盤導航**: 支援方向鍵、Enter、Esc 等快捷操作
- **拖拽移動**: 面板可自由拖拽移動位置

### 🔍 全局搜尋功能 (類似 uTools)
- **即時搜尋**: 預設使用 `Ctrl+Space` 呼叫搜尋面板
- **Everything 整合**: Windows 下支援 Everything 高速文件搜尋
- **文件搜尋**: 快速搜尋本地文件和文件夾
- **應用程式搜尋**: 搜尋已安裝的應用程式和快捷方式
- **模糊匹配**: 支援關鍵字模糊匹配，提高搜尋效率
- **即時結果**: 輸入時即時顯示搜尋結果

### ⚙️ 其他特性
- **開源免費**: 完全開源，支援社區協作
- **輕量高效**: 基於 Python + PyQt6，資源佔用少
- **跨平台潛力**: 設計時考慮了跨平台兼容性
- **可擴展性**: 模組化設計，便於功能擴展

## 安裝與使用

### 系統需求
- Python 3.7+
- PyQt6
- pynput

### 安裝步驟

1. **克隆專案**
   ```bash
   git clone https://github.com/yuki-sakura-0001/SmartPanel.git
   cd SmartPanel
   ```

2. **安裝依賴**
   ```bash
   pip install PyQt6 pynput
   ```

3. **運行程式**
   ```bash
   python main.py
   ```

### 基本使用

#### 快速啟動面板
1. 按下 `Ctrl+Alt+F12` 呼叫快速啟動面板
2. 點擊「設置」按鈕添加新的啟動項
3. 使用滑鼠點擊或鍵盤導航選擇項目
4. 按 Enter 或點擊執行選中的項目

#### 搜尋面板
1. 按下 `Ctrl+Space` 呼叫搜尋面板
2. 在搜尋框中輸入關鍵字
3. 即時查看搜尋結果
4. 使用方向鍵選擇結果，按 Enter 執行

#### 快捷鍵說明
- `Ctrl+Alt+F12`: 顯示/隱藏快速啟動面板
- `Ctrl+Space`: 顯示搜尋面板
- `Ctrl+F` 或 `F3`: 在快速啟動面板中打開搜尋
- `Esc`: 關閉當前面板
- `方向鍵`: 導航列表項目
- `Enter`: 執行選中項目

## 配置文件

SmartPanel 使用 `settings.json` 文件儲存配置：

```json
{
  "hotkey": {
    "main_panel": {
      "use_ctrl": true,
      "use_alt": true,
      "use_shift": false,
      "trigger_key": "f12"
    },
    "search_panel": {
      "use_ctrl": true,
      "use_alt": false,
      "use_shift": false,
      "trigger_key": "space"
    }
  },
  "startup_items": [
    {
      "name": "記事本",
      "path": "notepad.exe",
      "icon": ""
    }
  ]
}
```

## 開發計劃

### 已完成功能 ✅
- [x] 基本快速啟動面板
- [x] 熱鍵監聽系統
- [x] 啟動項管理（增刪改）
- [x] 全局搜尋面板
- [x] 文件和應用程式搜尋
- [x] 多熱鍵支援
- [x] Everything 整合（Windows 高速文件搜尋）
- [x] 滑鼠手勢觸發
- [x] 跨平台支援（macOS、Linux
- [x] 背景執行
- [x] 外觀主題自定義

### 計劃中功能 📋

- [ ] 自定義小工具編輯器
- [ ] 插件系統
- [ ] 自定義腳本製作執行
- [ ] 打包為可執行文件

### 以下等主體完善後才可能製作
### 計劃中可能加上的可選插件 📋
- [ ] 快捷翻譯
- [ ] ocr截圖
- [ ] 微軟365的格式一鍵更改
- [ ] 計算機功能
- [ ] utools的大多數功能如超级右键

## 技術架構

```
SmartPanel/
├── main.py                      # 主程式入口
├── hotkey_listener.py           # 基礎熱鍵監聽器
├── enhanced_hotkey_listener.py  # 增強版熱鍵監聽器
├── search_panel.py              # 搜尋面板模組
├── add_item_dialog.py           # 添加項目對話框
├── settings.json                # 配置文件
├── SYSTEM_DESIGN.md             # 系統設計文件
└── README.md                    # 說明文件
```

## 貢獻指南

歡迎社區貢獻！您可以通過以下方式參與：

1. **報告問題**: 在 GitHub Issues 中報告 bug 或提出功能建議
2. **提交代碼**: Fork 專案，創建功能分支，提交 Pull Request
3. **完善文檔**: 改進文檔、添加使用示例
4. **測試反饋**: 測試新功能並提供反饋

### 開發環境設置
```bash
# 克隆專案
git clone https://github.com/yuki-sakura-0001/SmartPanel.git
cd SmartPanel

# 創建虛擬環境（推薦）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\\Scripts\\activate   # Windows

# 安裝依賴
pip install PyQt6 pynput

# 運行測試
python main.py
```

## 授權協議

本專案採用 MIT 授權協議。詳見 [LICENSE](LICENSE) 文件。

## 致謝

- 感謝 [Quicker](https://getquicker.net/) 提供的設計靈感
- 感謝 [uTools](https://www.u-tools.cn/) 提供的功能參考
- 感謝所有貢獻者的支持

## 聯繫方式

- GitHub Issues: [提交問題或建議](https://github.com/yuki-sakura-0001/SmartPanel/issues)
- 專案主頁: [SmartPanel](https://github.com/yuki-sakura-0001/SmartPanel)
- ai製作：https://manus.im/share/Vrnri34rRKCHeW2UQMRBDc?replay=1

---

**SmartPanel** - 讓您的桌面操作更加智慧高效！ 🚀

