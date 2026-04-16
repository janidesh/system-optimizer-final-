import sys
import os
import shutil
import psutil
import ctypes
import time
import subprocess
import webbrowser
import platform
import winreg
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QProgressBar, 
                               QSplashScreen, QFrame, QStackedWidget, QScrollArea, 
                               QGridLayout, QSystemTrayIcon, QMenu, QStyle, 
                               QCheckBox, QSizePolicy)
from PySide6.QtCore import Qt, QTimer, QPoint, QSize, Signal
from PySide6.QtGui import QFont, QColor, QPalette, QPixmap, QPainter, QPen, QIcon, QCursor

# ==============================================================================
# --- ADVANCED OPTIMIZATION & SYSTEM TOOLS ---
# ==============================================================================
class OptimizationTools:
    @staticmethod
    def clean_ram():
        """Cleans working set RAM from active processes."""
        count = 0
        for proc in psutil.process_iter():
            try:
                handle = ctypes.windll.kernel32.OpenProcess(0x001F0FFF, False, proc.pid)
                if handle:
                    ctypes.windll.psapi.EmptyWorkingSet(handle)
                    ctypes.windll.kernel32.CloseHandle(handle)
                    count += 1
            except: continue
        return count

    @staticmethod
    def execute_tweak(command):
        """Executes system commands silently in the background."""
        try:
            # CREATE_NO_WINDOW flag = 0x08000000 hides the CMD console
            subprocess.Popen(command, shell=True, creationflags=0x08000000)
            return True
        except Exception:
            return False

    @staticmethod
    def kill_not_responding():
        """Force kills any process stuck in a 'Not Responding' state."""
        try:
            subprocess.Popen('taskkill /F /FI "STATUS eq NOT RESPONDING"', shell=True, creationflags=0x08000000)
            return True
        except Exception:
            return False

    @staticmethod
    def get_app_path():
        """Returns the appropriate path for registry execution depending on script/exe."""
        app_path = os.path.abspath(sys.argv[0])
        if app_path.endswith('.py'):
            return f'"{sys.executable}" "{app_path}"'
        return f'"{app_path}"'

    # --- STARTUP REGISTRY LOGIC ---
    @staticmethod
    def is_startup_enabled():
        """Checks if the app is currently in the startup registry."""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, 'JDR_PC_Optimizer')
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return False

    @staticmethod
    def toggle_startup(enable):
        """Adds or removes the application from the Windows Startup Registry."""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, winreg.KEY_SET_VALUE)
            if enable:
                winreg.SetValueEx(key, 'JDR_PC_Optimizer', 0, winreg.REG_SZ, OptimizationTools.get_app_path())
            else:
                winreg.DeleteValue(key, 'JDR_PC_Optimizer')
            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"Startup Registry Error: {e}")
            return False

    # --- CONTEXT MENU REGISTRY LOGIC ---
    @staticmethod
    def is_context_menu_enabled():
        """Checks if the app is currently in the desktop context menu."""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\Directory\Background\shell\JDR_Optimizer")
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return False

    @staticmethod
    def toggle_context_menu(enable):
        """Adds or removes the application from the desktop right-click menu."""
        base_path = r"Software\Classes\Directory\Background\shell\JDR_Optimizer"
        try:
            if enable:
                # Create main key
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, base_path)
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "Open PC Optimizer")
                
                # Try to add an icon if running as an exe
                app_path = os.path.abspath(sys.argv[0])
                icon_path = app_path if not app_path.endswith('.py') else sys.executable
                winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, f'"{icon_path}"')
                
                # Create command subkey
                cmd_key = winreg.CreateKey(key, "command")
                winreg.SetValueEx(cmd_key, "", 0, winreg.REG_SZ, OptimizationTools.get_app_path())
                
                winreg.CloseKey(cmd_key)
                winreg.CloseKey(key)
            else:
                # Must delete subkeys before deleting parent key in Windows Registry
                try: winreg.DeleteKey(winreg.HKEY_CURRENT_USER, base_path + r"\command")
                except: pass
                try: winreg.DeleteKey(winreg.HKEY_CURRENT_USER, base_path)
                except: pass
            return True
        except Exception as e:
            print(f"Context Menu Registry Error: {e}")
            return False

