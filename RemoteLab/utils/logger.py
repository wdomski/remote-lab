import time
from threading import Lock

def print_ok(text, **args):
    print('\033[92m' + text + '\033[0m', **args)

def print_error(text, **args):
    print('\033[91m' + text + '\033[0m', **args)

class Logger:
    color_debug = "blue"
    color_info = ""
    color_success = "green"
    color_error = "red"
    color_warning = "orange"
    timestamp_format = "[%Y-%m-%d %H:%M:%S]"
    level_enabled = True
    additional_msg = ""
    
    def __init__(self) -> None:
        self._lock = Lock()

    def _color_text(self, text: str, color: str):
        if color == "green":
            return '\033[92m' + text + '\033[0m'
        elif color == "red":
            return '\033[91m' + text + '\033[0m'
        elif color == "blue":
            return '\033[94m' + text + '\033[0m'
        elif color == "orange":
            return '\033[93m' + text + '\033[0m'
        else:
            return text
        
    def _get_timestamp(self):
        return time.strftime(self.timestamp_format, time.localtime())

    def _make_text(self, text: str, color: str, level=""):
        timestamp = self._get_timestamp()
        text = self._color_text(text, color)
        line = text
        header = ""
        if self.timestamp_format:
            header = timestamp + " "
        if self.level_enabled and level:
            header += f"[{level}] "
        if self.additional_msg:
            header += f"[{self.additional_msg}] "
        line = header + line
        return line
    
    def _print(self, text, **args):
        with self._lock:
            print(text, **args)
        
    def debug(self, text: str, **args):
        line = self._make_text(text, self.color_debug, "DEBUG")
        self._print(line, **args)
        
    def info(self, text: str, **args):
        line = self._make_text(text, self.color_info, "INFO")
        self._print(line, **args)
        
    def success(self, text: str, **args):
        line = self._make_text(text, self.color_success, "SUCCESS")
        self._print(line, **args)
        
    def error(self, text: str, **args):
        line = self._make_text(text, self.color_error, "ERROR")
        self._print(line, **args)    
        
    def warning(self, text: str, **args):
        line = self._make_text(text, self.color_warning, "WARNING")
        self._print(line, **args)