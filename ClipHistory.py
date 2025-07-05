import sys
import os
import json
import threading
import time
import ctypes
import winreg
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, QLineEdit, QListWidgetItem, QMenu, QCheckBox, QScrollBar, QFrame)
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon
import pyperclip
import pystray
from pystray import MenuItem as TrayMenuItem
from PIL import Image, ImageDraw
import math

# Store history.json in AppData/ClipHistory for persistence across restarts and autostart
APPDATA_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'ClipHistory')
if not os.path.exists(APPDATA_DIR):
    os.makedirs(APPDATA_DIR)
DB_FILE = os.path.join(APPDATA_DIR, 'history.json')
APP_NAME = 'ClipHistory By R ! Y 4 Z'
AUTO_START_REG_PATH = r'Software\\Microsoft\\Windows\\CurrentVersion\\Run'
FONT_PATH = os.path.join(os.path.dirname(__file__), 'Poppins.ttf')
if not os.path.exists(FONT_PATH):
    FONT_PATH = None

# JSON-based history helper
class ClipboardHistory:
    def __init__(self, file=DB_FILE, max_entries=100):
        self.file = file
        self.max_entries = max_entries
        self._ensure_file()
    def _ensure_file(self):
        if not os.path.exists(self.file):
            with open(self.file, 'w', encoding='utf-8') as f:
                json.dump([], f)
    def add_entry(self, text):
        entries = self.get_entries()
        # Remove duplicates first
        entries = [e for e in entries if e != text]
        # Add new entry at the beginning
        entries.insert(0, text)
        # Limit to max_entries to prevent memory issues
        if len(entries) > self.max_entries:
            entries = entries[:self.max_entries]
        with open(self.file, 'w', encoding='utf-8') as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
    def get_entries(self, search=None):
        self._ensure_file()
        with open(self.file, 'r', encoding='utf-8') as f:
            entries = json.load(f)
        if search:
            entries = [e for e in entries if search.lower() in e.lower()]
        return entries
    def delete_entry(self, text):
        entries = self.get_entries()
        entries = [e for e in entries if e != text]
        with open(self.file, 'w', encoding='utf-8') as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
    def clear(self):
        with open(self.file, 'w', encoding='utf-8') as f:
            json.dump([], f)