# ==============================================================================
# --- 100 SYSTEM TWEAKS REGISTRY ---
# ==============================================================================
SYSTEM_TWEAKS = {
    # CATEGORY 1: NETWORK & INTERNET
    "Flush DNS Cache": 'ipconfig /flushdns',
    "Release IP Address": 'ipconfig /release',
    "Renew IP Address": 'ipconfig /renew',
    "Reset Winsock Catalog": 'netsh winsock reset',
    "Reset TCP/IP Stack": 'netsh int ip reset',
    "Clear ARP Cache": 'arp -d *',
    "Reset Windows Firewall Rules": 'netsh advfirewall reset',
    "Disable Network Throttling": 'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v NetworkThrottlingIndex /t REG_DWORD /d 4294967295 /f',
    "Enable Network Throttling": 'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile" /v NetworkThrottlingIndex /t REG_DWORD /d 10 /f',
    "Force Sync Windows Time": 'w32tm /resync /force',

    # CATEGORY 2: SYSTEM CLEANUP & CACHE
    "Clear Current User Temp": 'del /q /f /s "%TEMP%\\*"',
    "Clear Windows System Temp": 'del /q /f /s "C:\\Windows\\Temp\\*"',
    "Clear Prefetch Cache": 'del /q /f /s "C:\\Windows\\Prefetch\\*"',
    "Clear Windows Update Cache": 'del /q /f /s "C:\\Windows\\SoftwareDistribution\\Download\\*"',
    "Empty Recycle Bin": 'rd /s /q %systemdrive%\\$Recycle.bin',
    "Clear Thumbnail Cache": 'del /f /s /q /a "%LocalAppData%\\Microsoft\\Windows\\Explorer\\thumbcache_*.db"',
    "Clear Icon Cache": 'del /f /s /q /a "%LocalAppData%\\IconCache.db"',
    "Clear Font Cache": 'del /f /s /q /a "%WinDir%\\ServiceProfiles\\LocalService\\AppData\\Local\\FontCache\\*FontCache*"',
    "Clear DirectX Shader Cache": 'del /q /f /s "%LocalAppData%\\D3DSCache\\*"',
    "Run Basic Disk Cleanup (Silent)": 'cleanmgr /sagerun:1',

    # CATEGORY 3: WINDOWS EXPLORER & WORKFLOW
    "Show Hidden Files": 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v Hidden /t REG_DWORD /d 1 /f',
    "Hide Hidden Files": 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v Hidden /t REG_DWORD /d 2 /f',
    "Show File Extensions": 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v HideFileExt /t REG_DWORD /d 0 /f',
    "Hide File Extensions": 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v HideFileExt /t REG_DWORD /d 1 /f',
    "Launch Explorer to This PC": 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v LaunchTo /t REG_DWORD /d 1 /f',
    "Launch Explorer to Quick Access": 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v LaunchTo /t REG_DWORD /d 2 /f',
    "Disable Aero Shake": 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v DisallowShaking /t REG_DWORD /d 1 /f',
    "Enable Aero Shake": 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v DisallowShaking /t REG_DWORD /d 0 /f',
    "Show Taskbar Seconds": 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v ShowSecondsInSystemClock /t REG_DWORD /d 1 /f',
    "Hide Taskbar Seconds": 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v ShowSecondsInSystemClock /t REG_DWORD /d 0 /f',

    # CATEGORY 4: VISUAL EFFECTS & ANIMATIONS
    "Disable Windows Transparency": 'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize" /v EnableTransparency /t REG_DWORD /d 0 /f',
    "Enable Windows Transparency": 'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize" /v EnableTransparency /t REG_DWORD /d 1 /f',
    "Disable Window Animations": 'reg add "HKCU\\Control Panel\\Desktop" /v UserPreferencesMask /t REG_BINARY /d 9012038010000000 /f',
    "Enable Window Animations": 'reg add "HKCU\\Control Panel\\Desktop" /v UserPreferencesMask /t REG_BINARY /d 9e3e078012000000 /f',
    "Disable Taskbar Animations": 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v TaskbarAnimations /t REG_DWORD /d 0 /f',
    "Enable Taskbar Animations": 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v TaskbarAnimations /t REG_DWORD /d 1 /f',
    "Disable Menu Shadows": 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v ListviewShadow /t REG_DWORD /d 0 /f',
    "Enable Menu Shadows": 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v ListviewShadow /t REG_DWORD /d 1 /f',
    "Disable Lock Screen Background": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Personalization" /v NoLockScreen /t REG_DWORD /d 1 /f',
    "Enable Lock Screen Background": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Personalization" /v NoLockScreen /t REG_DWORD /d 0 /f',

    # CATEGORY 5: PRIVACY & TELEMETRY
    "Disable App Telemetry": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f',
    "Disable Cortana": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search" /v AllowCortana /t REG_DWORD /d 0 /f',
    "Disable Location Tracking": 'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\CapabilityAccessManager\\ConsentStore\\location" /v Value /t REG_SZ /d Deny /f',
    "Disable Activity History": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\System" /v PublishUserActivities /t REG_DWORD /d 0 /f',
    "Disable Advertising ID": 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\AdvertisingInfo" /v Enabled /t REG_DWORD /d 0 /f',
    "Disable Tailored Experiences": 'reg add "HKCU\\Software\\Policies\\Microsoft\\Windows\\CloudContent" /v DisableTailoredExperiencesWithDiagnosticData /t REG_DWORD /d 1 /f',
    "Disable Feedback Prompts": 'reg add "HKCU\\Software\\Microsoft\\Siuf\\Rules" /v NumberOfSIUFInPeriod /t REG_DWORD /d 0 /f',
    "Disable Typing Insights": 'reg add "HKCU\\Software\\Microsoft\\Input\\TIPC" /v Enabled /t REG_DWORD /d 0 /f',
    "Disable Web Search in Start Menu": 'reg add "HKCU\\SOFTWARE\\Policies\\Microsoft\\Windows\\Explorer" /v DisableSearchBoxSuggestions /t REG_DWORD /d 1 /f',
    "Disable Wi-Fi Sense": 'reg add "HKLM\\SOFTWARE\\Microsoft\\WcmSvc\\wifinetworkmanager\\config" /v AutoConnectAllowedOEM /t REG_DWORD /d 0 /f',

    # CATEGORY 6: WINDOWS SERVICES
    "Disable SysMain (Superfetch)": 'sc config SysMain start=disabled & net stop SysMain',
    "Enable SysMain (Superfetch)": 'sc config SysMain start=auto & net start SysMain',
    "Disable Windows Search Indexing": 'sc config WSearch start=disabled & net stop WSearch',
    "Enable Windows Search Indexing": 'sc config WSearch start=delayed-auto & net start WSearch',
    "Disable Print Spooler": 'sc config Spooler start=disabled & net stop Spooler',
    "Enable Print Spooler": 'sc config Spooler start=auto & net start Spooler',
    "Disable Fax Service": 'sc config Fax start=disabled & net stop Fax',
    "Disable Downloaded Maps Manager": 'sc config MapsBroker start=disabled & net stop MapsBroker',
    "Disable Touch Keyboard Service": 'sc config TabletInputService start=disabled & net stop TabletInputService',
    "Disable Windows Error Reporting": 'sc config WerSvc start=disabled & net stop WerSvc',

    # CATEGORY 7: GAMING & XBOX
    "Enable Game Mode": 'reg add "HKCU\\Software\\Microsoft\\GameBar" /v AllowAutoGameMode /t REG_DWORD /d 1 /f',
    "Disable Game Mode": 'reg add "HKCU\\Software\\Microsoft\\GameBar" /v AllowAutoGameMode /t REG_DWORD /d 0 /f',
    "Disable Xbox Game Bar": 'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\GameDVR" /v AppCaptureEnabled /t REG_DWORD /d 0 /f',
    "Enable Xbox Game Bar": 'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\GameDVR" /v AppCaptureEnabled /t REG_DWORD /d 1 /f',
    "Disable Xbox Accessory Management": 'sc config XboxGipSvc start=disabled & net stop XboxGipSvc',
    "Enable Xbox Accessory Management": 'sc config XboxGipSvc start=demand & net start XboxGipSvc',
    "Disable Xbox Live Auth Manager": 'sc config XblAuthManager start=disabled & net stop XblAuthManager',
    "Disable Xbox Live Game Save": 'sc config XblGameSave start=disabled & net stop XblGameSave',
    "Disable Xbox Live Networking": 'sc config XboxNetApiSvc start=disabled & net stop XboxNetApiSvc',
    "Disable Fullscreen Optimizations": 'reg add "HKCU\\System\\GameConfigStore" /v GameDVR_FSEBehaviorMode /t REG_DWORD /d 2 /f',

    # CATEGORY 8: POWER & PERFORMANCE
    "Enable Ultimate Performance": 'powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61',
    "Set High Performance Plan": 'powercfg -setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c',
    "Set Balanced Power Plan": 'powercfg -setactive 381b4222-f694-41f0-9685-ff5bb260df2e',
    "Set Power Saver Plan": 'powercfg -setactive a1841308-3541-4fab-bc81-f71556f20b4a',
    "Disable Hibernation (Frees Space)": 'powercfg -h off',
    "Enable Hibernation": 'powercfg -h on',
    "Enable Fast Startup": 'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power" /v HiberbootEnabled /t REG_DWORD /d 1 /f',
    "Disable Fast Startup": 'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power" /v HiberbootEnabled /t REG_DWORD /d 0 /f',
    "Prioritize Foreground Apps": 'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\PriorityControl" /v Win32PrioritySeparation /t REG_DWORD /d 38 /f',
    "Prioritize Background Services": 'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\PriorityControl" /v Win32PrioritySeparation /t REG_DWORD /d 24 /f',

    # CATEGORY 9: QUICK FIXES & RESTARTS
    "Restart Windows Explorer": 'taskkill /f /im explorer.exe & start explorer.exe',
    "Restart Audio Service": 'net stop audiosrv & net start audiosrv',
    "Restart Print Spooler": 'net stop spooler & net start spooler',
    "Restart Windows Update Service": 'net stop wuauserv & net start wuauserv',
    "Restart Network Connections": 'net stop netman & net start netman',
    "Force Update Group Policies": 'gpupdate /force',
    "Clear Clipboard History": 'cmd /c "echo off | clip"',
    "Reset Windows Store Cache": 'wsreset.exe',
    "Run System Event Log Cleanser": 'for /F "tokens=*" %1 in (\'wevtutil.exe el\') DO wevtutil.exe cl "%1"',
    "Kill All Not Responding Apps": 'taskkill /F /FI "STATUS eq NOT RESPONDING"',

    # CATEGORY 10: ADVANCED SYSTEM SETTINGS
    "Disable Background Apps Globally": 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\BackgroundAccessApplications" /v GlobalUserDisabled /t REG_DWORD /d 1 /f',
    "Enable Background Apps Globally": 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\BackgroundAccessApplications" /v GlobalUserDisabled /t REG_DWORD /d 0 /f',
    "Disable Startup Delay": 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Serialize" /v StartupDelayInMSec /t REG_DWORD /d 0 /f',
    "Disable Auto Windows Restarts": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate\\AU" /v NoAutoRebootWithLoggedOnUsers /t REG_DWORD /d 1 /f',
    "Enable Classic Context Menu (W11)": 'reg add "HKCU\\Software\\Classes\\CLSID\\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\\InprocServer32" /f /ve',
    "Restore Default Context Menu (W11)": 'reg delete "HKCU\\Software\\Classes\\CLSID\\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}" /f',
    "Disable USB Selective Suspend": 'powercfg /SETACVALUEINDEX SCHEME_CURRENT 2a737441-1930-4402-8d77-b2bea1222653 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 0',
    "Enable Numlock on Boot": 'reg add "HKU\\.DEFAULT\\Control Panel\\Keyboard" /v InitialKeyboardIndicators /t REG_SZ /d 2 /f',
    "Disable Sticky Keys Prompt": 'reg add "HKCU\\Control Panel\\Accessibility\\StickyKeys" /v Flags /t REG_SZ /d 506 /f',
    "Enable Verbose Boot Messages": 'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v VerboseStatus /t REG_DWORD /d 1 /f'
}

