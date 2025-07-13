import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os
from PIL import Image
from pystray import Icon as TrayIcon, Menu, MenuItem

from main_manager import GadgetManagerLogic

APP_NAME = "GSF"
APP_DATA_PATH = os.path.join(os.getenv('APPDATA'), APP_NAME)
GADGETS_DIR = os.path.join(APP_DATA_PATH, 'gadgets')

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
        """当服务被停止时调用"""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        if self.tray_icon:
            self.tray_icon.stop()
        if self.manager_logic:
            self.manager_logic.quit_framework()
        win32event.SetEvent(self.hWaitStop)
        self.is_running = False

    def SvcDoRun(self):
        """当服务启动时调用，这是服务的主循环"""
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        self.main()

    def main(self):
        """服务的主要逻辑"""
        self.is_running = True
        
        self.manager_logic = GadgetManagerLogic(GADGETS_DIR)
        
        image = Image.open(os.path.join(os.path.dirname(__file__), 'assets', 'icon.png'))
        menu = Menu(
            MenuItem('Open Control Center...', self.show_control_center, default=True),
            MenuItem('Exit GSF', self.on_quit)
        )
        self.tray_icon = TrayIcon("Gadget System Framework", image, self._svc_display_name_, menu)
        
        self.tray_icon.run_detached()

        while self.is_running:
            win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)

    def show_control_center(self):
        """通过子进程启动管理中心UI"""
        
        control_center_script = os.path.join(os.path.dirname(__file__), 'control_center_runner.py')
        subprocess.Popen([sys.executable, control_center_script])

    def on_quit(self):
        self.SvcStop()

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(GSFService)