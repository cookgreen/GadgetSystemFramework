import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os
import threading

from PIL import Image
from pystray import Icon as TrayIcon, Menu, MenuItem

image_path = os.path.join(os.path.dirname(__file__), 'assets', 'icon.ico')

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
    image_path = os.path.join(application_path, 'gsf', 'assets', 'icon.ico')
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.abspath(os.path.join(application_path, '..')))

from gsf.main_manager import GadgetManagerLogic

APP_NAME = "GSF"
APP_DATA_PATH = os.path.join(os.getenv('APPDATA'), APP_NAME)
GADGETS_DIR = os.path.join(APP_DATA_PATH, 'gadgets')

import logging
from logging.handlers import RotatingFileHandler

LOG_FILE = os.path.join(APP_DATA_PATH, 'gsf_service.log')
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logger = logging.getLogger('GSFLogger')
logger.setLevel(logging.DEBUG)
if not logger.handlers: 
    handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(process)d - %(threadName)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class GSFService(win32serviceutil.ServiceFramework):
    _svc_name_ = "GSF-Service"
    _svc_display_name_ = "Gadget System Framework Service"
    _svc_description_ = "Manages and runs GSF-based desktop gadgets."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.is_running = False
        self.tray_icon = None
        self.manager_logic = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        logger.info("Service stop requested.")
        
        self.is_running = False
        
        if self.tray_icon:
            self.tray_icon.stop()
            logger.info("Tray icon stopped.")

        win32event.SetEvent(self.hWaitStop)
        
        if self.worker_thread and self.worker_thread.is_alive():
            logger.info("Waiting for worker thread to finish...")
            self.worker_thread.join(timeout=10)
            if self.worker_thread.is_alive():
                logger.warning("Worker thread did not exit gracefully.")

        logger.info("Service stopped.")
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        
        self.is_running = True
        self.worker_thread = threading.Thread(target=self.main_worker)
        self.worker_thread.daemon = True
        self.worker_thread.start()
        
        logger.info("Service is running, worker thread started.")
        
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
        logger.info("SvcDoRun loop exited.")
        
    def main_worker(self):
        try:
            logger.info("Worker thread started. Initializing logic...")

            self.manager_logic = GadgetManagerLogic()
            logger.info("GadgetManagerLogic initialized.")

            image = Image.open(image_path)
            menu = Menu(
                MenuItem('Open Control Center...', self.show_control_center, default=True),
                MenuItem('Exit GSF', self.on_quit)
            )
            self.tray_icon = TrayIcon("GSF", image, self._svc_display_name_, menu)
            
            logger.info("Starting tray icon...")
            self.tray_icon.run()

            logger.info("Tray icon run loop finished. Worker thread is exiting.")

        except Exception as e:
            logger.exception("FATAL ERROR in worker thread. Service will be unstable.")

        if self.manager_logic:
            self.manager_logic.quit_framework()

    def show_control_center(self):
        logger.info("Request to show control center.")
        try:
            import subprocess
            subprocess.Popen([sys.executable, control_center_runner.__file__])
        except Exception as e:
            logger.exception("Failed to launch Control Center.")

    def on_quit(self):
        logger.info("Quit requested from tray menu.")
        self.SvcStop()

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(GSFService)