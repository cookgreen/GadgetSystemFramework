import win32serviceutil
import win32service
import win32event
import win32api
import win32con
import servicemanager
import socket
import sys
import os
import threading
import subprocess
import logging
from logging.handlers import RotatingFileHandler
from PIL import Image
from pystray import Icon as TrayIcon, Menu, MenuItem
from PySide6.QtWidgets import QApplication

image_path = os.path.join(os.path.dirname(__file__), 'assets', 'icon.ico')

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
    image_path = os.path.join(application_path, 'gsf', 'assets', 'icon.ico')
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.abspath(os.path.join(application_path, '..')))

from gsf.main_manager import GadgetManagerLogic, ensure_gsf_dirs_exist, APP_DATA_PATH
from gsf.control_center_logic import ControlCenter

APP_NAME = "GSF"
APP_DATA_PATH = os.path.join(os.getenv('APPDATA'), APP_NAME)
GADGETS_DIR = os.path.join(APP_DATA_PATH, 'gadgets')

LOG_FILE = os.path.join(APP_DATA_PATH, 'gsf_service.log')
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True) 

logger = logging.getLogger('GSFLogger')
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(process)d - %(threadName)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

class GSFService(win32serviceutil.ServiceFramework):
    _svc_name_ = "GSF-Service"
    _svc_display_name_ = "Gadget System Framework Service"
    _svc_description_ = "Manages and runs GSF desktop gadgets."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        
        self.is_running = False
        self.tray_icon = None
        self.manager_logic = None
        self.worker_thread = None
        logger.info(f"GSFService object created with args: {args}")

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, servicemanager.PYS_SERVICE_STARTED, (self._svc_name_, ''))
        
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        self.is_running = True
        
        self.worker_thread = threading.Thread(target=self.main_worker, name="GSF_WorkerThread")
        self.worker_thread.daemon = True
        self.worker_thread.start()
        
        logger.info("Service is running, worker thread dispatched.")
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
        logger.info("SvcDoRun loop exited.")

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        
        logger.info("Service stop requested.")
        
        self.is_running = False
        
        if self.tray_icon:
            self.tray_icon.stop()
            logger.info("Tray icon stop signal sent.")
        
        win32event.SetEvent(self.hWaitStop)
        
        if self.worker_thread and self.worker_thread.is_alive():
            logger.info("Waiting for worker thread to finish...")
            self.worker_thread.join(timeout=10)
            if self.worker_thread.is_alive():
                logger.warning("Worker thread did not exit gracefully.")
            else:
                logger.info("Worker thread finished.")
        
        logger.info("Service stopped.")
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def main_worker(self):
        logger.info("Worker thread started.")
        try:
            logger.info("Ensuring GSF directories exist...")
            ensure_gsf_dirs_exist()
            logger.info("Directories checked/created.")

            logger.info("Initializing GadgetManagerLogic...")
            self.manager_logic = GadgetManagerLogic()
            logger.info("GadgetManagerLogic initialized successfully.")

            logger.info("Preparing to create tray icon...")

            logger.info(f"Attempting to load icon from: {image_path}")
            if not os.path.exists(image_path):
                logger.error(f"Icon file not found at {image_path}!")
                raise FileNotFoundError(f"Icon file not found: {image_path}")
            
            image = Image.open(image_path)
            menu = Menu(
                MenuItem('Open Control Center...', self.show_control_center, default=True),
                MenuItem('Exit', self.on_quit)
            )
            self.tray_icon = TrayIcon("GSF", image, self._svc_display_name_, menu)
            
            logger.info("Tray icon created. Starting its run loop...")
            self.tray_icon.run()
            logger.info("Tray icon run loop finished.")

        except Exception:
            logger.exception("FATAL ERROR in worker thread. Thread is terminating.")
        finally:
            logger.info("Worker thread is exiting. Performing cleanup...")
            if self.manager_logic:
                self.manager_logic.quit_framework()
            logger.info("Cleanup complete.")

    def show_control_center(self):
        logger.info("Request to show control center.")
        try:
            command_to_run = []
    
            if getattr(sys, 'frozen', False):
                launcher_path = sys.executable
                command_to_run = [launcher_path, "launch_ui"]
            else:
                python_exe = "python" 
                script_path = os.path.abspath(__file__)
                
                command_to_run = [python_exe, script_path, "launch_ui"]
    
            logger.info(f"Launching UI with command: {command_to_run}")
            subprocess.Popen(command_to_run)
            logger.info("Control Center launch command sent.")
    
        except Exception:
            logger.exception("Failed to launch Control Center.")
            if self.tray_icon:
                self.tray_icon.notify("Cannot start the control center.\nPlease check log to get details", "Error")

    def on_quit(self):
        logger.info("Quit requested from tray menu. Stopping service...")
        self.SvcStop()

def run_control_center_ui():
    logger.info("UI process started.")
    try:
        app = QApplication(sys.argv)
        window = ControlCenter()
        window.show()
        sys.exit(app.exec())
    except Exception:
        logger.exception("FATAL ERROR in Control Center UI process.")
        sys.exit(1)

if __name__ == '__main__':
    logger.info(f"Script launched with args: {sys.argv}")

    if len(sys.argv) == 1:
        win32serviceutil.HandleCommandLine(GSFService)
    else:
        command = sys.argv[1].lower()
        if command == 'launch_ui':
            run_control_center_ui()
            sys.exit()
        
        win32serviceutil.HandleCommandLine(GSFService)