import time
import os
import sys
import traceback
import datetime
import logging
import ctypes
import atexit

from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QUrl, QSize, pyqtSlot, QEvent
from PyQt5.QtGui import QIcon, QFont, QColor, QPixmap, QPainter, QImage, QKeySequence
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QLineEdit,
    QTextEdit, QComboBox, QCheckBox, QRadioButton, QSlider, QProgressBar,
    QListWidget, QTreeWidget, QTableWidget, QTabWidget, QSplitter,
    QGroupBox, QFormLayout, QHBoxLayout, QVBoxLayout, QGridLayout,
    QDialog, QMessageBox, QFileDialog, QInputDialog, QColorDialog,
    QMenu, QToolBar, QStatusBar, QAction, QSystemTrayIcon, QMenuBar,
    QLayout, QTextBrowser, QDialogButtonBox
)
# 定义 Windows API 相关常量和函数
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104
VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_ESCAPE = 0x1B

# 键盘钩子处理函数
keyboard_hook = None

# 全局标志，用于追踪任务栏状态
taskbar_hidden = False


# 键盘钩子回调函数
def low_level_keyboard_handler(nCode, wParam, lParam):
	if nCode >= 0:
		vk_code = ctypes.c_uint(lParam[0]).value
		
		# 检查Win键
		if vk_code in (VK_LWIN, VK_RWIN):
			ctrl_pressed = user32.GetKeyState(0x11) & 0x8000
			left_pressed = user32.GetKeyState(0x25) & 0x8000
			right_pressed = user32.GetKeyState(0x27) & 0x8000
			
			if ctrl_pressed and (left_pressed or right_pressed):
				return user32.CallNextHookEx(keyboard_hook, nCode, wParam, lParam)
			
			return 1
	
	return user32.CallNextHookEx(keyboard_hook, nCode, wParam, lParam)


# 设置键盘钩子
def set_keyboard_hook():
	global keyboard_hook
	try:
		CMPFUNC = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p))
		hook_callback = CMPFUNC(low_level_keyboard_handler)
		
		keyboard_hook = user32.SetWindowsHookExA(
			WH_KEYBOARD_LL,
			hook_callback,
			kernel32.GetModuleHandleA(None),
			0
		)
		
		if not keyboard_hook:
			error_code = ctypes.GetLastError()
			logger = logging.getLogger()
			logger.error(f"Failed to install keyboard hook. Error code: {error_code}")
			return False
		logger = logging.getLogger()
		logger.info("Keyboard hook installed successfully")
		return True
	except Exception as e:
		logger = logging.getLogger()
		logger.error(f"Exception while setting keyboard hook: {str(e)}")
		return False


# 移除键盘钩子
def remove_keyboard_hook():
	global keyboard_hook
	try:
		if keyboard_hook:
			result = user32.UnhookWindowsHookEx(keyboard_hook)
			if result:
				logger = logging.getLogger()
				logger.info("Keyboard hook uninstalled successfully")
			else:
				error_code = ctypes.GetLastError()
				logger = logging.getLogger()
				logger.error(f"Failed to uninstall keyboard hook. Error code: {error_code}")
			keyboard_hook = None
	except Exception as e:
		logger = logging.getLogger()
		logger.error(f"Exception while removing keyboard hook: {str(e)}")


# 禁用任务栏
def disable_taskbar():
	global taskbar_hidden
	try:
		taskbar_hwnd = user32.FindWindowW("Shell_TrayWnd", None)
		
		if taskbar_hwnd:
			user32.ShowWindow(taskbar_hwnd, 0)  # SW_HIDE
			logger = logging.getLogger()
			logger.info("Taskbar hidden")
		
		taskbar_hidden = True
	except Exception as e:
		logger = logging.getLogger()
		logger.error(f"Failed to disable taskbar: {str(e)}")


# 恢复任务栏
def enable_taskbar():
	global taskbar_hidden
	try:
		taskbar_hwnd = user32.FindWindowW("Shell_TrayWnd", None)
		
		if taskbar_hwnd:
			user32.ShowWindow(taskbar_hwnd, 1)  # SW_SHOW
			logger = logging.getLogger()
			logger.info("Taskbar shown")
		
		taskbar_hidden = False
	except Exception as e:
		logger = logging.getLogger()
		logger.error(f"Failed to enable taskbar: {str(e)}")


