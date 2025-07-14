#!/bin/bash
# install.sh - SmartPanel 安裝腳本

echo "=== SmartPanel 安裝腳本 ==="

# 檢查 Python 版本
python_version=$(python3 --version 2>/dev/null | cut -d' ' -f2 | cut -d'.' -f1,2)
if [[ -z "$python_version" ]]; then
    echo "錯誤: 未找到 Python 3"
    exit 1
fi

echo "檢測到 Python 版本: $python_version"

# 安裝系統依賴 (Ubuntu/Debian)
if command -v apt-get >/dev/null 2>&1; then
    echo "安裝系統依賴..."
    sudo apt-get update
    sudo apt-get install -y python3-pip python3-dev
    sudo apt-get install -y libxcb-cursor0 libxcb-xinerama0 libxcb-randr0 libxcb-render-util0 libxcb-icccm4 libxcb-keysyms1 libxcb-image0
fi

# 安裝 Python 依賴
echo "安裝 Python 依賴..."
pip3 install --user -r requirements.txt

# 檢查安裝
echo "檢查安裝..."
python3 -c "import PyQt6; print('PyQt6 安裝成功')" || {
    echo "錯誤: PyQt6 安裝失敗"
    exit 1
}

echo "=== 安裝完成 ==="
echo "使用方法:"
echo "  python3 simple_test.py  # 運行簡化測試版"
echo "  python3 main.py         # 運行完整版 (需要 pynput)"
echo ""
echo "注意: 在無圖形環境中運行時，請使用:"
echo "  export QT_QPA_PLATFORM=offscreen"
echo "  python3 simple_test.py"

