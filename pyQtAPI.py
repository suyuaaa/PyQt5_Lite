from BSODwindow import BSODWindow
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QUrl, QSize, pyqtSlot, QEvent
from PyQt5.QtGui import QIcon, QFont, QColor, QPixmap, QPainter, QImage, QKeySequence
from PyQt5.QtWidgets import (
	QApplication, QMainWindow, QWidget, QLabel, QPushButton, QLineEdit,
	QTextEdit, QComboBox, QCheckBox, QRadioButton, QSlider, QProgressBar,
	QListWidget, QTreeWidget, QTableWidget, QTabWidget, QSplitter,
	QGroupBox, QFormLayout, QHBoxLayout, QVBoxLayout, QGridLayout,
	QDialog, QMessageBox, QFileDialog, QInputDialog, QColorDialog,
	QMenu, QToolBar, QStatusBar, QAction, QSystemTrayIcon, QMenuBar,
	QLayout, QTextBrowser, QDialogButtonBox, QButtonGroup, QSizePolicy, QScrollArea, QFrame
)
import time
import os
import sys
import traceback
import datetime
import logging
import ctypes
import atexit


class CollapsibleVBox(QWidget):
	def __init__(self, title="", css=None, parent=None):
		super().__init__(parent)
		self.title = title
		self.css = css or {}
		self.initUI()
	
	def initUI(self):
		# 主布局
		self.main_layout = QVBoxLayout(self)
		self.main_layout.setContentsMargins(0, 0, 0, 0)
		self.main_layout.setSpacing(0)
		
		# 标题按钮
		self.toggle_button = QPushButton(self.title)
		self.toggle_button.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px 15px;
                background-color: #2A2A4A;
                color: #FFFFFF;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #3D3D6B;
            }
        """)
		self.toggle_button.clicked.connect(self.toggle)
		self.main_layout.addWidget(self.toggle_button)
		
		# 内容区域
		self.content_area = QWidget()
		self.content_layout = QVBoxLayout(self.content_area)
		self.content_layout.setContentsMargins(15, 15, 15, 15)
		self.content_area.hide()
		self.main_layout.addWidget(self.content_area)
		
		# 应用CSS样式
		self.setStyleSheet(self._generate_css())
	
	def toggle(self):
		self.content_area.setVisible(not self.content_area.isVisible())
	
	def _generate_css(self):
		# 确保self.css是字典
		css_dict = self.css if isinstance(self.css, dict) else {}
		
		return f"""
            background-color: {css_dict.get('background-color', '#2A2A4A')};
            border-radius: {css_dict.get('border-radius', '12px')};
            padding: {css_dict.get('padding', '10px')};
            margin-top: {css_dict.get('margin-top', '10px')};
            box-shadow: {css_dict.get('box-shadow', '0 2px 10px rgba(0,0,0,0.2)')};
            color: {css_dict.get('color', '#FFFFFF')};
        """
	
	def get_content_layout(self):
		return self.content_layout

class AutoScaledLabel(QLabel):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.original_pixmap = None
		self.setAlignment(Qt.AlignCenter)
		# 关键修复：设置尺寸策略为可忽略
		self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

	def setPixmap(self, pixmap):
		self.original_pixmap = pixmap
		# 初始时不设置图片，等待首次resizeEvent
		self.rescale_pixmap()

	def rescale_pixmap(self):
		"""独立出来的缩放方法"""
		if self.original_pixmap and not self.original_pixmap.isNull():
			# 获取当前可用空间（排除边框和内边距）
			available_size = self.size()

			# 计算保持宽高比的缩放
			scaled = self.original_pixmap.scaled(
				available_size,
				Qt.KeepAspectRatio,
				Qt.SmoothTransformation
			)
			super().setPixmap(scaled)

	def resizeEvent(self, event):
		# 只在有原始图片时才缩放
		if self.original_pixmap:
			self.rescale_pixmap()
			self.setMinimumSize(1, 1)  # 最小尺寸为1px
			self.setMaximumSize(16777215, 16777215)  # 恢复最大尺寸限制

		super().resizeEvent(event)

class CollapsibleWidget(QWidget):
	def __init__(self, title, parent=None):
		super().__init__(parent)
		self.initUI(title)

	def initUI(self, title):
		# 创建布局
		self.layout = QVBoxLayout()
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.setLayout(self.layout)

		# 创建折叠按钮
		self.toggle_button = QPushButton(title)
		self.toggle_button.setStyleSheet("text-align: left;")
		self.toggle_button.clicked.connect(self.toggle_collapse)
		self.layout.addWidget(self.toggle_button)

		# 创建容器
		self.content_area = QFrame()
		self.content_area.setFrameShape(QFrame.NoFrame)
		self.content_area.setContentsMargins(0, 0, 0, 0)
		self.content_layout = QVBoxLayout(self.content_area)
		self.content_layout.setContentsMargins(10, 0, 0, 0)
		self.content_area.setVisible(False)
		self.layout.addWidget(self.content_area)

	def add_widget(self, widget):
		# 向容器中添加子控件
		self.content_layout.addWidget(widget)

	def toggle_collapse(self):
		# 切换折叠状态
		if self.content_area.isVisible():
			self.content_area.setVisible(False)
		else:
			self.content_area.setVisible(True)
	def get_content_layout(self):
		return self.content_layout
class WindowMaker:
	"""简化PyQt5开发的辅助类"""

	POSITIONING_AUTO = "auto"  # 自动布局模式
	POSITIONING_MANUAL = "manual"  # 手动定位模式

	BUTTON_STYLES = {
		"primary": "background-color: #4CAF50; color: white; border-radius: 4px;",
		"danger": "background-color: #f44336; color: white; border-radius: 4px;",
		"warning": "background-color: #ff9800; color: white; border-radius: 4px;",
	}

	FEEDBACK_POPUP = "popup"
	FEEDBACK_LOG = "log"
	FEEDBACK_BOTH = "both"

	def __init__(self, title="PyQt Window", icon=None, size=None, feedback_type=FEEDBACK_POPUP,
				 log_file_path="error.log", fixedsize=None, CSS=None):
		"""
		初始化WindowMaker实例

		:param title: 窗口标题
		:param icon: 窗口图标路径
		:param size: 窗口大小，元组形式(width, height)
		:param feedback_type: 反馈类型，可选值为 "popup", "log", "both"
		:param log_file_path: 日志文件路径
		"""
		# 初始化日志系统
		self._init_logging(log_file_path)

		try:
			self.app = QApplication.instance()
			if not self.app:
				self.app = QApplication(sys.argv)
			self.main_window = QMainWindow()
			self.menu_bar = None
			self.feedback_type = feedback_type
			self.log_file_path = log_file_path

			# 设置窗口标题
			self.main_window.setWindowTitle(title)

			# 设置窗口图标
			if icon:
				try:
					abs_path = os.path.abspath(icon)
					if os.path.exists(abs_path):
						self.main_window.setWindowIcon(QIcon(abs_path))
					else:
						self._handle_warning(f"图标文件不存在: {abs_path}")
				except Exception as e:
					self._handle_error(f"设置窗口图标时出错: {str(e)}")

			# 验证并设置窗口大小
			if size:
				if not isinstance(size, tuple) or len(size) != 2:
					self._handle_error("窗口大小参数必须是一个包含两个元素的元组(width, height)")
				else:
					try:
						width, height = size
						if not isinstance(width, int) or not isinstance(height, int):
							self._handle_error("窗口宽度和高度必须是整数")
						else:
							self.main_window.resize(width, height)
					except Exception as e:
						self._handle_error(f"设置窗口大小时出错: {str(e)}")

			if CSS is not None:
				self.main_window.setAttribute(Qt.WA_TranslucentBackground)
				self.main_window.setWindowFlags(self.main_window.windowFlags() | Qt.FramelessWindowHint)

			if fixedsize is not None:
				self.main_window.setFixedSize(size[0], size[1])

			final_style = ""

			if CSS and isinstance(CSS, dict):
				for key, value in CSS.items():
					final_style += f"{key}: {value};"

			if final_style:
				self.main_window.setStyleSheet(final_style)

			# 创建中央部件和主布局
			self.central_widget = QWidget()
			self.main_window.setCentralWidget(self.central_widget)
			self.main_layout = QVBoxLayout(self.central_widget)

			if final_style:
				# 应用样式到中央部件
				self.central_widget.setStyleSheet(final_style)

			# 当前布局上下文栈
			self.layout_stack = [self.main_layout]

			# 定位模式
			self.positioning_mode = self.POSITIONING_AUTO

			# 记录初始化成功
			self.logger.info("WindowMaker 初始化成功")

		except Exception as e:
			self._handle_critical_error(f"初始化过程中发生严重错误: {str(e)}")

	def _init_logging(self, log_file_path):
		"""初始化日志系统"""
		self.logger = logging.getLogger("WindowMaker")
		self.logger.setLevel(logging.DEBUG)

		# 创建文件处理器
		try:
			file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
			file_handler.setLevel(logging.DEBUG)

			# 创建控制台处理器
			console_handler = logging.StreamHandler()
			console_handler.setLevel(logging.INFO)

			# 创建格式化器
			formatter = logging.Formatter(
				'%(asctime)s - %(name)s - %(levelname)s - %(message)s',
				datefmt='%Y-%m-%d %H:%M:%S'
			)

			file_handler.setFormatter(formatter)
			console_handler.setFormatter(formatter)

			# 添加处理器
			self.logger.addHandler(file_handler)
			self.logger.addHandler(console_handler)
		except Exception as e:
			print(f"无法初始化日志系统: {str(e)}")

	def _handle_warning(self, message):
		"""处理警告信息"""
		self.logger.warning(message)
		if self.feedback_type in [self.FEEDBACK_POPUP, self.FEEDBACK_BOTH]:
			self._show_error_dialog("警告", message, QMessageBox.Warning)

	def _handle_error(self, message):
		"""处理错误信息"""
		self.logger.error(message)
		if self.feedback_type in [self.FEEDBACK_POPUP, self.FEEDBACK_BOTH]:
			self._show_error_dialog("错误", message, QMessageBox.Critical)
		# 不退出，让程序继续运行

	def _handle_critical_error(self, message):
		"""处理严重错误信息并退出"""
		exc_info = traceback.format_exc()
		full_message = f"{message}\n\n错误详情:\n{exc_info}"
		self.logger.critical(full_message)

		if self.feedback_type in [self.FEEDBACK_POPUP, self.FEEDBACK_BOTH]:
			self._show_error_dialog("严重错误", full_message, QMessageBox.Critical, True)

		# 安全退出
		if hasattr(self, 'main_window') and self.main_window:
			self.main_window.close()
		sys.exit(1)

	def _show_error_dialog(self, title, message, icon=QMessageBox.Critical, is_critical=False):
		"""显示错误对话框"""
		try:
			dialog = QDialog()
			dialog.setWindowTitle(title)
			dialog.resize(600, 400)

			layout = QVBoxLayout()

			# 错误消息
			message_label = QLabel(message)
			message_label.setWordWrap(True)
			layout.addWidget(message_label)

			# 错误详情（可滚动）
			if is_critical:
				details_browser = QTextBrowser()
				details_browser.setPlainText(traceback.format_exc())
				layout.addWidget(details_browser)

			# 按钮
			button_box = QDialogButtonBox()
			if is_critical:
				exit_button = button_box.addButton("退出", QDialogButtonBox.RejectRole)
				exit_button.clicked.connect(lambda: sys.exit(1))
			else:
				ok_button = button_box.addButton(QDialogButtonBox.Ok)
				ok_button.clicked.connect(dialog.accept)

			layout.addWidget(button_box)
			dialog.setLayout(layout)
			dialog.exec_()
		except Exception as e:
			# 如果对话框创建失败，使用简单消息框
			msg_box = QMessageBox()
			msg_box.setIcon(icon)
			msg_box.setWindowTitle(title)
			msg_box.setText(message)
			msg_box.exec_()

	def use_auto_layout(self):
		"""
		切换到自动布局模式

		:return: 返回WindowMaker实例，支持链式调用
		"""
		self.positioning_mode = self.POSITIONING_AUTO
		return self

	def use_manual_positioning(self):
		"""
		切换到手动定位模式

		:return: 返回WindowMaker实例，支持链式调用
		"""
		self.positioning_mode = self.POSITIONING_MANUAL
		return self

	def get_menu_bar(self):
		"""
		获取或创建菜单栏

		:return: 返回菜单栏对象
		"""
		if not self.menu_bar:
			self.menu_bar = self.main_window.menuBar()
		return self.menu_bar

	def add_menu(self, title, CSS=None, hover_style=None, selected_style=None):
		"""
		添加一个顶级菜单到菜单栏

		:param title: 菜单标题
		:return: 返回新创建的菜单对象
		"""
		menu_bar = self.get_menu_bar()
		final_style = ""
		if hover_style is not None:
			final_style += f":hover {{ {hover_style} }}"
		if selected_style is not None:
			final_style += f":selected {{ {selected_style} }}"
		if CSS and isinstance(CSS, dict):
			for key, value in CSS.items():
				final_style += f"{key}: {value};"
		if final_style:
			menu_bar.setStyleSheet(final_style)
		return menu_bar.addMenu(title)

	def add_menu_item(self, menu, text, slot=None, shortcut=None,
					  icon=None, checkable=False, checked=False, CSS=None, hover_style=None,
					  selected_style=None):
		"""
		添加菜单项

		:param menu: 父菜单对象
		:param text: 菜单项文本
		:param slot: 菜单项被点击时调用的函数
		:param shortcut: 快捷键字符串，如"Ctrl+O"
		:param icon: 图标路径
		:param checkable: 是否为可勾选菜单项
		:param checked: 菜单项的初始勾选状态
		:return: 返回新创建的菜单项(QAction)对象
		"""
		try:
			action = QAction(text, self.main_window)

			if slot:
				# 验证slot是否可调用
				if not callable(slot):
					self._handle_error(f"菜单项 '{text}' 的slot参数必须是可调用对象")
				else:
					action.triggered.connect(slot)

			if shortcut:
				try:
					action.setShortcut(QKeySequence(shortcut))
				except:
					self._handle_error(f"无效的快捷键: {shortcut}")

			final_style = ""
			if hover_style is not None:
				final_style += f":hover {{ {hover_style} }}"
			if selected_style is not None:
				final_style += f":selected {{ {selected_style} }}"
			if CSS and isinstance(CSS, dict):
				for key, value in CSS.items():
					final_style += f"{key}: {value};"
			if final_style:
				menu.setStyleSheet(final_style)

			if icon:
				try:
					abs_path = os.path.abspath(icon)
					if os.path.exists(abs_path):
						action.setIcon(QIcon(abs_path))
					else:
						self._handle_warning(f"图标文件不存在: {abs_path}")
				except Exception as e:
					self._handle_error(f"设置菜单图标时出错: {str(e)}")

			if checkable:
				action.setCheckable(True)
				action.setChecked(checked)

			menu.addAction(action)
			return action
		except Exception as e:
			self._handle_error(f"添加菜单项时出错: {str(e)}")
			return None

	def add_sub_menu(self, parent_menu, title):
		"""
		在父菜单下添加子菜单

		:param parent_menu: 父菜单对象
		:param title: 子菜单标题
		:return: 返回新创建的子菜单对象
		"""
		return parent_menu.addMenu(title)

	def row(self, parent=None, margin=None, spacing=None):
		"""
		开始一行（水平布局）

		:param parent: 父部件，默认为中央部件
		:param margin: 布局边距，元组形式(left, top, right, bottom)
		:param spacing: 控件间距
		:return: 返回WindowMaker实例，支持链式调用
		"""
		try:
			if parent is None:
				parent = self.central_widget

			layout = QHBoxLayout()

			# 设置布局边距
			if margin:
				# 验证margin参数
				if not isinstance(margin, tuple) or len(margin) != 4:
					self._handle_error("margin参数必须是包含4个整数的元组(left, top, right, bottom)")
				else:
					left, top, right, bottom = margin
					layout.setContentsMargins(left, top, right, bottom)

			# 设置控件间距
			if spacing is not None:
				if not isinstance(spacing, int):
					self._handle_error("spacing参数必须是整数")
				else:
					layout.setSpacing(spacing)

			current_layout = self.layout_stack[-1]
			current_layout.addLayout(layout)
			self.layout_stack.append(layout)
			return self
		except Exception as e:
			self._handle_error(f"创建水平布局时出错: {str(e)}")
			return self

	def column(self, parent=None, margin=None, spacing=None):
		"""
		开始一列（垂直布局）

		:param parent: 父部件，默认为中央部件
		:param margin: 布局边距，元组形式(left, top, right, bottom)
		:param spacing: 控件间距
		:return: 返回WindowMaker实例，支持链式调用
		"""
		try:
			if parent is None:
				parent = self.central_widget

			layout = QVBoxLayout()

			# 设置布局边距
			if margin:
				left, top, right, bottom = margin
				layout.setContentsMargins(left, top, right, bottom)

			# 设置控件间距
			if spacing is not None:
				layout.setSpacing(spacing)

			current_layout = self.layout_stack[-1]
			current_layout.addLayout(layout)
			self.layout_stack.append(layout)
			return self
		except Exception as e:
			self._handle_error(f"创建垂直布局时出错: {str(e)}")

	def end(self):
		"""
		结束当前行/列，返回上一级布局

		:return: 返回WindowMaker实例，支持链式调用
		"""
		if len(self.layout_stack) > 1:
			self.layout_stack.pop()
		return self

	def add_button(self, text, parent=None, command=None, shortcut=None,
				   checkable=False, checked=False, style=None, css=None,
				   position=None, size=None, min_size=None, max_size=None,
				   stretch=0, alignment=None):
		try:
			if parent is None:
				parent = self.central_widget
			button = QPushButton(text, parent)

			# 设置按钮最小尺寸
			if min_size:
				width, height = min_size
				button.setMinimumSize(width, height)

			# 设置按钮最大尺寸
			if max_size:
				width, height = max_size
				button.setMaximumSize(width, height)

			if shortcut:
				button.setShortcut(QKeySequence(shortcut))

			if checkable:
				button.setCheckable(True)
				if checked:
					button.setChecked(checked)

			if command:
				button.clicked.connect(command)

			# 应用样式
			normal_style = ""
			hover_style = ""

			if style and style in self.BUTTON_STYLES:
				normal_style += self.BUTTON_STYLES[style]

			if css and isinstance(css, dict):
				for key, value in css.items():
					if key.startswith("hover-"):
						# 处理 :hover 样式
						hover_key = key.replace("hover-", "")
						hover_style += f"{hover_key}: {value};"
					else:
						normal_style += f"{key}: {value};"

			final_style = f"QPushButton {{{normal_style}}}"
			if hover_style:
				final_style += f" QPushButton:hover {{{hover_style}}}"

			if final_style:
				button.setStyleSheet(final_style)

			# 根据定位模式处理位置和大小
			if self.positioning_mode == self.POSITIONING_MANUAL:
				if position:
					button.move(position[0], position[1])
				if size:
					button.resize(size[0], size[1])
			else:
				# 在自动布局中添加按钮
				current_layout = self.layout_stack[-1]
				if alignment is not None:
					current_layout.addWidget(button, stretch, alignment)
				else:
					current_layout.addWidget(button, stretch)

			return button
		except Exception as e:
			self._handle_error(f"添加按钮时出错: {str(e)}")
	
	def add_collapsible_box(self, title, parent=None, css=None):
		"""添加可折叠容器"""
		try:
			if parent is None:
				parent = self.central_widget
			
			box = CollapsibleVBox(title, parent)
			
			# 应用样式
			if css and isinstance(css, dict):
				style = "; ".join([f"{k}: {v}" for k, v in css.items()])
				box.setStyleSheet(style)
			
			# 添加到当前布局
			current_layout = self.layout_stack[-1]
			current_layout.addWidget(box)
			
			return box
		
		except Exception as e:
			self._handle_error(f"添加可折叠容器时出错: {str(e)}")
			return None
		
	def add_img(self, img_path, parent=None, position=None, size=None, min_size=None,
				max_size=None, stretch=0, alignment=None, auto_scale=True):
		try:
			if parent is None:
				parent = self.central_widget
			# 创建标签
			if auto_scale:
				img = AutoScaledLabel(self.central_widget)
			else:
				img = QLabel(self.central_widget)

			# 加载图片但不立即设置（等待resizeEvent）
			pixmap = QPixmap(img_path)
			if pixmap.isNull():
				self._handle_error(f"无法加载图片: {img_path}")
			else:
				if auto_scale:
					img.original_pixmap = pixmap  # 保存但不立即设置
				else:
					img.setPixmap(pixmap)

			# 设置尺寸约束
			if min_size:
				img.setMinimumSize(*min_size)
			else:
				# 没有指定最小尺寸时设为1px
				img.setMinimumSize(1, 1)

			if max_size:
				img.setMaximumSize(*max_size)

			# 布局处理
			if self.positioning_mode == self.POSITIONING_MANUAL:
				if position: img.move(*position)
				if size: img.resize(*size)
			else:
				current_layout = self.layout_stack[-1]
				if alignment:
					current_layout.addWidget(img, stretch, alignment)
				else:
					current_layout.addWidget(img, stretch)

			# 首次强制触发缩放
			if auto_scale:
				QTimer.singleShot(0, img.rescale_pixmap)

			return img
		except Exception as e:
			self._handle_error(f"加载图片时出错: {str(e)}")

	def add_label(self, text, parent=None, position=None, size=None, min_size=None,
				  max_size=None, stretch=0, alignment=None, css=None):
		try:
			if parent is None:
				parent = self.central_widget
			label = QLabel(text, self.central_widget)
			final_style = ""

			if css and isinstance(css, dict):
				for key, value in css.items():
					final_style += f"{key}: {value};"

			if final_style:
				label.setStyleSheet(final_style)
			if min_size:
				width, height = min_size
				label.setMinimumSize(width, height)
			if max_size:
				width, height = max_size
				label.setMaximumSize(width, height)
			if self.positioning_mode == self.POSITIONING_MANUAL:
				if position:
					label.move(position[0], position[1])
				if size:
					label.resize(size[0], size[1])
			else:
				# 在自动布局中添加按钮
				current_layout = self.layout_stack[-1]
				if alignment is not None:
					current_layout.addWidget(label, stretch, alignment)
				else:
					current_layout.addWidget(label, stretch)

			return label
		except Exception as e:
			self._handle_error(f"添加标签时出错: {str(e)}")

	def add_line_edit(self, parent=None, text="", placeholder="", is_password=False, position=None, size=None, min_size=None,
					  max_size=None, stretch=0, alignment=None, css=None):
		"""
		添加单行输入框(QLineEdit)

		:param text: 初始文本内容
		:param placeholder: 占位文本（输入框为空时显示的提示文本）
		:param is_password: 是否为密码输入框（启用后文本会显示为圆点）
		:param position: 手动模式下的位置(x, y)
		:param size: 手动模式下的大小(width, height)
		:param min_size: 最小尺寸(width, height)，防止被压缩
		:param max_size: 最大尺寸(width, height)，防止被拉伸
		:param stretch: 自动布局中的拉伸系数（值越大占比越高）
		:param alignment: 自动布局中的对齐方式（如Qt.AlignLeft）
		:return: 返回QLineEdit对象
		"""
		try:
			if parent is None:
				parent = self.central_widget
			line = QLineEdit(text, self.central_widget)

			normal_style = ""
			hover_style = ""

			if css and isinstance(css, dict):
				for key, value in css.items():
					if key.startswith("hover-"):
						# 处理 :hover 样式
						hover_key = key.replace("hover-", "")
						hover_style += f"{hover_key}: {value};"
					else:
						normal_style += f"{key}: {value};"

			final_style = f"QLineEdit {{{normal_style}}}"
			if hover_style:
				final_style += f" QLineEdit:hover {{{hover_style}}}"

			if final_style:
				line.setStyleSheet(final_style)

			# 设置占位文本
			if placeholder:
				line.setPlaceholderText(placeholder)

			# 设置密码模式
			if is_password:
				line.setEchoMode(QLineEdit.Password)

			# 设置最小尺寸
			if min_size:
				width, height = min_size
				line.setMinimumSize(width, height)

			# 设置最大尺寸
			if max_size:
				width, height = max_size
				line.setMaximumSize(width, height)

			# 根据定位模式处理位置和大小
			if self.positioning_mode == self.POSITIONING_MANUAL:
				if position:
					line.move(position[0], position[1])
				if size:
					line.resize(size[0], size[1])
			else:
				# 在自动布局中添加输入框
				current_layout = self.layout_stack[-1]
				if alignment is not None:
					current_layout.addWidget(line, stretch, alignment)
				else:
					current_layout.addWidget(line, stretch)

			return line
		except Exception as e:
			self._handle_error(f"添加单行输入框时出错: {str(e)}")

	def add_text_edit(self, parent=None, text="", placeholder="", position=None, size=None, min_size=None,
					  max_size=None, stretch=0, alignment=None, css=None):
		try:
			if parent is None:
				parent = self.central_widget
			edit = QTextEdit(text, self.central_widget)
			normal_style = ""
			hover_style = ""

			if css and isinstance(css, dict):
				for key, value in css.items():
					if key.startswith("hover-"):
						# 处理 :hover 样式
						hover_key = key.replace("hover-", "")
						hover_style += f"{hover_key}: {value};"
					else:
						normal_style += f"{key}: {value};"

			final_style = f"QTextEdit {{{normal_style}}}"
			if hover_style:
				final_style += f" QTextEdit:hover {{{hover_style}}}"

			if final_style:
				edit.setStyleSheet(final_style)
			if placeholder:
				edit.setPlaceholderText(placeholder)
			if min_size:
				width, height = min_size
				edit.setMinimumSize(width, height)
			if max_size:
				width, height = max_size
				edit.setMaximumSize(width, height)
			if self.positioning_mode == self.POSITIONING_MANUAL:
				if position:
					edit.move(position[0], position[1])
				if size:
					edit.resize(size[0], size[1])
			else:
				# 在自动布局中添加按钮
				current_layout = self.layout_stack[-1]
				if alignment is not None:
					current_layout.addWidget(edit, stretch, alignment)
				else:
					current_layout.addWidget(edit, stretch)
			return edit
		except Exception as e:
			self._handle_error(f"添加多行输入框时出错: {str(e)}")

	def add_list_widget(self, parent=None, position=None, size=None, min_size=None,
						max_size=None, stretch=0, alignment=None, css=None):
		"""
		添加列表控件(QListWidget)

		:param position: 手动定位模式下的位置，元组形式(x, y)
		:param size: 手动定位模式下的大小，元组形式(width, height)
		:param min_size: 最小尺寸，元组形式(width, height)
		:param max_size: 最大尺寸，元组形式(width, height)
		:param stretch: 布局拉伸系数
		:param alignment: 对齐方式，如Qt.AlignLeft
		:return: 返回新创建的列表控件对象
		"""
		try:
			if parent is None:
				parent = self.central_widget
			list_widget = QListWidget(self.central_widget)

			# 设置最小尺寸
			if min_size:
				width, height = min_size
				list_widget.setMinimumSize(width, height)

			# 设置最大尺寸
			if max_size:
				width, height = max_size
				list_widget.setMaximumSize(width, height)

				# 应用样式
				final_style = ""

				if css and isinstance(css, dict):
					for key, value in css.items():
						final_style += f"{key}: {value};"

				if final_style:
					list_widget.setStyleSheet(final_style)

			# 根据定位模式处理位置和大小
			if self.positioning_mode == self.POSITIONING_MANUAL:
				if position:
					list_widget.move(position[0], position[1])
				if size:
					list_widget.resize(size[0], size[1])
			else:
				# 在自动布局中添加列表控件
				current_layout = self.layout_stack[-1]
				if alignment is not None:
					current_layout.addWidget(list_widget, stretch, alignment)
				else:
					current_layout.addWidget(list_widget, stretch)

			return list_widget
		except Exception as e:
			self._handle_error(f"添加列表控件时出错: {str(e)}")

	def add_box(self, parent=None, text="", size=None, min_size=None,
				max_size=None, stretch=0, alignment=None, position=None,
				editable=False):
		try:
			if parent is None:
				parent = self.central_widget
			box = QComboBox(parent)
			box.setEditable(editable)
			# 设置最小尺寸
			if min_size:
				width, height = min_size
				box.setMinimumSize(width, height)

			# 设置最大尺寸
			if max_size:
				width, height = max_size
				box.setMaximumSize(width, height)

			# 根据定位模式处理位置和大小
			if self.positioning_mode == self.POSITIONING_MANUAL:
				if position:
					box.move(position[0], position[1])
				if size:
					box.resize(size[0], size[1])
			else:
				# 在自动布局中添加列表控件
				current_layout = self.layout_stack[-1]
				if alignment is not None:
					current_layout.addWidget(box, stretch, alignment)
				else:
					current_layout.addWidget(box, stretch)

			return box
		except Exception as e:
			self._handle_error(f"添加下拉框时出错: {str(e)}")

	def add_box_item(self, parent, slot=None, text=""):
		try:
			if not isinstance(parent, QComboBox):
				self._handle_error("parent必须是QComboBox实例，下拉选项创建失败")
				return
			if slot is None:
				parent.addItem(text)
				return
			if slot and callable(slot):
				parent.currentIndexChanged.connect(slot)
			else:
				self._handle_error(f"添加下拉选项 {str(text)} 时发现无效的函数: {str(slot)}")
			return
		except Exception as e:
			self._handle_error(f"添加下拉选项时出错: {str(e)}")

	def add_checkbox(self, parent, text="", checked=False, tristate=False,
					 command=None, position=None, size=None,
					 min_size=None, max_size=None, stretch=0, alignment=None):
		"""
		添加复选框

		:param text: 复选框文本
		:param checked: 初始选中状态
		:param tristate: 是否支持三态
		:param command: 状态改变时调用的函数
		:param position: 手动定位模式下的位置
		:param size: 手动定位模式下的大小
		:param min_size: 最小尺寸
		:param max_size: 最大尺寸
		:param stretch: 布局拉伸系数
		:param alignment: 对齐方式
		:return: 返回新创建的复选框对象
		"""
		try:
			if parent is None:
				parent = self.central_widget
			checkbox = QCheckBox(text, parent)

			# 设置初始状态
			checkbox.setChecked(checked)
			checkbox.setTristate(tristate)

			# 设置尺寸约束
			if min_size:
				checkbox.setMinimumSize(*min_size)
			if max_size:
				checkbox.setMaximumSize(*max_size)

			# 定位处理
			if self.positioning_mode == self.POSITIONING_MANUAL:
				if position:
					checkbox.move(*position)
				if size:
					checkbox.resize(*size)
			else:
				current_layout = self.layout_stack[-1]
				current_layout.addWidget(checkbox, stretch, alignment or Qt.AlignLeft)

			# 绑定事件
			if command and callable(command):
				checkbox.stateChanged.connect(command)

			return checkbox
		except Exception as e:
			self._handle_error(f"添加复选框时出错: {str(e)}")
			return None

	def check_checkbox(self, checkbox):
		try:
			if not isinstance(checkbox, QCheckBox):
				self._handle_error("参数必须是 QCheckBox 实例")
				return
			return checkbox.checkState()
		except Exception as e:
			self._handle_error(f"获取勾选组件bool值是出错: {str(e)}")

	def add_radio_button(self, parent=None, text="", checked=False, group=None,
						 command=None, position=None, size=None,
						 min_size=None, max_size=None, stretch=0, alignment=None):
		"""
		添加单选按钮

		:param text: 按钮文本
		:param checked: 初始选中状态
		:param group: 所属按钮组（QButtonGroup 对象）
		:param command: 点击时调用的函数
		:param position: 手动定位模式下的位置
		:param size: 手动定位模式下的大小
		:param min_size: 最小尺寸
		:param max_size: 最大尺寸
		:param stretch: 布局拉伸系数
		:param alignment: 对齐方式
		:return: 返回新创建的单选按钮对象
		"""
		try:
			if parent is None:
				parent = self.central_widget
			radio = QRadioButton(text, self.central_widget)

			# 设置初始状态
			radio.setChecked(checked)

			# 设置尺寸约束
			if min_size:
				radio.setMinimumSize(*min_size)
			if max_size:
				radio.setMaximumSize(*max_size)

			# 定位处理
			if self.positioning_mode == self.POSITIONING_MANUAL:
				if position:
					radio.move(*position)
				if size:
					radio.resize(*size)
			else:
				current_layout = self.layout_stack[-1]
				current_layout.addWidget(radio, stretch, alignment or Qt.AlignLeft)

			if group and isinstance(group, QButtonGroup):
				group.addButton(radio)

			# 绑定事件
			if command and callable(command):
				radio.toggled.connect(command)

			return radio
		except Exception as e:
			self._handle_error(f"添加单选按钮时出错: {str(e)}")
			return None

	def create_button_group(self):
		"""创建按钮组（用于管理单选按钮的互斥性）"""
		return QButtonGroup(self.central_widget)

	def add_scroll_area(self, parent=None, min_size=None, max_size=None,
						stretch=0, alignment=None, position=None, size=None, css=None):
		try:
			if parent is None:
				parent = self.central_widget
			area = QScrollArea(parent)

			content_widget = QWidget()
			area.setWidget(content_widget)
			area.setWidgetResizable(True)

			if min_size:
				area.setMinimumSize(*min_size)
			if max_size:
				area.setMaximumSize(*max_size)

			final_style = ""

			if css and isinstance(css, dict):
				for key, value in css.items():
					final_style += f"{key}: {value};"

			if final_style:
				area.setStyleSheet(final_style)

			# 定位处理
			if self.positioning_mode == self.POSITIONING_MANUAL:
				if position:
					area.move(*position)
				if size:
					area.resize(*size)
			else:
				current_layout = self.layout_stack[-1]
				current_layout.addWidget(area, stretch, alignment or Qt.AlignLeft)
			return content_widget
		except Exception as e:
			self._handle_error(f"创建滚动窗口时出错: {str(e)}")

	def get_status_bar(self):
		"""
		获取状态栏对象

		:return: 返回状态栏对象
		"""
		return self.main_window.statusBar()

	def run(self):
		"""
		:return: 应用程序退出代码
		"""
		try:
			self.logger.info("启动应用程序")
			self.main_window.show()
			return_code = self.app.exec_()
			self.logger.info(f"应用程序退出，返回代码: {return_code}")
			sys.exit(return_code)
		except Exception as e:
			self._handle_critical_error(f"运行应用程序时出错: {str(e)}")

	def __show_fake_bsod(self, path=0, more=0):
		"""

		:param path: 决定是否蓝屏
		:param more: 错误或教学性蓝屏
		:return:
		"""
		if path:
			if more == 1:
				self.logger.info("教学性调用，并非线程过多或栈溢出")
			else:
				self.logger.info("警告：怀疑线程过多，线程不应多余max(500,CPU核数*2)")
			return 0
		if more == 1:
			self.logger.info("教学性蓝屏，并非线程过多或栈溢出")
		else:
			self.logger.info("警告：怀疑线程过多，线程不应多余max(1000,CPU核数*2)")
		"""显示蓝屏窗口"""
		bsod = BSODWindow()
		bsod.show()

