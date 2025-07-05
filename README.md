# 🗂️ ClipHistory - Advanced Clipboard Manager

A feature-rich, sci-fi themed clipboard manager for Windows with real-time monitoring, persistent history, and eye-catching animations.

![ClipHistory](https://img.shields.io/badge/Status-Ready-green) ![Python](https://img.shields.io/badge/Python-3.7+-blue) ![Windows](https://img.shields.io/badge/Platform-Windows-lightgrey)

## ✨ Features

### 🎯 Core Functionality
- **📋 Real-time Clipboard Monitoring**: Instantly detects and saves copied text
- **💾 Persistent History**: All clipboard items saved in AppData, survives restarts
- **🔍 Smart Search**: Filter clipboard history by keyword with real-time feedback
- **🖱️ Quick Actions**: Double-click to copy, right-click for context menu
- **🗑️ Individual Delete**: Remove specific items with right-click menu
- **🧹 Clear All**: One-click to erase entire clipboard history

### 🎨 User Interface
- **🧑‍💻 Sci-Fi Theme**: Futuristic green/black color scheme (#0dff00/#000)
- **🎭 Custom Title Bar**: Draggable sci-fi styled title bar
- **📊 Activity Indicator**: Eye-catching animated status messages
- **🎪 Smooth Animations**: Pulsing glow effects for all activities
- **📜 Custom Scrollbar**: Styled scrollbar matching the theme
- **🔤 Poppins Font**: Modern typography throughout the interface

### 🗂️ System Integration
- **🗂️ Tray Integration**: Minimize to system tray instead of closing
- **🔄 Auto-Start**: Option to launch on Windows boot
- **🎯 Double-Click Restore**: Restore window by double-clicking tray icon
- **⚙️ Tray Menu**: Quick access to show/hide and exit

### 🚀 Performance & Optimization
- **⚡ Memory Efficient**: Limited to 100 entries to prevent bloat
- **🎯 Smart Polling**: Optimized clipboard checking (1-second intervals)
- **🔄 Duplicate Prevention**: No duplicate entries in history
- **📱 Responsive UI**: Smooth scrolling and interactions
- **💾 JSON Storage**: Lightweight, human-readable history format

## 🖼️ Screenshots

*[Screenshots will be added here showing the main interface, activity animations, and tray integration]*

## 📦 Installation

### Option 1: Download Pre-built Executable
1. Download `ClipHistory.exe` from the [Releases](https://github.com/yourusername/ClipHistory/releases) page
2. Run the executable - no installation required
3. The app will create its data folder automatically

### Option 2: Build from Source
```bash
# Clone the repository
git clone https://github.com/yourusername/ClipHistory.git
cd ClipHistory

# Install dependencies
pip install -r requirements.txt

# Build executable
pyinstaller --noconfirm --onefile --windowed --icon=logo.ico --add-data "Poppins.ttf;." ClipHistory.py
```

## 🎮 Usage

### Basic Operations
1. **Copy Text**: Simply copy text from any application - it's automatically detected and saved
2. **View History**: All copied items appear in the main list
3. **Copy from History**: Double-click any item to copy it back to clipboard
4. **Search**: Use the search bar to filter clipboard history
5. **Delete**: Right-click any item and select "🗑️ Delete"

### Advanced Features
- **Minimize to Tray**: Click the ❌ button to minimize to system tray
- **Restore from Tray**: Double-click the tray icon to restore the window
- **Auto-Start**: Check the "🔁 Auto start on Windows boot" option
- **Clear History**: Click "🧼 Clear History" to erase all saved items

### Activity Status Messages
The app shows animated status messages for all actions:
- 📋 "New text detected!" - When new text is copied
- 📋 "Text copied to clipboard!" - When copying from history
- 🔍 "Searching for: 'keyword'" - When searching
- 🗑️ "Item removed from history!" - When deleting items
- 🧼 "All history cleared!" - When clearing history
- 🗂️ "Minimized to tray" / "Restored from tray" - Window actions
- 🔁 "Auto-start enabled/disabled!" - Auto-start changes

## 🛠️ Requirements

- **OS**: Windows 10/11
- **Python**: 3.7+ (for building from source)
- **Dependencies**: PyQt5, pyperclip, pystray, pillow

## 📁 File Structure

```
ClipHistory/
├── ClipHistory.py          # Main application
├── requirements.txt        # Python dependencies
├── logo.ico              # Application icon
├── Poppins.ttf          # Custom font
├── README.md            # This file
└── dist/
    └── ClipHistory.exe  # Built executable
```

## 🔧 Configuration

### Data Storage
Clipboard history is stored in:
```
%APPDATA%/ClipHistory/history.json
```

### Auto-Start Registry
Auto-start settings are stored in:
```
HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run
```

## 🎨 Customization

### Theme Colors
The app uses a sci-fi green/black theme:
- **Primary Green**: `#0dff00`
- **Background**: `#000000`
- **Accent**: `#00cc00` (hover states)

### Font
- **Primary**: Poppins (bundled)
- **Fallback**: Arial

## 🚀 Development

### Building the Executable
```bash
# Install PyInstaller
pip install pyinstaller

# Build with custom icon and font
pyinstaller --noconfirm --onefile --windowed --icon=logo.ico --add-data "Poppins.ttf;." ClipHistory.py
```

### Key Components
- **ClipboardHistory**: JSON-based storage class
- **ClipboardManager**: Main PyQt5 application window
- **Activity Animation**: Pulsing glow effects for status messages
- **Tray Integration**: System tray functionality with pystray

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **R ! Y 4 Z** - Original developer
- **Google Fonts** - Poppins font
- **PyQt5** - GUI framework
- **pystray** - System tray integration

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/ClipHistory/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/ClipHistory/discussions)
- **Email**: your.email@example.com

---

**Made with ❤️ by R ! Y 4 Z**

*"The future of clipboard management is here"* 