# 蓝屏窗口类（强制全屏版）
class BSODWindow(QMainWindow):
	def __init__(self):
		log_file = os.path.join(os.getenv('TEMP'), 'bsod_error.log')
		logging.basicConfig(filename=log_file, level=logging.INFO)
		super().__init__()
		# 窗口标志：无边框、置顶、覆盖全屏
		self.setWindowFlags(
			Qt.FramelessWindowHint |
			Qt.WindowStaysOnTopHint |
			Qt.WindowFullscreenButtonHint
		)
		
		# 窗口属性
		self.setAttribute(Qt.WA_DeleteOnClose, True)
		self.setAttribute(Qt.WA_ShowWithoutActivating, True)
		
		# 初始化UI
		self.init_ui()
		
		# 倒计时计数器
		self.countdown = 10
		self.start_countdown()
		
		# 设置键盘钩子
		if not set_keyboard_hook():
			logger = logging.getLogger()
			logger.warning("Failed to set keyboard hook, Win key will not be disabled")
		
		# 注册退出清理
		atexit.register(self.cleanup_resources)
		
		# 安装事件过滤器
		app = QApplication.instance()
		if app:
			app.installEventFilter(self)
	
	def init_ui(self):
		# 隐藏任务栏
		disable_taskbar()
		
		# 强制全屏显示（关键修改）
		self.showFullScreen()
		# 确保覆盖所有屏幕区域
		self.setGeometry(
			QApplication.desktop().x(),
			QApplication.desktop().y(),
			QApplication.desktop().width(),
			QApplication.desktop().height()
		)
		
		# 背景色设置为经典蓝屏色
		self.setStyleSheet("background-color: #0000AA;")
		
		# 创建中央部件
		central_widget = QWidget()
		self.setCentralWidget(central_widget)
		main_layout = QVBoxLayout(central_widget)
		main_layout.setContentsMargins(50, 50, 50, 50)
		
		# 蓝屏文本内容
		text = """
        你的电脑遇到问题，需要重启。我们只收集某些错误信息，
        然后重启你的电脑。

        错误代码: SYSTEM_THREAD_EXCEPTION_NOT_HANDLED

        问题签名:
        Problem Event Name: BlueScreen
        OS Version: 10.0.19044.1.0.0.768.101
        Locale ID: 2052

        已收集错误数据，正在寻找解决方案...

        解决方案: 不要在你的电脑上运行危险操作！
        """
		
		# 文本标签
		text_label = QLabel(text)
		text_label.setFont(QFont("Consolas", 12))
		text_label.setStyleSheet("color: white;")
		text_label.setAlignment(Qt.AlignLeft)
		text_label.setWordWrap(True)
		main_layout.addWidget(text_label, 1)
		
		# 倒计时标签
		self.countdown_label = QLabel("自动重启将在 10 秒后进行...")
		self.countdown_label.setFont(QFont("Consolas", 12, QFont.Bold))
		self.countdown_label.setStyleSheet("color: white;")
		self.countdown_label.setAlignment(Qt.AlignCenter)
		main_layout.addWidget(self.countdown_label)
		main_layout.setAlignment(self.countdown_label, Qt.AlignBottom)
		
		# 开发者提示
		dev_label = QLabel("开发者提示: Ctrl+Alt+Shift+ESC 退出,但是不一定能用\n搞那么多线程必遭严惩！")
		dev_label.setFont(QFont("Consolas", 8))
		dev_label.setStyleSheet("color: #AAAAFF;")
		dev_label.setAlignment(Qt.AlignRight)
		main_layout.addWidget(dev_label)
	
	# 启动倒计时
	def start_countdown(self):
		self.update_countdown()
	
	def update_countdown(self):
		self.countdown -= 1
		if self.countdown > 0:
			self.countdown_label.setText(f"自动重启将在 {self.countdown} 秒后进行，请不要关闭电源...")
			QTimer.singleShot(1000, self.update_countdown)
		else:
			self.close_and_exit()
	
	# 安全退出
	def close_and_exit(self):
		logger = logging.getLogger()
		logger.info("Initiating safe exit procedure")
		self.cleanup_resources()
		QApplication.quit()
		sys.exit(0)
	
	# 清理资源
	def cleanup_resources(self):
		logger = logging.getLogger()
		logger.info("Cleaning up resources")
		enable_taskbar()
		remove_keyboard_hook()
	
	# 重写关闭事件
	def closeEvent(self, event):
		if self.countdown > 0:
			event.ignore()
			self.countdown_label.setText("系统正在保存数据...请勿关闭电源！")
		else:
			self.close_and_exit()
			event.accept()
	
	# 键盘事件处理
	def keyPressEvent(self, event):
		# 开发者后门：Ctrl+Alt+Shift+ESC
		if (event.modifiers() == (Qt.ControlModifier | Qt.AltModifier | Qt.ShiftModifier) and
				event.key() == Qt.Key_Escape):
			logger = logging.getLogger()
			logger.info("Developer backdoor activated")
			self.close_and_exit()
		# 忽略Alt+F4
		elif event.key() == Qt.Key_F4 and event.modifiers() == Qt.AltModifier:
			event.ignore()
		else:
			super().keyPressEvent(event)
	
	# 窗口状态改变事件
	def changeEvent(self, event):
		# 防止窗口被最小化
		if event.type() == event.WindowStateChange:
			if self.windowState() & Qt.WindowMinimized:
				self.showFullScreen()
		super().changeEvent(event)
	
	# 事件过滤器
	def eventFilter(self, obj, event):
		try:
			if event.type() == QEvent.Type.Quit:
				logger = logging.getLogger()
				logger.info("Application quit event detected")
				self.cleanup_resources()
		except AttributeError:
			if event.type() == 12:  # QEvent.Quit 的整数值
				logger = logging.getLogger()
				logger.info("Application quit event detected")
				self.cleanup_resources()
		
		return super().eventFilter(obj, event)