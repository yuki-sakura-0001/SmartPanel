# startup_manager.py - 開機啟動管理模組

import os
import sys
import logging
import winreg
from pathlib import Path

class StartupManager:
    """開機啟動管理器"""
    
    def __init__(self):
        self.app_name = "SmartPanel"
        self.app_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
        
    def is_startup_enabled(self) -> bool:
        """檢查是否已設置開機啟動"""
        try:
            if sys.platform == "win32":
                return self._is_windows_startup_enabled()
            elif sys.platform == "darwin":
                return self._is_macos_startup_enabled()
            else:
                return self._is_linux_startup_enabled()
        except Exception as e:
            logging.error(f"檢查開機啟動狀態失敗: {e}")
            return False
            
    def enable_startup(self) -> bool:
        """啟用開機啟動"""
        try:
            if sys.platform == "win32":
                return self._enable_windows_startup()
            elif sys.platform == "darwin":
                return self._enable_macos_startup()
            else:
                return self._enable_linux_startup()
        except Exception as e:
            logging.error(f"啟用開機啟動失敗: {e}")
            return False
            
    def disable_startup(self) -> bool:
        """禁用開機啟動"""
        try:
            if sys.platform == "win32":
                return self._disable_windows_startup()
            elif sys.platform == "darwin":
                return self._disable_macos_startup()
            else:
                return self._disable_linux_startup()
        except Exception as e:
            logging.error(f"禁用開機啟動失敗: {e}")
            return False
            
    def _is_windows_startup_enabled(self) -> bool:
        """檢查 Windows 開機啟動狀態"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ
            )
            
            try:
                value, _ = winreg.QueryValueEx(key, self.app_name)
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
                
        except Exception:
            return False
            
    def _enable_windows_startup(self) -> bool:
        """啟用 Windows 開機啟動"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            
            winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, self.app_path)
            winreg.CloseKey(key)
            return True
            
        except Exception as e:
            logging.error(f"設置 Windows 開機啟動失敗: {e}")
            return False
            
    def _disable_windows_startup(self) -> bool:
        """禁用 Windows 開機啟動"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            
            try:
                winreg.DeleteValue(key, self.app_name)
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return True  # 已經不存在，視為成功
                
        except Exception as e:
            logging.error(f"移除 Windows 開機啟動失敗: {e}")
            return False
            
    def _is_macos_startup_enabled(self) -> bool:
        """檢查 macOS 開機啟動狀態"""
        plist_path = Path.home() / "Library/LaunchAgents" / f"com.{self.app_name.lower()}.plist"
        return plist_path.exists()
        
    def _enable_macos_startup(self) -> bool:
        """啟用 macOS 開機啟動"""
        try:
            plist_dir = Path.home() / "Library/LaunchAgents"
            plist_dir.mkdir(exist_ok=True)
            
            plist_path = plist_dir / f"com.{self.app_name.lower()}.plist"
            
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.{self.app_name.lower()}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{self.app_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>"""
            
            with open(plist_path, 'w') as f:
                f.write(plist_content)
                
            # 載入 LaunchAgent
            os.system(f"launchctl load {plist_path}")
            return True
            
        except Exception as e:
            logging.error(f"設置 macOS 開機啟動失敗: {e}")
            return False
            
    def _disable_macos_startup(self) -> bool:
        """禁用 macOS 開機啟動"""
        try:
            plist_path = Path.home() / "Library/LaunchAgents" / f"com.{self.app_name.lower()}.plist"
            
            if plist_path.exists():
                # 卸載 LaunchAgent
                os.system(f"launchctl unload {plist_path}")
                plist_path.unlink()
                
            return True
            
        except Exception as e:
            logging.error(f"移除 macOS 開機啟動失敗: {e}")
            return False
            
    def _is_linux_startup_enabled(self) -> bool:
        """檢查 Linux 開機啟動狀態"""
        desktop_file = Path.home() / ".config/autostart" / f"{self.app_name}.desktop"
        return desktop_file.exists()
        
    def _enable_linux_startup(self) -> bool:
        """啟用 Linux 開機啟動"""
        try:
            autostart_dir = Path.home() / ".config/autostart"
            autostart_dir.mkdir(parents=True, exist_ok=True)
            
            desktop_file = autostart_dir / f"{self.app_name}.desktop"
            
            desktop_content = f"""[Desktop Entry]
Type=Application
Name={self.app_name}
Comment=Smart desktop panel
Exec={self.app_path}
Icon={self.app_name.lower()}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
            
            with open(desktop_file, 'w') as f:
                f.write(desktop_content)
                
            # 設置執行權限
            desktop_file.chmod(0o755)
            return True
            
        except Exception as e:
            logging.error(f"設置 Linux 開機啟動失敗: {e}")
            return False
            
    def _disable_linux_startup(self) -> bool:
        """禁用 Linux 開機啟動"""
        try:
            desktop_file = Path.home() / ".config/autostart" / f"{self.app_name}.desktop"
            
            if desktop_file.exists():
                desktop_file.unlink()
                
            return True
            
        except Exception as e:
            logging.error(f"移除 Linux 開機啟動失敗: {e}")
            return False

# 全局開機啟動管理器實例
startup_manager = StartupManager()

# 使用示例
if __name__ == "__main__":
    manager = StartupManager()
    
    print(f"開機啟動狀態: {manager.is_startup_enabled()}")
    
    if not manager.is_startup_enabled():
        print("啟用開機啟動...")
        if manager.enable_startup():
            print("開機啟動已啟用")
        else:
            print("啟用開機啟動失敗")
    else:
        print("禁用開機啟動...")
        if manager.disable_startup():
            print("開機啟動已禁用")
        else:
            print("禁用開機啟動失敗")