# ==============================================================================
# --- UI COMPONENTS (DEEP DARK MODERN STYLED) ---
# ==============================================================================

class SidebarButton(QPushButton):
    """Custom stylized button for the side navigation."""
    def __init__(self, text, icon_char=""):
        super().__init__(text)
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        self.setFixedHeight(45)
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #ECECF1;
                border: none;
                border-radius: 6px;
                text-align: left;
                padding-left: 15px;
                font-family: 'Segoe UI', Inter, sans-serif;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2A2A2A;
            }
            QPushButton:checked {
                background-color: #212121;
                font-weight: bold;
            }
        """)

class ModernTitleBar(QWidget):
    """Custom title bar to replace the default Windows frame, keeping the dark aesthetic."""
    close_signal = Signal()
    minimize_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setStyleSheet("background-color: #171717; border-top-left-radius: 10px; border-top-right-radius: 10px;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 10, 0)
        
        # Title Label
        title_label = QLabel("JDR Optimizer")
        title_label.setStyleSheet("color: #ECECF1; font-family: 'Segoe UI'; font-size: 13px; font-weight: bold;")
        
        # Window Controls
        self.btn_min = QPushButton("—")
        self.btn_close = QPushButton("✕")
        
        for btn in [self.btn_min, self.btn_close]:
            btn.setFixedSize(30, 30)
            btn.setCursor(Qt.PointingHandCursor)
            
        self.btn_min.setStyleSheet("QPushButton { color: #ECECF1; border: none; background: transparent; border-radius: 4px; } QPushButton:hover { background-color: #2A2A2A; }")
        self.btn_close.setStyleSheet("QPushButton { color: #ECECF1; border: none; background: transparent; border-radius: 4px; } QPushButton:hover { background-color: #EF4444; color: white; }")
        
        self.btn_min.clicked.connect(self.minimize_signal.emit)
        self.btn_close.clicked.connect(self.close_signal.emit)

        self.parent = parent
        self.startPos = None

        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(self.btn_min)
        layout.addWidget(self.btn_close)

    # Enable window dragging from the custom title bar
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.startPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.startPos is not None:
            delta = event.globalPosition().toPoint() - self.startPos
            self.parent.move(self.parent.x() + delta.x(), self.parent.y() + delta.y())
            self.startPos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.startPos = None

# ==============================================================================
# --- MAIN APPLICATION WINDOW ---
# ==============================================================================

class JanithOptimizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.boot_time = psutil.boot_time() 
        
        # Window Configuration
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(900, 650)
        
        # Main Container (Deep Black/Dark Modern look)
        self.container = QFrame(self)
        self.container.setGeometry(0, 0, 900, 650)
        self.container.setStyleSheet("""
            QFrame#MainContainer {
                background-color: #212121;
                border: 1px solid #2F2F2F;
                border-radius: 10px;
            }
        """)
        self.container.setObjectName("MainContainer")
        
        main_v_layout = QVBoxLayout(self.container)
        main_v_layout.setContentsMargins(0, 0, 0, 0)
        main_v_layout.setSpacing(0)

        # 1. Custom Title Bar
        self.title_bar = ModernTitleBar(self)
        self.title_bar.close_signal.connect(self.close)
        self.title_bar.minimize_signal.connect(self.showMinimized)
        main_v_layout.addWidget(self.title_bar)

        # 2. Main Content Layout (Sidebar + Stacked Pages)
        content_h_layout = QHBoxLayout()
        content_h_layout.setContentsMargins(0, 0, 0, 0)
        content_h_layout.setSpacing(0)

        # --- SIDEBAR ---
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(220)
        self.sidebar.setStyleSheet("""
            QFrame {
                background-color: #171717;
                border-bottom-left-radius: 10px;
                border-right: 1px solid #2A2A2A;
            }
        """)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(5)

        # Navigation Buttons
        self.btn_dash = SidebarButton("Dashboard")
        self.btn_tweaks = SidebarButton("Advanced Tweaks")
        self.btn_settings = SidebarButton("Settings")
        self.btn_about = SidebarButton("About")
        
        # Set Dashboard as active initially
        self.btn_dash.setChecked(True)
        
        sidebar_layout.addWidget(self.btn_dash)
        sidebar_layout.addWidget(self.btn_tweaks)
        sidebar_layout.addWidget(self.btn_settings)
        sidebar_layout.addWidget(self.btn_about)
        sidebar_layout.addStretch()

        # Branding in Sidebar with clickable website link
        brand_label = QLabel(
            "Designed by<br>Janith Rathnayake<br>"
            "<a href='https://janidesh.pages.dev' style='color: #10A37F; text-decoration: none;'>janidesh.pages.dev</a>"
        )
        brand_label.setOpenExternalLinks(True)
        brand_label.setStyleSheet("color: #8E8EA0; font-size: 11px; text-align: center; margin-top: 10px;")
        brand_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(brand_label)

        content_h_layout.addWidget(self.sidebar)

        # --- STACKED WIDGET (Pages) ---
        self.stack = QStackedWidget()
        content_h_layout.addWidget(self.stack)
        main_v_layout.addLayout(content_h_layout)

        # Initialize Pages
        self.init_dashboard_page()
        self.init_tweaks_page()
        self.init_settings_page()
        self.init_about_page()

        # Connect Navigation
        self.btn_dash.clicked.connect(lambda: self.switch_page(0))
        self.btn_tweaks.clicked.connect(lambda: self.switch_page(1))
        self.btn_settings.clicked.connect(lambda: self.switch_page(2))
        self.btn_about.clicked.connect(lambda: self.switch_page(3))

        # --- SYSTEM TRAY SETUP ---
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
            
        tray_menu = QMenu()
        restore_action = tray_menu.addAction("Open Dashboard")
        restore_action.triggered.connect(self.showNormal)
        quit_action = tray_menu.addAction("Exit Completely")
        quit_action.triggered.connect(QApplication.instance().quit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        # Start Timers
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_live_stats)
        self.timer.start(1000)

        # 10-Minute Auto RAM Clean Timer
        self.auto_clean_timer = QTimer()
        self.auto_clean_timer.timeout.connect(OptimizationTools.clean_ram)
        self.auto_clean_timer.start(600000)

    def switch_page(self, index):
        """Switches the active page and handles button active states."""
        self.stack.setCurrentIndex(index)
        buttons = [self.btn_dash, self.btn_tweaks, self.btn_settings, self.btn_about]
        for i, btn in enumerate(buttons):
            btn.setChecked(i == index)

    # --- UI PAGE BUILDERS ---

    def init_dashboard_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(25)

        # Header Title
        header = QLabel("System Overview")
        header.setStyleSheet("color: #ECECF1; font-size: 28px; font-weight: bold; font-family: 'Segoe UI';")
        layout.addWidget(header)

        # Info Cards Area
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)

        # RAM Card
        self.ram_card, self.ram_bar, self.ram_val = self.create_chatgpt_stat_card("Memory Usage")
        # CPU Card
        self.cpu_card, self.cpu_bar, self.cpu_val = self.create_chatgpt_stat_card("Processor Load")

        cards_layout.addWidget(self.ram_card)
        cards_layout.addWidget(self.cpu_card)
        layout.addLayout(cards_layout)

        # Live Text Stats
        stats_h_layout = QHBoxLayout()
        self.lbl_procs = QLabel("Active Processes: --")
        self.lbl_uptime = QLabel("System Uptime: --:--:--")
        stat_style = "color: #C5C5D2; font-size: 14px; font-family: 'Segoe UI';"
        self.lbl_procs.setStyleSheet(stat_style)
        self.lbl_uptime.setStyleSheet(stat_style)
        self.lbl_uptime.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        stats_h_layout.addWidget(self.lbl_procs)
        stats_h_layout.addWidget(self.lbl_uptime)
        layout.addLayout(stats_h_layout)

        layout.addStretch()

        # Action Buttons
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(15)

        self.opt_btn = QPushButton("Boost System Performance")
        self.opt_btn.setCursor(Qt.PointingHandCursor)
        self.opt_btn.setFixedHeight(50)
        self.opt_btn.setStyleSheet("""
            QPushButton {
                background-color: #10A37F; color: white; border-radius: 6px;
                font-family: 'Segoe UI'; font-size: 15px; font-weight: bold; border: none;
            }
            QPushButton:hover { background-color: #1A7F64; }
        """)
        self.opt_btn.clicked.connect(self.run_optimization)

        self.kill_btn = QPushButton("Terminate Hung Applications")
        self.kill_btn.setCursor(Qt.PointingHandCursor)
        self.kill_btn.setFixedHeight(50)
        self.kill_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #EF4444; border-radius: 6px;
                font-family: 'Segoe UI'; font-size: 15px; font-weight: bold; border: 1px solid #EF4444;
            }
            QPushButton:hover { background-color: rgba(239, 68, 68, 0.1); }
        """)
        self.kill_btn.clicked.connect(self.run_kill_switch)

        actions_layout.addWidget(self.opt_btn)
        actions_layout.addWidget(self.kill_btn)
        layout.addLayout(actions_layout)

        self.stack.addWidget(page)

    def create_chatgpt_stat_card(self, title):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #2F2F2F;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #ECECF1; font-size: 16px; font-weight: bold; border: none;")
        
        lbl_val = QLabel("0%")
        lbl_val.setStyleSheet("color: #10A37F; font-size: 24px; font-weight: bold; border: none;")
        lbl_val.setAlignment(Qt.AlignRight)

        top_row = QHBoxLayout()
        top_row.addWidget(lbl_title)
        top_row.addWidget(lbl_val)

        bar = QProgressBar()
        bar.setFixedHeight(8)
        bar.setTextVisible(False)
        bar.setStyleSheet("""
            QProgressBar { background: #171717; border-radius: 4px; border: none; }
            QProgressBar::chunk { background-color: #10A37F; border-radius: 4px; }
        """)

        layout.addLayout(top_row)
        layout.addWidget(bar)
        return card, bar, lbl_val

    def init_tweaks_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        header = QLabel("Advanced Registry & Command Tweaks")
        header.setStyleSheet("color: #ECECF1; font-size: 22px; font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(header)
        
        warning = QLabel("⚠ Please proceed with caution and understanding before applying these system tweaks.")
        warning.setStyleSheet("color: #F59E0B; font-size: 13px; font-style: italic; margin-bottom: 10px;")
        layout.addWidget(warning)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { background: #171717; width: 10px; margin: 0px; }
            QScrollBar::handle:vertical { background: #424242; min-height: 20px; border-radius: 5px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        grid = QGridLayout(container)
        grid.setSpacing(10)

        row, col = 0, 0
        for tweak_name, tweak_cmd in SYSTEM_TWEAKS.items():
            btn = QPushButton(tweak_name)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(45)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2F2F2F; color: #ECECF1; border: 1px solid #424242;
                    border-radius: 6px; padding: 0 15px; text-align: left; font-family: 'Segoe UI'; font-size: 13px;
                }
                QPushButton:hover { background-color: #424242; border-color: #10A37F; }
            """)
            btn.clicked.connect(lambda checked=False, cmd=tweak_cmd, b=btn: self.execute_ui_tweak(cmd, b))
            
            grid.addWidget(btn, row, col)
            col += 1
            if col > 1: # 2 Columns
                col = 0
                row += 1

        scroll.setWidget(container)
        layout.addWidget(scroll)
        self.stack.addWidget(page)

    def init_settings_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        header = QLabel("Application Settings")
        header.setStyleSheet("color: #ECECF1; font-size: 28px; font-weight: bold; font-family: 'Segoe UI';")
        layout.addWidget(header)

        desc = QLabel("Customize how JDR Optimizer integrates with Windows.")
        desc.setStyleSheet("color: #8E8EA0; font-size: 14px;")
        layout.addWidget(desc)

        # Settings Container
        settings_frame = QFrame()
        settings_frame.setStyleSheet("""
            QFrame { background-color: #2F2F2F; border-radius: 8px; }
            QCheckBox { color: #ECECF1; font-size: 16px; font-family: 'Segoe UI'; spacing: 15px; }
            QCheckBox::indicator { width: 24px; height: 24px; border-radius: 4px; border: 2px solid #424242; background: #171717; }
            QCheckBox::indicator:checked { background: #10A37F; border-color: #10A37F; image: url(); }
        """)
        sf_layout = QVBoxLayout(settings_frame)
        sf_layout.setContentsMargins(25, 25, 25, 25)
        sf_layout.setSpacing(25)

        # 1. Startup Checkbox
        self.chk_startup = QCheckBox("Run on Windows Startup (Hidden in Tray)")
        self.chk_startup.setCursor(Qt.PointingHandCursor)
        self.chk_startup.setChecked(OptimizationTools.is_startup_enabled())
        self.chk_startup.toggled.connect(self.handle_startup_toggle)
        
        # 2. Context Menu Checkbox
        self.chk_context = QCheckBox("Add to Desktop Right-Click (Context) Menu")
        self.chk_context.setCursor(Qt.PointingHandCursor)
        self.chk_context.setChecked(OptimizationTools.is_context_menu_enabled())
        self.chk_context.toggled.connect(self.handle_context_toggle)

        sf_layout.addWidget(self.chk_startup)
        sf_layout.addWidget(self.chk_context)
        
        layout.addWidget(settings_frame)
        layout.addStretch()

        self.stack.addWidget(page)

    def init_about_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        header = QLabel("About JDR Optimizer")
        header.setStyleSheet("color: #ECECF1; font-size: 28px; font-weight: bold; font-family: 'Segoe UI';")
        layout.addWidget(header)

        # About Container
        about_frame = QFrame()
        about_frame.setStyleSheet("""
            QFrame { background-color: #2F2F2F; border-radius: 8px; }
        """)
        af_layout = QVBoxLayout(about_frame)
        af_layout.setContentsMargins(30, 30, 30, 30)
        af_layout.setSpacing(20)

        praise_label = QLabel(
            "<b>Designed & Developed solely by Janith Rathnayake</b><br><br>"
            "This application was built entirely from scratch By me to provide a powerful, modern, "
            "and sleek system optimization tool. Its development was heavily debugged by cutting-edge "
            "AI technologies, including <b>Gemma 4 e4B models</b>, <b>Ollama Qwen3.5 9B</b>, and AI models such as <b>Nemotron 3 nano 4B</b>, "
            "which helped architect its pristine object-oriented structure and user interface."
        )
        praise_label.setWordWrap(True)
        praise_label.setStyleSheet("color: #ECECF1; font-size: 15px; line-height: 1.5;")

        license_label = QLabel(
            "<b>License:</b> MIT License<br>"
            "<b>Copyright:</b> © 2026 by Janith Rathnayake. All rights reserved.<br><br>"
            "To get in touch, provide feedback, or explore more of my work, please visit my website: "
            "<a href='https://janidesh.pages.dev' style='color: #10A37F; text-decoration: none;'>janidesh.pages.dev</a>"
        )
        license_label.setOpenExternalLinks(True)
        license_label.setWordWrap(True)
        license_label.setStyleSheet("color: #C5C5D2; font-size: 14px; line-height: 1.5;")

        disclaimer_label = QLabel(
            "<b>⚠ IMPORTANT DISCLAIMER:</b><br>"
            "By using this software, you acknowledge and agree that Janith Rathnayake assumes zero responsibility "
            "or liability for any direct or indirect damage, data loss, software corruption, or hardware malfunctions "
            "that may occur. These advanced system tweaks modify critical operating system settings. "
            "<b>You are using this tool entirely at your own risk.</b>"
        )
        disclaimer_label.setWordWrap(True)
        disclaimer_label.setStyleSheet("""
            color: #EF4444; 
            font-size: 14px; 
            background-color: rgba(239, 68, 68, 0.1); 
            padding: 15px; 
            border: 1px solid #EF4444;
            border-radius: 6px;
        """)

        af_layout.addWidget(praise_label)
        af_layout.addWidget(license_label)
        af_layout.addWidget(disclaimer_label)
        
        layout.addWidget(about_frame)
        layout.addStretch()

        self.stack.addWidget(page)

    # --- LOGIC HANDLERS ---

    def handle_startup_toggle(self, state):
        success = OptimizationTools.toggle_startup(state)
        if not success:
            self.chk_startup.blockSignals(True)
            self.chk_startup.setChecked(not state)
            self.chk_startup.blockSignals(False)

    def handle_context_toggle(self, state):
        success = OptimizationTools.toggle_context_menu(state)
        if not success:
            self.chk_context.blockSignals(True)
            self.chk_context.setChecked(not state)
            self.chk_context.blockSignals(False)

    def update_live_stats(self):
        ram = psutil.virtual_memory().percent
        cpu = psutil.cpu_percent()
        
        self.ram_val.setText(f"{ram}%")
        self.cpu_val.setText(f"{cpu}%")
        self.ram_bar.setValue(int(ram))
        self.cpu_bar.setValue(int(cpu))
        
        # Dynamic color changing for high usage
        for bar, val in [(self.ram_bar, ram), (self.cpu_bar, cpu)]:
            color = "#10A37F" if val < 75 else ("#F59E0B" if val < 90 else "#EF4444")
            bar.setStyleSheet(f"QProgressBar {{ background: #171717; border-radius: 4px; border: none; }} QProgressBar::chunk {{ background-color: {color}; border-radius: 4px; }}")
            
        procs = len(psutil.pids())
        uptime_seconds = time.time() - self.boot_time
        uptime_string = time.strftime("%H:%M:%S", time.gmtime(uptime_seconds))
        
        self.lbl_procs.setText(f"Active Processes: {procs}")
        self.lbl_uptime.setText(f"System Uptime: {uptime_string}")

    def run_optimization(self):
        original_text = self.opt_btn.text()
        self.opt_btn.setText("Optimizing Memory...")
        self.opt_btn.setEnabled(False)
        QApplication.processEvents()
        
        cleaned = OptimizationTools.clean_ram()
        
        self.opt_btn.setText(f"Successfully Cleared {cleaned} Processes!")
        self.opt_btn.setStyleSheet(self.opt_btn.styleSheet().replace("background-color: #10A37F;", "background-color: #3B82F6;"))
        
        QTimer.singleShot(2500, lambda: (
            self.opt_btn.setText(original_text),
            self.opt_btn.setEnabled(True),
            self.opt_btn.setStyleSheet(self.opt_btn.styleSheet().replace("background-color: #3B82F6;", "background-color: #10A37F;"))
        ))

    def run_kill_switch(self):
        original_text = self.kill_btn.text()
        self.kill_btn.setText("Scanning for Hung Apps...")
        self.kill_btn.setEnabled(False)
        QApplication.processEvents()
        
        OptimizationTools.kill_not_responding()
        
        self.kill_btn.setText("Hung Applications Terminated.")
        QTimer.singleShot(2500, lambda: (
            self.kill_btn.setText(original_text),
            self.kill_btn.setEnabled(True)
        ))

    def execute_ui_tweak(self, command, button):
        original_text = button.text()
        button.setText("Applying Tweak...")
        QApplication.processEvents()
        
        success = OptimizationTools.execute_tweak(command)
        
        if success:
            button.setText("✓ Tweak Applied")
            button.setStyleSheet(button.styleSheet().replace("color: #ECECF1;", "color: #10A37F; border-color: #10A37F;"))
        else:
            button.setText("✗ Tweak Failed")
            button.setStyleSheet(button.styleSheet().replace("color: #ECECF1;", "color: #EF4444; border-color: #EF4444;"))
            
        # Revert UI state after 2 seconds
        QTimer.singleShot(2000, lambda: (
            button.setText(original_text), 
            button.setStyleSheet(button.styleSheet()
                .replace("color: #10A37F; border-color: #10A37F;", "color: #ECECF1;")
                .replace("color: #EF4444; border-color: #EF4444;", "color: #ECECF1;"))
        ))

    # Overwrite close event to minimize to tray
    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "JDR PC Optimizer",
            "Running securely in the background. Auto-RAM clear is active.",
            QSystemTrayIcon.Information,
            3000
        )


# ==============================================================================
# --- MODERN DEEP DARK SPLASH SCREEN & BOOTSTRAP ---
# ==============================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Clean Deep Dark Splash Screen
    splash_pix = QPixmap(500, 300)
    splash_pix.fill(Qt.transparent)
    
    painter = QPainter(splash_pix)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Base Box
    painter.setBrush(QColor("#171717"))
    painter.setPen(QPen(QColor("#2F2F2F"), 2))
    painter.drawRoundedRect(5, 5, 490, 290, 15, 15)
    
    # Title Text
    painter.setPen(QColor("#ECECF1"))
    painter.setFont(QFont("Segoe UI", 24, QFont.Bold))
    painter.drawText(splash_pix.rect().adjusted(0, -20, 0, 0), Qt.AlignCenter, "JDR SYSTEM OPTIMIZER")
    
    # Accent Text
    painter.setPen(QColor("#10A37F"))
    painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
    painter.drawText(splash_pix.rect().adjusted(0, 30, 0, 0), Qt.AlignCenter, "MODERN ENGINE V2")

    # Loading Text
    painter.setPen(QColor("#8E8EA0"))
    painter.setFont(QFont("Segoe UI", 10))
    painter.drawText(splash_pix.rect().adjusted(0, 100, 0, 0), Qt.AlignCenter, "Loading Modules & Core Settings...")
    
    # Creator Text
    painter.setPen(QColor("#565869"))
    painter.setFont(QFont("Segoe UI", 9))
    painter.drawText(splash_pix.rect().adjusted(0, 130, 0, 0), Qt.AlignCenter, "Janith Rathnayake Creations")
    
    painter.end()

    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
    splash.setAttribute(Qt.WA_TranslucentBackground)
    splash.show()
    
    QApplication.processEvents()
    time.sleep(1.2) 
    
    main_win = JanithOptimizer()
    main_win.show()
    splash.finish(main_win)
    
    sys.exit(app.exec())