class ClipboardManager(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)  # type: ignore
        self.setGeometry(200, 200, 500, 600)
        self.history = ClipboardHistory()
        self.tray_icon = None
        self.is_tray_minimized = False
        self.last_clipboard = ''
        self.status_timer = QtCore.QTimer()
        self.status_timer.setSingleShot(True)
        self.status_timer.timeout.connect(self.set_idle_status)
        self.drag_pos = None
        self.is_copying_from_program = False
        self.clipboard_check_count = 0  # Prevent excessive checking
        self.init_ui()
        self.load_history()
        self.setup_clipboard_monitor()
        self.setup_tray_icon()
        self.show()

    def init_ui(self):
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.title_bar = self.create_title_bar()
        main_layout.addWidget(self.title_bar)
        
        # Activity indicator above search bar
        self.activity_label = QtWidgets.QLabel('💤 Clipboard idle...')
        self.activity_label.setAlignment(Qt.AlignCenter)  # type: ignore
        self.activity_label.setStyleSheet('''
            QLabel {
                background: #000;
                color: #0dff00;
                border: 2px solid #0dff00;
                border-radius: 8px;
                padding: 8px;
                margin: 5px;
                font-family: Poppins, Arial, sans-serif;
                font-size: 14px;
                font-weight: bold;
            }
        ''')
        main_layout.addWidget(self.activity_label)
        
        search_layout = QtWidgets.QHBoxLayout()
        self.search_box = QtWidgets.QLineEdit()
        self.search_box.setPlaceholderText('🔍 Search clipboard history...')
        self.search_box.textChanged.connect(self.on_search)
        search_layout.addWidget(self.search_box)
        main_layout.addLayout(search_layout)
        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # type: ignore
        self.list_widget.itemDoubleClicked.connect(self.copy_item)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)  # type: ignore
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        # Optimize scrolling performance
        self.list_widget.setUniformItemSizes(False)
        self.list_widget.setSpacing(2)
        self.list_widget.setResizeMode(QtWidgets.QListView.Adjust)
        self.list_widget.setViewMode(QtWidgets.QListView.ListMode)
        # Ensure scrollbar shows when needed
        self.list_widget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)  # type: ignore
        self.list_widget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)  # type: ignore
        # Disable animations for better performance
        self.list_widget.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        main_layout.addWidget(self.list_widget)
        btn_layout = QtWidgets.QHBoxLayout()
        self.clear_btn = QtWidgets.QPushButton('🧼 Clear History')
        self.clear_btn.clicked.connect(self.clear_history)
        btn_layout.addWidget(self.clear_btn)
        self.about_btn = QtWidgets.QPushButton('ℹ️ About Me')
        self.about_btn.clicked.connect(self.show_about)
        btn_layout.addWidget(self.about_btn)
        self.auto_start_cb = QtWidgets.QCheckBox('🔁 Auto start on Windows boot')
        self.auto_start_cb.setChecked(self.is_auto_start_enabled())
        self.auto_start_cb.stateChanged.connect(self.toggle_auto_start)
        btn_layout.addWidget(self.auto_start_cb)
        main_layout.addLayout(btn_layout)
        self.apply_styles()
        self.setLayout(main_layout)

    def create_title_bar(self):
        bar = QtWidgets.QFrame(self)
        bar.setFixedHeight(40)
        bar.setStyleSheet('background: #000; border-bottom: 2px solid #0dff00;')
        layout = QtWidgets.QHBoxLayout(bar)
        layout.setContentsMargins(10, 0, 10, 0)
        self.title_label = QtWidgets.QLabel('🗂️ ClipHistory By R ! Y 4 Z')
        font = QtGui.QFont()
        if FONT_PATH and os.path.exists(FONT_PATH):
            font.setFamily('Poppins')
        else:
            font.setFamily('Arial')
        font.setPointSize(14)
        self.title_label.setFont(font)
        self.title_label.setStyleSheet('color: #0dff00; letter-spacing: 2px;')
        layout.addWidget(self.title_label)
        layout.addStretch()
        self.min_btn = QtWidgets.QPushButton('➖')
        self.min_btn.setFixedSize(30, 30)
        self.min_btn.clicked.connect(self.showMinimized)
        self.min_btn.setStyleSheet('background: #000; color: #0dff00; border: none;')
        layout.addWidget(self.min_btn)
        self.close_btn = QtWidgets.QPushButton('❌')
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.clicked.connect(self.minimize_to_tray)
        self.close_btn.setStyleSheet('background: #000; color: #0dff00; border: none;')
        layout.addWidget(self.close_btn)
        bar.setLayout(layout)
        return bar

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.childAt(event.pos()) == self.title_bar:  # type: ignore
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.drag_pos and event.buttons() == Qt.LeftButton:  # type: ignore
            self.move(event.globalPos() - self.drag_pos)
            event.accept()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.drag_pos = None
        super().mouseReleaseEvent(event)

    def apply_styles(self):
        self.setStyleSheet('''
            QWidget {
                background: #000;
                color: #0dff00;
                font-family: Poppins, Arial, sans-serif;
            }
            QListWidget {
                background: #000;
                border: 2px solid #0dff00;
                font-size: 13px;
                color: #0dff00;
                font-family: Poppins, Arial, sans-serif;
                outline: none;
                selection-background-color: #0dff00;
                selection-color: #000;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #0dff00;
                background: transparent;
            }
            QListWidget::item:selected {
                background: #0dff00;
                color: #000;
            }
            QListWidget::item:hover {
                background: rgba(13, 255, 0, 0.2);
            }
            QLineEdit {
                background: #000;
                border: 2px solid #0dff00;
                color: #0dff00;
                font-family: Poppins, Arial, sans-serif;
                font-size: 13px;
            }
            QPushButton {
                background: #000;
                color: #0dff00;
                border: 2px solid #0dff00;
                border-radius: 8px;
                padding: 5px 10px;
                font-family: Poppins, Arial, sans-serif;
            }
            QPushButton:hover {
                background: #0dff00;
                color: #000;
            }
            QCheckBox {
                color: #0dff00;
                font-family: Poppins, Arial, sans-serif;
                spacing: 12px;
            }
            QCheckBox::indicator {
                width: 22px;
                height: 22px;
                border: 2px solid #0dff00;
                border-radius: 6px;
                background: #000;
            }
            QCheckBox::indicator:checked {
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.8, fx:0.5, fy:0.5, stop:0 #0dff00, stop:1 #000);
                border: 2px solid #0dff00;
            }
            QLabel {
                font-family: Poppins, Arial, sans-serif;
                color: #0dff00;
            }
            QScrollBar:vertical {
                background: #000;
                width: 16px;
                border: 1px solid #0dff00;
                border-radius: 8px;
            }
            QScrollBar::handle:vertical {
                background: #0dff00;
                min-height: 20px;
                border-radius: 8px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #00cc00;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                background: transparent;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        ''')

    def setup_clipboard_monitor(self):
        self.clipboard_timer = QtCore.QTimer()
        self.clipboard_timer.timeout.connect(self.check_clipboard)
        self.clipboard_timer.start(1000)  # Check every 1 second instead of 500ms

    def check_clipboard(self):
        try:
            # Prevent excessive checking
            self.clipboard_check_count += 1
            if self.clipboard_check_count % 2 == 0:  # Only check every other time
                return
                
            text = pyperclip.paste()
            if text and text != self.last_clipboard and not self.is_copying_from_program:
                # Check if text is not empty and not just whitespace
                if text.strip():
                    self.last_clipboard = text
                    # Check if text is already in the list efficiently
                    current_items = [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
                    if text not in current_items:
                        self.history.add_entry(text)
                        self.add_list_item(text, top=True)
                        self.set_status('📋 New text detected!')
        except Exception:
            pass

    def load_history(self, search=None):
        # Block signals during loading to prevent UI updates
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        entries = self.history.get_entries(search)
        # Limit display to prevent UI lag
        for text in entries[:50]:  # Only show first 50 items in UI
            self.add_list_item(text)
        # Unblock signals after loading
        self.list_widget.blockSignals(False)

    def add_list_item(self, text, top=False):
        item = QtWidgets.QListWidgetItem(text)
        # Set item flags for better performance (use correct Qt enums)
        item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)  # type: ignore
        if top:
            self.list_widget.insertItem(0, item)
            # Remove oldest item if list gets too long
            if self.list_widget.count() > 50:
                self.list_widget.takeItem(self.list_widget.count() - 1)
        else:
            self.list_widget.addItem(item)

    def on_search(self, text):
        # Add a small delay to prevent excessive searching while typing
        if hasattr(self, 'search_timer'):
            self.search_timer.stop()
        else:
            self.search_timer = QtCore.QTimer()
            self.search_timer.setSingleShot(True)
            self.search_timer.timeout.connect(lambda: self.perform_search(text))
        self.search_timer.start(300)  # 300ms delay

    def perform_search(self, text):
        if text.strip():
            self.set_status(f'🔍 Searching for: "{text}"')
        else:
            self.set_status('🔍 Showing all items')
        self.load_history(search=text)

    def set_status(self, message, timeout=2000):
        self.activity_label.setText(message)
        # Start eye-catching animation
        self.start_activity_animation()
        self.status_timer.start(timeout)

    def start_activity_animation(self):
        # Create pulsing/glowing animation
        self.animation_timer = QtCore.QTimer()
        self.animation_timer.timeout.connect(self.animate_activity)
        self.animation_step = 0
        self.animation_timer.start(50)  # 50ms intervals for smooth animation

    def animate_activity(self):
        self.animation_step += 1
        if self.animation_step > 20:  # Stop after 1 second (20 * 50ms)
            self.animation_timer.stop()
            self.activity_label.setStyleSheet('''
                QLabel {
                    background: #000;
                    color: #0dff00;
                    border: 2px solid #0dff00;
                    border-radius: 8px;
                    padding: 8px;
                    margin: 5px;
                    font-family: Poppins, Arial, sans-serif;
                    font-size: 14px;
                    font-weight: bold;
                }
            ''')
            return
        
        # Create pulsing effect with color transitions
        intensity = abs(math.sin(self.animation_step * 0.3)) * 255
        glow_color = f'rgb({int(13 * intensity / 255)}, {int(255 * intensity / 255)}, {int(0)})'
        shadow_color = f'rgb({int(13 * intensity / 255)}, {int(255 * intensity / 255)}, {int(0)})'
        
        self.activity_label.setStyleSheet(f'''
            QLabel {{
                background: #000;
                color: {glow_color};
                border: 3px solid {glow_color};
                border-radius: 8px;
                padding: 8px;
                margin: 5px;
                font-family: Poppins, Arial, sans-serif;
                font-size: 14px;
                font-weight: bold;
                text-shadow: 0 0 10px {shadow_color};
            }}
        ''')

    def set_idle_status(self):
        self.activity_label.setText('💤 Clipboard idle...')
        # Reset to normal styling
        self.activity_label.setStyleSheet('''
            QLabel {
                background: #000;
                color: #0dff00;
                border: 2px solid #0dff00;
                border-radius: 8px;
                padding: 8px;
                margin: 5px;
                font-family: Poppins, Arial, sans-serif;
                font-size: 14px;
                font-weight: bold;
            }
        ''')

    def copy_item(self, item):
        text = item.text()
        self.is_copying_from_program = True
        pyperclip.copy(text)
        self.set_status('📋 Text copied to clipboard!')
        QtCore.QTimer.singleShot(1000, self.reset_copy_flag)  # Increased delay to 1 second

    def reset_copy_flag(self):
        self.is_copying_from_program = False

    def show_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if not item:
            return
        menu = QtWidgets.QMenu()
        copy_action = menu.addAction('📋 Copy')
        delete_action = menu.addAction('🗑️ Delete')
        action = menu.exec_(self.list_widget.mapToGlobal(pos))
        if action == copy_action:
            self.copy_item(item)
        elif action == delete_action:
            self.delete_item(item)

    def delete_item(self, item):
        text = item.text()
        self.history.delete_entry(text)
        self.list_widget.takeItem(self.list_widget.row(item))
        self.set_status('🗑️ Item removed from history!')

    def clear_history(self):
        self.history.clear()
        self.list_widget.clear()
        self.set_status('🧼 All history cleared!')

    def show_about(self):
        self.set_status('ℹ️ About dialog opened')
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle('About Me')
        dialog.setFixedSize(500, 400)
        layout = QtWidgets.QVBoxLayout(dialog)
        label = QtWidgets.QLabel('R ! Y 4 Z')
        # Use Poppins if available, else fallback
        if FONT_PATH and os.path.exists(FONT_PATH):
            font = QtGui.QFont()
            font.setFamily('Poppins')
            font.setPointSize(28)
            font.setBold(True)
        else:
            font = QtGui.QFont('Arial', 28, QtGui.QFont.Bold)
        label.setFont(font)
        label.setAlignment(Qt.AlignCenter)  # type: ignore
        label.setStyleSheet('color: #0dff00; text-shadow: 0 0 10px #0dff00;')
        layout.addWidget(label)
        emoji_label = QtWidgets.QLabel('👾🗂️🤖✨')
        emoji_label.setAlignment(Qt.AlignCenter)  # type: ignore
        emoji_label.setStyleSheet('font-size: 24px; color: #0dff00;')
        layout.addWidget(emoji_label)
        # Features section
        features = QtWidgets.QLabel('''<b>🗂️ ClipHistory Features:</b><br><ul style="color:#0dff00;">
<li>📋 <b>Real-time Clipboard Monitoring</b>: Instantly detects and saves copied text.</li>
<li>💾 <b>Persistent History</b>: All clipboard items are saved even after restart.</li>
<li>🔍 <b>Search</b>: Filter your clipboard history by keyword.</li>
<li>🖱️ <b>Quick Actions</b>: Double-click to copy, right-click for copy/delete menu.</li>
<li>🧹 <b>Clear History</b>: One-click to erase all clipboard items.</li>
<li>🔁 <b>Auto-Start</b>: Option to launch ClipHistory on Windows boot.</li>
<li>🗑️ <b>Delete</b>: Remove individual items with right-click.</li>
<li>🧑‍💻 <b>Custom Sci-Fi UI</b>: Futuristic green/black theme, custom title bar, and styled controls.</li>
<li>🗂️ <b>Minimize to Tray</b>: Hides to tray instead of closing, with tray menu.</li>
<li>ℹ️ <b>About Me</b>: Animated RGB name and program info.</li>
</ul>''')
        features.setStyleSheet('color: #0dff00; font-size: 14px; font-family: Poppins, Arial, sans-serif; background: #000; border: 1px solid #0dff00; border-radius: 8px; padding: 10px;')
        features.setAlignment(Qt.AlignLeft | Qt.AlignTop)  # type: ignore
        layout.addWidget(features)
        # Animate RGB glow
        self.rgb_timer = QtCore.QTimer(dialog)
        self.rgb_hue = 0
        def animate():
            self.rgb_hue = (self.rgb_hue + 2) % 360
            color = QtGui.QColor()
            color.setHsv(self.rgb_hue, 255, 255)
            label.setStyleSheet(f'color: {color.name()}; text-shadow: 0 0 20px {color.name()};')
        self.rgb_timer.timeout.connect(animate)
        self.rgb_timer.start(30)
        dialog.exec_()
        self.rgb_timer.stop()

    def is_auto_start_enabled(self):
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTO_START_REG_PATH, 0, winreg.KEY_READ) as key:
                value, _ = winreg.QueryValueEx(key, APP_NAME)
                exe_path = sys.executable
                return exe_path in value
        except Exception:
            return False

    def toggle_auto_start(self, state):
        exe_path = sys.executable
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTO_START_REG_PATH, 0, winreg.KEY_SET_VALUE) as key:
                if state == Qt.Checked:  # type: ignore
                    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path + ' "' + os.path.abspath(__file__) + '"')
                    self.set_status('🔁 Auto-start enabled!')
                else:
                    winreg.DeleteValue(key, APP_NAME)
                    self.set_status('🔁 Auto-start disabled!')
        except Exception:
            self.set_status('❌ Failed to update auto-start')

    def setup_tray_icon(self):
        image = Image.new('RGB', (64, 64), color=(0, 0, 0))  # type: ignore
        draw = ImageDraw.Draw(image)
        draw.rectangle([8, 24, 56, 40], fill='#0dff00')
        draw.rectangle([20, 16, 44, 24], fill='#0dff00')
        draw.rectangle([24, 40, 40, 48], fill='#0dff00')
        draw.rectangle([12, 28, 52, 36], fill=(0, 0, 0))
        menu = (
            TrayMenuItem('⚙️ Show Program', self.restore_from_tray),
            TrayMenuItem('🗂️ About', self.show_about),
            TrayMenuItem('🛑 Exit', self.exit_from_tray)
        )
        self.tray_icon = pystray.Icon(APP_NAME, image, APP_NAME, menu, on_activate=lambda icon: self.restore_from_tray())
        self.tray_icon.run_detached()
        self.tray_icon.visible = False

    def minimize_to_tray(self):
        self.hide()
        if self.tray_icon:
            self.tray_icon.visible = True
        self.is_tray_minimized = True
        self.set_status('🗂️ Minimized to tray')

    def restore_from_tray(self, *args):
        self.showNormal()
        self.activateWindow()
        if self.tray_icon:
            self.tray_icon.visible = False
        self.is_tray_minimized = False
        self.set_status('🗂️ Restored from tray')

    def exit_from_tray(self, *args):
        if self.tray_icon:
            self.tray_icon.stop()
        QtWidgets.QApplication.quit()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = ClipboardManager()
    sys.exit(app.exec_())
