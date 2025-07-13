import sys
import os
import json
import subprocess
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from .control_center import ControlCenter # import the control center

# determine root dir and important dir
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GADGETS_DIR = os.path.join(ROOT_DIR, 'gadgets')
CONFIG_DIR = os.path.join(ROOT_DIR, 'config')
SESSION_FILE = os.path.join(CONFIG_DIR, 'session.json')
DEFAULT_ICON = os.path.join(os.path.dirname(__file__), 'assets', 'icon.png')

class GadgetManager:
    def __init__(self):
        self.app = QApplication(sys.argv)
        # prevent app exit when no window
        self.app.setQuitOnLastWindowClosed(False)

        os.makedirs(CONFIG_DIR, exist_ok=True)

        self.running_gadgets = {}  # { 'gadget_id': process_object }

        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setIcon(QIcon(DEFAULT_ICON))
        self.tray_icon.setToolTip("Gadget System Framework")
        self.tray_icon.setVisible(True)

        self.setup_tray_menu()
        self.load_session()
        
        self.control_center_window = None

    def setup_tray_menu(self):
        menu = QMenu()
        open_center_action = menu.addAction("Open Control Center")
        open_center_action.triggered.connect(self.show_control_center)
        
        add_gadget_menu = menu.addMenu("Add Gadget")
        self.discover_gadgets(add_gadget_menu)
        
        menu.addSeparator()
        
        quit_action = menu.addAction("Exit")
        quit_action.triggered.connect(self.quit_framework)
        
        self.tray_icon.setContextMenu(menu)

    def discover_gadgets(self, menu):
        for name in os.listdir(GADGETS_DIR):
            gadget_path = os.path.join(GADGETS_DIR, name)
            manifest_path = os.path.join(gadget_path, 'gadget.json')
            
            if os.path.isdir(gadget_path) and os.path.exists(manifest_path):
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                
                action = QAction(manifest.get('name', name), self.app)
                action.triggered.connect(
                    lambda checked=False, p=gadget_path, n=name: self.launch_gadget(p, n)
                )
                menu.addAction(action)
                
    def show_control_center(self):
        """create and show control center window"""
        if not self.control_center_window:
            self.control_center_window = ControlCenter(GADGETS_DIR, self.running_gadgets)
            # connect control center signal to manager
            self.control_center_window.request_launch_gadget.connect(self.launch_gadget)
            self.control_center_window.request_terminate_gadget.connect(self.terminate_gadget)
            # when control center closed，make reference to None，to make it can recreate next time
            self.control_center_window.setAttribute(Qt.WA_DeleteOnClose)
            self.control_center_window.destroyed.connect(lambda: setattr(self, 'control_center_window', None))

        self.control_center_window.show()
        self.control_center_window.activateWindow() # 激活窗口

    def launch_gadget(self, gadget_path, gadget_id):
        if gadget_id in self.running_gadgets and self.running_gadgets[gadget_id].poll() is None:
            print(f"Gadget {gadget_id} has already running。")
            return

        manifest_path = os.path.join(gadget_path, 'gadget.json')
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        entry_point = os.path.join(gadget_path, manifest['entry_point'])
        
        # Start gadget process，and press the dir as argument to it
        process = subprocess.Popen([sys.executable, entry_point, gadget_path])
        self.running_gadgets[gadget_id] = process
        print(f"Running gadget: {gadget_id}")
        
        self.update_ui_status()

    def save_session(self):
        # only save the gadget process id list which are running
        active_gadgets = [
            gid for gid, proc in self.running_gadgets.items() if proc.poll() is None
        ]
        session_data = {"active_gadgets": active_gadgets}
        with open(SESSION_FILE, 'w') as f:
            json.dump(session_data, f)
        print("session has been saved。")

    def load_session(self):
        if not os.path.exists(SESSION_FILE):
            return
        try:
            with open(SESSION_FILE, 'r') as f:
                session_data = json.load(f)
            
            for gadget_id in session_data.get("active_gadgets", []):
                gadget_path = os.path.join(GADGETS_DIR, gadget_id)
                if os.path.exists(gadget_path):
                    self.launch_gadget(gadget_path, gadget_id)
        except (json.JSONDecodeError, FileNotFoundError):
            print("Cannot load the session file.")

    def terminate_gadget(self, gadget_id):
        """stop specific gadget func"""
        if gadget_id in self.running_gadgets:
            process = self.running_gadgets[gadget_id]
            if process.poll() is None: # process still running
                process.terminate()
                process.wait() # Wait process to end
                print(f"Gadget has been stopped: {gadget_id}")
            # remove from gadget dic
            del self.running_gadgets[gadget_id]
            # update UI
            self.update_ui_status()

    def update_ui_status(self):
        """if control center opened，then update its status"""
        if self.control_center_window:
            self.control_center_window.update_status(self.running_gadgets)

    def quit_framework(self):
        self.save_session()
        
        for gadget_id in list(self.running_gadgets.keys()):
            self.terminate_gadget(gadget_id)
        
        self.app.quit()

    def run(self):
        sys.exit(self.app.exec())