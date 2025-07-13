import sys
import os
import json
import subprocess
from threading import Timer
from PySide6.QtWidgets import *
from PySide6.QtGui import *

# Define app name which used as folder name
APP_NAME = "Gadget System Framework"

# Get the user-specific Application Data Dir
APP_DATA_PATH = os.path.join(os.getenv('APPDATA'), APP_NAME)

# Define all important sub dirs
GADGETS_DIR = os.path.join(APP_DATA_PATH, 'gadgets')
CONFIG_DIR = os.path.join(APP_DATA_PATH, 'config')
SESSION_FILE = os.path.join(CONFIG_DIR, 'session.json')
DEFAULT_ICON = os.path.join(os.path.dirname(__file__), 'assets', 'icon.png')

# --- Key Step：make sure these dirs exist ---
def ensure_gsf_dirs_exist():
    """Call when app started to make sure all necessary dirs has been created"""
    print(f"GSF Home Directory: {APP_DATA_PATH}")
    os.makedirs(GADGETS_DIR, exist_ok=True)
    os.makedirs(CONFIG_DIR, exist_ok=True)

def main():
    """Application entry point."""
    print("Starting Gadget System Framework (GSF)...")
    # QApplication must be created here
    app = QApplication(sys.argv)
    manager = GadgetManager(app) # push app instance
    sys.exit(manager.run())

class GadgetManagerLogic:
    """
    GSF core logic controller，no any GUI
    which can be instance by service or any background threads safely
    """
    def __init__(self):
        print("Initializing GadgetManagerLogic...")
        ensure_gsf_dirs_exist()
        
        self.gadgets_dir = GADGETS_DIR
        self.session_file = SESSION_FILE
        self.running_gadgets = {}  # { 'gadget_id': subprocess.Popen object }
        
        # Timer for polling
        self.status_poll_timer = None
        self.on_status_change = None # callback，for notifying external changes

        self.load_session()

    def set_status_change_callback(self, callback):
        """setup a callback func, called when gadget status changed"""
        self.on_status_change = callback
        self.start_polling()

    def start_polling(self):
        """Start check gadget process status"""
        # Check process whether exit accidently
        for gadget_id, process in list(self.running_gadgets.items()):
            if process.poll() is not None: # process has ended
                print(f"Gadget '{gadget_id}' terminated unexpectedly.")
                del self.running_gadgets[gadget_id]
                if self.on_status_change:
                    self.on_status_change()
        
        # check every 5 seconds
        self.status_poll_timer = Timer(5.0, self.start_polling)
        self.status_poll_timer.daemon = True # Make sure all threads exited when main app exits
        self.status_poll_timer.start()

    def discover_gadgets(self):
        """
        Scan gadgets dir and return a list which contain gadget information
        Return: [{'id': str, 'path': str, 'manifest': dict}, ...]
        """
        discovered = []
        if not os.path.exists(self.gadgets_dir):
            return discovered

        for name in sorted(os.listdir(self.gadgets_dir)):
            gadget_path = os.path.join(self.gadgets_dir, name)
            manifest_path = os.path.join(gadget_path, 'gadget.json')
            
            if os.path.isdir(gadget_path) and os.path.exists(manifest_path):
                try:
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        manifest = json.load(f)
                    discovered.append({
                        'id': name,
                        'path': gadget_path,
                        'manifest': manifest
                    })
                except Exception as e:
                    print(f"Error reading manifest for {name}: {e}")
        return discovered

    def get_running_gadgets_info(self):
        """return current running gadget information, for UI using"""
        # cleanup the ended process
        active_pids = {p.pid for p in self.running_gadgets.values() if p.poll() is None}
        return {
            gid: proc for gid, proc in self.running_gadgets.items() 
            if proc.pid in active_pids
        }

    def launch_gadget(self, gadget_path, gadget_id):
        """start a gadget sub-process"""
        if gadget_id in self.running_gadgets and self.running_gadgets[gadget_id].poll() is None:
            print(f"Gadget {gadget_id} is already running.")
            return

        manifest_path = os.path.join(gadget_path, 'gadget.json')
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
        except Exception as e:
            print(f"Cannot launch {gadget_id}, manifest error: {e}")
            return
        
        entry_point = os.path.join(gadget_path, manifest.get('entry_point', 'main.py'))
        
        if not os.path.exists(entry_point):
            print(f"Error: Entry point not found for {gadget_id} at {entry_point}")
            return

        # Use sys.executable to make sure use the current environment python interpreter
        process = subprocess.Popen([sys.executable, entry_point, gadget_path])
        self.running_gadgets[gadget_id] = process
        print(f"Launched gadget: {gadget_id} with PID: {process.pid}")

        if self.on_status_change:
            self.on_status_change()

    def terminate_gadget(self, gadget_id):
        """stop a gadget process"""
        if gadget_id in self.running_gadgets:
            process = self.running_gadgets[gadget_id]
            if process.poll() is None:
                process.terminate()
                try:
                    # wait most 3 seconds, timeout then continue
                    process.wait(timeout=3)
                    print(f"Terminated gadget: {gadget_id}")
                except subprocess.TimeoutExpired:
                    print(f"Gadget {gadget_id} did not terminate gracefully, killing.")
                    process.kill()
            
            del self.running_gadgets[gadget_id]
            
            if self.on_status_change:
                self.on_status_change()
        else:
            print(f"Cannot terminate: Gadget {gadget_id} not found in running list.")

    def save_session(self):
        """save the session (current running gadget list) to file"""
        active_gadgets = list(self.get_running_gadgets_info().keys())
        session_data = {"active_gadgets": active_gadgets}
        try:
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f, indent=4)
            print("Session saved.")
        except Exception as e:
            print(f"Error saving session: {e}")

    def load_session(self):
        """load session from session and start the gadget run before"""
        if not os.path.exists(self.session_file):
            print("No session file found, starting fresh.")
            return
        try:
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)
            
            print(f"Loading session, active gadgets: {session_data.get('active_gadgets', [])}")
            all_gadgets = {g['id']: g['path'] for g in self.discover_gadgets()}
            for gadget_id in session_data.get("active_gadgets", []):
                if gadget_id in all_gadgets:
                    self.launch_gadget(all_gadgets[gadget_id], gadget_id)
                else:
                    print(f"Gadget '{gadget_id}' from session not found in installed gadgets.")
        except Exception as e:
            print(f"Error loading session: {e}")

    def quit_framework(self):
        """cleanup and close framework"""
        print("Quitting framework logic...")
        self.save_session()
        if self.status_poll_timer:
            self.status_poll_timer.cancel()
        
        for gadget_id in list(self.running_gadgets.keys()):
            self.terminate_gadget(gadget_id)
        print("Framework logic shutdown complete.")


class GadgetManager:
    def __init__(self, app):
        
        ensure_gsf_dirs_exist()
        
        self.app = app
        # prevent app exit when no window
        self.app.setQuitOnLastWindowClosed(False)

        os.makedirs(CONFIG_DIR, exist_ok=True)

        self.running_gadgets = {}  # { 'gadget_id': process_object }

        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setIcon(QIcon(DEFAULT_ICON))
        self.tray_icon.setToolTip("Gadget System Framework")
        self.tray_icon.setVisible(True)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

        self.setup_tray_menu()
        self.load_session()
        
        self.control_center_window = None
    
    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_control_center()
    
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
        self.control_center_window.activateWindow() # Activate window

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