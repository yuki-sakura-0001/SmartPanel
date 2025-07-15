@echo off
REM install_windows.bat - SmartPanel Windows 安裝腳本

echo === SmartPanel Windows 安裝腳本 ===

REM 檢查 Python 版本
python --version >nul 2>&1
if errorlevel 1 (
    echo 錯誤: 未找到 Python
    echo 請先安裝 Python 3.7+ 64-bit 版本
    pause
    exit /b 1
)

echo 檢測到 Python 版本:
python --version

REM 安裝基本依賴
echo 安裝基本 Python 依賴...
pip install PyQt6 python-xlib

REM 安裝 PyEverything (Everything 整合)
echo 安裝 PyEverything (Everything 整合)...
pip install git+https://github.com/nambread/PyEverything#egg=PyEverything

REM 檢查 Everything 是否安裝
echo 檢查 Everything 是否安裝...
if exist "C:\Program Files\Everything\Everything.exe" (
    echo Everything 已安裝: C:\Program Files\Everything\Everything.exe
) else if exist "C:\Program Files (x86)\Everything\Everything.exe" (
    echo Everything 已安裝: C:\Program Files (x86)\Everything\Everything.exe
) else (
    echo 警告: 未找到 Everything
    echo 請從 https://www.voidtools.com/ 下載並安裝 Everything
    echo 以獲得最佳搜尋體驗
)

REM 檢查安裝
echo 檢查安裝...
python -c "import PyQt6; print('PyQt6 安裝成功')" || (
    echo 錯誤: PyQt6 安裝失敗
    pause
    exit /b 1
)

python -c "import PyEverything; print('PyEverything 安裝成功')" || (
    echo 警告: PyEverything 安裝失敗，Everything 整合功能將不可用
)

echo === 安裝完成 ===
echo 使用方法:
echo   python main.py         # 運行完整版
echo   python simple_test.py  # 運行簡化測試版
echo.
echo 注意: 確保 Everything 正在運行以獲得最佳搜尋體驗
pause

