# everything_integration.py - Everything 搜尋引擎整合模組 (Windows 專用)

import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Any
from PyQt6.QtCore import QThread, pyqtSignal

class EverythingSearchResult:
    """Everything 搜尋結果類別"""
    
    def __init__(self, name: str, path: str, size: int = 0, 
                 date_modified: str = "", is_folder: bool = False):
        self.name = name
        self.path = path
        self.size = size
        self.date_modified = date_modified
        self.is_folder = is_folder
        
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "name": self.name,
            "path": self.path,
            "size": self.size,
            "date_modified": self.date_modified,
            "is_folder": self.is_folder,
            "type": "folder" if self.is_folder else "file"
        }

class EverythingIntegration:
    """Everything 搜尋引擎整合類別"""
    
    def __init__(self):
        self.is_available = False
        self.everything_path = None
        self.es_path = None  # Everything 命令列工具路徑
        self._check_everything_availability()
        
    def _check_everything_availability(self):
        """檢查 Everything 是否可用"""
        if os.name != 'nt':
            logging.warning("Everything 僅支援 Windows 系統")
            return
            
        # 檢查 Everything 是否安裝
        possible_paths = [
            r"C:\Program Files\Everything\Everything.exe",
            r"C:\Program Files (x86)\Everything\Everything.exe",
            os.path.expanduser(r"~\AppData\Local\Everything\Everything.exe")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                self.everything_path = path
                break
                
        # 檢查 ES (Everything 命令列工具) 是否可用
        es_paths = [
            r"C:\Program Files\Everything\es.exe",
            r"C:\Program Files (x86)\Everything\es.exe",
            os.path.expanduser(r"~\AppData\Local\Everything\es.exe"),
            "es.exe"  # 如果在 PATH 中
        ]
        
        for path in es_paths:
            try:
                if path == "es.exe":
                    # 檢查是否在 PATH 中
                    result = subprocess.run([path, "-h"], 
                                          capture_output=True, 
                                          text=True, 
                                          timeout=5)
                    if result.returncode == 0:
                        self.es_path = path
                        break
                elif os.path.exists(path):
                    self.es_path = path
                    break
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
                
        self.is_available = self.everything_path is not None or self.es_path is not None
        
        if self.is_available:
            logging.info(f"Everything 可用: {self.everything_path or self.es_path}")
        else:
            logging.warning("Everything 不可用，請確保已安裝 Everything")
            
    def is_everything_running(self) -> bool:
        """檢查 Everything 服務是否正在運行"""
        if not self.is_available or os.name != 'nt':
            return False
            
        try:
            # 使用 tasklist 檢查 Everything 進程
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq Everything.exe"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return "Everything.exe" in result.stdout
        except Exception as e:
            logging.error(f"檢查 Everything 運行狀態失敗: {e}")
            return False
            
    def start_everything(self) -> bool:
        """啟動 Everything 服務"""
        if not self.everything_path or os.name != 'nt':
            return False
            
        try:
            subprocess.Popen([self.everything_path, "-startup"])
            logging.info("Everything 服務已啟動")
            return True
        except Exception as e:
            logging.error(f"啟動 Everything 失敗: {e}")
            return False
            
    def search_with_es(self, query: str, max_results: int = 100) -> List[EverythingSearchResult]:
        """使用 ES 命令列工具進行搜尋"""
        if not self.es_path or not query.strip():
            return []
            
        try:
            # 構建 ES 命令
            cmd = [
                self.es_path,
                "-n", str(max_results),  # 限制結果數量
                "-s",  # 顯示大小
                "-d",  # 顯示修改日期
                query
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                encoding='utf-8'
            )
            
            if result.returncode != 0:
                logging.error(f"ES 搜尋失敗: {result.stderr}")
                return []
                
            return self._parse_es_output(result.stdout)
            
        except subprocess.TimeoutExpired:
            logging.error("ES 搜尋超時")
            return []
        except Exception as e:
            logging.error(f"ES 搜尋錯誤: {e}")
            return []
            
    def _parse_es_output(self, output: str) -> List[EverythingSearchResult]:
        """解析 ES 命令輸出"""
        results = []
        lines = output.strip().split('\n')
        
        for line in lines:
            if not line.strip():
                continue
                
            try:
                # ES 輸出格式通常是: 大小 修改日期 完整路徑
                parts = line.split('\t') if '\t' in line else line.split()
                
                if len(parts) >= 3:
                    size_str = parts[0]
                    date_str = parts[1]
                    path = ' '.join(parts[2:])
                    
                    # 解析大小
                    size = 0
                    if size_str.isdigit():
                        size = int(size_str)
                    elif size_str == "<DIR>":
                        size = 0
                        
                    # 判斷是否為資料夾
                    is_folder = size_str == "<DIR>" or os.path.isdir(path)
                    
                    # 獲取檔案名
                    name = os.path.basename(path)
                    
                    result = EverythingSearchResult(
                        name=name,
                        path=path,
                        size=size,
                        date_modified=date_str,
                        is_folder=is_folder
                    )
                    results.append(result)
                    
            except Exception as e:
                logging.debug(f"解析搜尋結果行失敗: {line}, 錯誤: {e}")
                continue
                
        return results
        
    def search_with_pyeverything(self, query: str, max_results: int = 100) -> List[EverythingSearchResult]:
        """使用 PyEverything 進行搜尋 (需要在 Windows 環境中安裝)"""
        try:
            import PyEverything
            
            PyEverything.SetSearch(query)
            PyEverything.SetMax(max_results)
            
            if not PyEverything.Query():
                logging.error("PyEverything 查詢失敗")
                return []
                
            results = []
            num_results = PyEverything.GetNumResults()
            
            for i in range(num_results):
                try:
                    name = PyEverything.GetResultFileName(i)
                    path = PyEverything.GetResultFullPathName(i)
                    size = PyEverything.GetResultSize(i)
                    is_folder = PyEverything.GetResultIsFolder(i)
                    
                    # 獲取修改日期
                    date_modified = ""
                    try:
                        date_obj = PyEverything.GetResultDateModified(i)
                        if date_obj:
                            date_modified = date_obj.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        pass
                        
                    result = EverythingSearchResult(
                        name=name,
                        path=path,
                        size=size,
                        date_modified=date_modified,
                        is_folder=is_folder
                    )
                    results.append(result)
                    
                except Exception as e:
                    logging.debug(f"獲取搜尋結果 {i} 失敗: {e}")
                    continue
                    
            return results
            
        except ImportError:
            logging.warning("PyEverything 未安裝，使用 ES 命令列工具")
            return self.search_with_es(query, max_results)
        except Exception as e:
            logging.error(f"PyEverything 搜尋錯誤: {e}")
            return []
            
    def search(self, query: str, max_results: int = 100) -> List[EverythingSearchResult]:
        """執行搜尋 (自動選擇最佳方法)"""
        if not self.is_available:
            logging.warning("Everything 不可用")
            return []
            
        if not self.is_everything_running():
            logging.info("Everything 未運行，嘗試啟動...")
            if not self.start_everything():
                logging.error("無法啟動 Everything")
                return []
                
        # 優先使用 PyEverything，回退到 ES
        try:
            return self.search_with_pyeverything(query, max_results)
        except:
            return self.search_with_es(query, max_results)

class EverythingSearchThread(QThread):
    """Everything 搜尋執行緒"""
    
    results_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, query: str, max_results: int = 100):
        super().__init__()
        self.query = query
        self.max_results = max_results
        self.everything = EverythingIntegration()
        
    def run(self):
        """執行搜尋"""
        try:
            results = self.everything.search(self.query, self.max_results)
            # 轉換為字典格式以便傳遞
            result_dicts = [result.to_dict() for result in results]
            self.results_ready.emit(result_dicts)
        except Exception as e:
            self.error_occurred.emit(str(e))

# 使用示例
if __name__ == "__main__":
    # 測試 Everything 整合
    everything = EverythingIntegration()
    
    if everything.is_available:
        print("Everything 可用")
        
        # 測試搜尋
        results = everything.search("*.py", max_results=10)
        
        print(f"找到 {len(results)} 個結果:")
        for result in results:
            print(f"  {result.name} - {result.path}")
    else:
        print("Everything 不可用，請確保已安裝 Everything")

